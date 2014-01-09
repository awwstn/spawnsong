from __future__ import absolute_import
import subprocess
from django.conf import settings
import tempfile
import shutil
import logging
import os
from django.core.files import File
import requests
import time
from django.db import transaction
from celery.utils.log import get_task_logger
from celery.utils import gen_task_name
from mail_templated import EmailMessage
import datetime
import itertools

from sites.spawnsongsite.celery import app
from . import models

logger = get_task_logger("spawnsong.tasks")

# Decorator to handle errors and retries

def snippet_processing_task(max_retries=3, retry_delay=30):
    def _decorator(task_fn):
        @app.task(name=gen_task_name(app, task_fn.__name__, task_fn.__module__))
        def _task(snippet_id, *args, **kwargs):
            retry_number = kwargs.pop('retry_number', 0)
            try:
                snippet = models.Snippet.objects.get(pk=snippet_id)
            except models.Snippet.DoesNotExist:
                logger.warn("Can't find Snippet object to transcode, maybe it's been deleted?")
                return 
            if snippet.state != "processing":
                logger.warn("Snippet is now longer in processing state (state=%s), ignoring" % (snippet.state,))
                return 
            try:
                return task_fn(snippet, *args, **kwargs)
            except:
               if retry_number == max_retries: 
                   logger.exception("Exception during processing task, processing failed...") 
                   snippet.set_processing_error()
                   return
               logger.exception("Exception during processing task, retrying...") 
               kwargs["retry_number"] = retry_number + 1
               _task.apply_async(args=[snippet.pk] + list(args), kwargs=kwargs, countdown=retry_delay)
        return _task
    return _decorator
            

@snippet_processing_task()
def transcode_snippet_audio(snippet):
    # print "Transcode?"
    logger.debug("Transcoding!")
    logger.info("Transcoding audio for snippet id %s" % (snippet.id))
    
    tmpdir = tempfile.mkdtemp()
    try:
        infile = os.path.join(tmpdir, "input")
        outfile = os.path.join(tmpdir, "output.mp3")
        logger.debug("Downloading data")
        open(infile, "wb").write(snippet.uploaded_audio.read())
        logger.debug("Running ffmpeg")
        returncode = subprocess.call([
            settings.FFMPEG_EXECUTABLE, "-i",infile,
            "-acodec", "libmp3lame", "-ab", settings.AUDIO_BITRATE,
            outfile
            ])
        # print returncode
        if returncode != 0:
            logger.error("ffmpeg returned code: %s" % (returncode,))
            snippet.set_processing_error()
            return
        logger.debug("Saving transcoded audio")
        # print "Save"
        # Re-get the snippet usint SELECT FOR UPDATE to avoid race conditions
        with transaction.atomic():
            snippet = models.Snippet.objects.select_for_update().get(pk=snippet.pk)
            # print "About to save transcoding %r, %r, %r" % (snippet.state, snippet.audio_mp3, snippet.echonest_track_analysis is None)
            
            snippet.audio_mp3.save("audio.mp3", File(open(outfile, "rb")))
            snippet.maybe_ready(commit=False)
            snippet.save()
            # print "Haved saved after transcoding %r, %r, %r" % (snippet.state, snippet.audio_mp3, snippet.echonest_track_analysis is None)
    finally:
        logger.debug("Cleaing up temporary directory")
        shutil.rmtree(tmpdir)
    # print "Done transcoding"
    logger.debug("Done")
    
@snippet_processing_task()
def request_echonest_data(snippet):
    # print "Echonest!"
    logger.debug("Transcoding!")
    response = requests.post(
        "http://developer.echonest.com/api/v4/track/upload",
        data={"url": snippet.uploaded_audio.url, "api_key": settings.ECHONEST_API_KEY})
    
    try:
        echonest_id = response.json()["response"]["track"]["id"]
    except:
        logger.error("Bad response from echonest upoad: %s" % (response.text,))
        raise
   

    # print response
    check_echonest_response(snippet.pk, echonest_id)

@snippet_processing_task()
def check_echonest_response(snippet, echonest_id):
    # print "Check response"
    try:
        snippet = models.Snippet.objects.get(pk=snippet.pk)
    except models.Snippet.DoesNotExist:
        logger.warn("Can't find Snippet object to get echonest data for, maybe it's been deleted?")
        return 
    
    # print "Echonest id", echonest_id
    response = requests.get(
        "http://developer.echonest.com/api/v4/track/profile",
        params={"api_key": settings.ECHONEST_API_KEY, "id": echonest_id, "bucket": "audio_summary"})

    # print "Response json", response.json()
    try:
        track = response.json()["response"]["track"]
    except:
        logger.error("Bad response from echonest profile: %s" % (response.text,))
        raise
    # print "Got track"
    if track["status"] == "pending":
        # Check again in 5 seconds time
        # print "Check again in 5 seconds"
        check_echonest_response.apply_async(args=[snippet.pk, echonest_id], countdown=5)
        return
    else:
        # print "Get track analysis"
        track_analysis = requests.get(
                track["audio_summary"]["analysis_url"]).json()
        with transaction.atomic():
            # Re-get the snippet usint SELECT FOR UPDATE to avoid race conditions
            snippet = models.Snippet.objects.select_for_update().get(pk=snippet.pk)
            # print "About to save echonest %r, %r, %r" % (snippet.state, snippet.audio_mp3, snippet.echonest_track_analysis is None)
            
            snippet.echonest_track_profile = track
            snippet.echonest_track_analysis = track_analysis
            # print "Saving echonest data"
            snippet.maybe_ready(commit=False)
            snippet.save()
            # print "Have saved after echonest %r, %r, %r" % (snippet.state, snippet.audio_mp3, snippet.echonest_track_analysis is None)

            
@app.task
def deliver_full_song(song_id):
    "Deliver the full version of a song to anyone who has ordered it but hasn't received it already"
    song = models.Song.objects.select_for_update().get(pk=song_id)
    if not song.is_complete():
        print song
        print song.complete_audio
        print song.completed_at
        logger.warn("Song #%s is not complete so there is no full song to deliver" % (song.id,))
        return
    orders = list(song.order_set.select_for_update().filter(delivered=False, refunded=False))
    if len(orders) == 0:
        logger.debug("No orders to be delivered from song #%s" % (song.id,))
        return
    logger.info("Delivering full version of song #%s to %d users" % (song.id, len(orders)))
    for order in orders:
        deliver_full_song_to_order.apply_async(args=[order.id, False])
        
@app.task
def deliver_full_song_to_order(order_id, redeliver=False):
    logger.debug("Deliver order #%s" % (order_id,))
    with transaction.atomic():
        order_qs = models.Order.objects.select_for_update().filter(refunded=False, pk=order_id)
        if not redeliver:
            order_qs = order_qs.filter(delivered=False)
        order = order_qs.get()
        song = order.song
        if not song.is_complete():
            logger.warn("Song #%s is not complete so there is no full song to deliver to order #%s" % (song.id, order_id))
            return
        
        logger.info("Delivering song #%s to order #%s" % (song.id, order_id))
        message = EmailMessage('spawnsong/email/full-song-delivery.tpl', {'order': order, 'song': order.song}, to=[order.purchaser_email])
        message.send()

        logger.info("Marking as delivered for song #%s to order #%s" % (song.id, order_id))
        order.delivered = True
        order.save()
    
        
@app.task
def send_artist_sales_emails():
    """Send out the daily email to artists with details for the previous
    day's sales"""
    # Find all artists with sales made yesterday
    logger.info("Preparing daily artist sales emails")
    yesterday = datetime.date.today() - datetime.timedelta(1)
    artists = models.Artist.objects.filter(
        song__order__created_at__range= (datetime.datetime.combine(yesterday, datetime.time.min),
                                         datetime.datetime.combine(yesterday, datetime.time.max))).distinct()
    for (artist_id,) in artists.values_list("id"):
       logger.debug("Queueing artist sales email send for Artist #%s" % (artist_id,))
       send_artist_sales_emails_for_arist.apply_async(args=(artist_id,))
    
@app.task
def send_artist_sales_emails_for_arist(artist_id):
    yesterday = datetime.date.today() - datetime.timedelta(1)
    artist = models.Artist.objects.get(id=artist_id)
    orders = models.Order.objects.filter(
        song__artist=artist,
        created_at__range=(datetime.datetime.combine(yesterday, datetime.time.min),
                           datetime.datetime.combine(yesterday, datetime.time.max))).order_by("song")
    grouped = list((x,list(y)) for (x,y) in itertools.groupby(orders, lambda o: o.song))
    for song,song_orders in grouped:
        song_orders = list(song_orders)
        song.order_count = len(list(song_orders))
    
    logger.debug("Send artist sales email send for Artist #%s (%s songs)" % (artist_id,len(grouped)))
    message = EmailMessage(
        'spawnsong/email/artist-daily-report.tpl',
        {'songs': [song for (song,song_orders) in grouped]},
        to=[artist.user.email])
    message.send()

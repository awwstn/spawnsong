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
import time
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from sites.spawnsongsite.celery import app
from . import models

logger = get_task_logger("spawnsong.tasks")

# Decorator to handle errors and retries

def snippet_processing_task(*args, **kwargs):
    def _decorator(task_fn):
        kwargs.setdefault("retries", 3)
        kwargs["bind"] = True
        kwargs["name"] = gen_task_name(app, task_fn.__name__, task_fn.__module__)
        @app.task(*args, **kwargs)
        def _task(self, snippet_id, *args, **kwargs):
            try:
                snippet = models.Snippet.objects.get(pk=snippet_id)
            except models.Snippet.DoesNotExist:
                logger.warn("Can't find Snippet object to transcode, maybe it's been deleted?")
                return 
            if snippet.state != "processing":
                logger.warn("Snippet is now longer in processing state (state=%s), ignoring" % (snippet.state,))
                return 
            return task_fn(self, snippet, *args, **kwargs)
        return _task
    return _decorator
            
    
@snippet_processing_task()
def request_echonest_data(self, snippet):
    print "Echonest!"
    logger.debug("Transcoding!")
    try:
        response = requests.post(
            "http://developer.echonest.com/api/v4/track/upload",
            data={"url": snippet.audio.original.url, "api_key": settings.ECHONEST_API_KEY})
    
        echonest_id = response.json()["response"]["track"]["id"]
    except:
        logger.error("Bad response from echonest upoad: %s" % (response.text,))
        self.retry()
   
    print "Check response"
    try:
        snippet = models.Snippet.objects.get(pk=snippet.pk)
    except models.Snippet.DoesNotExist:
        logger.warn("Can't find Snippet object to get echonest data for, maybe it's been deleted?")
        return 
    
    print "Echonest id", echonest_id

    while True:
        response = None
        try:
            response = requests.get(
                "http://developer.echonest.com/api/v4/track/profile",
                params={"api_key": settings.ECHONEST_API_KEY, "id": echonest_id, "bucket": "audio_summary"})
            track = response.json()["response"]["track"]
        except:
            logger.error("Bad response from echonest profile: %s" % (response.text,))
            self.retry()
            
        print "Response json", response.json()
        # print "Got track"
        if track["status"] == "pending":
            # Check again in 10 seconds time
            print "Check again in 10 seconds"
            time.sleep(10)
        else:
            break
            
    print "Get track analysis"
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

@snippet_processing_task()
def complete_snippet_processing(self, snippet):
    snippet.maybe_ready()
    
@snippet_processing_task()
def fail_snippet_processing(self, snippet):
    print "Failed!"
    snippet.set_processing_error()
            
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
        
        # logger.info("Delivering song #%s to order #%s" % (song.id, order_id))
        # message = EmailMessage('spawnsong/email/full-song-delivery.tpl', {'order': order, 'song': order.song}, to=[order.purchaser_email])
        # message.send()

        logger.info("Marking as delivered for song #%s to order #%s" % (song.id, order_id))
        order.delivered = True
        order.save()
    
@app.task
def send_new_song_emails():
    """Send out the daily email to artists with details for the previous
    day's sales"""
    # Find all artists with sales made yesterday
    logger.info("Preparing daily new song list emails")
    users = User.objects.filter(order__email_notified=False, order__delivered=True, order__refunded=False).distinct()
    for (user_id,) in users.values_list("id"):
       logger.debug("Queueing user daily songs email for user #%s" % (user_id,))
       send_new_song_emails_for_user.apply_async(args=(user_id,))

@app.task
def send_new_song_emails_for_user(user_id):
    with transaction.atomic():
        user = User.objects.get(id=user_id)
        orders = models.Order.objects.select_for_update().filter(email_notified=False, delivered=True, refunded=False, purchaser=user).select_related("song__snippet")
        if orders.count() == 0:
            logger.info("No orders to notify user #%s about" % (user_id,))
            return
        logger.debug("Notify user #%s about new deliveries" % (user_id, ))
        playlist_url = settings.BASE_URL + reverse("personal-playlist")
        message = EmailMessage(
            'spawnsong/email/new-songs.tpl',
            {'orders': orders, "playlist_url": playlist_url},
            to=[user.email])
        message.send()
        orders.update(email_notified=True)
        
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

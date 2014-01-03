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

from .celery import app
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
        data={"url": snippet.uploaded_audio.url, "api_key": settings.ECHONEST_API_KEY}).json()
    response["response"]["track"]["id"]

    # print response
    check_echonest_response(snippet.pk, response["response"]["track"]["id"])

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
    track = response.json()["response"]["track"]
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

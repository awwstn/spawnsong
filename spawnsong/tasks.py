from .celery import app
import subprocess
import models
from django.conf import settings
import tempfile
import shutil
import logging
import os
from django.core.files import File
import requests

logger = logging.getLogger("tasks")

@app.task
def transcode_snippet_audio(snippet_id):
    print "Transcode?"
    logger.debug("Transcoding!")
    try:
        snippet = models.Snippet.objects.get(pk=snippet_id)
    except models.Snippet.DoesNotExist:
        logger.warn("Can't find Snippet object to transcode, maybe it's been deleted?")
        return 
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
        print returncode
        if returncode != 0:
            logger.error("ffmpeg returned code: %s" % (returncode,))
            # TODO: Mark snippet as having failed transcoding
            return
        logger.debug("Saving transcoded audio")
        print "Save"
        snippet.audio_mp3.save("audio.mp3", File(open(outfile, "rb")))
        snippet.save()
    finally:
        logger.debug("Cleaing up temporary directory")
        shutil.rmtree(tmpdir)
    print "Done"
    logger.debug("Done")
    snippet.maybe_ready()
    
@app.task
def request_echonest_data(snippet_id):
    print "Echonest!"
    logger.debug("Transcoding!")
    try:
        snippet = models.Snippet.objects.get(pk=snippet_id)
    except models.Snippet.DoesNotExist:
        logger.warn("Can't find Snippet object to get echonest data for, maybe it's been deleted?")
        return 
    response = requests.post(
        "http://developer.echonest.com/api/v4/track/upload",
        data={"url": snippet.uploaded_audio.url, "api_key": settings.ECHONEST_API_KEY}).json()

    print response
    check_echonest_response(response["response"]["track"]["id"], snippet_id)
    
@app.task
def check_echonest_response(echonest_id, snippet_id):
    print "Check response"
    try:
        snippet = models.Snippet.objects.get(pk=snippet_id)
    except models.Snippet.DoesNotExist:
        logger.warn("Can't find Snippet object to get echonest data for, maybe it's been deleted?")
        return 
    
    print echonest_id
    response = requests.get(
        "http://developer.echonest.com/api/v4/track/profile",
        params={"api_key": settings.ECHONEST_API_KEY, "id": echonest_id, "bucket": "audio_summary"})
    

    print response.json()
    track = response.json()["response"]["track"]
    if track["status"] == "pending":
        # Check again in 5 seconds time
        check_echonest_response.apply_async(args=[echonest_id, snippet_id], countdowd=5)
        return
    else:
        snippet.echonest_track_profile = track
        snippet.echonest_track_analysis = requests.get(
            track["audio_summary"]["analysis_url"]).json()
        snippet.save()
        snippet.maybe_ready()

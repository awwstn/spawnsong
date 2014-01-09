
import os
import shutil
import subprocess
import tempfile

from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.files import File
from django.db import transaction

import models
from sites.spawnsongsite.celery import app

import shlex

logger = get_task_logger("media.tasks")

@app.task(bind=True,retries=3)
def transcode_audio(self, audioformat_id, profile):
    # print "Transcode?"
    logger.debug("Transcoding!")
    logger.info("Transcoding audio for audio format id %s" % (audioformat_id,))
    
    tmpdir = tempfile.mkdtemp()
    audioformat = models.AudioFormat.objects.get(pk=audioformat_id)
    try:
        infile = os.path.join(tmpdir, "input")
        outfile = os.path.join(tmpdir, "output.mp3")
        logger.debug("Downloading data")
        open(infile, "wb").write(audioformat.audio.original.read())
        logger.debug("Running ffmpeg")
        command = shlex.split(profile["command"].format(input=infile, output=outfile))
        print command
        returncode = subprocess.call(command)
        # print returncode
        if returncode != 0:
            logger.error("ffmpeg returned code: %s" % (returncode,))
            audioformat.last_error="Failed to encode audio, ffpmeg returned code: %s" % (returncode,)
            audioformat.save()
            return self.retry()
        logger.debug("Saving transcoded audio")
        
        audioformat.audio_data.save("audio.%s" % (profile["extension"],), File(open(outfile, "rb")))
        audioformat.state = "ready"
        audioformat.save()
    finally:
        logger.debug("Cleaing up temporary directory")
        shutil.rmtree(tmpdir)
    logger.debug("Done transcoding")
    return True

@app.task(bind=True)
def transcode_audio_failed(self, audioformat_id):
    models.AudioFormat.objects.filter(pk=audioformat_id).update(state="failed")

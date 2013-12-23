from .celery import app

@app.task
def transcode_snippet_audio(snippet_id):
    print "Transcoding!"
    pass

@app.task
def retireve_echonest_data(snippet_id):
    print "Echonest!"
    pass

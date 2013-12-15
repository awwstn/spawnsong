SongSpawn.com
=============


Components
----------

 - Upload storage on S3
 - File conversion using ffmpeg running on Heroku (use the Linux 64 binary) and run in another process via Celery
 - Echonest for beat locations
 
Deploy Notes
------------

Styles are written in LESS and compiled automatically with django-static-precompiler which requires `lessc` to be available on the path.

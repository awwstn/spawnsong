SongSpawn.com
=============


Setting up for development
--------------------------

Follow these instructions to run a local copy of the site or to prepare to deploy a remote server.

 - Install Python 2.7
 - Install `pip` and `virtualenv` python packages (often you can install both with `easy_install virtualenv`)
 - Setup a Virtualenv for the project (this is an isolated copy of Python and the required libraries)
   - Make the vitualenv `virtualenv ~/envs/reetraining`
   - Activate it `source ~/envs/reetraining/bin/activate.sh` 
   - Install the needed python libraries (must be run from project root): `pip install -r requirements.txt`
 - Install LESS and Yuglify (for the static file procesing pipeline).
   - Install Node.JS
   - Run `npm install -g less yuglify`

At this point you should have a working Virtualenv, whenever you want to work on the project you must activate it first with `source ~/envs/reetraining/bin/activate.sh`. You will know this has worked because it will put "(reetraining)" before your shell prompt.

Setting up local settings
-------------------------

For local configuration you can create a local_settings.py file in the `sites/spawnsongsite` folder. This can be based on local_settings.py.example and should *not* be added to the repository, it allows you to overide some settings just for your local machine. The example version shows settings for using an sqlite database but for a closer match to the production system you may want to use a local copy of PostgreSQL.

Running a local dev server
--------------------------

Once you're swtiched into the Virtualenv and have your `local_settings.py` you can run `honcho -f ProcfileHoncho start` to start the development server. This will also run the Celery server which handles out of process tasks such as transcoding. The web server part will retstart when you make a change but the you will need to manually restart (hit Ctrl-C to shut it down) if you make changes to the Celery tasks.


Thirs Party Components
----------

 - Heroku for hosting
 - Upload storage on Amazon S3
 - File conversion using ffmpeg running on Heroku (use the Linux 64 binary) and run in another process via Celery
 - Echonest for beat locations
 - Mailgun fo rmail delivery
 - Memcachier for caching
 - Stripe for payments
 - Twitter for login
 
Heroku Config
-------------

Uses a special build pack because we need ffmpeg:

    heroku config:add BUILDPACK_URL=https://github.com/almost/heroku-buildpack-python-ffmpeg.git

Needs memcachier addon for memcached

Need the following additonal Heroku config options:

    AWS_ACCESS_KEY
    AWS_SECRET_ACCESS_KEY
    ECHONEST_API_KEY
    MAILGUN_ACCESS_KEY
    MAILGUN_SERVER_NAME
    STRIPE_PUBLIC_KEY
    STRIPE_SECRET_KEY
    TWITTER_CONSUMER_KEY
    TWITTER_CONSUMER_SECRET

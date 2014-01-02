# Django settings for spawnsong project.
import os,sys

DEBUG = False
TEMPLATE_DEBUG = DEBUG

PATH_TO_HERE = os.getcwd()

ADMINS = (
    ('Thomas Parslow', 'tom@almostobsolete.net'),
)

ALLOWED_HOSTS = ["songspawn.herokuapp.com"]
if DEBUG:
    ALLOWED_HOSTS.append("localhost")
# To lockdown pages set a password here and enable the middleware below
LOCKDOWN_PASSWORDS = ("demo",)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = 'staticfiles'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = "/static/"

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    "static",
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

PIPELINE_COMPILERS = (
  'pipeline.compilers.less.LessCompiler',
)

PIPELINE_CSS = {
    'styles': {
        'source_filenames': (
          'less/app.less',
          'mediaelement/mediaelementplayer.css',
        ),
        'output_filename': 'css/style.css',
    },
}

# PIPELINE_JS = {
#     'scripts': {
#         'source_filenames': (
#           'js/vendor/jquery.js',
#           'js/app.js',
#           'mediaelement/mediaelement-and-player.js',
#         ),
#         'output_filename': 'js/compiled/site.js',
#     },
# }

PIPELINE_MIMETYPES = (
    ('text/coffeescript', '.coffee'),
    ('text/less', '.less'),
    ('text/javascript', '.js'),
    ('text/x-sass', '.sass'),
    ('text/x-scss', '.scss')
    )

STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'

# PIPELINE_ENABLED = False
# PIPELINE_DISABLE_WRAPPER = True

# If we are on heroku we want to re-define the location of the less binary.
HEROKU_LESSC = os.path.join(PATH_TO_HERE, '/app/.heroku/python/bin/lessc')
if os.path.exists(HEROKU_LESSC):
    PIPELINE_LESS_BINARY = HEROKU_LESSC
    
HEROKU_YUGLIFY = os.path.join(PATH_TO_HERE, '/app/.heroku/python/bin/yuglify')
if os.path.exists(HEROKU_YUGLIFY):
    PIPELINE_YUFLIFY_BINARY = HEROKU_YUGLIFY
 

# Make this unique, and don't share it with anybody.
SECRET_KEY = '70aafb9b05c88cdd116adb4779c11849-bb18f1b98a94a805de5ab7d3b79784e6'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line to password protect the whole site
    'lockdown.middleware.LockdownMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'spawnsong.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'spawnsong.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.comments',
    'django.contrib.humanize',
    'social_auth',
#    'social_auth.backends.facebook.FacebookBackend',
    'spawnsong',
    'lockdown',
     'pipeline',
    'storages',
    'south',
    'gunicorn',
    'crispy_forms',
    'djcelery',
    'sorl.thumbnail',
    'kombu.transport.django',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

try:
    from memcacheify import memcacheify
except ImportError:
    print "Failed to import memacheify, no cache configuration will be set!"
else:
    CACHES = memcacheify()

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'social_auth.backends.facebook.FacebookBackend',
)

FACEBOOK_APP_ID = 'TODO'
FACEBOOK_API_SECRET = 'TODO'

FACEBOOK_EXTENDED_PERMISSIONS = ['publish_stream']

#LOGIN_URL          = '/login/facebook/'
LOGIN_URL          = '/login/'

LOGIN_REDIRECT_URL = '/'


AWS_STORAGE_BUCKET_NAME = "spawnsong-test"
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

#STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'stream': sys.stdout,
            # 'formatter': 'standard'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': [],
            'propagate': False,
        },
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}

SONG_PRICE = 500

CRISPY_TEMPLATE_PACK = 'bootstrap3'

CELERY_RESULT_BACKEND='djcelery.backends.database:DatabaseBackend'

BROKER_URL = 'django://'

FFMPEG_EXECUTABLE = "vendor/ffmpeg/bin/ffmpeg"

AUDIO_BITRATE = "128k"

EMAIL_BACKEND = 'django_mailgun.MailgunBackend'



try:
    from local_settings import *
except ImportError:
    # Heroku setup
    
    # If there isn't a local_settings then get settings from the enviroment

    # Get database settings from DATABASE_URL enviroment, this may be overidden in the local settings
    import dj_database_url
    DATABASES = {'default': dj_database_url.config(default='postgres://localhost')}

    AWS_ACCESS_KEY=os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_ACCESS_KEY_ID = AWS_ACCESS_KEY
    
    MAILGUN_ACCESS_KEY = os.getenv("MAILGUN_ACCESS_KEY")
    MAILGUN_SERVER_NAME = os.getenv("MAILGUN_SERVER_NAME")
    
    ECHONEST_API_KEY = os.getenv("ECHONEST_API_KEY")

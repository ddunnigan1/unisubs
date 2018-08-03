# Amara, universalsubtitles.org
#
# Copyright (C) 2013 Participatory Culture Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see
# http://www.gnu.org/licenses/agpl-3.0.html.

from datetime import timedelta
from settings import *
import logging
import os

HOSTNAME = 'unisubs.example.com:8000'

INSTALLED_APPS += (
    'sslserver',
)
if not env_flag_set('DISABLE_DEBUG_TOOLBAR'):
    INSTALLED_APPS += ('debug_toolbar',)
    MIDDLEWARE_CLASSES = (
            'debug_toolbar.middleware.DebugToolbarMiddleware',
    ) + MIDDLEWARE_CLASSES

BROKER_URL = 'amqp://guest:guest@queue:5672'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

FEEDWORKER_PASS_DURATION=300

JS_USE_COMPILED = True

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': "amara",
        'USER': "amara",
        'PASSWORD': "amara",
        'HOST': 'db',
        'PORT': 3306,
        'OPTIONS': {
            'init_command': 'SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED',
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'cache:11211',
    }
}

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'a9yr_yzp2vmj-2q1zq)d2+b^w(7fqu2o&jh18u9dozjbd@-$0!'

TWITTER_CONSUMER_KEY = '6lHYqtxzQBD3lQ55Chi6Zg'
TWITTER_CONSUMER_SECRET = 'ApkJPIIbBKp3Wph0JBoAg2Nsk1Z5EG6PFTevNpd5Y00'

MEDIA_URL = "http://unisubs.example.com:8000/user-data/"

FACEBOOK_APP_KEY = FACEBOOK_APP_ID = '255603057797860'
FACEBOOK_SECRET_KEY = '2a18604dac1ad7e9817f80f3aa3a69f2'

OAUTH_CALLBACK_PROTOCOL = 'http'

# allow devs to use insecure passwords on local instances
MINIMUM_PASSWORD_SCORE = 0

# Celery
CELERY_ALWAYS_EAGER = False
CELERY_TASK_RESULT_EXPIRES = timedelta(days=7)

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: not request.is_ajax()
}

# Or you can use redis as backend
#BROKER_BACKEND = 'redis'
#BROKER_HOST = "localhost"
#BROKER_VHOST = "/"

# 1. Run Redis
# 2. >>> python manage.py celeryd -E --concurrency=10 -n worker1.localhost
# 3. >>> ./dev-runserver
# 4. >>> python manage.py celerycam #this is optional. It allow see in admin-interface tasks running

CACHE_PREFIX = 'unisubsdevsettings'
CACHE_TIMEOUT = 0

COMPRESS_MEDIA = not DEBUG

try:
    from dev_settings_local import *
except ImportError:
    pass

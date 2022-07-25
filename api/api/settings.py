"""
Django settings for api project.

Generated by 'django-admin startproject' using Django 4.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import os
import sys
from pathlib import Path
from celery.schedules import crontab


def get_from_env_or_file(var_name, default=None):
    file_var_name = '%s_FILE' % var_name
    path = os.environ.get(file_var_name)
    if path and os.path.isfile(path):
        with open(path, 'r') as f:
            return f.read()
    else:
        return os.environ.get(var_name, default)


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-8cbj*@yl)w6(=y%yksh_g1+*3maxm)tp8g7&g%gejj^v)+vi2h'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
TEST = 'test' in sys.argv

ALLOWED_HOSTS = [
    s.strip() for s in os.getenv(
        'DJANGO_ALLOWED_HOSTS', '.cesium.tv').split(',')
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'django_celery_beat',
    'djcelery_email',
    'drf_recaptcha',
    'mail_templated',
    'rest_framework',
    'debug_toolbar',
    'corsheaders',
    'rest',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
if DEBUG:
    MIDDLEWARE.insert(3, 'whitenoise.middleware.WhiteNoiseMiddleware')
    MIDDLEWARE.insert(3, 'debug_toolbar.middleware.DebugToolbarMiddleware')


ROOT_URLCONF = 'api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'api.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DJANGO_DB_PASSWORD = get_from_env_or_file('DJANGO_DB_PASSWORD', 'password')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ.get('DJANGO_DB_HOST', 'db'),
        'NAME': os.environ.get('DJANGO_DB_NAME', 'cesium'),
        'USER': os.environ.get('DJANGO_DB_USER', 'user'),
        'PASSWORD': DJANGO_DB_PASSWORD,
    }
}


REDIS_HOST = os.getenv('DJANGO_REDIS_HOST', 'website-redis')
REDIS_PORT = int(os.getenv('DJANGO_REDIS_PORT', '6379'))


CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/1',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = Path(BASE_DIR).joinpath('static')

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'rest.User'
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'


CELERY_BROKER_URL = os.environ.get(
    'CELERY_BROKER_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/0')
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_BEAT_SCHEDULER = os.environ.get(
    'CELERY_BEAT_SCHEDULER',
    'django_celery_beat.schedulers:DatabaseScheduler')
CELERY_COMMAND = ('celery', '-A', 'api', 'worker', '-l', 'info')
CELERY_AUTORELOAD = False
CELERY_ALWAYS_EAGER = TEST
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    'rest.tasks.video.import_videos': {
        'task': 'rest.tasks.video.import_videos',
        'schedule': crontab(minute=0),
    }
}


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        # 'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
}

EMAIL_BACKEND = os.environ.get(
    'DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')

CELERY_EMAIL_BACKEND = 'django_mailjet.backends.MailjetBackend'
MAILJET_API_KEY = get_from_env_or_file('DJANGO_MAILJET_API_KEY', None)
MAILJET_API_SECRET = get_from_env_or_file('DJANGO_MAILJET_API_SECRET', None)
DEFAULT_FROM_EMAIL = 'admin@cesium.tv'

DRF_RECAPTCHA_TESTING = TEST
DRF_RECAPTCHA_SECRET_KEY = get_from_env_or_file(
    'DJANGO_RECAPTCHA_SECRET_KEY', None)

INTERNAL_IPS = [
    "127.0.0.1",
]

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: True,
}

CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOWED_ORIGINS = os.getenv('DJANGO_ALLOWED_CORS_ORIGINS', '').split(',')

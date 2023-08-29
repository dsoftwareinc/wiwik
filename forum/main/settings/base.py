"""
Django settings for wiwik project.
"""
import os

from dotenv import load_dotenv, find_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
from .base_dir import BASE_DIR

load_dotenv(find_dotenv())


def getenv_asbool(key, default='False'):
    return os.getenv(key, default=default).lower() in ('true', '1', 't')


def getenv_asint(key, default=None):
    val = os.getenv(key, default=default)
    return int(val) if val is not None else None


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-ge#=&h34r27hjgv!0tu!xzt1a(h7^-!ybzzl1#cf*1&pdcvfz)')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = getenv_asbool("DEBUG", default="TRUE")
SEND_EMAILS = getenv_asbool("SEND_EMAILS", default="FALSE")
DEBUG_EMAIL_TO = os.environ.get("DEBUG_EMAIL_TO", default="style.daniel@gmail.com")
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", default='*').split(" ")
CSRF_TRUSTED_ORIGINS = os.environ.get("CSRF_TRUSTED_ORIGINS", default='https://* http://*').split(" ")
# Application definition
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SKIP_USER_VISIT_LOG = False
MIDDLEWARE = [
    'wiwik_lib.middleware.UserVisitMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'main.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'wiwik_lib.context_processor.env_context',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'debug': DEBUG,
        },
    },
]

WSGI_APPLICATION = 'main.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("SQL_DATABASE", os.path.join(BASE_DIR, "db.sqlite3")),
        "USER": os.environ.get("SQL_USER", "user"),
        "PASSWORD": os.environ.get("SQL_PASSWORD", "password"),
        "HOST": os.environ.get("SQL_HOST", "localhost"),
        "PORT": os.environ.get("SQL_PORT", "5432"),
    }
}
USE_TZ = (DATABASES['default']['ENGINE'] == "django.db.backends.sqlite3")

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)
STATIC_ROOT = os.path.join(BASE_DIR, '..', 'static')
MEDIA_ROOT = os.getenv('MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))
MEDIA_URL = '/media/'
# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# userauth
AUTH_USER_MODEL = 'userauth.ForumUser'
LOGIN_REDIRECT_URL = 'forum:home'
LOGIN_URL = 'userauth:login'

EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
INTERNAL_IPS = ('127.0.0.1',)
# SITE_URL = "https://example.com"
# SESSION_COOKIE_AGE = 600  # https://docs.djangoproject.com/en/3.2/ref/settings/#session-cookie-age

REDIS_CACHE_URL = os.getenv('REDIS_CACHE_URL', None)
if REDIS_CACHE_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            "LOCATION": REDIS_CACHE_URL,
            "OPTIONS": {
            },
            "KEY_PREFIX": "cache",
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

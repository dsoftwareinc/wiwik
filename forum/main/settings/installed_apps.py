import os

INSTALLED_APPS = [
    # django related
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'admin_numeric_filter',  # django admin numeric filter
    'rangefilter',  # django admin related
    'userauth',  # user related data
    'allauth',  # allauth supplies the basic endpoints and models for social login, etc.
    'allauth.account',
    'allauth.socialaccount',
    'wiwik_lib',
    'forum',  # basic forum app
    'articles',  # support for articles, proxy of Question
    'crispy_forms',  # bootstrap django forms
    'crispy_bootstrap5',
    'tags',  # tags related data
    'badges',  # Support for badges
    'scheduler',  # Ability to schedule tasks
    'compressor',  # minify js/css
    'similarity',  # app for question similarity calculations
    'spaces',  # app for associating posts with spaces
]
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

if os.getenv('OKTA_BASE_URL', None):
    INSTALLED_APPS.append('allauth.socialaccount.providers.okta')
if os.getenv('GOOGLE_CLIENT_ID', None):
    INSTALLED_APPS.append('allauth.socialaccount.providers.google')
if os.getenv('FACEBOOK_CLIENT_ID', None):
    INSTALLED_APPS.append('allauth.socialaccount.providers.facebook')

# django-allauth
import os

SITE_ID = 1
LOGIN_REDIRECT_URL = "/"
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    },
    "facebook": {
        "METHOD": "oauth2",
        "SCOPE": ["email", "public_profile"],
        "AUTH_PARAMS": {"auth_type": "reauthenticate"},
        "INIT_PARAMS": {"cookie": True},
        "FIELDS": [
            "id",
            "first_name",
            "last_name",
            "middle_name",
            "name",
            "name_format",
            "picture",
            "short_name",
        ],
        "EXCHANGE_TOKEN": True,
        "LOCALE_FUNC": "path.to.callable",
        "VERIFIED_EMAIL": False,
        "VERSION": "v7.0",
    },
}
if "OKTA_BASE_URL" in os.environ:
    SOCIALACCOUNT_PROVIDERS["okta"] = {
        "OKTA_BASE_URL": os.getenv("OKTA_BASE_URL", None),
        "OAUTH_PKCE_ENABLED": True,
    }
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_ADAPTER = "wiwik_lib.adapters.CustomSocialAccountAdapter"
ALLOWED_REGISTRATION_EMAIL_DOMAINS = list(
    filter(
        lambda x: x != "",
        os.environ.get("ALLOWED_REGISTRATION_EMAIL_DOMAINS", default="").split(" "),
    )
)

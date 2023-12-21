from django.db.models import F
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from forum.models import UserTagStats
from userauth.models import ForumUser
from userauth.views.tokens import account_activation_token
from wiwik_lib.utils import CURRENT_SITE


def unsubscribe_link_with_base(u: ForumUser) -> str:
    uid = urlsafe_base64_encode(force_bytes(u.pk))
    token = account_activation_token.make_token(u)
    return CURRENT_SITE + reverse("userauth:unsubscribe", args=[uid, token])


def user_most_active_tags(u: ForumUser, count: int = 3) -> list[str]:
    return (
        UserTagStats.objects.filter(user=u)
        .annotate(items_by_user=F("questions_by_user") + F("answers_by_user"))
        .order_by("-items_by_user")
        .values_list("tag__tag_word", flat=True)[:count]
    )

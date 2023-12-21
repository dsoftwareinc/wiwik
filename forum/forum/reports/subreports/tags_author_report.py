from django.template import loader

from wiwik_lib.utils import CURRENT_SITE
from tags.models import Tag
from userauth.models import ForumUser


def tags_author_should_report(user: ForumUser):
    tags_list = Tag.objects.filter(author=user, description__isnull=True)
    if len(tags_list) == 0:
        return ""
    template = loader.get_template("emails/reports/includes/tags_empty_desc.report.html")
    res = template.render(
        context={
            "tags": tags_list,
            "basesite": CURRENT_SITE,
        }
    )
    return res

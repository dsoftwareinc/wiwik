from datetime import date

from django.db.models import Count, Q
from django.template import loader

from wiwik_lib.utils import CURRENT_SITE
from tags.models import Tag


def tags_activity_email_report(from_date: date):
    tags_list = list(
        Tag.objects.annotate(
            num_questions=Count(
                "question", filter=Q(question__created_at__gte=from_date)
            )
        )
        .filter(num_questions__gt=0)
        .order_by("-num_questions")
    )
    template = loader.get_template("emails/reports/includes/tags.report.html")
    res = template.render(
        context={
            "fromdate": from_date,
            "tags": tags_list,
            "basesite": CURRENT_SITE,
        }
    )
    return res

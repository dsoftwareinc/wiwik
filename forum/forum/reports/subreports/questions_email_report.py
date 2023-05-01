from datetime import date
from typing import List

from django.conf import settings
from django.db.models import Count, Q
from django.template import loader
from django.utils import timezone

from forum.models import Question
from wiwik_lib.utils import CURRENT_SITE


def old_unanswered_questions_email_report(
        tags_list: List[str] = None,
        skip_if_empty: bool = True) -> str:
    """
    Generate a report with old unanswered questions on a list of tags.
    Old question is defined as created_at is before now minus settings.QUESTION_OLD_ON_DAYS
    If there are no questions in the report, then based on :skip_if_empty value it
    can either generate an empty report or return an empty string.

    Args:
        tags_list: list of tags to query questions with, if empty/None, ignore this parameter
        skip_if_empty: if report has no questions, should it be skipped (i.e., return empty string)

    Returns:
        A report as string to be joined with other reports in generate_report_html
    """
    if settings.DAYS_FOR_QUESTION_TO_BECOME_OLD is None:
        return ""
    from_date = timezone.now() - timezone.timedelta(days=settings.DAYS_FOR_QUESTION_TO_BECOME_OLD)
    query_filter = Q(created_at__lt=from_date)  # Old questions
    if tags_list:  # In tags
        query_filter = query_filter & Q(tags__tag_word__in=tags_list)
    questions_list = list(Question.objects
                          .filter(query_filter)
                          .annotate(num_answers=Count('answer'))
                          .filter(num_answers=0)  # unanswered
                          .order_by('-votes', '-created_at')
                          )
    if len(questions_list) == 0 and skip_if_empty:
        return ''
    template = loader.get_template('emails/reports/includes/unanswered-questions.report.html')
    res = template.render(context={'questions': questions_list,
                                   'basesite': CURRENT_SITE,
                                   })
    return res


def recent_questions_email_report(from_date: date,
                                  tags_list: List[str] = None,
                                  skip_if_empty: bool = True) -> str:
    """
    Generate a report with all the questions that were created from :from_date and
    have tags from :tags_list. If :tags_list is empty, then sends all questions that were
    created from from_date on all tags.
    If there are no questions in the report, then based on :skip_if_empty value it
    can either generate an empty report or return an empty string.

    Args:
        from_date: Date to query questions from
        tags_list: list of tags to query questions with, if empty/None, ignore this parameter
        skip_if_empty: if report has no questions, should it be skipped (i.e., return empty string)

    Returns:
        A report as string to be joined with other reports in generate_report_html
    """
    query_filter = Q(created_at__gte=from_date)
    total_questions = 0  # If this is report is for all tags no need to present it
    if tags_list:
        query_filter = query_filter & Q(tags__tag_word__in=tags_list)
        total_questions = Question.objects.filter(created_at__gte=from_date).count()
    questions_list = list(Question.objects
                          .filter(query_filter)
                          .annotate(num_answers=Count('answer'))
                          .order_by('-votes', '-created_at')
                          )
    if len(questions_list) == 0 and skip_if_empty:
        return ''
    template = loader.get_template('emails/reports/includes/questions.report.html')
    res = template.render(context={'fromdate': from_date,
                                   'questions': questions_list,
                                   'total_questions': total_questions,
                                   'basesite': CURRENT_SITE,
                                   })
    return res

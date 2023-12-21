from datetime import date

from django.db.models import Count
from django.template import loader

from wiwik_lib.utils import CURRENT_SITE
from userauth.models import ForumUser


class UserData(object):
    def __init__(
        self,
        username: str,
        reputation: int,
        num_questions: int = 0,
        num_answers: int = 0,
        num_question_comments=0,
        num_answer_comments=0,
        num_visits=0,
        search_count=0,
    ):
        self.username = username
        self.user = ForumUser.objects.get(username=username)
        self.reputation = reputation
        self.num_questions = num_questions
        self.num_answers = num_answers
        self.num_question_comments = num_question_comments
        self.num_answer_comments = num_answer_comments
        self.num_visits = num_visits
        self.search_count = search_count

    def valid(self) -> bool:
        return (
            self.num_questions > 0
            or self.num_answers > 0
            or self.num_question_comments > 0
            or self.num_answer_comments > 0
            or self.search_count > 0
        )

    def __lt__(self, other) -> bool:
        return self.num_visits < other.num_visits


def user_activity_email_report(from_date: date):
    users_dict = dict()
    users_visited = list(
        ForumUser.objects.filter(uservisit__visit_date__gte=from_date)
        .annotate(num_visits=Count("uservisit"))
        .filter(num_visits__gt=0)
        .values_list(
            "username",
            "num_visits",
            "additional_data__reputation_score",
            "additional_data__search_count",
        )
    )
    for username, num_visits, reputation, search_count in users_visited:
        users_dict[username] = UserData(
            username, reputation, num_visits=num_visits, search_count=search_count
        )
    users_questions_list = list(
        ForumUser.objects.filter(question__created_at__gte=from_date)
        .annotate(num_questions=Count("question"))
        .filter(num_questions__gt=0)
        .values_list("username", "num_questions", "additional_data__reputation_score")
    )
    for username, num_questions, reputation in users_questions_list:
        if username in users_dict:
            users_dict[username].num_questions = num_questions
        else:
            users_dict[username] = UserData(
                username, reputation, num_questions=num_questions
            )

    users_answers_list = list(
        ForumUser.objects.filter(answer__created_at__gte=from_date)
        .annotate(num_answers=Count("answer"))
        .filter(num_answers__gt=0)
        .values_list("username", "num_answers", "additional_data__reputation_score")
    )
    for username, num_answers, reputation in users_answers_list:
        if username in users_dict:
            users_dict[username].num_answers = num_answers
        else:
            users_dict[username] = UserData(
                username, reputation, num_answers=num_answers
            )

    users_qcomments_list = list(
        ForumUser.objects.filter(questioncomment__created_at__gte=from_date)
        .annotate(num_qcomments=Count("questioncomment"))
        .filter(num_qcomments__gt=0)
        .values_list("username", "num_qcomments", "additional_data__reputation_score")
    )
    for username, num_qcomments, reputation in users_qcomments_list:
        if username in users_dict:
            users_dict[username].num_question_comments = num_qcomments
        else:
            users_dict[username] = UserData(
                username, reputation, num_question_comments=num_qcomments
            )

    users_acomments_list = list(
        ForumUser.objects.filter(answercomment__created_at__gte=from_date)
        .annotate(num_acomments=Count("answercomment"))
        .filter(num_acomments__gt=0)
        .values_list("username", "num_acomments", "additional_data__reputation_score")
    )
    for username, num_acomments, reputation in users_acomments_list:
        if username in users_dict:
            users_dict[username].num_answer_comments = num_acomments
        else:
            users_dict[username] = UserData(
                username, reputation, num_answer_comments=num_acomments
            )

    num_users_visited = len(users_dict)
    users_list = sorted(filter(lambda u: u.valid(), users_dict.values()), reverse=True)

    template = loader.get_template("emails/reports/includes/users.report.html")
    res = template.render(
        context={
            "fromdate": from_date,
            "users_data": users_list,
            "basesite": CURRENT_SITE,
            "num_users_visited": num_users_visited,
        }
    )
    return res

from django.urls import reverse

from wiwik_lib.utils import CURRENT_SITE


def get_model_url(model_name: str, model) -> str:
    if model_name == 'tag':
        return reverse('forum:tag', args=[model.tag_word, ])
    if model_name == "comment_answer":
        parent_model_name = "answer"
        parent_pk = model.answer.pk
    elif model_name == "answer":
        parent_model_name = "answer"
        parent_pk = model.pk
    elif model_name == "comment_question":
        parent_model_name = "question"
        parent_pk = model.question.pk
    else:
        parent_model_name = "question"
        parent_pk = model.pk
    anchor = f'#{parent_model_name}_{parent_pk}'
    return reverse('forum:thread', args=[model.get_question().pk]) + anchor


def get_model_url_with_base(model_name: str, model) -> str:
    return CURRENT_SITE + get_model_url(model_name, model)

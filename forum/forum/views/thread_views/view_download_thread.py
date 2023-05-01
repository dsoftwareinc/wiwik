from io import BytesIO
from typing import Union

from django.http import HttpResponse, HttpResponseNotFound

from forum import models


def write_section(out, text, sep: Union[str, None] = '-'):
    out.write(bytes(text + '\n', encoding='utf-8'))
    if sep:
        splitted = text.split('\n')
        max_len = min(50, max([len(s) for s in splitted]))
        seperator = bytes(('\n' if sep == '-' else '') + (sep * max_len) + '\n', encoding='utf-8')
        out.write(seperator)


def thread_markdown_bytesio(question: models.Question, **kwargs) -> BytesIO:
    out = BytesIO()
    write_section(out, question.title, '=')
    write_section(out, 'Tags: ' + ', '.join(question.tag_words()))
    if kwargs.get('include_authors', True):
        write_section(out, f'Author: {question.author.username} ({question.author.name})')
    write_section(out, question.content)
    answers = question.answer_set.order_by('-votes')
    for answer in answers:
        if kwargs.get('include_authors', True):
            write_section(out, f'Author: {answer.author.username} ({answer.author.name})', sep=None)
        write_section(out, answer.content)
    return out


def view_download_thread(request, question_pk: int):
    question = models.Question.objects.filter(pk=question_pk).first()
    if question is None:
        return HttpResponseNotFound()

    out = thread_markdown_bytesio(question)
    filename = f'post{question_pk}.md'
    response = HttpResponse(out.getvalue(), content_type='text/markdown')
    response['Content-Disposition'] = f'attachment; filename={filename}'

    return response

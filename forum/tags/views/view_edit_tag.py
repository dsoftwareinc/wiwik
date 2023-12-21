from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from tags import models
from wiwik_lib.views import ask_to_edit_resource, finish_edit_resource


class TagError(Exception):
    pass


def validate_tag_data(tag: models.Tag, description, wiki, summary) -> None:
    if description is None or len(description) < settings.MIN_TAG_DESCRIPTION_LENGTH:
        raise TagError("Description too short")
    if (
        tag.wiki is not None
        and wiki != tag.wiki
        and (wiki is None or len(wiki) < settings.MIN_TAG_WIKI_LENGTH)
    ):
        raise TagError(
            f"Wiki content should have at least {settings.MIN_TAG_WIKI_LENGTH} characters"
        )
    if len(description) > settings.MAX_TAG_DESCRIPTION_LENGTH:
        raise TagError(
            f"Description too long, max is {settings.MAX_TAG_DESCRIPTION_LENGTH} characters"
        )
    if len(wiki) > settings.MAX_TAG_WIKI_LENGTH:
        raise TagError("Wiki content too long")
    if summary is None or len(summary) < settings.MIN_TAG_EDIT_SUMMARY_LENGTH:
        raise TagError(
            f"Edit summary should have at least {settings.MIN_TAG_EDIT_SUMMARY_LENGTH} characters"
        )
    if len(summary) > settings.MAX_TAG_EDIT_SUMMARY_LENGTH:
        raise TagError(
            f"Edit summary too long, max is {settings.MIN_TAG_EDIT_SUMMARY_LENGTH} characters"
        )


@login_required
def view_edit_tag(request, tag_word: str):
    tag = get_object_or_404(models.Tag, tag_word=tag_word)
    if not ask_to_edit_resource(request.user, tag):
        messages.warning(
            request, f"Tag {tag_word} is currently edited by a different user"
        )
        return redirect("tags:info", tag_word=tag_word)
    if request.method == "GET":
        return render(
            request,
            "tags/edit_tag.html",
            {
                "tag": tag,
                "len_description_min": settings.MIN_TAG_DESCRIPTION_LENGTH,
                "len_description_max": settings.MAX_TAG_DESCRIPTION_LENGTH,
                "len_wiki_min": settings.MIN_TAG_WIKI_LENGTH,
                "len_wiki_max": settings.MAX_TAG_WIKI_LENGTH,
                "len_summary_min": settings.MIN_TAG_EDIT_SUMMARY_LENGTH,
                "len_summary_max": settings.MAX_TAG_EDIT_SUMMARY_LENGTH,
                "title": f"wiwik - {tag.tag_word} tag",
            },
        )
    tag_data = request.POST.dict()
    updated_description = tag_data.get("description")
    updated_wiki = tag_data.get("wiki")
    finish_edit_resource(tag)
    if updated_description == tag.description and updated_wiki == tag.wiki:
        messages.info(request, f"No changes made in tag {tag_word} data")
        return redirect("tags:info", tag_word=tag_word)
    edit_summary = tag_data.get("summary", "")
    try:
        validate_tag_data(tag, updated_description, updated_wiki, edit_summary)
    except TagError as e:
        messages.warning(request, f"Error: {e}")
        return redirect("tags:info", tag_word=tag_word)
    last_edit = models.TagEdit.objects.order_by("-created_at").first()
    if last_edit is not None and last_edit.author == request.user:
        last_edit.summary = edit_summary
        last_edit.save()
    else:
        last_edit = models.TagEdit.objects.create(
            tag=tag,
            author=request.user,
            summary=edit_summary,
            before_wiki=tag.wiki,
            before_description=tag.description,
        )
    tag.description = updated_description
    tag.wiki = updated_wiki
    tag.save()
    messages.info(request, f"Tag {tag_word} edited successfully")
    return redirect("tags:info", tag_word=tag_word)

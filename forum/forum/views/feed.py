from django.contrib.syndication.views import Feed
from django.urls import reverse

from forum.models import Question


class LatestEntriesFeed(Feed):
    title = "Latest questions on wiwik"
    link = "/rss/feed/"
    description = "Latest questions on wiwik"
    description_template = "main/rss.feed.description.html"

    def items(self):
        return Question.objects.order_by("-created_at")[:30]

    def item_title(self, item):
        return item.title

    # item_link is only needed if NewsItem has no get_absolute_url method.
    def item_link(self, item):
        return reverse("forum:thread", args=[item.pk])

    def item_pubdate(self, item):
        return item.created_at

    def item_author_name(self, item: Question):
        return item.author.display_name()

    def item_author_link(self, item: Question):
        return reverse("userauth:profile", args=[item.author.username, "questions"])

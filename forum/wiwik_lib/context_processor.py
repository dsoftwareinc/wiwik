from django.conf import settings

from common.utils import TabEnum


def env_context(request):
    """
    This context dictionary is added to every response.
    It adds number of reputation items and number of bookmarks to display in the top nav-bar
    as well as a favicon url.
    """
    context = dict()
    context['favicon_link_light'] = settings.FAVICON_LINK_LIGHT
    context['favicon_link_dark'] = settings.FAVICON_LINK_DARK
    context['MAX_BOOKMARK_ITEMS'] = settings.MAX_BOOKMARK_ITEMS
    context['MAX_REPUTATION_ITEMS'] = settings.MAX_REPUTATION_ITEMS
    context['LATEX_SUPPORT_ENABLED'] = settings.LATEX_SUPPORT_ENABLED
    context['GOOGLE_ANALYTICS_KEY'] = settings.GOOGLE_ANALYTICS_KEY
    context['TABS'] = TabEnum
    context['SHOWCASE'] = settings.SHOWCASE_DEPLOYMENT
    return context

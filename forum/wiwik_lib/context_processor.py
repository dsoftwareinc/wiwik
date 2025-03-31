from common.utils import TabEnum


def env_context(request):
    """
    This context dictionary is added to every response.
    """
    context = dict()
    context["TABS"] = TabEnum
    return context

from datetime import datetime, date
from typing import List

import bleach
import pymdownx.arithmatex as arithmatex
from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe
from markdown import Markdown
from pymdownx import superfences

from forum.models import TagFollow
from tags.models import Tag
from userauth.models import ForumUser
from userauth.utils import user_most_active_tags

register = template.Library()

MARKDOWN_EXTENSIONS = [
    'nl2br',
    'toc',
    'pymdownx.magiclink',
    'pymdownx.extra',
    'pymdownx.emoji',
    'pymdownx.details',
    'pymdownx.keys',
    'pymdownx.superfences',
    'pymdownx.arithmatex',
]
MARKDOWN_EXTENSIONS_CONFIG = {
    "pymdownx.superfences": {
        "custom_fences": [
            {
                'name': 'mermaid',
                'class': 'mermaid',
                'format': superfences.fence_div_format,
            },
        ]
    },
}
if settings.LATEX_SUPPORT_ENABLED:
    MARKDOWN_EXTENSIONS_CONFIG["pymdownx.arithmatex"] = {
        'generic': True,
    }
    MARKDOWN_EXTENSIONS_CONFIG["pymdownx.superfences"]["custom_fences"].append({
        "name": "math",
        "class": "arithmatex",
        'format': arithmatex.fence_generic_format,
    })


@register.filter('startswith')
def startswith(text, starts):
    return isinstance(text, str) and text.startswith(starts)


ALLOWED_ATTRIBUTES = {
    "div": ["class"],
    "a": ["href", "title"],
    "abbr": ["title"],
    "acronym": ["title"],
}
ALLOWED_TAGS = frozenset({
    'kbd',
    "h1", "h2", "h3", "h4", "h5", "h6",
    "b", "i", "strong", "em", "tt",
    "p", "br",
    "span", "div", "blockquote", "code", "pre", "hr",
    "ul", "ol", "li", "dd", "dt",
    "img",
    "a",
    "sub", "sup",
    "details", "summary",
})


@register.filter(is_safe=True)
def markdownify(text: str):
    markdown = Markdown(
        extensions=MARKDOWN_EXTENSIONS,
        extension_configs=MARKDOWN_EXTENSIONS_CONFIG
    )
    html = markdown.convert(text)
    html = bleach.clean(html, attributes=ALLOWED_ATTRIBUTES, tags=ALLOWED_TAGS)
    return mark_safe(html)


@register.filter(is_safe=True)
def absolute_datetime(value: datetime):
    return value.strftime('%Y-%m-%d at %H:%M') if value is not None else ''


@register.filter(is_safe=True)
def absolute_date(value: date):
    return value.strftime('%Y-%m-%d') if value is not None else ''


@register.filter(is_safe=True)
def humanize_number(value: int):
    if value is None:
        return ''
    if value > 1_000_000_000:
        return '{:,}B'.format((value // 100_000_000) / 10)
    if value > 1_000_000:
        return '{:,}m'.format((value // 100_000) / 10)
    if value > 1_000:
        return '{:,}k'.format((value // 100) / 10)
    return value


@register.filter(is_safe=True)
def tag_experts(tag: Tag) -> List[TagFollow]:
    """
    Returns list of three users with most reputation on the tag.

    The reason to use this method and not tag.experts property is because this
    method returns the TagFollow objects which have the user reputation for the tag.

    Args:
        tag (Tag): tag to search experts for

    Returns:
        List of up to 3 TagFollow objects with the most reputation.

    """
    return tag.tagfollow_set.filter(reputation__gt=0).order_by('-reputation')[:3]


@register.filter(is_safe=True)
def user_active_tags(u: ForumUser):
    return user_most_active_tags(u)


VERSION_BOOTSTRAP = '5.3.1'
VERSION_EASYMDE = '2.18.0'
VERSION_CROPPIE = '2.6.5'
VERSION_FONTAWESOME = '4.7.0'
VERSION_TAGIFY = '4.17.9'
VERSION_MERMAIDJS = '10.3.1'
VERSION_KATEX = '0.16.8'
VERSION_BOOTSTRAP_DATEPICKER = '1.10.0'

_3RD_PARTY_URLS = {
    'CDN': {
        'bootstrap-css': f'https://cdn.jsdelivr.net/npm/bootstrap@{VERSION_BOOTSTRAP}/dist/css/bootstrap.min.css',
        'bootstrap-js': f'https://cdn.jsdelivr.net/npm/bootstrap@{VERSION_BOOTSTRAP}/dist/js/bootstrap.min.js',
        'bootstrap-bundle-js': f'https://cdn.jsdelivr.net/npm/bootstrap@{VERSION_BOOTSTRAP}/dist/js/bootstrap.bundle.min.js',
        'easymde-js': f'https://cdn.jsdelivr.net/npm/easymde@{VERSION_EASYMDE}/dist/easymde.min.js',
        'easymde-css': f'https://cdn.jsdelivr.net/npm/easymde@{VERSION_EASYMDE}/dist/easymde.min.css',
        'croppie-js': f'https://cdn.jsdelivr.net/npm/croppie@{VERSION_CROPPIE}/croppie.min.js',
        'croppie-css': f'https://cdn.jsdelivr.net/npm/croppie@{VERSION_CROPPIE}/croppie.css',
        'font-awesome-css': f'https://cdn.jsdelivr.net/npm/font-awesome@{VERSION_FONTAWESOME}/css/font-awesome.min.css',
        'tagify-js': f'https://cdn.jsdelivr.net/npm/@yaireo/tagify@{VERSION_TAGIFY}/dist/tagify.min.js',
        'tagify-polyfills-js': f'https://cdn.jsdelivr.net/npm/@yaireo/tagify@{VERSION_TAGIFY}/dist/tagify.polyfills.min.js',
        'mermaidjs': f'https://cdn.jsdelivr.net/npm/mermaid@{VERSION_MERMAIDJS}/dist/mermaid.esm.min.mjs',
        'katex-css': f'https://cdn.jsdelivr.net/npm/katex@{VERSION_KATEX}/dist/katex.min.css',
        'katex-js': f'https://cdn.jsdelivr.net/npm/katex@{VERSION_KATEX}/dist/katex.min.js',
        'katex-autorender-js': f'https://cdn.jsdelivr.net/npm/katex@{VERSION_KATEX}/dist/contrib/auto-render.min.js',
        'katex-mjs': f'https://cdn.jsdelivr.net/npm/katex@{VERSION_KATEX}/dist/katex.mjs',
        'bootstrap-datepicker-js': f'https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datepicker/{VERSION_BOOTSTRAP_DATEPICKER}/js/bootstrap-datepicker.min.js',
        'bootstrap-datepicker-css': f'https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datepicker/{VERSION_BOOTSTRAP_DATEPICKER}/css/bootstrap-datepicker.standalone.min.css',
    },
    'STATIC': {
        'bootstrap-css': 'bootstrap/css/bootstrap.min.css',
        'bootstrap-js': 'bootstrap/js/bootstrap.min.js',
        'bootstrap-bundle-js': 'bootstrap/js/bootstrap.bundle.min.js',
        'easymde-js': 'easymde/easymde.min.js',
        'easymde-css': 'easymde/easymde.min.css',
        'croppie-js': 'croppie/croppie.min.js',
        'croppie-css': 'croppie/croppie.min.css',
        'font-awesome-css': 'css/font-awesome.min.css',
        'tagify-js': 'tagify/tagify.js',
        'tagify-polyfills-js': 'tagify/tagify.polyfills.min.js',
        'mermaidjs': 'mermaidjs/dist/mermaid.esm.min.mjs',
        'katex-mjs': 'katex/katex.mjs',
        'katex-js': 'katex/katex.min.js',
        'katex-css': 'katex/katex.min.css',
        'bootstrap-datepicker-js': 'bootstrap-datepicker/bootstrap-datepicker.min.js',
        'bootstrap-datepicker-css': 'bootstrap-datepicker/bootstrap-datepicker.min.css',
    },
}


@register.simple_tag(name='tool_url')
def get_url(tool_name: str):
    if tool_name not in _3RD_PARTY_URLS['CDN'] or tool_name not in _3RD_PARTY_URLS['STATIC']:
        raise template.TemplateSyntaxError(f'{tool_name} does not exist!')
    if settings.USE_CDN:
        return _3RD_PARTY_URLS['CDN'][tool_name]
    else:
        return static(_3RD_PARTY_URLS['STATIC'][tool_name])

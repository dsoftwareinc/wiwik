from datetime import datetime

from django import template

register = template.Library()


@register.filter(is_safe=True)
def absolute_datetime(value: datetime):
    return value.strftime('%Y-%m-%d at %H:%M')


@register.filter(is_safe=True)
def absolute_date(value: datetime):
    return value.strftime('%Y-%m-%d')


@register.filter(is_safe=True)
def negative(value: int):
    return -value

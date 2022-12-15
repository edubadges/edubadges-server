from django import template
from django.templatetags.static import (do_static as _do_static, static as _static, )

register = template.Library()


def static(path):
    return _static(path)


@register.tag('static')
def do_static(parser, token):
    return _do_static(parser, token)

from django import template
from django.templatetags.static import (
    do_static as _do_static,
)
from django.templatetags.static import (
    static as _static,
)

register = template.Library()


def staticfiles(path):
    return _static(path)


@register.tag("static")
def do_static(parser, token):
    return _do_static(parser, token)

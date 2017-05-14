# encoding: utf-8
from __future__ import unicode_literals

import functools


def apispec_operation(*spec_args, **spec_kwargs):

    def decorator(wrapped):
        @functools.wraps(wrapped)
        def wrapper(*args, **kwargs):
            return wrapped(*args, **kwargs)
        wrapper._apispec_wrapped = wrapped
        wrapper._apispec_operation = {
            'args': spec_args,
            'kwargs': spec_kwargs,
        }
        return wrapper

    return decorator




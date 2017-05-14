# encoding: utf-8
from __future__ import unicode_literals

import functools


def apispec_operation(*spec_args, **spec_kwargs):

    def decorator(wrapped):
        @functools.wraps(wrapped)
        def wrapper(*args, **kwargs):
            return wrapped(*args, **kwargs)
        wrapper._apispec_wrapped = wrapped
        wrapper._apispec_args = spec_args
        wrapper._apispec_kwargs = spec_kwargs
        return wrapper

    return decorator



def apispec_definition(*spec_args, **spec_kwargs):

    def decorator(wrapped):
        @functools.wraps(wrapped)
        def wrapper(*args, **kwargs):
            return wrapped(*args, **kwargs)

        # pull fields from wrapped serializer class
        properties = {}
        serializer = wrapped()
        for field_name, field in serializer.get_fields().items():
            help_text = getattr(field, 'help_text', None)
            properties[field_name] = {
                'type': "string",
                'format': field.__class__.__name__,  # fixme
            }
            if help_text:
                properties['description'] = help_text
        wrapper._apispec_field_properties = properties.copy()

        #properties specified in spec_kwargs override field defaults
        properties.update( spec_kwargs.get('properties', {}) )
        spec_kwargs['properties'] = properties

        wrapper._apispec_wrapped = wrapped
        wrapper._apispec_args = spec_args
        wrapper._apispec_kwargs = spec_kwargs
        return wrapper

    return decorator


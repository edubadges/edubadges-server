# encoding: utf-8
from __future__ import unicode_literals

import functools
from collections import OrderedDict

from mainsite.api_docs import BadgrAPISpec, BadgrAPISpecBuilder


def _decorate_wrapper_with_apispec(wrapper, wrapped, *args, **kwargs):
    wrapper._apispec_wrapped = wrapped
    wrapper._apispec_args = args
    wrapper._apispec_kwargs = kwargs
    return wrapper


def apispec_operation(*spec_args, **spec_kwargs):
    def decorator(wrapped):
        @functools.wraps(wrapped)
        def wrapper(*args, **kwargs):
            return wrapped(*args, **kwargs)
        return _decorate_wrapper_with_apispec(wrapper, wrapped, *spec_args, **spec_kwargs)
    return decorator


def apispec_get_operation(entity_class_name, *spec_args, **spec_kwargs):

    defaults = {
        'responses': OrderedDict([
            ("200", {
                'schema': {'$ref': '#/definitions/{}'.format(entity_class_name)},
                'description': "Successful operation"
            }),
            ("404", {
                'description': "{} not found".format(entity_class_name)
            })
        ])
    }
    spec_kwargs = BadgrAPISpec.merge_specs(defaults, spec_kwargs)

    def decorator(wrapped):
        @functools.wraps(wrapped)
        def wrapper(*args, **kwargs):
            return wrapped(*args, **kwargs)
        return _decorate_wrapper_with_apispec(wrapper, wrapped, *spec_args, **spec_kwargs)
    return decorator


def apispec_put_operation(entity_class_name, *spec_args, **spec_kwargs):
    defaults = {
        'responses': OrderedDict([

            ("200", {
                'schema': {'$ref': '#/definitions/{}'.format(entity_class_name)},
                'description': "Successfully updated"
            }),
            ("400", {
                'description': "Validation error"
            }),
            ("404", {
                'description': "{} not found".format(entity_class_name)
            })
        ]),
        'parameters': [
            {
                "in": "body",
                "name": "body",
                "required": True,
                'schema': {'$ref': '#/definitions/{}'.format(entity_class_name)},
            }
        ]
    }
    spec_kwargs = BadgrAPISpec.merge_specs(defaults, spec_kwargs)

    def decorator(wrapped):
        @functools.wraps(wrapped)
        def wrapper(*args, **kwargs):
            return wrapped(*args, **kwargs)
        return _decorate_wrapper_with_apispec(wrapper, wrapped, *spec_args, **spec_kwargs)
    return decorator


def apispec_delete_operation(entity_class_name, *spec_args, **spec_kwargs):

    defaults = {
        'responses': OrderedDict([
            ("204", {
                'description': "{} was deleted successfully.".format(entity_class_name)
            }),
            ("404", {
                'description': "{} not found".format(entity_class_name)
            })
        ])
    }
    spec_kwargs = BadgrAPISpec.merge_specs(defaults, spec_kwargs)

    def decorator(wrapped):
        @functools.wraps(wrapped)
        def wrapper(*args, **kwargs):
            return wrapped(*args, **kwargs)
        return _decorate_wrapper_with_apispec(wrapper, wrapped, *spec_args, **spec_kwargs)
    return decorator


def apispec_list_operation(entity_class_name, *spec_args, **spec_kwargs):

    defaults = {
        'responses': OrderedDict([
            ("200", {
                'schema': {
                    'type': "array",
                    'items': {'$ref': '#/definitions/{}'.format(entity_class_name)},
                },
                'description': "Successful operation"
            }),
        ])
    }
    spec_kwargs = BadgrAPISpec.merge_specs(defaults, spec_kwargs)

    def decorator(wrapped):
        @functools.wraps(wrapped)
        def wrapper(*args, **kwargs):
            return wrapped(*args, **kwargs)
        return _decorate_wrapper_with_apispec(wrapper, wrapped, *spec_args, **spec_kwargs)
    return decorator


def apispec_post_operation(entity_class_name, *spec_args, **spec_kwargs):

    defaults = {
        'responses': OrderedDict([
            ("201", {
                'schema': {'$ref': '#/definitions/{}'.format(entity_class_name)},
                'description': "Successfully created"
            }),
            ("400", {
                'description': "Validation error"
            })
        ]),
        'parameters': [
            {
                "in": "body",
                "name": "body",
                "required": True,
                'schema': {'$ref': '#/definitions/{}'.format(entity_class_name)},
            }
        ]
    }
    spec_kwargs = BadgrAPISpec.merge_specs(defaults, spec_kwargs)

    def decorator(wrapped):
        @functools.wraps(wrapped)
        def wrapper(*args, **kwargs):
            return wrapped(*args, **kwargs)
        return _decorate_wrapper_with_apispec(wrapper, wrapped, *spec_args, **spec_kwargs)
    return decorator

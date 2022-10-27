from django.core.cache import cache
from functools import wraps

from cachemodel import CACHE_FOREVER_TIMEOUT
from cachemodel.utils import generate_cache_key

def cached_method(auto_publish=False):
    """A decorator for CacheModel methods."""
    def decorator(target):
        @wraps(target)
        def wrapper(self, *args, **kwargs):
            key = generate_cache_key([self.__class__.__name__, target.__name__, self.pk], *args, **kwargs)
            data = cache.get(key)
            if data is None:
                data = target(self, *args, **kwargs)
                cache.set(key, data, CACHE_FOREVER_TIMEOUT)
            return data
        wrapper._cached_method = True
        wrapper._cached_method_auto_publish = auto_publish
        wrapper._cached_method_target = target
        return wrapper

    if callable(auto_publish):
        # we were used with no parens, fixup args 
        func = auto_publish
        auto_publish = False
        return decorator(func)
    else:
        return decorator


def denormalized_field(field_name):
    """A decorator for CacheModel methods.

    - pass the field name to denormalize into into the decorator
    - the return of the function will be stored in the database field on each save

    Arguments:
      field_name -- the name of a field on the model that will store the results of the function
    """
    def decorator(target):
        @wraps(target)
        def wrapper(self):
            return target(self)
        wrapper._denormalized_field = True
        wrapper._denormalized_field_name = field_name
        return wrapper

    if callable(field_name):
        # we were used without an argument
        raise ArgumentErrror("You must pass a field name to @denormalized_field")
        
    return decorator

def find_fields_decorated_with(instance, property_name):
    """helper function that finds all methods decorated with property_name"""
    non_field_attributes = set(dir(instance.__class__)) - set(instance._meta.get_fields())
    for m in non_field_attributes:
        if hasattr(getattr(instance.__class__, m), property_name):
            yield getattr(instance.__class__, m)


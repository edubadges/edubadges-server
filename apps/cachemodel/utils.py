from hashlib import md5

import six
from django.utils.encoding import smart_bytes


def generate_cache_key(prefix, *args, **kwargs):
    arg_str = ":".join(smart_bytes(a) for a in args)
    kwarg_str = ":".join("{}={}".format(smart_bytes(k), smart_bytes(v)) for k, v in list(kwargs.items()))
    key_str = "{}::{}".format(arg_str, kwarg_str)
    argkwarg_str = md5(smart_bytes(key_str)).hexdigest()
    if not isinstance(prefix, six.string_types):
        prefix = "_".join(str(a) for a in prefix)
    return "{}__{}".format(prefix, argkwarg_str)

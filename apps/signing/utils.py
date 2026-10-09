import hashlib


def hash_string(str):  # noqa: A002
    return hashlib.sha256(str).hexdigest()

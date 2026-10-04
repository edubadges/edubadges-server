import hashlib


def hash_string(str):
    return hashlib.sha256(str).hexdigest()

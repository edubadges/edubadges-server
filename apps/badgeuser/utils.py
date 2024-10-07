import random
import string
import base64
from hashlib import sha256


def generate_badgr_username(email):
    # sha256 hash the email and then encode as base64 to take up only 25 characters
    salted_email = (
        email + "".join(random.choice(string.ascii_lowercase) for i in range(64))
    ).encode("utf-8")
    hashed = str(
        base64.b64encode(sha256(salted_email).hexdigest().encode("utf-8")), "utf-8"
    )
    return "badgr{}".format(hashed[:25])

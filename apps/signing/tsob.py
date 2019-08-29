import requests
import json
from signing.models import PrivateKey

TSOB_BASE_URL = 'http://127.0.0.1:3000/'


def create_new_symmetric_key(password, salt='salt', length=32, n=1048576, r=8, p=1):
    return requests.post(TSOB_BASE_URL+'symmetrickey/',
                         data=json.dumps({
                             "password": password,
                             "salt": salt,
                             "length": length,
                             "n": n,
                             "r": r,
                             "p": p
                         }),
                         headers={'content-type': 'application/json'})


def create_new_private_key(password, symmetric_key):
    response = requests.post(TSOB_BASE_URL + 'privatekey/',
                             data=json.dumps({
                                 "password": password,
                                 "salt": symmetric_key.salt,
                                 "length": symmetric_key.length,
                                 "n": symmetric_key.n,
                                 "r": symmetric_key.r,
                                 "p": symmetric_key.p
                             }),
                             headers={'content-type': 'application/json'}).json()
    private_key = PrivateKey.objects.create(
        user=symmetric_key.user,
        symmetric_key=symmetric_key,
        encrypted_private_key=response['encrypted_private_key'],
        initialization_vector=response['initialization_vector'],
        tag=response['tag'],
        associated_data=response['associated_data'],
        time_created=response['time_created'],
        hash_of_public_key=response['hash_of_public_key']
    )
    return private_key



def re_encrypt_private_keys(old_symmetric_key, new_symmetric_key, private_key_list):
    return requests.post(TSOB_BASE_URL + 'reencrypt/',
                         data=json.dumps({
                             "old_symmetric_key": old_symmetric_key,
                             "new_symmetric_key": new_symmetric_key,
                             "private_key_list": private_key_list
                         }),
                         headers={'content-type': 'application/json'})


def sign_badges(list_of_assertions, password, symmetric_key):
    symmetric_key.validate_password(password)
    symkey_params = symmetric_key.get_params()
    symkey_params['password'] = password
    private_key = create_new_private_key(password, symmetric_key)
    private_key_params = private_key.get_params()
    list_of_badges = []
    for assertion in list_of_assertions:
        list_of_badges.append(assertion.get_json(expand_badgeclass=True, expand_issuer=True, signed=True))

    response = requests.post(TSOB_BASE_URL + 'sign/',
                                      data=json.dumps({
                                         "list_of_badges": list_of_badges,
                                         "symmetric_key": symkey_params,
                                         "private_key": private_key_params
                                      }),
                                      headers={'content-type': 'application/json'}).json()

    return response['signed_badges']


def deep_validate(signed_badges, symmetric_key, private_key):
    return requests.post(TSOB_BASE_URL + 'deepvalidate/',
                  data=json.dumps({
                      "signed_badges": signed_badges,
                      "symmetric_key": symmetric_key,
                      "private_key": private_key
                  }),
                  headers={'content-type': 'application/json'})



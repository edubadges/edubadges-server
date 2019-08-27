import requests
import json

TSOB_BASE_URL = 'http://127.0.0.1:3000/'


def create_new_symmetric_key(password, salt, length=32, n=1048576, r=8, p=1):
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


def create_new_private_key(password, symmmetric_key):
    return requests.post(TSOB_BASE_URL+'privatekey/',
                         data=json.dumps({
                             "password": password,
                             "salt": symmmetric_key['salt'],
                             "length": symmmetric_key['length'],
                             "n": symmmetric_key['n'],
                             "r": symmmetric_key['r'],
                             "p": symmmetric_key['p']
                         }),
                         headers={'content-type': 'application/json'})


def re_encrypt_private_keys(old_symmetric_key, new_symmetric_key, private_key_list):
    return requests.post(TSOB_BASE_URL + 'reencrypt/',
                         data=json.dumps({
                             "old_symmetric_key": old_symmetric_key,
                             "new_symmetric_key": new_symmetric_key,
                             "private_key_list": private_key_list
                         }),
                         headers={'content-type': 'application/json'})


def sign_badges(list_of_badges, symmetric_key, private_key):
    return requests.post(TSOB_BASE_URL + 'sign/',
                         data=json.dumps({
                             "list_of_badges": list_of_badges,
                             "symmetric_key": symmetric_key,
                             "private_key": private_key
                         }),
                         headers={'content-type': 'application/json'})


def deep_validate(signed_badges, symmetric_key, private_key):
    return requests.post(TSOB_BASE_URL + 'deepvalidate/',
                  data=json.dumps({
                      "signed_badges": signed_badges,
                      "symmetric_key": symmetric_key,
                      "private_key": private_key
                  }),
                  headers={'content-type': 'application/json'})



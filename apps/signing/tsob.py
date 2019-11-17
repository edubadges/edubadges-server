import requests
import json
from django.conf import settings
from signing.models import PrivateKey, PublicKey, SymmetricKey
from signing import utils

def create_new_symmetric_key(password, user, salt='salt', length=32, n=1048576, r=8, p=1):
    symkey_json = requests.post(settings.TIME_STAMPED_OPEN_BADGES_BASE_URL+'symmetrickey/',
                         data=json.dumps({
                             "password": password,
                             "salt": salt,
                             "length": length,
                             "n": n,
                             "r": r,
                             "p": p
                         }),
                         headers={'content-type': 'application/json'}).json()
    new_symkey = SymmetricKey.objects.create(
        password_hash=utils.hash_string(password),
        salt=symkey_json['salt'],
        length=symkey_json['length'],
        n=symkey_json['n'],
        r=symkey_json['r'],
        p=symkey_json['p'],
        current=False,
        user=user
    )
    return new_symkey


def create_new_private_key(password, symmetric_key):
    response = requests.post(settings.TIME_STAMPED_OPEN_BADGES_BASE_URL + 'privatekey/',
                             data=json.dumps({
                                 "password": password,
                                 "salt": symmetric_key.salt,
                                 "length": symmetric_key.length,
                                 "n": symmetric_key.n,
                                 "r": symmetric_key.r,
                                 "p": symmetric_key.p
                             }),
                             headers={'content-type': 'application/json'}).json()

    public_key = PublicKey.objects.create(
        public_key_pem=response['public_key'],
        time_created=response['time_created'],
    )

    private_key = PrivateKey.objects.create(
        symmetric_key=symmetric_key,
        encrypted_private_key=response['encrypted_private_key'],
        initialization_vector=response['initialization_vector'],
        tag=response['tag'],
        associated_data=response['associated_data'],
        time_created=response['time_created'],
        public_key=public_key
    )
    private_key.refresh_from_db()  # must do this so time_created is not unicode, but datetime object
    return private_key


def re_encrypt_private_keys(old_symmetric_key, new_symmetric_key, old_password, new_password, private_key_list):
    for pk in private_key_list:
        if pk.symmetric_key != old_symmetric_key:
            raise ValueError('Private keys must belong to the symmetric key.')

    if not private_key_list:
        raise ValueError('No private keys passed to function.')

    old_symmetric_key_params = old_symmetric_key.get_params()
    old_symmetric_key_params['password'] = old_password
    new_symmetric_key_params = new_symmetric_key.get_params()
    new_symmetric_key_params['password'] = new_password

    response = requests.post(settings.TIME_STAMPED_OPEN_BADGES_BASE_URL + 'reencrypt/',
                         data=json.dumps({
                             "old_symmetric_key": old_symmetric_key_params,
                             "new_symmetric_key": new_symmetric_key_params,
                             "private_key_list": [pk.get_params() for pk in private_key_list]
                         }),
                         headers={'content-type': 'application/json'})
    if response.status_code == 200:
        for reencrypted_private_key in response.json():
            matching_previous_private_key = [pk for pk in private_key_list if pk.public_key.public_key_pem == reencrypted_private_key['public_key']][0]
            matching_previous_private_key.symmetric_key = new_symmetric_key
            matching_previous_private_key.encrypted_private_key = reencrypted_private_key['encrypted_private_key']
            matching_previous_private_key.initialization_vector=reencrypted_private_key['initialization_vector']
            matching_previous_private_key.tag = reencrypted_private_key['tag']
            matching_previous_private_key.associated_data = reencrypted_private_key['associated_data']
            matching_previous_private_key.time_created = reencrypted_private_key['time_created'],
            matching_previous_private_key.time_created = reencrypted_private_key['time_created']
            matching_previous_private_key.save()
    else:
        message = response.json().get('message', '')
        if message == 'Encrypted key error: Not able to decrypted private key. - Derived tag invalid.':
            raise ValueError('Wrong password entered. Please try again.')
        else:
            raise ValueError(message)


def sign_badges(list_of_assertions, private_key, symmetric_key, password):
    private_key_params = private_key.get_params()
    symmetric_key_params = symmetric_key.get_params()
    symmetric_key_params['password'] = password

    response = requests.post(settings.TIME_STAMPED_OPEN_BADGES_BASE_URL + 'sign/',
                                      data=json.dumps({
                                         "list_of_badges": list_of_assertions,
                                         "symmetric_key": symmetric_key_params,
                                         "private_key": private_key_params
                                      }),
                                      headers={'content-type': 'application/json'})

    if response.status_code == 200:
        signed_badges_json = response.json()['signed_badges']
        return signed_badges_json
    else:
        raise ValueError(response.json()['message'])


def deep_validate(signed_badges, symmetric_key, private_key):
    return requests.post(settings.TIME_STAMPED_OPEN_BADGES_BASE_URL + 'deepvalidate/',
                  data=json.dumps({
                      "signed_badges": signed_badges,
                      "symmetric_key": symmetric_key,
                      "private_key": private_key
                  }),
                  headers={'content-type': 'application/json'})

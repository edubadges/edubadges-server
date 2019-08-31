import requests
import json
from django.conf import settings
from signing.models import PrivateKey


def create_new_symmetric_key(password, salt='salt', length=32, n=1048576, r=8, p=1):
    return requests.post(settings.TIME_STAMPED_OPEN_BADGES_BASE_URL+'symmetrickey/',
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


def re_encrypt_private_keys(old_symmetric_key, new_symmetric_key, old_password, new_password):
    private_keys_to_reencrypt = PrivateKey.objects.filter(symmetric_key=old_symmetric_key)

    if not private_keys_to_reencrypt:
        new_symmetric_key.current = True
        new_symmetric_key.save()
        old_symmetric_key.current = False
        old_symmetric_key.save()
        return

    old_symmetric_key_params = old_symmetric_key.get_params()
    old_symmetric_key_params['password'] = old_password
    new_symmetric_key_params = new_symmetric_key.get_params()
    new_symmetric_key_params['password'] = new_password
    private_key_list = [pk.get_params() for pk in private_keys_to_reencrypt]

    response = requests.post(settings.TIME_STAMPED_OPEN_BADGES_BASE_URL + 'reencrypt/',
                         data=json.dumps({
                             "old_symmetric_key": old_symmetric_key_params,
                             "new_symmetric_key": new_symmetric_key_params,
                             "private_key_list": private_key_list
                         }),
                         headers={'content-type': 'application/json'})
    if response.status_code == 200:
        for reencrypted_private_key in response.json():
            PrivateKey.objects.create(
                user=new_symmetric_key.user,
                symmetric_key=new_symmetric_key,
                encrypted_private_key=reencrypted_private_key['encrypted_private_key'],
                initialization_vector=reencrypted_private_key['initialization_vector'],
                tag=reencrypted_private_key['tag'],
                associated_data=reencrypted_private_key['associated_data'],
                time_created=reencrypted_private_key['time_created'],
                hash_of_public_key=reencrypted_private_key['hash_of_public_key']
            )
        [pk.delete() for pk in private_keys_to_reencrypt]
        new_symmetric_key.current = True
        new_symmetric_key.save()
        old_symmetric_key.current = False
        old_symmetric_key.save()
    else:
        new_symmetric_key.delete()
        message = response.json().get('message', '')
        if message == 'Encrypted key error: Not able to decrypted private key. - Derived tag invalid.':
            raise ValueError('Wrong password entered. Please try again.')
        else:
            raise ValueError(message)


def sign_badges(list_of_assertions, password, symmetric_key):
    symmetric_key.validate_password(password)
    symkey_params = symmetric_key.get_params()
    symkey_params['password'] = password
    private_key = create_new_private_key(password, symmetric_key)
    private_key_params = private_key.get_params()
    list_of_badges = []
    for assertion in list_of_assertions:
        list_of_badges.append(assertion.get_json(expand_badgeclass=True, expand_issuer=True, signed=True))

    response = requests.post(settings.TIME_STAMPED_OPEN_BADGES_BASE_URL + 'sign/',
                                      data=json.dumps({
                                         "list_of_badges": list_of_badges,
                                         "symmetric_key": symkey_params,
                                         "private_key": private_key_params
                                      }),
                                      headers={'content-type': 'application/json'}).json()

    return response['signed_badges']


def deep_validate(signed_badges, symmetric_key, private_key):
    return requests.post(settings.TIME_STAMPED_OPEN_BADGES_BASE_URL + 'deepvalidate/',
                  data=json.dumps({
                      "signed_badges": signed_badges,
                      "symmetric_key": symmetric_key,
                      "private_key": private_key
                  }),
                  headers={'content-type': 'application/json'})



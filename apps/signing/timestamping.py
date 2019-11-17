import json
import subprocess
from signing.utils import hash_string


def canonicalize_json(json_object):
    """
    :param json_object: json
    :return: canonicalized json string
    """
    return json.dumps(
        json_object,
        sort_keys=True,
        separators=(',', ':'),
    ).encode()


def submit_hash(hash256):
    """
    :param hash256: a hash as string
    :return: a list of node_hash_ids
    """
    node_hash_ids = []
    outputs_raw = subprocess.check_output(['chp', 'submit', hash256])
    outputs = outputs_raw.split('\n')
    for output in outputs:
        try:
            node_hash_id, hash_as_string, action = output.split(' | ')
            if action == 'submitted':
                node_hash_ids.append(node_hash_id)
        except ValueError:
            pass
    return node_hash_ids


def retrieve_proof(node_hash_id):
    """
    :param node_hash_id: a node_hash_id
    :return: proof as canonicalized json
    """
    shown_proof = subprocess.check_output(['chp', 'show', node_hash_id])
    try:
        return json.loads(shown_proof)
    except ValueError:
        raise ValueError('Returned proof invalid')


def verify_proof(node_hash_id):
    """
    :param node_hash_id: the id for the proof
    :return: verification object
    """
    verification = subprocess.check_output(['chp', 'verify', node_hash_id])
    return verification.split(' | ')


def submit_json_for_timestamping(json_object):
    canonicalized_json = canonicalize_json(json_object)
    hashed_json = hash_string(canonicalized_json)
    node_hash_ids = submit_hash(hashed_json)
    return canonicalized_json, hashed_json, node_hash_ids
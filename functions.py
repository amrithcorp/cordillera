from stellar_sdk import (
    TransactionBuilder,
    Network,
    Server,
    Account,
    Keypair,
    Asset as Stellar_Asset,
    Claimant,
    ClaimPredicate,
)
from stellar_sdk.sep.stellar_web_authentication import (
    build_challenge_transaction,
    read_challenge_transaction,
    verify_challenge_transaction_signed_by_client_master_key,
    verify_challenge_transaction_threshold,
)
from stellar_sdk.exceptions import NotFoundError
from stellar_sdk.sep.exceptions import InvalidSep10ChallengeError

import datetime
import jwt
import hashlib 

from app import other_config

from flask import request

horizon_server = Server(other_config['horizon'])
server_keypair = Keypair.from_secret(other_config['auth_server_key'])

import hashlib

def verify_authorization(instance_id,source_account,authorization):
    keypair = Keypair.from_public_key(source_account)
    signed_message = (source_account + ":" + instance_id)
    hashed_message = hashlib.sha256(signed_message.encode('utf-8')).digest()
    try:
        keypair.verify(hashed_message,bytes.fromhex(authorization))
        return {
        "error" : False
        }
    except:
        return {
            "error" : True,
            "error_message" : "bad_authorization"
        }


def build_challenge(key):
    # Three possible outcomes:
    #   - Success, return a valid transaction XDR
    #   - Error, Invalid key, return error: invalid_key
    #   - Error, Account does not exist, return error: no_account
    try:
        if len(key) != 56 or key[0] != "G":
            return {
                "error" : True,
                "error_message" : "invalid_key"
            }

        client_account = None

        try:
            client_account = horizon_server.load_account(key)
        except NotFoundError:
            return {
                "error" : True,
                "error_message" : "no_account"
            }

        challenge_transaction = build_challenge_transaction(
            other_config['auth_server_key'],
            key,
            other_config['domain'],
            other_config['domain'],
            Network.PUBLIC_NETWORK_PASSPHRASE,
            300
        )    

        return {
            "error" : False,
            "challenge_transaction" : challenge_transaction
        }
    except:
        return {
            "error" : True,
            "error_message" : "bad_request"
        }

def verify_challenge(key,challenge_transaction):
    # Four possible outcomes:
    #   - Success, return a valid session token
    #   - Error, Invalid challenge transaction: invalid_challange_tx
    #   - Error, Incorrect signer: bad_signer
    try:
        client_account = None
        try: 
            client_account = horizon_server.load_account(key)
        except NotFoundError:
            return {
                "error" : True,
                "error_message" : "no_account"
            }
        signers = client_account.load_ed25519_public_key_signers()
        threshold = client_account.thresholds.med_threshold
        try:
            signers_found = verify_challenge_transaction_threshold(
                challenge_transaction,
                server_keypair.public_key,
                other_config['domain'],
                other_config['domain'],
                Network.PUBLIC_NETWORK_PASSPHRASE,
                threshold,
                signers,
            )
        except InvalidSep10ChallengeError as e:
            return {
                "error" : True,
                "error_message" : "bad_challenge_transaction"
            }
        time_now = datetime.datetime.utcnow()
        new_session = jwt.encode({
            "sub" : key,
            # "iat" : time_now.timestamp(),
            "exp" : (time_now + datetime.timedelta(hours=12)).timestamp()
            },
            other_config['auth_key'],
            algorithm = 'HS256'
        )
        return {
            "error" : False,
            "session_token" : new_session
        }
    except:
        return {
            "error" : True,
            "error_message" : "bad_request"
        }

def authorize():
    auth_token = request.cookies.get('auth_session')
    if auth_token == None:
        return {
            "error" : True,
            "error_message" : "no_token"
        }
    try:
        token = jwt.decode(auth_token,other_config['auth_key'],['HS256'])
        return {
            "error" : False,
            "key" : token['sub']
        }
    except jwt.ExpiredSignatureError:
        return {
            "error" : True,
            "error_message" : "expired_sig"
        }

def ca_check(response):
    class ca_check_class:
        valid = True
        error = None 
    check = ca_check_class
    total_percent = 0
    for i in response['trades']:
        total_percent += i['percent']
    if len(response['source_account']) != 56 and response['source_account'][0] != "G":
        check.valid = False
        check.error = "bad_source_account"
    elif (
        len(response['source_asset']) > 68
        and len(response['source_asset']) < 57 
        and len(response['source_asset'].split(":")) !=2
        and response['source_asset'].split(":")[1][0] == "G"
        and len(response['source_asset'].split(":")[1]) == 56
        ):
        check.valid = False
        check.error = "bad_source_asset"
    elif len(response['send_to']) != 56 and response['send_to'][0] != "G":
        check.valid = False
        check.error = "bad_send_to"
    elif not isinstance(response['op_fee'],int):
        check.valid = False
        check.error = "bad_op_fee"  
    elif response['amount'] != "all" and not isinstance(response['amount'],int):
        check.valid = False
        check.error = "bad_amount"
    elif not isinstance(response['max_slippage'],int):
        check.valid = False
        check.error = "bad_max_slippage"
    elif total_percent != 100:
        check.valid = False
        check.error = "percent_not_100"  
    else:
        for trade in response['trades']:
            if(len(response['source_asset']) > 68
                and len(response['source_asset']) < 57 
                and len(response['source_asset'].split(":")) !=2
                and response['source_asset'].split(":")[1][0] == "G"
                and len(response['source_asset'].split(":")[1]) == 56
            ):
                check.valid = False
                check.error = "bad_trade_asset"
    return check

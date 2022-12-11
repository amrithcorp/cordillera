server_address = "GBCPV3SCOKFJBSIM3JNLZVWEVEJVSADN4E3FFP3NVXLGA4K5QOKLA2ME"
server_secret = "SALREOZKMVAPCSZQ56IYZ2FEGF6VIMPZT7H2A55BP7HU3BHCIVGENHI7"

from stellar_sdk import (
    Server,
    Account,
    Asset,
    TransactionBuilder,
    Keypair,
    Network
)
from stellar_sdk.exceptions import BadRequestError

import hashlib

server = Server('https://horizon.stellar.org/')

from models import *

class ca_check_class:
    valid = True
    error = None 

def ca_check(config):
    check = ca_check_class
    total_percent = 0
    for i in config['trades']:
        total_percent += i['percent']
    if len(config['source_account']) != 56 and config['source_account'][0] != "G":
        check.valid = False
        check.error = "bad_source_account"
    elif (
        len(config['source_asset']) > 68
        and len(config['source_asset']) < 57 
        and len(config['source_asset'].split(":")) !=2
        and config['source_asset'].split(":")[1][0] == "G"
        and len(config['source_asset'].split(":")[1]) == 56
        ):
        check.valid = False
        check.error = "bad_source_asset"
    elif len(config['send_to']) != 56 and config['send_to'][0] != "G":
        check.valid = False
        check.error = "bad_send_to"
    elif not isinstance(config['op_fee'],int):
        check.valid = False
        check.error = "bad_op_fee"  
    elif config['source_asset']['amount_per_hour'] != "all" and (not isinstance(config['source_asset']['amount_per_hour'],int) and not isinstance(config['source_asset']['amount_per_hour'],float)):
        check.valid = False
        check.error = "bad_amount"
    elif not isinstance(config['max_slippage'],float):
        check.valid = False
        check.error = "bad_max_slippage"
    elif total_percent != 100:
        check.valid = False
        check.error = "percent_not_100"  
    else:
        for trade in config['trades']:
            if(
                len(trade['code']) > 12
                or len(trade['issuer']) != 56
                or not isinstance(trade['percent'],int)
            ):
                check.valid = False
                check.error = "bad_trade_asset"
    if check.valid:
        return {
            "error" : False
        }
    else:
        return {
            "error" : True,
            "msg" : check.error
        }

def is_valid_signer(server_address,source_account):
    check = ca_check_class()

    account = server.load_account(source_account)
    
    signers = account.load_ed25519_public_key_signers()
    server_present = False
    server_weight = 0
    for signer in signers:
        if signer.account_id == server_address:
            server_present = True
            server_weight = signer.weight
    if not server_present:
        return {
            "error" : True,
            "msg" : "server_not_present"
        }
    else:
        if server_weight < account.thresholds.med_threshold:
            return {
                "error" : True,
                "msg" : "bad_med_threshold"
            }
        else:
            return {
                "error" : False
            }

def check_balance(balances,source_account,asset_code,asset_issuer):
    for balance in balances:
        if (
            (balance['asset_type'] == "credit_alphanum4" or balance['asset_type'] == "credit_alphanum12") 
            and (balance['asset_code'] == asset_code and balance['asset_issuer'] == asset_issuer)):
            return {
                "error" : False,
                "balance" : float(balance['balance'])
            }
    else:
        return {
            "error" : True,
            "msg" : "mssing_source_trustline"
        }

def has_all_trustlines(send_to_account,trades):
    account = server.load_account(send_to_account)
    for trade in trades:
        if check_balance(
            balances = account.raw_data['balances'],
            source_account = send_to_account,
            asset_code = trade['code'],
            asset_issuer = trade['issuer']
        )['error']:
            return {
                "error" : True,
                "msg" : "missing_send_to_trustlines"
            }
    return {
        "error" : False
    }

def get_best_path(send_asset, to_asset,amount,config):
    if amount == 0:
        return {
            "error" : True,
            "msg" : "amount_zero"
        }
    amount=str(round(amount,7))
    r = server.strict_send_paths(
        source_asset=Asset(send_asset['code'],send_asset['issuer']),
        source_amount=amount,
        destination=[Asset(to_asset['code'],to_asset['issuer'])]
    ).call()
    path = []
    if len(r['_embedded']['records']) > 0:
        for i in r['_embedded']['records'][0]['path']:
            if i['asset_type'] == "native":
                path.append(Asset.native())
            else:
                path.append(Asset(
                    code = i['asset_code'],
                    issuer = i['asset_issuer']
                ))
        minimum_amount = str(round((float( r['_embedded']['records'][0]['destination_amount'])*((100 - config['max_slippage'])/100)),7))
        return {
            "error" : False,
            "path" : path,
            "amount" : r['_embedded']['records'][0]['destination_amount'],
            "minimum_amount" : (minimum_amount if minimum_amount != "0.0000001" else "0.0000001")
        }
    else:
        return {
            "error" : True,
            "msg" : "no_paths"
        }

def send_trades(trades,config,server_secret):
    source_account = server.load_account(config['source_account'])
    transaction = (TransactionBuilder(
        source_account = source_account,
        network_passphrase = Network.PUBLIC_NETWORK_PASSPHRASE,
        base_fee = config['op_fee']
        )
        .set_timeout(300)
        .add_text_memo(config['memo'])
    )
    op_count = 0
    total_usd_settled = 0
    for trade in trades:
        if trade['asset']['code'] == config['source_asset']['code'] and trade['asset']['issuer'] == config['source_asset']['issuer']:
            transaction.append_payment_op(
                destination = config['send_to'],
                asset = Asset(config['source_asset']['code'],config['source_asset']['issuer']),
                amount = str(round(
                    (0.01*trade['asset']['percent'])*(config['source_asset']['amount_per_hour']),7
                )),
            )
        else:
            transaction.append_path_payment_strict_send_op(
                source = config['source_account'],
                send_asset = Asset(
                    config['source_asset']['code'],
                    config['source_asset']['issuer']
                ),
                send_amount = str(round(
                    (0.01*trade['asset']['percent'])*(config['source_asset']['amount_per_hour']),7
                )),
                dest_asset = Asset(
                    trade['asset']['code'],
                    trade['asset']['issuer']
                ),
                dest_min = trade['minimum_amount'],
                path = trade['path'],
                destination = config['send_to']
            )
        op_count += 1
        if not trade['usd_settled']['error']:
            total_usd_settled += float(trade['usd_settled']['usd_settled'])
    if op_count == 0:
        return {
            "error" : True,
            "msg" : "no_ops"
        }
    else:
        completed = transaction.build()
        server_keypair = Keypair.from_secret(server_secret)
        completed.sign(server_keypair)
        try:
            response = server.submit_transaction(completed)
            return {
                "error" : False,
                "transaction_hash" : response['hash'],
            }
        except BadRequestError as response:
            return {
                "error" : True,
                "msg" : "horizon_error",
                "context" : response.extras['result_codes']
            }

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



def get_usd_settled(asset_code,asset_issuer,amount):
    try:
        path = get_best_path(
            {"code" : asset_code, "issuer" : asset_issuer},
            {"code" : "USDC","issuer": "GA5ZSEJYB37JRC5AVCIA5MOP4RHTM335X2KGX3IHOJAPP5RE34K4KZVN"},
            float(amount)
        )
        if path['error']:
            return path
        else: return {
            "error" : False,
            "usd_settled" : path['amount']
        }
    except:
        return{
            "error" : True,
            "msg" : "usd_error"
        }

def script(config):
    config_check = ca_check(config)
    if config_check['error']: 
        return config_check
    else:
        signer_check = is_valid_signer(
            server_address = server_address,
            source_account = config['source_account']
        )
        if signer_check['error']:
            return signer_check
        else:
            account = server.load_account(config['source_account'])
            balance_check = check_balance(
                account.raw_data['balances'],
                config['source_account'],
                config['source_asset']['code'],
                config['source_asset']['issuer']
            )
            if balance_check['error']:
                return balance_check
            else:
                trustlines_check = has_all_trustlines(
                    send_to_account = config['send_to'],
                    trades = config['trades']
                )
                if trustlines_check['error']:
                    return trustlines_check
                else:
                    if config['source_asset']['amount_per_hour'] == "all": config['source_asset']['amount_per_hour'] = balance_check['balance']
                    if (balance_check['balance']) < config['source_asset']['amount_per_hour']:
                        return {
                            "error" : True,
                            "msg" : "insufficient_balance"
                        }
                    tradeList = []
                    for trade in config['trades']:
                        path_check = get_best_path(
                            config['source_asset'],
                            trade,
                            (config['source_asset']['amount_per_hour']*(0.01*trade['percent'])),
                            config
                        )    
                        if not path_check['error']:
                            tradeList.append({
                                "asset" : trade,
                                "amount" : path_check['amount'],
                                "minimum_amount" : path_check['minimum_amount'],
                                "path" : path_check['path'],
                                "usd_settled" : get_usd_settled(
                                    trade['code'],
                                    trade['issuer'],
                                    path_check['amount']
                                )
                            })
                    trade_transaction = send_trades(tradeList,config,server_secret)
                    if trade_transaction['error'] and trade_transaction['msg'] == 'horizon_error': 
                        return {
                            "error" : True,
                            "msg" : "horizon_error",
                            "context" : trade_transaction
                        }
                    elif trade_transaction['error'] and trade_transaction['msg'] != "horizon_error":
                        return trade_transaction
                    else:
                        for trade in tradeList:
                            trade['path'] = None
                        return ({
                            "error" : False,
                            "transaction_hash" : trade_transaction['transaction_hash'],
                            "trades" : tradeList
                        })



from sqlalchemy import create_engine
from sqlalchemy.orm import Session

engine = create_engine('postgresql://qtcoxuvx:U_Qo1gyQr3CcEcNrUbtdA3EZxkFqfJqO@peanut.db.elephantsql.com/qtcoxuvx')
session = Session(engine)

import logging

logging.basicConfig()
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)

from models import (
    User,
    Costaverage,
    Costaverage_logs,
    Costaverage_trades
)
import json
import secrets

def run(run_id):
    run = session.query(Costaverage_logs).filter_by(log_lookup=run_id).one_or_none()
    if run != None:
        trades = []
        for trade in run.contract.trades:
            trades.append(
                {
                    "code" : trade.asset.split(':')[0],
                    "issuer" : trade.asset.split(':')[1],
                    "percent" : trade.percent
                }
            )
        config = {
            "source_account" : run.contract.source_account,
            "send_to" : run.contract.send_to,
            "op_fee" : run.contract.fee,
            "memo" : run.contract.memo,
            "max_slippage" : run.contract.max_slippage,
            "source_asset" : {
                "code" : run.contract.source_asset.split(":")[0],
                "issuer" : run.contract.source_asset.split(":")[1],
                "amount_per_hour" : (
                    "all" if run.contract.amount_all else run.contract.amount
                )
            },
            "trades" : trades
        }
        
        run_instance = script(config)
        print(run_instance)
        if run_instance['error']:
            run.error = True
            run.output = run_instance['msg']
        else:
            run.error = False
            run.output = json.dumps(run_instance)
        run.running = False
        run.contract.running = False
        session.commit()

    
run("ebc01520286ba6a2bd35")

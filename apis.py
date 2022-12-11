from app import app,other_config
from flask import render_template, jsonify as js, request
from functions import verify_authorization,verify_challenge, build_challenge,authorize,ca_check
from flask_cors import cross_origin
from models import User,Costaverage,db,Costaverage_trades,Costaverage_logs
from secrets import token_hex
import json
import secrets

@cross_origin
@app.route('/api/build_challenge_tx/<address>')
def build_challenge_tx(address):
    return js(build_challenge(address))

@cross_origin
@app.route('/api/verify_challenge_tx/<address>',methods=['GET','POST'])
def verify_challenge_tx(address):
    challenge_transaction = request.get_json()['challenge_transaction']
    return js(verify_challenge(address,challenge_transaction))

@cross_origin
@app.route('/api/user_info')
def user_info():
    auth = authorize()
    if auth['error']:
        return js({"error" : True, "error_message" : auth['error_message']})
    else:
        ca_contracts = []
        user = User.query.filter_by(public_key = auth['key']).first()
        for ca_contract in user.ca_contracts:
            ca_contracts.append({
                "source_account" : ca_contract.source_account,
                "source_asset" : ca_contract.source_asset,
                "tracker"  : ca_contract.memo,
                "amount" : ("all" if ca_contract.amount_all else ca_contract.amount),
                "instance_lookup" : ca_contract.instance_lookup,
            })
        return js({
            "error" : False,
            "ca_contracts" : ca_contracts
        })

@cross_origin
@app.route('/api/info/trader/<instance_lookup>')
def get_trader_info(instance_lookup):
    auth = authorize()
    if auth['error']:
        return js({"error" : True, "error_message" : auth['error_message']})    
    else:
        user = User.query.filter_by(public_key = auth['key']).first()
        instance = Costaverage.query.filter_by(instance_lookup=instance_lookup).first()
        if not instance == None and instance.owner_id == user.id:
            trades = []        
            for trade in instance.trades:
                trades.append({
                    "percent" : trade.percent,
                    "asset" : trade.asset,
                })
            return js({
                "error" : False,
                "running" : instance.running,
                "server_public" : other_config['worker_public_key'],
                "source_account" : instance.source_account,
                "source_asset" : instance.source_asset,
                "tracker" : instance.memo,
                "amount" : ("all" if instance.amount_all else instance.amount),
                "trades" : trades,
                "slippage" : instance.max_slippage,
                "send_to" : instance.send_to,
                "fee" : instance.fee,
                "instance_id" : instance.instance_lookup,
                "auth_required" : (True if instance.authorization == None else False)

                
            })
        else:
            return js({"error" : True, "error_message" : "no_resource"}) 
import datetime
@app.route('/api/logs/trader/<instance_id>')
def get_trader_logs(instance_id):
    auth = authorize()
    if auth['error']:
        return js({"error" : True, "error_message" : auth['error_message']})    
    else:
        user = User.query.filter_by(public_key = auth['key']).first()
        instance = Costaverage.query.filter_by(instance_lookup=instance_id).first()
        if not instance == None and instance.owner_id == user.id:
            logs = []
            now = datetime.datetime.utcnow()
            for log in instance.logs:
                logs.append({
                    "error" : log.error,
                    "running" : log.running,
                    "id" : log.log_lookup,
                    "log_time" : (now - log.time).total_seconds()
                })
            return js({
                "error" : False,
                "logs" : sorted(logs, key=lambda i: i['log_time'])
            })
        else:
            return js({
                "error" : True,
                "error_message" : "no_resource"
            })

@app.route('/api/delete_contract/trader/<instance_id>')
def delete_trader(instance_id):
    auth = authorize()
    if auth['error']:
        return js({"error" : True, "error_message" : auth['error_message']})    
    else:
        user = User.query.filter_by(public_key = auth['key']).first()
        instance = Costaverage.query.filter_by(instance_lookup=instance_id).first()
        for trade in instance.trades:
            db.session.delete(trade)
        for logs in instance.logs:
            db.session.delete(logs)
        if user.id == instance.owner_id:
            db.session.delete(instance)
            db.session.commit()
            return js({
                "error" : False
            })
        else:
            return js({
                "error" : True,
                "error_message" : "bad_auth"
            })

@app.route('/api/log/trader/<log_id>')
def trader_log(log_id):
    auth = authorize()
    if auth['error']:
        return js({"error" : True, "error_message" : auth['error_message']})    
    else:
        user = User.query.filter_by(public_key = auth['key']).first()

@app.route('/api/create_run/trader/<instance_id>')
def trader_run(instance_id):
    auth = authorize()
    if auth['error']:
        return js({"error" : True, "error_message" : auth['error_message']})    
    else:
        user = User.query.filter_by(public_key = auth['key']).first()
        instance = Costaverage.query.filter_by(instance_lookup=instance_id).first()
        if instance != None and user.id == instance.owner_id:
            if instance.running:
                return js({"error" : True, "error_message" : "instance_already_running"})
            else:
                instance.running = True
                new_run = Costaverage_logs(
                    log_lookup = secrets.token_hex(10),
                    running = True,
                    time = datetime.datetime.utcnow(),
                    contract = instance
                )
                db.session.add(new_run)
                db.session.commit()
                return js({"error" : False, "error_message" : new_run.log_lookup})
        else:
            return js({"error" : True, "error_message" : "no_resource"})

@app.route('/api/submit_authorization/trader/<instance_id>',methods=['GET','POST'])
def trader_authorization(instance_id):
    auth = authorize()
    if auth['error']:
        return js({"error" : True, "error_message" : auth['error_message']})    
    else:
        user = User.query.filter_by(public_key = auth['key']).first()
        instance = Costaverage.query.filter_by(instance_lookup=instance_id).first()
        if instance != None and user.id == instance.owner_id:
            authorization = request.get_json()['authorization']
            verif = verify_authorization(
                instance.instance_lookup,
                instance.source_account,
                authorization
            )
            if not verif['error']:
                instance.authorization = authorization
                db.session.commit()
            return js(verif)
        else:
            return js({
                "error" : True,
                "error_message" : "no_resource"
            })
 
@app.route('/api/create_contract/trader',methods=['GET','POST'])
def create_trader():
    auth = authorize()
    if auth['error']:
        return js({"error" : True, "error_message" : auth['error_message']})    
    else:
        user = User.query.filter_by(public_key = auth['key']).first()
        params = request.get_json()
        check = ca_check(params)
        if(check.valid):
            instance_id = token_hex(10)
            new_trader = Costaverage(
                    running = False,
                    instance_lookup = instance_id,
                    owner = user,
                    source_asset = params['source_asset'],
                    source_account = params['source_account'],
                    send_to = params['send_to'],
                    amount_all = (True if params['amount'] == "all" else False),
                    amount = (None if params['amount'] == "all" else params['amount']),
                    fee = params['op_fee'],
                    max_slippage = params['max_slippage'],
                    memo = token_hex(10)
                )
            db.session.add(new_trader)
            for trade in params['trades']:
                new_trade = Costaverage_trades(
                    contract = new_trader,
                    asset = trade['asset'],
                    percent = trade['percent']
                )
                db.session.add(new_trade)
            db.session.commit()
            return js({
                "error" : False,
                "instance_id" : instance_id
            })
        else:
            return js({
                "error" : False,
                "error_message" : check.error
            })
from app import app
from flask import render_template,jsonify,redirect,url_for
from functions import build_challenge,verify_challenge,authorize
from stellar_sdk import Keypair
from models import db,User,Costaverage,Costaverage_logs


@app.route('/')
def login_screen():
    auth = authorize()
    if auth['error']:
        return render_template('/landing/index.html')
    else:
        return redirect('/contracts')

@app.route('/contracts')
def home():
    auth = authorize()
    if auth['error']:
        return render_template('error.html',message=auth['error_message'])
    else:
        user = User.query.filter_by(public_key = auth['key']).first()
        if user == None:
            user = User(public_key = auth['key'])
            db.session.add(user)
            db.session.commit()
        return render_template(
            '/dashboard/dashboard.html',
            user=user,
            type="contract-dash"    
        )

@app.route('/contracts/trader/<instance_lookup>')
def trader_manage(instance_lookup):
    auth = authorize()
    if auth['error']:
        return render_template('error.html',message=auth['error_message'])
    else:
        user = User.query.filter_by(public_key = auth['key']).first()
        contract = Costaverage.query.filter_by(instance_lookup=instance_lookup).first()
        if user.id != contract.owner_id:
            return render_template('error.html',message="bad_authorization")
        else:
            return render_template(
                '/trader/info.html',
                user=user,
                instance_id=instance_lookup,
            )


@app.route('/new/trader')
def new_trader():
    auth = authorize()
    if auth['error']:
        return render_template('error.html',message=auth['error_message'])
    else:
        user = User.query.filter_by(public_key = auth['key']).first()
        return render_template(
            'trader/new.html',
            user=user
            )

@app.route('/logs/trader/<log_lookup>')
def log_view(log_lookup):
    auth = authorize()
    if auth['error']:
        return render_template('error.html',message=auth['error_message'])
    else:
        user = User.query.filter_by(public_key = auth['key']).first()
        log = Costaverage_logs.query.filter_by(log_lookup = log_lookup).first()
        if log.contract.owner_id == user.id:
            return log_lookup
        else:
            return render_template('error.html',message=auth['error_message'])
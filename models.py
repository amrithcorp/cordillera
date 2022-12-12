from app import db
import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    public_key = db.Column(db.String(60))
    ca_contracts = db.relationship('Costaverage', backref='user')  
    
class Costaverage(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    running = db.Column(db.Boolean)
    instance_lookup = db.Column(db.String(20))
    owner_id = db.Column(db.Integer,db.ForeignKey("user.id"))
    owner = db.relationship("User",foreign_keys=[owner_id])
    trades = db.relationship('Costaverage_trades', backref='costaverage') 
    logs = db.relationship('Costaverage_logs', backref='costaverage') 
    source_asset = db.Column(db.String(80))
    source_account = db.Column(db.String(60))
    send_to = db.Column(db.String(60))
    amount_all = db.Column(db.Boolean)
    amount = db.Column(db.Float)
    fee = db.Column(db.Integer)
    max_slippage = db.Column(db.Float)
    memo = db.Column(db.String(28))
    authorization = db.Column(db.Text)

class Costaverage_trades(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    contract_id = db.Column(db.Integer,db.ForeignKey("costaverage.id"))
    contract = db.relationship("Costaverage",foreign_keys=[contract_id])
    asset = db.Column(db.String(80))
    percent = db.Column(db.Integer)

class Costaverage_logs(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    log_lookup = db.Column(db.String(20))
    contract_id = db.Column(db.Integer,db.ForeignKey("costaverage.id"))
    contract = db.relationship("Costaverage",foreign_keys=[contract_id])
    error = db.Column(db.Boolean)
    running = db.Column(db.Boolean)
    output = db.Column(db.Text)
    time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
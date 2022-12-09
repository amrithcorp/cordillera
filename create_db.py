from app import app

with app.app_context():
    from models import db,User,Costaverage,Costaverage_trades
    db.create_all()
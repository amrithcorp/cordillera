from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    Float,
    DateTime,
    ForeignKey,
    create_engine
)
from sqlalchemy.orm import (
    declarative_base, 
    relationship,
    Session
)
import datetime


Base = declarative_base()


import datetime

class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key = True)
    public_key = Column(String(60))
    ca_contracts = relationship('Costaverage', backref='user')  
    
class Costaverage(Base):
    __tablename__ = "costaverage"
    id = Column(Integer, primary_key = True)
    running = Column(Boolean)
    instance_lookup = Column(String(20))
    owner_id = Column(Integer,ForeignKey("user.id"))
    owner = relationship("User",foreign_keys=[owner_id])
    trades = relationship('Costaverage_trades', backref='costaverage') 
    logs = relationship('Costaverage_logs', backref='costaverage') 
    source_asset = Column(String(80))
    source_account = Column(String(60))
    send_to = Column(String(60))
    amount_all = Column(Boolean)
    amount = Column(Float)
    fee = Column(Integer)
    max_slippage = Column(Float)
    memo = Column(String(28))
    authorization = Column(Text)

class Costaverage_trades(Base):
    __tablename__ = "costaverage_trades"
    id = Column(Integer, primary_key = True)
    contract_id = Column(Integer,ForeignKey("costaverage.id"))
    contract = relationship("Costaverage",foreign_keys=[contract_id])
    asset = Column(String(80))
    percent = Column(Integer)

class Costaverage_logs(Base):
    __tablename__ = "costaverage_logs"
    id = Column(Integer, primary_key = True)
    log_lookup = Column(String(20))
    contract_id = Column(Integer,ForeignKey("costaverage.id"))
    contract = relationship("Costaverage",foreign_keys=[contract_id])
    error = Column(Boolean)
    running = Column(Boolean)
    output = Column(Text)
    time = Column(DateTime)

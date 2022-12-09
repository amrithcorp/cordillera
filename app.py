from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

other_config = {
    "horizon" : "https://horizon.stellar.org/",
    "auth_server_key" : "SCR22UEX3XIGR3KLISV3QKWFH46EPJYI2JPRU7KUBTXA75GADFVENEO3",
    "worker_public_key" : "GBCPV3SCOKFJBSIM3JNLZVWEVEJVSADN4E3FFP3NVXLGA4K5QOKLA2ME",
    "domain" : "defiants.co",
    "auth_key" : "thisisthesecretkey"
}

app = Flask(__name__,instance_relative_config=False)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://qtcoxuvx:U_Qo1gyQr3CcEcNrUbtdA3EZxkFqfJqO@peanut.db.elephantsql.com/qtcoxuvx"

db = SQLAlchemy(app)

CORS(app)

app.route('/favicon.ico',redirect_to='https://cdn.jsdelivr.net/gh/atomiclabs/cryptocurrency-icons@1a63530be6e374711a8554f31b17e4cb92c25fa5/128/icon/evx.png')

from views import *
from apis import *


if __name__ == "__main__":
    app.run(
        debug=True,
        # ssl_context='adhoc'
    )
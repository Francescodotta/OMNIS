from flask import Flask
import os
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import datetime
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app, origins="*")

# Config mongodb connection for metabolomics
app.config["MONGO_URI_METABOLOMICS"] = os.getenv("MONGO_URI_METABOLOMICS")
mongo_metabolomics = PyMongo(app, uri=app.config["MONGO_URI_METABOLOMICS"])

# Config mongodb connection for authentication
app.config["MONGO_URI_AUTH"] = os.getenv("MONGO_URI_AUTH")
mongo_auth = PyMongo(app, uri=app.config["MONGO_URI_AUTH"])


# Config JWT
app.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY')
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(minutes = 15)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = datetime.timedelta(days=1)

# configura la blacklist
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = ["access", "refresh"]

jwt = JWTManager(app)

blacklist = set()

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in blacklist 

#Register blueprints and routes
with app.app_context():
    from .routes import metabolomics_routes, standardized_fields
    app.register_blueprint(metabolomics_routes.bp)
    app.register_blueprint(standardized_fields.bp)
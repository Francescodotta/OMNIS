from flask import Flask
import os
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import datetime
from flask_cors import CORS
import json, logging, logging.config

load_dotenv()


app = Flask(__name__)
CORS(app, origins="*")


# Config mongodb connection
if os.getenv('AUTH_ENV') == 'testing':
    app.config["MONGO_URI"] = os.getenv("MONGO_URI_TESTING")
else:
    app.config["MONGO_URI"] = os.getenv("MONGO_URI_AUTH")

# Config JWT
app.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY')
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(hours = 10)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = datetime.timedelta(days=1)

# configura la blacklist
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = ["access", "refresh"]

jwt = JWTManager(app)

mongo = PyMongo(app)

# Carica la configurazione del log dal file JSON
log_json_path = os.path.join(os.path.dirname(__file__), "logger_config.json")
with open(log_json_path, 'r') as file:
    log_config = json.load(file)
    logging.config.dictConfig(log_config)
    logger = logging.getLogger("auth_microservice")


blacklist = set()

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in blacklist 

with app.app_context():
    from .routes import auth_routes, project_routes
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(project_routes.bp)


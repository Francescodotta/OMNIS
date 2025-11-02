from flask import Flask, jsonify
import os
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import datetime
from flask_cors import CORS
import logging.config
import json



load_dotenv()

app = Flask(__name__)
CORS(app, origins="*")

# Config mongodb connection for flow cytometry
if os.getenv("FLOW_CYTOMETRY_ENV") == "production":
    app.config["MONGO_URI_FLOW_CYTOMETRY"] = os.getenv("MONGO_URI_FLOW_CYTOMETRY")
    mongo_flow_cytometry = PyMongo(app, uri=app.config["MONGO_URI_FLOW_CYTOMETRY"])
else:
    app.config["MONGO_URI_FLOW_CYTOMETRY"] = os.getenv("MONGO_URI_FLOW_CYTOMETRY_DEV")
    mongo_flow_cytometry = PyMongo(app, uri=app.config["MONGO_URI_FLOW_CYTOMETRY"])

# Config mongodb connection for authentication
app.config["MONGO_URI_AUTH"] = os.getenv("MONGO_URI_AUTH")
mongo_auth = PyMongo(app, uri=app.config["MONGO_URI_AUTH"])

# Config JWT - Match auth microservice configuration
app.config["JWT_SECRET_KEY"] = os.getenv('JWT_SECRET_KEY')
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(minutes=15)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = datetime.timedelta(days=1)
app.config["JWT_BLACKLIST_ENABLED"] = True
app.config["JWT_BLACKLIST_TOKEN_CHECKS"] = ["access", "refresh"]

jwt = JWTManager(app)



# Share blacklist with auth service
blacklist = set()

# Clear the blacklist
blacklist.clear()

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in blacklist

# Add error handlers for better debugging
@jwt.unauthorized_loader
def unauthorized_callback(callback):
    return jsonify({"msg": "Missing or invalid token"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(callback):
    return jsonify({"msg": "Invalid token"}), 401


# Ensure the log directory exists before setting up logging
log_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
if not os.path.exists(log_directory):
    os.makedirs(log_directory, exist_ok=True)  # `exist_ok=True` prevents errors if it already exists

# LOGGING SETUP
log_json_path = os.path.join(os.path.dirname(__file__), "logger_config.json")
print(log_json_path)

# Ensure log file exists if needed
log_file_path = os.path.join(log_directory, "custom_info_log.json")
if not os.path.exists(log_file_path):
    with open(log_file_path, 'w'):  # Create empty log file
        pass

with open(log_json_path, 'r') as file:
    log_config = json.load(file)
    logging.config.dictConfig(log_config)
    logger = logging.getLogger("flow_cytometry_microservice")


#Register blueprints and routes
with app.app_context():
    from .routes import flow_cytometry_routes
    app.register_blueprint(flow_cytometry_routes.bp)

from flask import Flask
from celery import Celery
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os 
import logging
import logging.config
import json 

load_dotenv()



def make_celery(app):
    celery_microservice = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND'],
        include=['app.pipeline_tasks']
    )
    celery_microservice.conf.update(app.config)
    return celery_microservice

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',
    CELERY_RESULT_BACKEND='redis://localhost:6379/0'
)

app.config["MONGO_URI_FLOW_CYTOMETRY"] = os.getenv("MONGO_URI_FLOW_CYTOMETRY")
mongo_flow_cytometry_pipeline = PyMongo(app, uri=app.config["MONGO_URI_FLOW_CYTOMETRY"])

# proteomics config
app.config["MONGO_URI_PROTEOMICS"] = os.getenv("MONGO_URI_PROTEOMICS")
mongo_proteomics_pipeline = PyMongo(app, uri=app.config["MONGO_URI_PROTEOMICS"])

# metabolomics config
app.config["MONGO_URI_METABOLOMICS"] = os.getenv("MONGO_URI_METABOLOMICS")
mongo_metabolomics_pipeline = PyMongo(app, uri=app.config["MONGO_URI_METABOLOMICS"])


print("working")

log_json_path = os.path.join(os.path.dirname(__file__), "logger_config.json")

print("\n\npath:",log_json_path)
with open(log_json_path, 'r') as file:
    log_config = json.load(file)
    logging.config.dictConfig(log_config)
    logger = logging.getLogger("flow_cytometry_microservice")


celery_microservice = make_celery(app)

with app.app_context():
    from . import routes
    app.register_blueprint(routes.bp)
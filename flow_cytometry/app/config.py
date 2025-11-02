import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGODB_URI = os.getenv('MONGODB_URI')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    FLOW_CYTOMETRY_BASE_PATH = os.getenv('FLOW_CYTOMETRY_BASE_PATH', '/media/datastorage/it_cast/omnis_microservice_db/flow_cytometry/')
    ALLOWED_EXTENSIONS = {'fcs'} 
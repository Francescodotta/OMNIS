import pytest
from unittest.mock import Mock
from flask import Flask
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
import datetime
import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

@pytest.fixture(autouse=True)
def env_setup():
    """Set up testing environment variables before each test"""
    os.environ['AUTH_ENV'] = 'testing'
    yield
    os.environ.pop('AUTH_ENV', None)

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    
    from app import app
    # Test configuration
    app.config.update({
        'TESTING': True,
        'JWT_SECRET_KEY': os.getenv("JWT_SECRET_KEY"),
        'JWT_ACCESS_TOKEN_EXPIRES': datetime.timedelta(hours=1),
        'JWT_REFRESH_TOKEN_EXPIRES': datetime.timedelta(days=1),
        'JWT_BLACKLIST_ENABLED': True,
        'JWT_BLACKLIST_TOKEN_CHECKS': ['access', 'refresh'],
        'MONGO_URI': os.getenv("MONGO_URI_TESTING"),
    })
    # Initialize extensions
    #jwt = JWTManager(app)
    # Create mock MongoDB instance
    mongo = PyMongo(app)
    app.mongo = mongo
    
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()
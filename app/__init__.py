import redis
from flask import Flask, request
from flask_limiter import Limiter
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import dotenv_values


# Initialization of global variables:
# Create an instance of SQlAlchemy to interact with DB
db = SQLAlchemy()
# Connect Redis server
cache = redis.StrictRedis(host='localhost', port=6379, db=0)
# Reading configuration values from ".env" file
config = dotenv_values('.env')

# Initializing a limiter object using the Authorization header as a key
limiter = Limiter(
    key_func=lambda: request.headers.get('Authorization'),
    storage_uri='redis://localhost:6379/1'
)

def create_app():
    """Create Flask app"""
    app = Flask(__name__)
    # Setting up CORS policy for application (allows make requests to application from any domains)
    CORS(app)

    # PostgreSQL DB configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{config['db_user']}:{config['db_password']}@{config['db_host']}:5432/{config['db_name']}"

    # Initializing the SQLAlchemy extension
    db.init_app(app)
    # Initializing the limiter extension
    limiter.init_app(app)
    return app
import redis
from flask import Flask
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

def create_app():
    """Create Flask app"""
    app = Flask(__name__)
    # Setting up CORS policy for application (allows make requests to application from any domains)
    CORS(app)

    # PostgreSQL DB configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{config['db_user']}:{config['db_password']}@{config['db_host']}:5432/{config['db_name']}"

    # Initializing the SQLAlchemy extension
    db.init_app(app)
    return app
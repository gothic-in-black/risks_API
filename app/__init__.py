import redis
import logging
from flask import Flask, request, g
from flask_limiter import Limiter
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import dotenv_values


# Set up a basic configuration for logging
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding='utf-8'
)
# Create a logger instance
logger = logging.getLogger(__name__)
# Initialization of global variables:
# Create an instance of SQlAlchemy to interact with DB
db = SQLAlchemy()
# Connect Redis server
try:
    cache = redis.StrictRedis(host='localhost', port=6379, db=0)
    # Check connection
    cache.ping()
    logger.info("Connected to Redis successfully.")
except redis.ConnectionError as e:
    logger.error(f"Failed to connect to Redis: {e}")
# Reading configuration values from ".env" file
config = dotenv_values('.env')


def get_id_firm():
    """Returns if_firm if it exists in global variable 'g' else returns client IP."""
    return getattr(g, 'id_firm', request.remote_addr)


# Initializing a limiter object using the id_firm as a key
limiter = Limiter(
    key_func=get_id_firm,
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
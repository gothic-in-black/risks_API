import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from dotenv import dotenv_values



db = SQLAlchemy()
cache = redis.StrictRedis(host='localhost', port=6379, db=0)
config = dotenv_values('.env')

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{config['db_user']}:{config['db_password']}@{config['db_host']}:5432/{config['db_name']}"

    db.init_app(app)
    return app
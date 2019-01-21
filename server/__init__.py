from flask import Flask, session
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler

server_app = Flask(__name__)

# Load the config
server_app.config.from_object(Config)

# Load the database
db = SQLAlchemy(server_app)

# Setup ZORA scheduler
scheduler = APScheduler()
scheduler.init_app(server_app)
scheduler.start()

from server import models, routes, zoraAPI


# TODO: Implement scheduled task for pulling papers from ZORA
#server_app.apscheduler.add_job(func=zoraAPI.get_all_records, trigger='date')

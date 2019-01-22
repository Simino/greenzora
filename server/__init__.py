from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler

server_app = Flask(__name__)

# Load the config
server_app.config.from_object(Config)

# Load the database
db = SQLAlchemy(server_app)

from server import models, routes, zoraAPI


# Setup ZORA scheduler
scheduler = APScheduler()
scheduler.init_app(server_app)
scheduler.start()

# TODO: Implement scheduled task for pulling papers from ZORA
#server_app.apscheduler.add_job(func=zoraAPI.get_records, trigger='interval', days=1, id='zoraAPI_get_records_job')

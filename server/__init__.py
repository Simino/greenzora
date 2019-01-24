from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from datetime import datetime

server_app = Flask(__name__)

# Load the config
server_app.config.from_object('config')

# Setup ZORA scheduler
scheduler = APScheduler()
scheduler.init_app(server_app)
scheduler.start()

# Load the database and create the tables if they don't already exist
db = SQLAlchemy(server_app)
from server import models

models.initialize_db()

# We import the other modules only here to avoid circular imports
from server import routes, zoraAPI, utils, cli

# Add zoraAPI_get_records_job that pulls data from the ZORA repository in a fixed interval
interval_setting = models.ServerSetting.query.filter_by(name='zora_pull_interval').first()
job_interval = utils.parse_db_value(interval_setting)
server_app.apscheduler.add_job(func=zoraAPI.get_records,
                               trigger='interval',
                               days=job_interval,
                               next_run_time=datetime.now(),
                               id=server_app.config['ZORA_API_JOB_ID'])

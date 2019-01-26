from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from datetime import datetime
import csv

server_app = Flask(__name__)

# Load the config
server_app.config.from_object('config')

# Setup ZORA scheduler
scheduler = APScheduler()
scheduler.init_app(server_app)
scheduler.start()

# Load the database and create the tables if they don't already exist
db = SQLAlchemy(server_app)
from server import models   # Not at top of file to avoid circular imports

models.initialize_db()

from server import routes, ml_tool, zoraAPI, utils, cli  # Not at top of file to avoid circular imports
ml_tool.initialize_ml_tool()

# Add zoraAPI_get_records_job that pulls data from the ZORA repository in a fixed interval
interval_setting = db.session.query(models.ServerSetting).filter_by(name='zora_pull_interval').first()
job_interval = utils.parse_db_value(interval_setting)
server_app.apscheduler.add_job(func=zoraAPI.get_records,
                               trigger='interval',
                               days=job_interval,
                               next_run_time=datetime.now(),
                               id=server_app.config['ZORA_API_JOB_ID'])

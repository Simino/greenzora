from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create the app
server_app = Flask(__name__)

# Load the config
server_app.config.from_object('config')

# Load the database
db = SQLAlchemy(server_app)

# Not at top of file to avoid circular imports (we need server_app)
from server import models, server_logic, routes

# Initialize the database
models.initialize_db()

# Initialize the ZORA API, machine learning tool, task scheduler and zora pull job
server_logic = server_logic.ServerLogic(server_app, db)

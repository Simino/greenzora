from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Create the app
server_app = Flask(__name__)

# Load the config
server_app.config.from_object('config')

# Load the database
db = SQLAlchemy(server_app)

# TODO: Handle fucked up imports.... (dependencies and shit)

from server import models

# Initialize the database
models.initialize_db()

# Not at top of file to avoid circular imports (we need server_app)
from server.server_logic import ServerLogic

# Initialize the ZORA API, machine learning tool, task scheduler and zora pull job
server_logic = ServerLogic(server_app, db)

from server import routes

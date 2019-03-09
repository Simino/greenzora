from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

# Create the app
server_app = Flask(__name__)

# Load the config
server_app.config.from_object('config')

# Load the database
db = SQLAlchemy(server_app)

# Initialize the LoginManager
login_manager = LoginManager(server_app)

# NOTE: These imports are not at the top of the file to avoid circular imports (we need server_app)
from greenzora import models, server_logic, routes

# Initialize the database
models.initialize_db()

# Initialize the greenzora logic, which includes the ZORA API, machine learning tool, task scheduler and jobs
server_logic = server_logic.ServerLogic()

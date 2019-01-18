from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(Config)      # Load the config
db = SQLAlchemy(app)


from flaskr import routes, models      # Imported at the end to avoid circular imports
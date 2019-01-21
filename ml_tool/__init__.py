from flask import Flask
from config import Config

ml_app = Flask(__name__)
ml_app.config.from_object(Config)      # Load the config

import os
from server import server_app

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Settings default values
DEFAULT_ZORA_PULL_INTERVAL = 1
DEFAULT_RESOURCE_TYPE_UPDATE_INTERVAL = 14
DEFAULT_INSTITUTE_UPDATE_INTERVAL = 14
DEFAULT_ZORA_URL = 'https://www.zora.uzh.ch/cgi/oai2'

# Machine Learning Tool
LEGACY_ANNOTATIONS_PATH = os.path.join(BASE_DIR, 'server\static\legacy_annotations.json')

SECRET_KEY = os.urandom(32)
server_app.config['SECRET_KEY'] = SECRET_KEY
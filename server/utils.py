from server import server_app
from datetime import datetime


def is_debug():
    return server_app.config['DEBUG']

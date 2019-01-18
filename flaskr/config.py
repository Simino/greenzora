import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SQLALCHEMY_DB_URI = os.path.join(basedir, 'flaskr.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
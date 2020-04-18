import os
from urllib.request import localhost

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'wocaonima110'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ELASTICSEARCH_URL = 'http://localhost:9200'
    LANGUAGES = ['en', 'es']
    POSTS_PER_PAGE = 5
    ADMINS = ['Fenglinjoyyy@gmail.com']
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = 1
    MAIL_USERNAME = 'Fenglinjoyyy@gmail.com'
    MAIL_PASSWORD = 'ZFl5948405'

from flask import Flask, request
from configure import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
from flask_login import LoginManager
from flask_cors import CORS
from elasticsearch import Elasticsearch
from flask_mail import Mail
import logging
from logging.handlers import SMTPHandler


app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)

CORS(app)

mail = Mail(app)
runDB = Manager(app)
runDB.add_command('db', MigrateCommand)
ES_HOST = {"host": "localhost", "port": 9200}
app.elasticsearch = Elasticsearch(hosts=[ES_HOST])

if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='EDPE Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


from myBlogApp import routes, models, error
login.login_view = 'index'

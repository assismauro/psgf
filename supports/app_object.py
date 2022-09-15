import os
from sqlalchemy.ext.declarative import declarative_base
from flask_migrate import Migrate
from flask_admin import Admin, AdminIndexView
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel
from flask_mail import Mail

app = Flask(__name__, static_folder="static")
app.root_path = app.root_path.replace('/supports','')
app.config.from_pyfile(f'{app.root_path}{os.sep}config.cfg')

db = SQLAlchemy(app)

mail = Mail(app)
babel = Babel(app)

admin = Admin(app, template_mode='bootstrap3', index_view=AdminIndexView(
    name='Plans de Gestió Forestal',
    url=r'/'))

migrate = Migrate()
migrate.init_app(app, db)

Base = declarative_base()
metadata = Base.metadata

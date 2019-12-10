from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
csrf = CSRFProtect()
csrf.init_app(app)
login = LoginManager(app)
bootstrap = Bootstrap(app)
login.login_view = 'login'
app.config.from_object(Config)
db = SQLAlchemy(app)
# 绑定app和数据库，以便进行操作
migrate = Migrate(app, db)

from app import routes

from __future__ import annotations
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "videos.home"
login_manager.login_message_category = "err"

from __future__ import annotations

from flask import Flask
from .config import Config
from .extensions import db, login_manager

def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config())

    # ensure folders
    app.config["UPLOADS_DIR"].mkdir(parents=True, exist_ok=True)
    app.config["VIDEOS_DIR"].mkdir(parents=True, exist_ok=True)
    app.config["THUMBS_DIR"].mkdir(parents=True, exist_ok=True)
    (Config.SQLALCHEMY_DATABASE_URI.split("///",1)[1])

    db.init_app(app)
    login_manager.init_app(app)

    from .blueprints.auth.routes import bp as auth_bp
    from .blueprints.videos.routes import bp as videos_bp
    from .blueprints.profile.routes import bp as profile_bp
    from .blueprints.admin.routes import bp as admin_bp
    from .blueprints.extras.routes import bp as extras_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(videos_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(extras_bp)

    with app.app_context():
        db.create_all()
        _seed_admin()

    return app

def _seed_admin():
    import os
    from werkzeug.security import generate_password_hash
    from .models import User
    from .extensions import db

    admin_user = os.environ.get("OLDTUBE_ADMIN_USER", "admin")
    admin_pass = os.environ.get("OLDTUBE_ADMIN_PASS", "admin")
    if User.query.filter_by(username=admin_user).first() is None:
        db.session.add(User(username=admin_user, password_hash=generate_password_hash(admin_pass), is_admin=True))
        db.session.commit()

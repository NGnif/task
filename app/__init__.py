import os
import tempfile
from flask import Flask
from flask_login import LoginManager
from .models import db, User
from .i18n import i18n_bp, init_i18n
from .pwa import pwa_bp


def create_app():
    instance_path = os.environ.get("INSTANCE_PATH") or tempfile.gettempdir()
    app = Flask(__name__, instance_path=instance_path)
    app.config.from_object("config.Config")

    # Init extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    # Register blueprints
    from .auth import auth_bp
    from .routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(i18n_bp)

    # i18n helpers
    init_i18n(app)
    app.register_blueprint(pwa_bp)

    # Create tables if not exist
    with app.app_context():
        db.create_all()

    return app

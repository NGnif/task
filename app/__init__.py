import os
import tempfile
from flask import Flask
from flask_login import LoginManager
from .models import db, User, Message, TaskCompletionRequest
from .i18n import i18n_bp, init_i18n
from .pwa import pwa_bp


def create_app():
    base_tmp = os.environ.get("INSTANCE_PATH") or tempfile.gettempdir()
    instance_dir = os.path.join(base_tmp, "flask-instance")
    try:
        os.makedirs(instance_dir, exist_ok=True)
    except Exception:
        # Best effort; continue if /tmp is available
        instance_dir = base_tmp

    app = Flask(__name__, instance_path=instance_dir)
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

    @app.context_processor
    def inject_notifications():  # type: ignore
        from flask_login import current_user
        msg_count = 0
        approvals_count = 0
        try:
            if current_user.is_authenticated:
                msg_count = (
                    Message.query.filter_by(receiver_id=current_user.id, read_at=None).count()
                )
                if getattr(current_user, "role", None) == "owner":
                    approvals_count = TaskCompletionRequest.query.filter_by(status="pending").count()
                else:
                    approvals_count = TaskCompletionRequest.query.filter_by(
                        status="pending", requested_by_id=current_user.id
                    ).count()
        except Exception:
            pass
        return {
            "notif_messages": msg_count,
            "notif_approvals": approvals_count,
        }

    return app

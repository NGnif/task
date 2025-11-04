from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from .models import User, db


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.tasks"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            error = "Invalid username or password"
        else:
            login_user(user)
            return redirect(url_for("main.tasks"))

    users_exist = User.query.count() > 0
    return render_template("login.html", error=error, users_exist=users_exist)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # If at least one user exists, only owner can create new users
    user_count = User.query.count()
    if user_count > 0 and (not current_user.is_authenticated or not current_user.is_owner()):
        flash("Only the owner can create new users.")
        return redirect(url_for("auth.login"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        if not username or not password:
            error = "Username and password are required"
        elif password != confirm:
            error = "Passwords do not match"
        elif User.query.filter_by(username=username).first():
            error = "Username already exists"

        if error is None:
            user = User(username=username)
            user.set_password(password)
            # First user becomes owner, others default to worker
            user.role = "owner" if user_count == 0 else "worker"
            db.session.add(user)
            db.session.commit()

            flash("User created successfully. You can now log in.")
            return redirect(url_for("auth.login"))

    return render_template("register.html", error=error)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.goodbye"))


@auth_bp.route("/goodbye")
def goodbye():
    # Minimal page that attempts to close the window/app with safe fallbacks
    return render_template("goodbye.html")

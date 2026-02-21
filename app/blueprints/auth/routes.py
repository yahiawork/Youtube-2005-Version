from __future__ import annotations
import re
from flask import Blueprint, redirect, url_for, request, flash, render_template
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from ...extensions import db
from ...models import User

bp = Blueprint("auth", __name__, url_prefix="/auth")

@bp.post("/login")
def login():
    username = (request.form.get("username") or "").strip().lower()
    password = (request.form.get("password") or "").strip()
    u = User.query.filter_by(username=username).first()
    if not u or not check_password_hash(u.password_hash, password):
        flash("Invalid username or password.", "err")
        return redirect(url_for("videos.home"))
    login_user(u)
    flash("Logged in.", "ok")
    return redirect(url_for("videos.home"))



@bp.get("/register")
def register_page():
    return render_template("register.html", user=current_user)

@bp.post("/register")
def register():
    username = (request.form.get("username") or "").strip().lower()
    password = (request.form.get("password") or "").strip()

    if not re.match(r"^[a-z0-9_]{3,20}$", username or ""):
        flash("Username: 3-20 (a-z, 0-9, _).", "err")
        return redirect(url_for("videos.home"))
    if len(password) < 6:
        flash("Password min 6 chars.", "err")
        return redirect(url_for("videos.home"))
    if User.query.filter_by(username=username).first():
        flash("Username already taken.", "err")
        return redirect(url_for("videos.home"))

    u = User(username=username, password_hash=generate_password_hash(password), is_admin=False)
    db.session.add(u)
    db.session.commit()
    login_user(u)
    flash("Account created.", "ok")
    return redirect(url_for("videos.home"))

@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "ok")
    return redirect(url_for("videos.home"))

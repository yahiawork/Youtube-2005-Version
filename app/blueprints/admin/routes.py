from __future__ import annotations
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from ...models import User, Video

bp = Blueprint("admin", __name__, url_prefix="/admin")

def _is_admin() -> bool:
    return bool(getattr(current_user, "is_admin", False))

@bp.get("/")
@login_required
def dashboard():
    if not _is_admin():
        flash("Admins only.", "err")
        return redirect(url_for("videos.home"))
    videos = Video.query.order_by(Video.id.desc()).limit(200).all()
    users = User.query.order_by(User.id.desc()).limit(200).all()
    return render_template("admin.html", videos=videos, users=users, user=current_user)

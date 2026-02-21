from __future__ import annotations
from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user
from ...models import User, Video, Like, Comment

bp = Blueprint("profile", __name__)

@bp.get("/me")
def me():
    if not getattr(current_user, "is_authenticated", False):
        return redirect(url_for("videos.home"))
    return redirect(url_for("profile.user_profile", username=current_user.username))

@bp.get("/u/<username>")
def user_profile(username: str):
    u = User.query.filter_by(username=username).first_or_404()
    vids = Video.query.filter_by(uploader_id=u.id).order_by(Video.id.desc()).limit(100).all()
    likes = Like.query.filter_by(user_id=u.id).count()
    comments = Comment.query.filter_by(user_id=u.id).count()
    return render_template("profile.html", profile=u, videos=vids, likes=likes, comments=comments, user=current_user)

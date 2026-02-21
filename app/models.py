from __future__ import annotations
from datetime import datetime
from .extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.String(25), default=lambda: datetime.utcnow().isoformat(timespec="seconds"))

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    filename = db.Column(db.String(200), nullable=False, unique=True)
    ext = db.Column(db.String(10), nullable=False)
    original_name = db.Column(db.String(200), nullable=False)
    thumb_filename = db.Column(db.String(200), nullable=True)
    uploaded_at = db.Column(db.String(25), default=lambda: datetime.utcnow().isoformat(timespec="seconds"))
    uploader_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    uploader = db.relationship("User", backref="videos")

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey("video.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    body = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.String(25), default=lambda: datetime.utcnow().isoformat(timespec="seconds"))
    user = db.relationship("User")
    video = db.relationship("Video", backref="comments")

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey("video.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    created_at = db.Column(db.String(25), default=lambda: datetime.utcnow().isoformat(timespec="seconds"))
    __table_args__ = (db.UniqueConstraint("video_id", "user_id", name="uq_like_video_user"),)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey("video.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    created_at = db.Column(db.String(25), default=lambda: datetime.utcnow().isoformat(timespec="seconds"))
    __table_args__ = (db.UniqueConstraint("video_id", "user_id", name="uq_fav_video_user"),)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    subject = db.Column(db.String(120), nullable=False)
    body = db.Column(db.String(1200), nullable=False)
    created_at = db.Column(db.String(25), default=lambda: datetime.utcnow().isoformat(timespec="seconds"))
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey("video.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    stars = db.Column(db.Integer, nullable=False)  # 1..5
    created_at = db.Column(db.String(25), default=lambda: datetime.utcnow().isoformat(timespec="seconds"))
    __table_args__ = (db.UniqueConstraint("video_id", "user_id", name="uq_rating_video_user"),)

    user = db.relationship("User")
    video = db.relationship("Video", backref="ratings")

from __future__ import annotations
from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user

from ...extensions import db
from ...models import Video, Favorite, Message, User

bp = Blueprint("extras", __name__)

@bp.get("/help")
def help_page():
    return render_template("help.html", user=current_user)

@bp.get("/favorites")
@login_required
def favorites():
    favs = (Favorite.query
            .filter_by(user_id=current_user.id)
            .order_by(Favorite.id.desc())
            .limit(200)
            .all())
    video_ids = [f.video_id for f in favs]
    videos = []
    if video_ids:
        vids = {v.id: v for v in Video.query.filter(Video.id.in_(video_ids)).all()}
        videos = [vids.get(i) for i in video_ids if i in vids]
    return render_template("favorites.html", videos=videos, user=current_user)

@bp.post("/favorite/<int:video_id>")
@login_required
def toggle_favorite(video_id: int):
    v = Video.query.get_or_404(video_id)
    existing = Favorite.query.filter_by(video_id=v.id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash("Removed from favorites.", "ok")
    else:
        db.session.add(Favorite(video_id=v.id, user_id=current_user.id))
        db.session.commit()
        flash("Added to favorites.", "ok")
    return redirect(url_for("videos.watch", video_id=v.id))

@bp.get("/messages")
@login_required
def inbox():
    msgs = (Message.query
            .filter_by(recipient_id=current_user.id)
            .order_by(Message.id.desc())
            .limit(200)
            .all())
    return render_template("messages_inbox.html", messages=msgs, user=current_user)

@bp.get("/messages/sent")
@login_required
def sent():
    msgs = (Message.query
            .filter_by(sender_id=current_user.id)
            .order_by(Message.id.desc())
            .limit(200)
            .all())
    return render_template("messages_sent.html", messages=msgs, user=current_user)

@bp.get("/messages/compose")
@login_required
def compose():
    to = (request.args.get("to") or "").strip().lower()
    subject = (request.args.get("subject") or "").strip()
    return render_template("messages_compose.html", to=to, subject=subject, user=current_user)

@bp.post("/messages/send")
@login_required
def send_message():
    to = (request.form.get("to") or "").strip().lower()
    subject = (request.form.get("subject") or "").strip()
    body = (request.form.get("body") or "").strip()

    if not to or not subject or not body:
        flash("Fill: To, Subject, Body.", "err")
        return redirect(url_for("extras.compose", to=to, subject=subject))
    if len(subject) > 120:
        flash("Subject too long (max 120).", "err")
        return redirect(url_for("extras.compose", to=to, subject=subject))
    if len(body) > 1200:
        flash("Message too long (max 1200).", "err")
        return redirect(url_for("extras.compose", to=to, subject=subject))

    recipient = User.query.filter_by(username=to).first()
    if not recipient:
        flash("User not found.", "err")
        return redirect(url_for("extras.compose", to=to, subject=subject))

    m = Message(sender_id=current_user.id, recipient_id=recipient.id, subject=subject, body=body, is_read=False)
    db.session.add(m)
    db.session.commit()
    flash("Message sent.", "ok")
    return redirect(url_for("extras.sent"))

@bp.get("/messages/read/<int:msg_id>")
@login_required
def read_message(msg_id: int):
    m = Message.query.get_or_404(msg_id)
    if m.recipient_id != current_user.id and m.sender_id != current_user.id:
        abort(403)
    if m.recipient_id == current_user.id and not m.is_read:
        m.is_read = True
        db.session.commit()
    return render_template("messages_read.html", m=m, user=current_user)

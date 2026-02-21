from __future__ import annotations
from pathlib import Path
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, send_from_directory
from flask_login import current_user, login_required

from ...extensions import db
from ...models import Video, Comment, Rating
from ...utils import allowed_video, allowed_image, unique_name, convert_to_mp4_if_needed, generate_thumbnail, send_file_range, ffmpeg_available

bp = Blueprint("videos", __name__)

@bp.get("/")
def home():
    latest = Video.query.order_by(Video.id.desc()).limit(12).all()
    return render_template("home.html", videos=latest, user=current_user, ffmpeg=ffmpeg_available())

@bp.get("/videos")
def list_videos():
    rows = Video.query.order_by(Video.id.desc()).all()
    return render_template("videos.html", videos=rows, user=current_user)

@bp.get("/watch/<int:video_id>")
def watch(video_id: int):
    v = Video.query.get_or_404(video_id)

    # rating summary (classic stars)
    ratings = Rating.query.filter_by(video_id=v.id).all()
    rating_count = len(ratings)
    rating_avg = 0.0
    if rating_count:
        rating_avg = sum(r.stars for r in ratings) / float(rating_count)

    user_rating = 0
    if getattr(current_user, "is_authenticated", False):
        ur = Rating.query.filter_by(video_id=v.id, user_id=current_user.id).first()
        user_rating = ur.stars if ur else 0

    comments = Comment.query.filter_by(video_id=v.id).order_by(Comment.id.desc()).limit(200).all()

    return render_template(
        "watch.html",
        v=v,
        comments=comments,
        user=current_user,
        rating_avg=rating_avg,
        rating_count=rating_count,
        user_rating=user_rating,
    )


@bp.get("/upload")
@login_required
def upload_page():
    max_mb = int(current_app.config.get("MAX_CONTENT_LENGTH", 0) / (1024*1024))
    return render_template("upload.html", user=current_user, max_mb=max_mb, ffmpeg=ffmpeg_available())

@bp.post("/upload")
@login_required
def upload_post():
    title = (request.form.get("title") or "").strip()
    file = request.files.get("file")
    thumb = request.files.get("thumb")

    if not title:
        flash("Title is required.", "err")
        return redirect(url_for("videos.upload_page"))
    if not file or not file.filename:
        flash("Choose a video file.", "err")
        return redirect(url_for("videos.upload_page"))
    if not allowed_video(file.filename):
        flash("Allowed: mp4, webm, ogg, mov, mkv", "err")
        return redirect(url_for("videos.upload_page"))

    videos_dir: Path = current_app.config["VIDEOS_DIR"]
    thumbs_dir: Path = current_app.config["THUMBS_DIR"]

    original = file.filename
    in_ext = original.rsplit(".", 1)[1].lower()
    base = original.rsplit(".", 1)[0]

    temp_name = unique_name(base, in_ext)
    temp_path = videos_dir / temp_name
    file.save(temp_path)

    final_path, final_ext, conv_err = convert_to_mp4_if_needed(temp_path)
    if conv_err:
        flash(conv_err, "err")

    thumb_name = None
    if thumb and thumb.filename:
        if not allowed_image(thumb.filename):
            flash("Thumbnail: png/jpg/jpeg/webp", "err")
            return redirect(url_for("videos.upload_page"))
        t_ext = thumb.filename.rsplit(".", 1)[1].lower()
        thumb_name = unique_name(f"{base}-thumb", t_ext)
        thumb.save(thumbs_dir / thumb_name)
    else:
        tname, terr = generate_thumbnail(final_path, base)
        if terr:
            flash(terr, "err")
        thumb_name = tname

    v = Video(
        title=title,
        filename=final_path.name,
        ext=final_ext,
        original_name=original,
        thumb_filename=thumb_name,
        uploader_id=current_user.id,
    )
    db.session.add(v)
    db.session.commit()
    flash("Uploaded.", "ok")
    return redirect(url_for("videos.watch", video_id=v.id))


@bp.post("/rate/<int:video_id>")
@login_required
def rate(video_id: int):
    v = Video.query.get_or_404(video_id)
    try:
        stars = int(request.form.get("stars") or "0")
    except ValueError:
        stars = 0
    if stars < 1 or stars > 5:
        flash("Choose 1 to 5 stars.", "err")
        return redirect(url_for("videos.watch", video_id=v.id))

    existing = Rating.query.filter_by(video_id=v.id, user_id=current_user.id).first()
    if existing:
        existing.stars = stars
    else:
        db.session.add(Rating(video_id=v.id, user_id=current_user.id, stars=stars))
    db.session.commit()
    flash("Thanks for rating!", "ok")
    return redirect(url_for("videos.watch", video_id=v.id))
def toggle_like(video_id: int):
    v = Video.query.get_or_404(video_id)
    existing = Like.query.filter_by(video_id=v.id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
    else:
        db.session.add(Like(video_id=v.id, user_id=current_user.id))
        db.session.commit()
    return redirect(url_for("videos.watch", video_id=v.id))

@bp.post("/comment/<int:video_id>")
@login_required
def add_comment(video_id: int):
    v = Video.query.get_or_404(video_id)
    body = (request.form.get("body") or "").strip()
    if not body:
        flash("Comment can't be empty.", "err")
        return redirect(url_for("videos.watch", video_id=v.id))
    if len(body) > 500:
        flash("Max 500 characters.", "err")
        return redirect(url_for("videos.watch", video_id=v.id))
    db.session.add(Comment(video_id=v.id, user_id=current_user.id, body=body))
    db.session.commit()
    return redirect(url_for("videos.watch", video_id=v.id))

@bp.get("/media/video/<path:filename>")
def media_video(filename: str):
    videos_dir: Path = current_app.config["VIDEOS_DIR"]
    return send_file_range(videos_dir, filename)

@bp.get("/media/thumb/<path:filename>")
def media_thumb(filename: str):
    thumbs_dir: Path = current_app.config["THUMBS_DIR"]
    return send_from_directory(thumbs_dir, filename, conditional=True)

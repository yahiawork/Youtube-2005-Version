from __future__ import annotations
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")
    db_path = (BASE_DIR / "instance" / "oldtube.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + str(db_path)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.environ.get("OLDTUBE_MAX_MB", "250")) * 1024 * 1024

    UPLOADS_DIR = BASE_DIR / "uploads"
    VIDEOS_DIR = UPLOADS_DIR / "videos"
    THUMBS_DIR = UPLOADS_DIR / "thumbs"

    OLDTUBE_CONVERT = os.environ.get("OLDTUBE_CONVERT", "1") == "1"
    OLDTUBE_THUMBNAIL = os.environ.get("OLDTUBE_THUMBNAIL", "1") == "1"
    FFMPEG_BIN = os.environ.get("FFMPEG_BIN", "")

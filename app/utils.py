from __future__ import annotations

import mimetypes
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from flask import Response, abort, request, send_from_directory, current_app

ALLOWED_VIDEO_EXTS = {"mp4", "webm", "ogg", "mov", "mkv"}
ALLOWED_IMAGE_EXTS = {"png", "jpg", "jpeg", "webp"}

def ext(filename: str) -> str:
    return filename.rsplit(".", 1)[1].lower().strip()

def allowed_video(filename: str) -> bool:
    return "." in filename and ext(filename) in ALLOWED_VIDEO_EXTS

def allowed_image(filename: str) -> bool:
    return "." in filename and ext(filename) in ALLOWED_IMAGE_EXTS

def slug_safe(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\-\_\s]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s[:60] or "video"

def unique_name(base: str, suffix_ext: str) -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    return f"{slug_safe(base)}-{stamp}.{suffix_ext}"

def ffmpeg_bin() -> str:
    cfg = current_app.config.get("FFMPEG_BIN") or ""
    return cfg or (shutil.which("ffmpeg") or "")

def ffmpeg_available() -> bool:
    b = ffmpeg_bin()
    return bool(b) and Path(b).name.lower().startswith("ffmpeg")

def run_ffmpeg(args: list[str]) -> Tuple[bool, str]:
    b = ffmpeg_bin()
    if not ffmpeg_available():
        return False, "ffmpeg not found"
    p = subprocess.run([b, *args], capture_output=True, text=True, check=False)
    ok = p.returncode == 0
    msg = (p.stderr or p.stdout or "").strip()[:2000]
    return ok, msg

def convert_to_mp4_if_needed(in_path: Path) -> Tuple[Path, str, Optional[str]]:
    auto = bool(current_app.config.get("OLDTUBE_CONVERT", True))
    in_ext = in_path.suffix.lower().lstrip(".")
    if in_ext == "mp4" or not auto:
        return in_path, in_ext, None
    if not ffmpeg_available():
        return in_path, in_ext, "ffmpeg not found (convert skipped)"

    out_path = in_path.with_suffix(".mp4")
    ok, msg = run_ffmpeg([
        "-y", "-i", str(in_path),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(out_path),
    ])
    if not ok:
        return in_path, in_ext, f"Convert failed: {msg}"
    try:
        in_path.unlink(missing_ok=True)
    except Exception:
        pass
    return out_path, "mp4", None

def generate_thumbnail(video_path: Path, base_name: str) -> Tuple[Optional[str], Optional[str]]:
    auto = bool(current_app.config.get("OLDTUBE_THUMBNAIL", True))
    if not auto:
        return None, None
    if not ffmpeg_available():
        return None, "ffmpeg not found (thumbnail skipped)"

    thumbs_dir: Path = current_app.config["THUMBS_DIR"]
    thumb_name = unique_name(f"{base_name}-thumb", "jpg")
    out_path = thumbs_dir / thumb_name
    ok, msg = run_ffmpeg([
        "-y", "-ss", "00:00:01.000", "-i", str(video_path),
        "-vframes", "1",
        # 120x90 box like classic, padded/cropped by CSS in UI
        "-vf", "scale=120:90:force_original_aspect_ratio=decrease,pad=120:90:(ow-iw)/2:(oh-ih)/2",
        str(out_path),
    ])
    if not ok or not out_path.exists():
        return None, f"Thumbnail failed: {msg}"
    return thumb_name, None

def send_file_range(directory: Path, filename: str) -> Response:
    path = directory / filename
    if not path.exists() or not path.is_file():
        abort(404)

    file_size = path.stat().st_size
    range_header = request.headers.get("Range", None)
    mime, _ = mimetypes.guess_type(str(path))
    mime = mime or "application/octet-stream"

    if not range_header:
        return send_from_directory(directory, filename, conditional=True, mimetype=mime)

    m = re.match(r"bytes=(\d+)-(\d*)", range_header)
    if not m:
        return send_from_directory(directory, filename, conditional=True, mimetype=mime)

    start = int(m.group(1))
    end = int(m.group(2)) if m.group(2) else file_size - 1
    start = max(0, min(start, file_size - 1))
    end = max(start, min(end, file_size - 1))
    length = end - start + 1

    def gen():
        with open(path, "rb") as f:
            f.seek(start)
            remaining = length
            chunk = 1024 * 256
            while remaining > 0:
                read_size = min(chunk, remaining)
                data = f.read(read_size)
                if not data:
                    break
                remaining -= len(data)
                yield data

    rv = Response(gen(), 206, mimetype=mime, direct_passthrough=True)
    rv.headers.add("Content-Range", f"bytes {start}-{end}/{file_size}")
    rv.headers.add("Accept-Ranges", "bytes")
    rv.headers.add("Content-Length", str(length))
    return rv

from __future__ import annotations

import hashlib
import threading
from io import BytesIO
from pathlib import Path

import requests
from kivy.clock import Clock
from PIL import Image as PILImage
from PIL import ImageDraw

_CACHE_DIR = Path.home() / ".cache" / "blitztools" / "avatars"
_CACHE_LOCK = threading.Lock()
_AVATAR_SIZE = 128


def _ensure_cache_dir() -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR


def _cache_path(url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
    return _ensure_cache_dir() / f"{digest}_round.png"


def _apply_circle_mask(image: PILImage.Image, size: int = _AVATAR_SIZE) -> PILImage.Image:
    image = image.convert("RGBA")
    image = image.resize((size, size), PILImage.Resampling.LANCZOS)
    mask = PILImage.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size - 1, size - 1), fill=255)
    output = PILImage.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(image, (0, 0), mask)
    return output


def _download_and_convert(url: str) -> str | None:
    path = _cache_path(url)
    if path.is_file():
        return str(path)

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        image = PILImage.open(BytesIO(response.content))
        if getattr(image, "is_animated", False):
            image.seek(0)
        image = _apply_circle_mask(image)
        temp_path = path.with_suffix(".png.tmp")
        with _CACHE_LOCK:
            image.save(temp_path, format="PNG")
            temp_path.replace(path)
        return str(path)
    except Exception:
        return None


def load_avatar(url: str, callback) -> None:
    """Invoke callback(local_png_path | None) on the main Kivy thread."""

    def deliver(path: str | None):
        Clock.schedule_once(lambda _dt: callback(path), 0)

    if not url:
        deliver(None)
        return

    cached = _cache_path(url)
    if cached.is_file():
        deliver(str(cached))
        return

    def worker():
        deliver(_download_and_convert(url))

    threading.Thread(target=worker, daemon=True).start()

from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageDraw

from lib.config.handler import ConfigHandler
from lib.replay_parser.avatar_frames import frame_color_for_kind
from utils.resource_path import get_resource_path

RATING_COEF = 10
PROFILE_SKIN_NATIVE_SIZE = (948, 112)
AVATAR_FRAME_STRIPE_WIDTH = 3
AVATAR_ZOOM = 1.35

_ROMAN = ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))

_CACHE_DIR = Path.home() / ".cache" / "blitztools" / "olenemer"
_TANK_TYPE_DIR = get_resource_path("res/images/tank_types")
_TANK_TYPE_ICON_NAMES = {
    "LT": "lt.png",
    "MT": "mt.png",
    "HT": "ht.png",
    "AT-SPG": "at-spg.png",
}
_LOCAL_IMAGE_CACHE: dict[tuple[str, str], Image.Image] = {}


def level_to_roman(level: int) -> str:
    if level <= 0:
        return "?"
    result = ""
    remaining = level
    for value, numeral in _ROMAN:
        while remaining >= value:
            result += numeral
            remaining -= value
    return result or "?"


def format_rating(rating: int, calibrated: bool) -> str:
    if not calibrated:
        return "0"
    if rating <= 3000:
        return "3000"
    return str(rating)


def tank_type_color(category: str) -> str:
    match category.upper():
        case "LT" | "MT":
            return "#BFE08B"
        case "HT":
            return "#E68E6F"
        case "AT-SPG":
            return "#6678db"
        case _:
            return "#ffffff"


def _tint_image(image: Image.Image, color_hex: str) -> Image.Image:
    base = image.convert("RGBA")
    alpha = base.getchannel("A")
    rgb = tuple(int(color_hex[index : index + 2], 16) for index in (1, 3, 5))
    tinted = Image.new("RGBA", base.size, (*rgb, 255))
    tinted.putalpha(alpha)
    return tinted


def load_tank_type_icon(category: str, *, colorize: bool = True) -> Image.Image | None:
    category_key = category.upper()
    filename = _TANK_TYPE_ICON_NAMES.get(category_key)
    if filename is None:
        return None

    color = tank_type_color(category_key) if colorize else "#ffffff"
    cache_key = (category_key, color)
    cached = _LOCAL_IMAGE_CACHE.get(cache_key)
    if cached is not None:
        return cached.copy()

    path = _TANK_TYPE_DIR / filename
    if not path.is_file():
        return None

    try:
        image = Image.open(path).convert("RGBA")
    except Exception:
        return None

    result = _tint_image(image, color) if colorize else image
    _LOCAL_IMAGE_CACHE[cache_key] = result
    return result.copy()


def frame_hex(kind: str) -> str:
    rgba = frame_color_for_kind(kind)
    return "#{:02x}{:02x}{:02x}".format(
        int(rgba[0] * 255),
        int(rgba[1] * 255),
        int(rgba[2] * 255),
    )


def battles_color(value: int) -> str:
    if value < 5000:
        return "#fffffd"
    if value < 20000:
        return "#b9e497"
    if value < 50000:
        return "#9ec3cf"
    return "#ac9eee"


def rating_color(value: int) -> str:
    if value <= 3000:
        return "#fffffd"
    if value < 4000:
        return "#c4b453"
    if value < 5000:
        return "#83c1ca"
    return "#b236b8"


def winrate_color(value: float) -> str:
    if value < 50:
        return "#fffffd"
    if value < 60:
        return "#b9e497"
    if value < 70:
        return "#9ec3cf"
    return "#ac9eee"


def damage_color(value: int) -> str:
    if value < 1500:
        return "#fffffd"
    if value < 2000:
        return "#b9e497"
    if value < 2500:
        return "#9ec3cf"
    return "#ac9eee"


def _cache_path(prefix: str, url: str, suffix: str = ".png") -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
    return _CACHE_DIR / f"{prefix}_{digest}{suffix}"


def load_image(url: str, prefix: str) -> Image.Image | None:
    if not url:
        return None
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(prefix, url)
    if path.is_file():
        return Image.open(path).convert("RGBA")

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        if getattr(image, "is_animated", False):
            image.seek(0)
        image = image.convert("RGBA")
        image.save(path, format="PNG")
        return image
    except Exception:
        return None


def load_row_avatar(
    url: str,
    width: int,
    height: int,
    frame_kind: str = "",
    zoom: float = AVATAR_ZOOM,
    stripe_on_right: bool = False,
) -> Image.Image | None:
    image = load_image(url, "avatar")
    if image is None:
        return None

    image = image.convert("RGBA")
    src_w, src_h = image.size
    stripe_w = AVATAR_FRAME_STRIPE_WIDTH
    image_width = max(1, width - stripe_w)
    scale = max(image_width / src_w, (height * zoom) / src_h)
    scaled_w = max(image_width, int(round(src_w * scale)))
    scaled_h = max(height, int(round(src_h * scale)))
    scaled = image.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)

    left = max(0, (scaled_w - image_width) // 2)
    top = max(0, (scaled_h - height) // 2)
    cropped = scaled.crop((left, top, left + image_width, top + height))

    output = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    image_x = 0 if stripe_on_right else stripe_w
    output.paste(cropped, (image_x, 0))

    draw = ImageDraw.Draw(output)
    stripe_x = width - stripe_w if stripe_on_right else 0
    draw.rectangle((stripe_x, 0, stripe_x + stripe_w - 1, height - 1), fill=frame_hex(frame_kind))
    return output

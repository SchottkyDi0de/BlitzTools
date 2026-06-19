from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from PIL import Image, ImageFilter

from lib.olenemer.window.theme import (
    BACKGROUND_IMAGE_BLUR_RADIUS,
    BACKGROUND_IMAGE_DARKEN,
    BACKGROUND_IMAGE_OPACITY,
    PANEL_BG,
    PANEL_BG_RGBA,
    ROW_SKIN_DARKEN,
    ROW_SKIN_OPACITY,
)
from utils.resource_path import get_resource_path


class BackgroundType(StrEnum):
    TRANSPARENT = "transparent"
    COLOR = "color"
    IMAGE = "image"


@dataclass(frozen=True)
class OlenemerBackground:
    mode: BackgroundType
    color: str
    image_path: Path | None
    opacity: float

    @property
    def uses_image(self) -> bool:
        return self.mode == BackgroundType.IMAGE

    @property
    def surface_color(self) -> str:
        if self.mode == BackgroundType.IMAGE:
            return "transparent"
        return self.color


def background_from_config(olenemer_config) -> OlenemerBackground:
    mode = BackgroundType(olenemer_config.background_type)
    if mode == BackgroundType.TRANSPARENT:
        color = PANEL_BG
    elif mode == BackgroundType.COLOR:
        color = olenemer_config.background_color
    else:
        color = PANEL_BG

    image_path = None
    if mode == BackgroundType.IMAGE:
        image_path = get_resource_path(olenemer_config.background_image)

    return OlenemerBackground(
        mode=mode,
        color=color,
        image_path=image_path,
        opacity=float(olenemer_config.window_transparency),
    )


def load_background_source(image_path: Path | None) -> Image.Image | None:
    if image_path is None or not image_path.is_file():
        return None
    return Image.open(image_path).convert("RGBA")


def cover_crop_image(image: Image.Image, width: int, height: int) -> Image.Image:
    if width <= 0 or height <= 0:
        return image.copy()

    src_w, src_h = image.size
    scale = max(width / src_w, height / src_h)
    scaled_w = max(1, int(round(src_w * scale)))
    scaled_h = max(1, int(round(src_h * scale)))
    scaled = image.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)

    left = max(0, (scaled_w - width) // 2)
    top = max(0, (scaled_h - height) // 2)
    return scaled.crop((left, top, left + width, top + height))


def apply_readability_overlay(
    image: Image.Image,
    *,
    opacity: float = ROW_SKIN_OPACITY,
    darken: float = ROW_SKIN_DARKEN,
    base_rgba: tuple[int, int, int, int] = PANEL_BG_RGBA,
) -> Image.Image:
    """Dim an image for text readability — same treatment as profile row skins."""
    image = image.convert("RGBA")
    if opacity < 1.0:
        alpha = image.getchannel("A").point(lambda value: int(value * opacity))
        image.putalpha(alpha)
    composited = Image.alpha_composite(Image.new("RGBA", image.size, base_rgba), image)
    if darken > 0:
        overlay_alpha = max(0, min(255, int(round(255 * darken))))
        dark = Image.new("RGBA", image.size, (0, 0, 0, overlay_alpha))
        composited = Image.alpha_composite(composited, dark)
    return composited.convert("RGB")


def blur_image(image: Image.Image, radius: float) -> Image.Image:
    if radius <= 0:
        return image
    return image.filter(ImageFilter.GaussianBlur(radius=radius))


_background_source_cache: dict[Path, Image.Image] = {}


def get_background_source(image_path: Path | None) -> Image.Image | None:
    if image_path is None:
        return None
    cached = _background_source_cache.get(image_path)
    if cached is not None:
        return cached
    loaded = load_background_source(image_path)
    if loaded is not None:
        _background_source_cache[image_path] = loaded
    return loaded


def build_cover_image(
    background: OlenemerBackground,
    width: int,
    height: int,
    *,
    mirrored: bool = False,
) -> Image.Image | None:
    if not background.uses_image:
        return None
    source = get_background_source(background.image_path)
    if source is None:
        return None
    cropped = cover_crop_image(source, width, height)
    blurred = blur_image(cropped, BACKGROUND_IMAGE_BLUR_RADIUS)
    cover = apply_readability_overlay(
        blurred,
        opacity=BACKGROUND_IMAGE_OPACITY,
        darken=BACKGROUND_IMAGE_DARKEN,
    )
    if mirrored:
        cover = cover.transpose(Image.FLIP_LEFT_RIGHT)
    return cover

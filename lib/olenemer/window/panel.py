from __future__ import annotations

import math
import tkinter as tk
from io import BytesIO

import customtkinter as ctk
from PIL import Image, ImageTk

from lib.olenemer.window.columns import FIXED_COLUMNS, HIDDEN_COLUMNS, TOGGLEABLE_COLUMNS
from lib.olenemer.window.assets import (
    PROFILE_SKIN_NATIVE_SIZE,
    battles_color,
    damage_color,
    format_rating,
    level_to_roman,
    load_image,
    load_row_avatar,
    load_tank_type_icon,
    rating_color,
    tank_type_color,
    winrate_color,
)
from lib.olenemer.window.background import BackgroundType, OlenemerBackground, apply_readability_overlay
from lib.olenemer.window.models import PlayerRowData, TeamViewData
from lib.olenemer.window.theme import (
    ACCENT_BORDER_WIDTH,
    ALLIES_TITLE_COLOR,
    AVATAR_IMAGE_HEIGHT,
    AVATAR_IMAGE_WIDTH,
    BASE_COLUMN_WIDTHS,
    BASE_TABLE_WIDTH,
    ENEMIES_TITLE_COLOR,
    HEADER_HEIGHT,
    PANEL_BG,
    PLATOON_BADGE_OUTLINE,
    PLATOON_BADGE_TEXT_COLOR,
    PLATOON_PENTAGON_RADIUS,
    ROW_HEIGHT,
    ROW_SKIN_DARKEN,
    ROW_SKIN_OPACITY,
    SUMMARY_HEIGHT,
    TITLE_HEIGHT,
    TITLE_PADDING_X,
)
from utils.tank_marks_image import render_tank_marks_png

TITLE_BLOCK_HEIGHT = TITLE_HEIGHT + 6


class ColumnVisibility:
    def __init__(self) -> None:
        self.avatar = False
        self.platoon = True
        self.nickname = True
        self.tank = True
        self.battles = True
        self.winrate = True
        self.damage = True
        self.rating = True

    @classmethod
    def from_config(cls, column_status) -> ColumnVisibility:
        visibility = cls()
        for field in TOGGLEABLE_COLUMNS:
            setattr(visibility, field, getattr(column_status, field, True))
        for field in FIXED_COLUMNS:
            setattr(visibility, field, True)
        for field in HIDDEN_COLUMNS:
            setattr(visibility, field, False)
        return visibility

    @classmethod
    def from_config_for_battle(cls, column_status, tv_data: dict[int, TeamViewData]) -> ColumnVisibility:
        visibility = cls.from_config(column_status)
        if not battle_has_platoons(tv_data):
            visibility.platoon = False
        return visibility

    def visible_keys(self) -> list[str]:
        keys = []
        if self.avatar:
            keys.append("avatar")
        if self.platoon:
            keys.append("platoon")
        if self.nickname:
            keys.append("nickname")
        if self.tank:
            keys.append("tank")
        if self.battles:
            keys.append("battles")
        if self.winrate:
            keys.append("winrate")
        if self.damage:
            keys.append("damage")
        if self.rating:
            keys.append("rating")
        return keys


def battle_has_platoons(tv_data: dict[int, TeamViewData]) -> bool:
    return any(
        row.platoon_index > 0
        for team_data in tv_data.values()
        for row in team_data.rows
    )


def _swap_column_order(keys: list[str], first: str, second: str) -> list[str]:
    result = list(keys)
    if first not in result or second not in result:
        return result
    first_idx = result.index(first)
    second_idx = result.index(second)
    result[first_idx], result[second_idx] = result[second_idx], result[first_idx]
    return result


def compute_column_widths(visible: list[str], table_width: int = BASE_TABLE_WIDTH) -> dict[str, int]:
    base_total = sum(BASE_COLUMN_WIDTHS[key] for key in visible)
    if base_total <= 0:
        return {}
    min_widths = {"platoon": 12, "avatar": 24}
    exact = {key: BASE_COLUMN_WIDTHS[key] * table_width / base_total for key in visible}
    widths = {
        key: max(min_widths.get(key, 24), int(math.floor(exact[key])))
        for key in visible
    }
    remainder = table_width - sum(widths.values())
    if remainder > 0:
        for key in sorted(visible, key=lambda item: exact[item] - math.floor(exact[item]), reverse=True):
            if remainder <= 0:
                break
            widths[key] += 1
            remainder -= 1
    return widths


def prepare_row_skin(
    url: str,
    width: int,
    height: int = ROW_HEIGHT,
    opacity: float = ROW_SKIN_OPACITY,
    darken: float = ROW_SKIN_DARKEN,
    mirrored: bool = False,
) -> Image.Image | None:
    image = load_image(url, "skin")
    if image is None:
        return None

    native_w, native_h = PROFILE_SKIN_NATIVE_SIZE
    if image.size != (native_w, native_h):
        image = image.resize((native_w, native_h), Image.Resampling.LANCZOS)

    scaled_h = max(height, int(round(width * native_h / native_w)))
    scaled = image.resize((width, scaled_h), Image.Resampling.LANCZOS)
    if scaled_h > height:
        top = (scaled_h - height) // 2
        scaled = scaled.crop((0, top, width, top + height))

    if mirrored:
        scaled = scaled.transpose(Image.FLIP_LEFT_RIGHT)

    return apply_readability_overlay(scaled, opacity=opacity, darken=darken)


class OlenemerPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        columns: ColumnVisibility | None = None,
        mirrored: bool = False,
        *,
        background: OlenemerBackground | None = None,
        show_profile_skins: bool = True,
        tank_display_type: str = "icon",
        border_color: str = "#00f0ff",
        show_border: bool = True,
        show_summary: bool = True,
        **kwargs,
    ):
        self.background = background or OlenemerBackground(
            mode=BackgroundType.TRANSPARENT,
            color=PANEL_BG,
            image_path=None,
            opacity=1.0,
        )
        self._cover_image: Image.Image | None = None
        kwargs.setdefault("border_width", 0)
        kwargs.setdefault("fg_color", self.background.surface_color)
        super().__init__(master, **kwargs)
        self.columns = columns or ColumnVisibility()
        self.mirrored = mirrored
        self.show_profile_skins = show_profile_skins
        self.tank_display_type = tank_display_type
        self._border_color = border_color
        self.show_border = show_border
        self.show_summary = show_summary
        self._images: list[ImageTk.PhotoImage | ctk.CTkImage] = []
        self._table_width = BASE_TABLE_WIDTH

        self.body = ctk.CTkFrame(self, fg_color=self.background.surface_color, border_width=0)
        self.body.pack(anchor="nw")

    def _canvas_bg(self) -> str:
        if self.background.uses_image:
            return PANEL_BG
        return self.background.color

    def _apply_canvas_background(self, canvas: tk.Canvas, y_offset: int, height: int) -> None:
        if not self.background.uses_image or self._cover_image is None:
            return
        y_end = min(self._cover_image.height, y_offset + height)
        if y_offset >= self._cover_image.height or y_end <= y_offset:
            return
        slice_image = self._cover_image.crop((0, y_offset, self._cover_image.width, y_end))
        photo = ImageTk.PhotoImage(slice_image)
        self._keep_image(photo)
        canvas.create_image(0, 0, anchor="nw", image=photo)
        canvas.bg_image = photo

    def _keep_image(self, image: ImageTk.PhotoImage | ctk.CTkImage):
        self._images.append(image)
        return image

    def _clear_body(self) -> None:
        for child in self.body.winfo_children():
            child.destroy()
        self._images.clear()

    def _visible_columns(self) -> list[str]:
        visible = self.columns.visible_keys()
        if self.mirrored:
            visible = _swap_column_order(visible, "platoon", "nickname")
            return visible[::-1]
        return visible

    def _title_color(self) -> str:
        return ENEMIES_TITLE_COLOR if self.mirrored else ALLIES_TITLE_COLOR

    def _column_anchor(self, key: str) -> str:
        if key in {"battles", "winrate", "damage", "rating", "platoon"}:
            return "center"
        return "w"

    def _column_text_x(self, x: int, width: int, anchor: str) -> int:
        if anchor == "center":
            return x + width // 2
        if anchor == "e":
            return x + width - 4
        return x + 4

    def _separator_height(self) -> int:
        return ACCENT_BORDER_WIDTH if self.show_border else 0

    def _pack_row_separator(self) -> None:
        if not self.show_border:
            return
        sep = tk.Frame(
            self.body,
            width=self._table_width,
            height=ACCENT_BORDER_WIDTH,
            bg=self._border_color,
            highlightthickness=0,
            bd=0,
            borderwidth=0,
        )
        sep.pack(anchor="nw", fill="x")
        sep.pack_propagate(False)

    def render(self, data: TeamViewData, *, cover_image: Image.Image | None = None) -> None:
        self._clear_body()
        self._cover_image = cover_image

        visible = self._visible_columns()
        col_widths = compute_column_widths(visible, BASE_TABLE_WIDTH)
        self._table_width = sum(col_widths.values())

        y_offset = 0

        self._render_title(data, self._table_width, y_offset)
        y_offset += TITLE_BLOCK_HEIGHT
        self._pack_row_separator()
        y_offset += self._separator_height()

        canvas_bg = self._canvas_bg()
        header = tk.Canvas(
            self.body,
            width=self._table_width,
            height=HEADER_HEIGHT,
            highlightthickness=0,
            bd=0,
            bg=canvas_bg,
        )
        header.pack(anchor="nw")
        self._apply_canvas_background(header, y_offset, HEADER_HEIGHT)
        self._draw_header_row(header, col_widths, visible)
        y_offset += HEADER_HEIGHT
        self._pack_row_separator()
        y_offset += self._separator_height()

        for row in data.rows:
            self._render_row(row, col_widths, visible, y_offset)
            y_offset += ROW_HEIGHT
            self._pack_row_separator()
            y_offset += self._separator_height()

        if self.show_summary:
            summary = tk.Canvas(
                self.body,
                width=self._table_width,
                height=SUMMARY_HEIGHT,
                highlightthickness=0,
                bd=0,
                bg=canvas_bg,
            )
            summary.pack(anchor="nw")
            self._apply_canvas_background(summary, y_offset, SUMMARY_HEIGHT)
            self._draw_summary_row(summary, data, col_widths, visible)

        self.configure(width=self._table_width, fg_color=self.background.surface_color)

    def panel_width(self) -> int:
        return self._table_width

    @staticmethod
    def _row_separator_count(row_count: int) -> int:
        return row_count + 2

    def content_height(self, row_count: int) -> int:
        separators = self._row_separator_count(row_count) * self._separator_height()
        height = TITLE_BLOCK_HEIGHT + HEADER_HEIGHT + row_count * ROW_HEIGHT + separators
        if self.show_summary:
            height += SUMMARY_HEIGHT
        return height

    def _render_title(self, data: TeamViewData, width: int, y_offset: int) -> None:
        canvas = tk.Canvas(
            self.body,
            width=width,
            height=TITLE_BLOCK_HEIGHT,
            highlightthickness=0,
            bd=0,
            bg=self._canvas_bg(),
        )
        canvas.pack(anchor="nw")
        self._apply_canvas_background(canvas, y_offset, TITLE_BLOCK_HEIGHT)

        anchor = "e" if self.mirrored else "w"
        text_x = width - TITLE_PADDING_X if self.mirrored else TITLE_PADDING_X
        canvas.create_text(
            text_x,
            TITLE_BLOCK_HEIGHT // 2,
            text=data.title,
            anchor=anchor,
            fill=self._title_color(),
            font=("Segoe UI", 14, "bold"),
        )

    def _header_labels(self) -> dict[str, str]:
        return {
            "avatar": "",
            "platoon": "",
            "nickname": "Ник",
            "tank": "Танк",
            "battles": "Бои",
            "winrate": "WR",
            "damage": "Урон",
            "rating": "Рейт.",
        }

    def _draw_header_row(self, canvas, col_widths: dict[str, int], visible: list[str]) -> None:
        labels = self._header_labels()
        x = 0
        mid_y = HEADER_HEIGHT // 2
        for key in visible:
            width = col_widths[key]
            anchor = self._column_anchor(key)
            canvas.create_text(
                self._column_text_x(x, width, anchor),
                mid_y,
                text=labels.get(key, ""),
                anchor=anchor,
                fill="#aaaaaa",
                font=("Segoe UI", 9, "bold"),
            )
            x += width

    def _summary_text_y(self) -> int:
        return SUMMARY_HEIGHT - 3

    @staticmethod
    def _summary_text_anchor(anchor: str) -> str:
        return {"w": "sw", "center": "s", "e": "se"}.get(anchor, "s")

    def _draw_summary_row(self, canvas, data: TeamViewData, col_widths: dict[str, int], visible: list[str]) -> None:
        values = {
            "avatar": "",
            "platoon": "",
            "nickname": "Сводка",
            "tank": "",
            "battles": f"{data.summary_battles:.0f}",
            "winrate": f"{data.summary_winrate:.2f}%",
            "damage": f"{data.summary_damage:.0f}",
            "rating": f"{data.summary_rating:.0f}" if data.summary_rating else "0",
        }
        colors = {
            "avatar": "#d0d0d0",
            "platoon": "#d0d0d0",
            "nickname": "#d0d0d0",
            "tank": "#d0d0d0",
            "battles": battles_color(int(data.summary_battles)),
            "winrate": winrate_color(data.summary_winrate),
            "damage": damage_color(int(data.summary_damage)),
            "rating": rating_color(int(data.summary_rating)) if data.summary_rating else "#fffffd",
        }
        x = 0
        text_y = self._summary_text_y()
        for key in visible:
            width = col_widths[key]
            anchor = self._column_anchor(key)
            canvas.create_text(
                self._column_text_x(x, width, anchor),
                text_y,
                text=values.get(key, ""),
                anchor=self._summary_text_anchor(anchor),
                fill=colors.get(key, "#d0d0d0"),
                font=("Segoe UI", 9, "bold"),
            )
            x += width

    def _render_row(self, row: PlayerRowData, col_widths: dict[str, int], visible: list[str], row_y: int) -> None:
        canvas = tk.Canvas(
            self.body,
            width=self._table_width,
            height=ROW_HEIGHT,
            highlightthickness=0,
            bd=0,
            bg=self._canvas_bg(),
        )
        canvas.pack(anchor="nw")
        self._apply_canvas_background(canvas, row_y, ROW_HEIGHT)

        if row.profile_skin_url and self.show_profile_skins and not self.background.uses_image:
            skin = prepare_row_skin(row.profile_skin_url, self._table_width, ROW_HEIGHT, mirrored=self.mirrored)
            if skin is not None:
                photo = ImageTk.PhotoImage(skin)
                self._keep_image(photo)
                canvas.create_image(0, 0, anchor="nw", image=photo)
                canvas.skin_image = photo

        x = 0
        mid_y = ROW_HEIGHT // 2
        for key in visible:
            width = col_widths[key]
            if key == "avatar":
                self._draw_avatar(canvas, row, x, width, mid_y)
            elif key == "platoon":
                self._draw_platoon(canvas, row, x, width, mid_y)
            elif key == "nickname":
                self._draw_nickname(canvas, row, x, width, mid_y)
            elif key == "tank":
                self._draw_tank(canvas, row, x, width, mid_y)
            elif key == "battles":
                self._draw_text(canvas, f"{row.battles:,}".replace(",", " "), x, width, mid_y, "center", battles_color(row.battles))
            elif key == "winrate":
                self._draw_text(canvas, f"{row.winrate:.2f}%", x, width, mid_y, "center", winrate_color(row.winrate))
            elif key == "damage":
                self._draw_text(canvas, str(row.avg_damage), x, width, mid_y, "center", damage_color(row.avg_damage))
            elif key == "rating":
                rating_text = format_rating(row.rating, row.calibrated)
                color = rating_color(row.rating if row.calibrated else 0)
                self._draw_text(canvas, rating_text, x, width, mid_y, "center", color)
            x += width

    def _draw_text(self, canvas, text: str, x: int, width: int, y: int, anchor: str, color: str) -> None:
        text_anchor = {"center": "center", "w": "w", "e": "e"}.get(anchor, "center")
        text_x = x + width // 2 if anchor == "center" else x + 4
        canvas.create_text(text_x, y, text=text, anchor=text_anchor, fill=color, font=("Segoe UI", 9, "bold"))

    def _measure_text(self, canvas, text: str) -> int:
        item = canvas.create_text(-10000, -10000, text=text, font=("Segoe UI", 9, "bold"))
        box = canvas.bbox(item)
        canvas.delete(item)
        return box[2] - box[0] if box else 0

    def _fit_text_to_width(self, canvas, text: str, max_width: int) -> str:
        if not text or max_width <= 0:
            return ""
        if self._measure_text(canvas, text) <= max_width:
            return text

        suffix = "..."
        trimmed = text
        while trimmed and self._measure_text(canvas, trimmed + suffix) > max_width:
            trimmed = trimmed[:-1]
        return (trimmed + suffix) if trimmed else suffix

    def _pentagon_points(self, cx: float, cy: float, radius: float) -> list[float]:
        return [
            coord
            for index in range(5)
            for coord in (
                cx + radius * math.cos(math.radians(-90 + index * 72)),
                cy + radius * math.sin(math.radians(-90 + index * 72)),
            )
        ]

    def _draw_platoon(self, canvas, row: PlayerRowData, x: int, width: int, y: int) -> None:
        if row.platoon_index <= 0:
            return

        cx = x + width // 2
        radius = min(PLATOON_PENTAGON_RADIUS, width // 2 - 1, ROW_HEIGHT // 2 - 2)
        canvas.create_polygon(
            self._pentagon_points(cx, y, radius),
            outline=PLATOON_BADGE_OUTLINE,
            fill="",
            width=1,
        )
        canvas.create_text(
            cx,
            y-1,
            text=str(row.platoon_index),
            fill=PLATOON_BADGE_TEXT_COLOR,
            font=("Segoe UI Black", 8, "bold"),
        )

    def _draw_avatar(self, canvas, row: PlayerRowData, x: int, width: int, y: int) -> None:
        avatar_y = (ROW_HEIGHT - AVATAR_IMAGE_HEIGHT) // 2
        if self.mirrored:
            avatar_x = x + width - AVATAR_IMAGE_WIDTH - 1
            stripe_on_right = True
        else:
            avatar_x = x + 1
            stripe_on_right = False

        avatar_image = load_row_avatar(
            row.avatar_url,
            width=AVATAR_IMAGE_WIDTH,
            height=AVATAR_IMAGE_HEIGHT,
            frame_kind=row.frame_kind,
            stripe_on_right=stripe_on_right,
        )
        if avatar_image is None:
            canvas.create_text(
                avatar_x + AVATAR_IMAGE_WIDTH // 2,
                y,
                text="?",
                fill="white",
                font=("Segoe UI", 9, "bold"),
            )
        else:
            photo = ImageTk.PhotoImage(avatar_image)
            self._keep_image(photo)
            canvas.create_image(avatar_x, avatar_y, anchor="nw", image=photo)

    def _draw_nickname(self, canvas, row: PlayerRowData, x: int, width: int, y: int) -> None:
        nick = row.nickname
        if row.nickname in ["nyTeLLlecTBeHHuK", "_Semen_Van_"]:
            nick = f"💻 {nick}"
            color = "#FF0000"
        elif row.clan_tag in ["WG"]:
            color = "#FF0000"
        elif row.clan_tag in ["LESTA", "LST"]:
            color = "#00AAFF"
        elif row.is_author:
            nick = f"⭐ {nick}"
            color = "#ffff00"
        elif row.clan_tag and row.author_clan_tag and row.clan_tag == row.author_clan_tag and not row.is_author:
            color = "#00ff00"
        else:
            color = "white"
        if row.clan_tag:
            nick = f"[{row.clan_tag}] {nick}"
        nick = self._fit_text_to_width(canvas, nick, max(8, width - 8))
        canvas.create_text(x + 4, y, text=nick, anchor="w", fill=color, font=("Segoe UI", 9, "bold"))

    def _draw_tank(self, canvas, row: PlayerRowData, x: int, width: int, y: int) -> None:
        tank_color = tank_type_color(row.tank_category)
        default_text_color = "#ffffff"
        level_text = level_to_roman(row.tank_level)
        show_icon = self.tank_display_type == "icon"
        colorize_name = self.tank_display_type == "color"
        icon_photo = None
        icon_w = 0

        if show_icon:
            tank_icon = load_tank_type_icon(row.tank_category)
            if tank_icon is not None:
                icon_image = tank_icon.resize((10, 10), Image.Resampling.LANCZOS)
                icon_w = icon_image.width
                icon_photo = ImageTk.PhotoImage(icon_image)
                self._keep_image(icon_photo)

        marks_photo = None
        marks_w = 0
        if row.marks > 0:
            png = render_tank_marks_png(
                row.marks,
                stripe_width=6,
                stripe_height=12,
                gap=0,
                overlap=2,
                vertical_lift=1,
            )
            if png:
                marks_image = Image.open(BytesIO(png))
                marks_w = marks_image.width
                marks_photo = ImageTk.PhotoImage(marks_image)
                self._keep_image(marks_photo)

        cursor_x = x + 2

        if icon_photo is not None:
            canvas.create_image(cursor_x, y, anchor="w", image=icon_photo)
            cursor_x += icon_w + 3

        canvas.create_text(
            cursor_x,
            y,
            text=level_text,
            anchor="w",
            fill=default_text_color,
            font=("Segoe UI", 9, "bold"),
        )
        cursor_x += self._measure_text(canvas, level_text) + (4 if marks_w else 2)

        if marks_photo is not None:
            canvas.create_image(cursor_x, y, anchor="w", image=marks_photo)
            cursor_x += marks_w + 4

        tank_name = self._fit_text_to_width(
            canvas,
            row.tank_name,
            max(8, width - (cursor_x - x) - 2),
        )
        name_color = tank_color if colorize_name else default_text_color
        canvas.create_text(cursor_x, y, text=tank_name, anchor="w", fill=name_color, font=("Segoe UI", 9, "bold"))

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk
from PIL import Image, ImageTk
from lib.olenemer.window.background import OlenemerBackground, build_cover_image
from lib.olenemer.window.monitor import MAGNET_THRESHOLD, get_monitor_at
from lib.olenemer.window.panel import ColumnVisibility, OlenemerPanel
from lib.olenemer.window.models import TeamViewData
from lib.olenemer.window.theme import ACCENT_BORDER_WIDTH, PANEL_BG, WINDOW_TITLE_PREFIX


def _apply_window_opacity(window: ctk.CTkToplevel, opacity: float) -> None:
    window.attributes("-alpha", opacity)


def _stack_widget_below(widget: tk.Misc, below: tk.Misc | None = None) -> None:
    """Lower a widget in the stacking order (Canvas.lower() is for canvas items)."""
    if below is None:
        widget.tk.call("lower", widget._w)
    else:
        widget.tk.call("lower", widget._w, below._w)


class OlenemerWindow(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        team: int,
        team_data: TeamViewData,
        *,
        background: OlenemerBackground,
        position: list[int],
        columns: ColumnVisibility,
        border_color: str,
        show_profile_skins: bool = True,
        tank_display_type: str = "icon",
        show_window_border: bool = True,
        show_border: bool = True,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.team = team
        self.team_data = team_data
        self.background = background
        self.title(f"{WINDOW_TITLE_PREFIX} — {team_data.title}")
        self.x: int | None = None
        self.y: int | None = None
        self._team_data: TeamViewData | None = team_data
        self._window_pos = list(position[:2])
        self.show_window_border = show_window_border
        self._border_width = ACCENT_BORDER_WIDTH if show_window_border else 0
        self._bg_canvas: tk.Canvas | None = None
        self._bg_photo: ImageTk.PhotoImage | None = None
        self._last_outer_size: tuple[int, int] | None = None
        self._bottom_border_bar: tk.Frame | None = None
        self.border_color = border_color
        self.overrideredirect(True)
        self.withdraw()
        self._ensure_topmost()
        _apply_window_opacity(self, background.opacity)
        self.configure(fg_color=self.background.color if not background.uses_image else PANEL_BG)

        root_color = self.background.color if not background.uses_image else PANEL_BG
        frame_color = border_color if show_window_border else root_color
        self.border_frame = ctk.CTkFrame(self, fg_color=frame_color, corner_radius=0, border_width=0)
        self.border_frame.pack(fill="both", expand=True)

        self.root_layer = ctk.CTkFrame(self.border_frame, fg_color=root_color, corner_radius=0, border_width=0)

        if background.uses_image:
            self._bg_canvas = tk.Canvas(
                self.root_layer,
                highlightthickness=0,
                bd=0,
                borderwidth=0,
                bg=PANEL_BG,
            )
            self._bg_canvas.place(x=0, y=0)
            self._bg_canvas.bind("<ButtonPress-1>", self.start_move)
            self._bg_canvas.bind("<B1-Motion>", self.do_move)
            self._bg_canvas.bind("<ButtonRelease-1>", self.stop_move)
        self.status_label = ctk.CTkLabel(
            self.root_layer,
            text="Нет данных",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffaa00",
            fg_color=self.background.surface_color,
        )

        self.panel = OlenemerPanel(
            self.root_layer,
            columns=columns,
            mirrored=(team == 2),
            background=background,
            show_profile_skins=show_profile_skins,
            tank_display_type=tank_display_type,
            border_color=border_color,
            show_border=show_border,
        )

        for widget in (self, self.border_frame, self.root_layer):
            widget.bind("<ButtonPress-1>", self.start_move)
            widget.bind("<B1-Motion>", self.do_move)
            widget.bind("<ButtonRelease-1>", self.stop_move)

        if team_data.rows:
            self.panel.pack(anchor="nw")
            self._bind_drag(self.panel)
            self._rerender()
        else:
            self._bind_drag(self.panel)

        self._sync_window_border_chrome(compact=not team_data.rows)

    def _outer_padding(self) -> tuple[int, int]:
        if not self.show_window_border:
            return 0, 0
        return self._border_width, self._border_width

    def _sync_window_border_chrome(self, *, compact: bool = False) -> None:
        if self._bottom_border_bar is not None:
            self._bottom_border_bar.destroy()
            self._bottom_border_bar = None

        self.root_layer.pack_forget()

        if self.show_window_border:
            self._bottom_border_bar = tk.Frame(
                self.border_frame,
                height=ACCENT_BORDER_WIDTH,
                bg=self.border_color,
                highlightthickness=0,
                bd=0,
                borderwidth=0,
            )
            self._bottom_border_bar.pack(side="bottom", fill="x")
            self._bottom_border_bar.pack_propagate(False)
            self._bottom_border_bar.bind("<ButtonPress-1>", self.start_move)
            self._bottom_border_bar.bind("<B1-Motion>", self.do_move)
            self._bottom_border_bar.bind("<ButtonRelease-1>", self.stop_move)

        pad_x, pad_top = self._outer_padding()
        pack_kwargs = {
            "in_": self.border_frame,
            "padx": pad_x,
            "pady": (pad_top, 0),
        }
        if compact:
            self.root_layer.pack(fill="both", expand=True, **pack_kwargs)
        else:
            self.root_layer.pack(anchor="nw", **pack_kwargs)

    def apply_window_border_settings(self, show_window_border: bool) -> None:
        self.show_window_border = show_window_border
        self._border_width = ACCENT_BORDER_WIDTH if show_window_border else 0
        root_color = self._root_inner_color()
        self.border_frame.configure(fg_color=self.border_color if show_window_border else root_color)
        compact = self.status_label.winfo_ismapped() and not (
            self._team_data and self._team_data.rows and self.panel.winfo_ismapped()
        )
        self._sync_window_border_chrome(compact=compact)

    def _root_inner_color(self) -> str:
        return self.background.color if not self.background.uses_image else PANEL_BG

    def _repack_root_layer_compact(self) -> None:
        self._sync_window_border_chrome(compact=True)

    def _repack_root_layer_content(self) -> None:
        self._sync_window_border_chrome(compact=False)

    def show_loading(self, message: str = "Загрузка...") -> None:
        self._team_data = TeamViewData(title=self.team_data.title, rows=[])
        self.team_data = self._team_data
        self.panel.pack_forget()
        if self._bg_canvas is not None:
            self._bg_canvas.place_forget()

        root_color = self._root_inner_color()
        self.root_layer.configure(fg_color=root_color)
        self._repack_root_layer_compact()
        self.status_label.pack_forget()
        self.status_label.configure(
            text=message,
            text_color="#ffaa00",
            fg_color=root_color,
        )
        self.status_label.place(relx=0.5, rely=0.5, anchor="center")
        self._apply_loading_geometry()

    def _apply_outer_geometry(self, outer_w: int, outer_h: int) -> None:
        self._last_outer_size = (outer_w, outer_h)
        x, y = self._window_pos
        self.geometry(f"{outer_w}x{outer_h}+{x}+{y}")
        self.minsize(outer_w, outer_h)
        self.maxsize(outer_w, outer_h)
        self.update_idletasks()
        self._ensure_topmost()

    def _apply_loading_geometry(self) -> None:
        if self._last_outer_size is not None:
            outer_w, outer_h = self._last_outer_size
        else:
            border = self._border_width * 2
            outer_w = 220 + border
            outer_h = 56 + border
        self._apply_outer_geometry(outer_w, outer_h)

    def clear_content(self) -> None:
        self._team_data = TeamViewData(title=self.team_data.title, rows=[])
        self.team_data = self._team_data
        self.status_label.place_forget()
        self.status_label.pack_forget()
        self.panel.pack_forget()
        if self._bg_canvas is not None:
            self._bg_canvas.place_forget()

    def _ensure_topmost(self) -> None:
        self.attributes("-topmost", True)

    def _bind_drag(self, widget) -> None:
        widget.bind("<ButtonPress-1>", self.start_move)
        widget.bind("<B1-Motion>", self.do_move)
        widget.bind("<ButtonRelease-1>", self.stop_move)
        for child in widget.winfo_children():
            self._bind_drag(child)

    def _update_background_image(self, cover_image: Image.Image | None, width: int, height: int) -> None:
        if self._bg_canvas is None:
            return
        if cover_image is None or width <= 0 or height <= 0:
            self._bg_canvas.place_forget()
            return

        self._bg_canvas.configure(width=width, height=height)
        self._bg_canvas.place(x=0, y=0, width=width, height=height)
        self._bg_photo = ImageTk.PhotoImage(cover_image)
        self._bg_canvas.delete("all")
        self._bg_canvas.create_image(0, 0, anchor="nw", image=self._bg_photo)
        _stack_widget_below(self._bg_canvas, self.panel)

    def _rerender(self) -> None:
        if self._team_data is None:
            return

        self.status_label.place_forget()
        self.status_label.pack_forget()
        self._repack_root_layer_content()
        if not self.panel.winfo_ismapped():
            self.panel.pack(anchor="nw")

        row_count = len(self._team_data.rows)
        inner_w = self.panel.panel_width()
        inner_h = self.panel.content_height(row_count)
        cover_image = build_cover_image(
            self.background,
            inner_w,
            inner_h,
            mirrored=(self.team == 2),
        )

        self.panel.render(self._team_data, cover_image=cover_image)
        self.title(f"{WINDOW_TITLE_PREFIX} — {self._team_data.title}")
        self._bind_drag(self.panel)
        self._update_background_image(cover_image, inner_w, inner_h)
        self.update_idletasks()

        inner_w = self.panel.panel_width()
        inner_h = max(self.panel.winfo_reqheight(), self.panel.content_height(row_count))
        self.panel.configure(width=inner_w, height=inner_h)
        self.root_layer.configure(width=inner_w, height=inner_h)
        if not self.background.uses_image:
            self.root_layer.configure(fg_color=self.background.color)
            self.configure(fg_color=self.background.color)

        pad_x, pad_top = self._outer_padding()
        outer_w = inner_w + pad_x * 2
        outer_h = inner_h + pad_top * 2
        self._apply_outer_geometry(outer_w, outer_h)
        if self._bg_canvas is not None and cover_image is not None:
            _stack_widget_below(self._bg_canvas, self.panel)
        _apply_window_opacity(self, self.background.opacity)
        self._ensure_topmost()

    def apply_opacity(self, opacity: float) -> None:
        self.background = OlenemerBackground(
            mode=self.background.mode,
            color=self.background.color,
            image_path=self.background.image_path,
            opacity=opacity,
        )
        _apply_window_opacity(self, opacity)
        self._ensure_topmost()

    def start_move(self, event):
        self.x = event.x_root - self.winfo_x()
        self.y = event.y_root - self.winfo_y()

    def stop_move(self, _event):
        self.x = None
        self.y = None
        app = self.master
        if hasattr(app, "save_window_positions"):
            app.save_window_positions()

    def do_move(self, event):
        if self.x is None or self.y is None:
            return

        x = event.x_root - self.x
        y = event.y_root - self.y
        win_w, win_h = self.winfo_width(), self.winfo_height()
        monitor = get_monitor_at(x, y)

        if x - monitor["x"] < MAGNET_THRESHOLD:
            x = monitor["x"]
        elif monitor["x"] + monitor["width"] - (x + win_w) < MAGNET_THRESHOLD:
            x = monitor["x"] + monitor["width"] - win_w

        if y - monitor["y"] < MAGNET_THRESHOLD:
            y = monitor["y"]
        elif monitor["y"] + monitor["height"] - (y + win_h) < MAGNET_THRESHOLD:
            y = monitor["y"] + monitor["height"] - win_h

        self._window_pos = [x, y]
        self.geometry(f"+{x}+{y}")

        app = self.master
        if not hasattr(app, "get_window"):
            return

        other = app.get_window(3 - self.team)
        if other is None or not other.winfo_exists():
            return

        other_w = other.winfo_width()
        mirror_x = monitor["x"] + monitor["width"] - other_w - (x - monitor["x"])
        other._window_pos = [mirror_x, y]
        other.geometry(f"+{mirror_x}+{y}")

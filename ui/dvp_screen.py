from __future__ import annotations

from pathlib import Path
from threading import Thread

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from lib.config.handler import ConfigHandler
from lib.dvpl_converter.batch import BatchResult, pack_files, pack_folder, unpack_files, unpack_folder
from lib.dvpl_converter.classes import CompressionTypes
from utils.file_dialogs import pick_files, pick_folder


_COMPRESSION_MAP = {
    "none": CompressionTypes.NONE,
    "lz4": CompressionTypes.LZ4,
    "lz4_hc": CompressionTypes.LZ4_HC,
}


class DvpScreen(MDScreen):
    name = "dvp"

    def __init__(self, **kwargs):
        self._busy = False
        self._compression = "lz4_hc"
        self._keep_original = True
        self._fast_mode = True
        self._skip_if_exist = True
        super().__init__(**kwargs)

    def on_enter(self, *_args):
        self._sync_compression_buttons()
        self._sync_compression_hint()
        self._sync_option_buttons()
        self._sync_output_dir_ui()
        Clock.schedule_once(lambda _dt: self._resync_button_appearance(), 0.05)

    def _resync_button_appearance(self):
        self._sync_compression_buttons()
        self._sync_compression_hint()
        self._sync_option_buttons()
        self._sync_output_dir_ui()

    def select_compression(self, value: str):
        if self._busy or value not in _COMPRESSION_MAP:
            return
        self._compression = value
        self._sync_compression_buttons()
        self._sync_compression_hint()

    def toggle_keep_original(self):
        if self._busy:
            return
        self._keep_original = not self._keep_original
        self._sync_option_buttons()

    def toggle_fast_mode(self):
        if self._busy:
            return
        self._fast_mode = not self._fast_mode
        self._sync_option_buttons()

    def toggle_skip_if_exist(self):
        if self._busy:
            return
        self._skip_if_exist = not self._skip_if_exist
        self._sync_option_buttons()

    def pick_output_dir(self):
        if self._busy:
            return
        loc = self._locale()
        folder = pick_folder(title=loc.actions.pick_output_dir_dialog)
        if not folder:
            return
        app = MDApp.get_running_app()
        if not app:
            return
        app.config.converter.output_dir = folder
        self._write_converter_config(app)
        self._sync_output_dir_ui()

    def reset_output_dir(self):
        if self._busy:
            return
        app = MDApp.get_running_app()
        if not app or not app.config.converter.output_dir:
            return
        app.config.converter.output_dir = ""
        self._write_converter_config(app)
        self._sync_output_dir_ui()

    def pick_and_pack(self):
        if self._busy:
            return
        loc = self._locale()
        paths = pick_files(title=loc.actions.pick_files_pack)
        if not paths:
            return
        self._run_task(
            lambda on_progress: pack_files(
                [Path(path) for path in paths],
                compression_type=_COMPRESSION_MAP[self._compression],
                keep_original=self._keep_original,
                skip_if_exist=self._skip_if_exist,
                output_dir=self._output_dir(),
                on_result=self._emit_result,
                on_progress=on_progress,
            )
        )

    def pick_and_unpack(self):
        if self._busy:
            return
        loc = self._locale()
        paths = pick_files(
            title=loc.actions.pick_files_unpack,
            filetypes=[("DVPL files", "*.dvpl"), ("All files", "*.*")],
        )
        if not paths:
            return
        self._run_task(
            lambda on_progress: unpack_files(
                [Path(path) for path in paths],
                keep_original=self._keep_original,
                skip_if_exist=self._skip_if_exist,
                output_dir=self._output_dir(),
                on_result=self._emit_result,
                on_progress=on_progress,
            )
        )

    def pick_folder_and_pack(self):
        if self._busy:
            return
        loc = self._locale()
        folder = pick_folder(title=loc.actions.pick_folder_pack)
        if not folder:
            return
        self._run_task(
            lambda on_progress: pack_folder(
                Path(folder),
                compression_type=_COMPRESSION_MAP[self._compression],
                keep_original=self._keep_original,
                skip_if_exist=self._skip_if_exist,
                output_dir=self._output_dir(),
                on_result=self._emit_result,
                on_progress=on_progress,
            )
        )

    def pick_folder_and_unpack(self):
        if self._busy:
            return
        loc = self._locale()
        folder = pick_folder(title=loc.actions.pick_folder_unpack)
        if not folder:
            return
        self._run_task(
            lambda on_progress: unpack_folder(
                Path(folder),
                keep_original=self._keep_original,
                skip_if_exist=self._skip_if_exist,
                output_dir=self._output_dir(),
                on_result=self._emit_result,
                on_progress=on_progress,
            )
        )

    def clear_log(self):
        if self._busy:
            return
        self.ids.log_label.text = self._locale().log.idle

    def refresh_locale(self):
        loc = self._locale()
        self.ids.screen_title.text = loc.title
        self.ids.screen_hint.text = loc.description
        self.ids.compression_section.text = loc.sections.compression
        self.ids.options_section.text = loc.sections.options
        self.ids.log_section.text = loc.sections.log

        labels = {
            "none": loc.compression.none,
            "lz4": loc.compression.lz4,
            "lz4_hc": loc.compression.lz4_hc,
        }
        for btn in self.ids.compression_group.children:
            if hasattr(btn, "option_value"):
                btn.option_label = labels.get(btn.option_value, btn.option_label)
                btn.sync_appearance()
        self._sync_compression_hint()

        self.ids.keep_original_btn.option_label = loc.options.keep_original
        self.ids.keep_original_hint.text = loc.options.keep_original_hint
        self.ids.fast_mode_btn.option_label = loc.options.fast_mode
        self.ids.fast_mode_hint.text = loc.options.fast_mode_hint
        self.ids.skip_if_exist_btn.option_label = loc.options.skip_if_exist
        self.ids.skip_if_exist_hint.text = loc.options.skip_if_exist_hint
        self._sync_option_buttons()
        self._sync_output_dir_ui()

        action_labels = {
            "pack_btn": loc.actions.pack,
            "unpack_btn": loc.actions.unpack,
            "pack_folder_btn": loc.actions.pack_folder,
            "unpack_folder_btn": loc.actions.unpack_folder,
            "clear_log_btn": loc.actions.clear_log,
            "pick_output_dir_btn": loc.actions.pick_output_dir,
            "reset_output_dir_btn": loc.actions.reset_output_dir,
        }
        for widget_id, text in action_labels.items():
            widget = self.ids.get(widget_id)
            if widget is not None and hasattr(widget, "action_label"):
                widget.action_label = text
                widget.sync_appearance()

    def _locale(self):
        app = MDApp.get_running_app()
        code = app.config.app_global.language if app else "ru"
        if app and code not in app.locales.data:
            code = "ru"
        return app.locales.data[code].main.dvp if app else None

    def _sync_compression_buttons(self):
        for btn in self.ids.compression_group.children:
            if hasattr(btn, "option_value"):
                btn.active = btn.option_value == self._compression
                btn.sync_appearance()

    def _sync_compression_hint(self):
        loc = self._locale()
        if not loc:
            return
        hints = {
            "none": loc.compression.none_hint,
            "lz4": loc.compression.lz4_hint,
            "lz4_hc": loc.compression.lz4_hc_hint,
        }
        self.ids.compression_hint.text = hints.get(
            self._compression, loc.compression.lz4_hc_hint
        )

    def _sync_option_buttons(self):
        mapping = {
            "keep_original_btn": self._keep_original,
            "fast_mode_btn": self._fast_mode,
            "skip_if_exist_btn": self._skip_if_exist,
        }
        for btn_id, active in mapping.items():
            btn = self.ids[btn_id]
            btn.active = active
            btn.sync_appearance()

    def _output_dir(self) -> Path | None:
        app = MDApp.get_running_app()
        if not app:
            return None
        raw = (app.config.converter.output_dir or "").strip()
        if not raw:
            return None
        path = Path(raw)
        return path if path.is_dir() else None

    def _sync_output_dir_ui(self):
        loc = self._locale()
        if not loc:
            return
        app = MDApp.get_running_app()
        raw = ""
        if app:
            raw = (app.config.converter.output_dir or "").strip()
        if raw:
            self.ids.output_dir_hint.text = loc.options.output_dir_active.format(path=raw)
        else:
            self.ids.output_dir_hint.text = loc.options.output_dir_hint
        reset_btn = self.ids.reset_output_dir_btn
        reset_btn.disabled = self._busy or not raw
        reset_btn.sync_appearance()
        pick_btn = self.ids.pick_output_dir_btn
        pick_btn.disabled = self._busy
        pick_btn.sync_appearance()

    def _write_converter_config(self, app):
        handler = ConfigHandler()
        handler.config = app.config
        handler.write_config()

    def _run_task(self, worker):
        loc = self._locale()
        self._set_busy(True)
        self._reset_progress()
        if not self._fast_mode:
            self._append_log(loc.log.working)

        def on_progress(current: int, total: int, name: str) -> None:
            Clock.schedule_once(
                lambda _dt: self._apply_progress(current, total, name),
                0,
            )

        def run():
            try:
                result = worker(on_progress)
            except Exception as exc:
                result = BatchResult(failed=1)
                Clock.schedule_once(
                    lambda _dt: self._append_log(
                        loc.results.failed.format(name="-", error=exc)
                    ),
                    0,
                )
            else:
                summary = loc.log.summary.format(
                    ok=result.ok,
                    failed=result.failed,
                    skipped=result.skipped,
                )
                Clock.schedule_once(lambda _dt: self._append_log(summary), 0)
            finally:
                Clock.schedule_once(lambda _dt: self._set_busy(False), 0)

        Thread(target=run, daemon=True).start()

    def _reset_progress(self) -> None:
        self.ids.progress_fill.size_hint_x = 0
        loc = self._locale()
        if loc:
            self.ids.progress_label.text = loc.log.working

    def _apply_progress(self, current: int, total: int, name: str) -> None:
        if not self._busy:
            return

        loc = self._locale()
        if not loc:
            return

        label = self.ids.progress_label
        fill = self.ids.progress_fill
        if total <= 0:
            fill.size_hint_x = 0
            label.text = loc.log.working
            return

        ratio = min(1.0, max(0.0, current / total))
        fill.size_hint_x = ratio if ratio > 0 else 0
        display_name = name or "…"
        label.text = loc.log.progress.format(
            current=current,
            total=total,
            name=display_name,
        )

    def _set_progress_visible(self, visible: bool) -> None:
        panel = self.ids.progress_panel
        panel.opacity = 1 if visible else 0
        panel.disabled = not visible
        panel.height = dp(42) if visible else 0
        if visible:
            self._reset_progress()
        else:
            self.ids.progress_fill.size_hint_x = 0
            self.ids.progress_label.text = ""

    def _emit_result(self, payload: str):
        kind, name, detail = (payload.split(":", 2) + ["", ""])[:3]
        if kind == "failed":
            loc = self._locale()
            line = loc.results.failed.format(name=name, error=detail)
            Clock.schedule_once(lambda _dt: self._append_log(line), 0)
            return

        if self._fast_mode:
            return

        loc = self._locale()
        if kind == "packed":
            line = loc.results.packed.format(name=name, out=detail)
        elif kind == "unpacked":
            line = loc.results.unpacked.format(name=name, out=detail)
        elif kind == "skipped":
            line = loc.results.skipped.format(name=name, out=detail)
        else:
            return
        Clock.schedule_once(lambda _dt: self._append_log(line), 0)

    def _append_log(self, line: str):
        label = self.ids.log_label
        current = (label.text or "").strip()
        idle = self._locale().log.idle
        if not current or current == idle:
            label.text = line
        else:
            label.text = f"{current}\n{line}"
        label.height = max(dp(120), label.texture_size[1] + dp(8))

    def _set_busy(self, busy: bool):
        self._busy = busy
        for widget_id in (
            "pack_btn",
            "unpack_btn",
            "pack_folder_btn",
            "unpack_folder_btn",
            "clear_log_btn",
            "pick_output_dir_btn",
            "reset_output_dir_btn",
        ):
            widget = self.ids.get(widget_id)
            if widget is not None:
                widget.disabled = busy
        self._set_progress_visible(busy)
        self._sync_output_dir_ui()

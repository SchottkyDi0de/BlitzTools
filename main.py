# libraries imports
import json
import time
import pathlib
import datetime
from pynput.keyboard import Key, Listener
import threading
import traceback
import PIL.Image
from typing import Tuple, Optional, Union
from lib.utils.resources import resource_path

# gui imports
from customtkinter import (
    CTkButton, 
    CTkFrame, 
    CTkLabel, 
    CTkImage, 
    CTkFont,
    CTk
)

# program files imports
from replay_parser.parser import ReplayParser, ReplayParserError, ReplayData
from lib.watchdog.handle_replays import FileWatchDog, NewFileEvent, NewFolderEvent
from settings.settings import _settings
from ui.settings_window import SettingsWindow
from ui.sessions_window import SessionsWindow
from ui.olenemer import OlenemerWindow



# constants and globals
SERVER_URL = "http://212.80.7.214:20060/verify_key"
tanks_file_path = resource_path('tanks_names.json')

with open(tanks_file_path, 'r', encoding='utf-8-sig') as f:
    TANKS_DICT = json.load(f)


class HotkeyManager:
    def __init__(self, app):
        self.app = app
        self.f1_pressed = False
        self.f2_pressed = False
        self.listener: Optional[Listener] = None
        self.action_cooldown = 0.1  # 500ms cooldown
        self.last_f1_time = 0
        self.last_f2_time = 0

    def action_f1(self):
        current_time = time.time()
        if current_time - self.last_f1_time < self.action_cooldown:
            return
        self.last_f1_time = current_time
        
        self.app.after(0, self.app._refresh_olenemers)
        print("F1")

    def action_f2(self):
        current_time = time.time()
        if current_time - self.last_f2_time < self.action_cooldown:
            return
        self.last_f2_time = current_time
        
        self.app.after(0, self.app.open_olenemer)
        print("F2")

    def on_press(self, key):
        if key == Key.f1:
            if not self.f1_pressed:
                self.f1_pressed = True
                self.action_f1()
        elif key == Key.f2:
            if not self.f2_pressed:
                self.f2_pressed = True
                self.action_f2()

    def on_release(self, key):
        if key == Key.f1:
            self.f1_pressed = False
        elif key == Key.f2:
            self.f2_pressed = False

    def start(self):
        def start_listener():
            with Listener(on_press=self.on_press, on_release=self.on_release) as listener:
                self.listener = listener
                listener.join()
        threading.Thread(target = start_listener, daemon = True).start()

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.listener = None

# data structures
class TankSession:
    battles: int = 0
    wins: int = 0
    damage_dealt: int = 0
    hits: int = 0
    shots: int = 0
    xp: int = 0

    wr: float = 0.0
    ac: float = 0.0
    avg_dmg: int = 0
    avg_xp: int = 0

    def save_divide(self, dividend: int, divisor: int, return_int: bool = False, default: float = 0.0):
        try:
            res = dividend / divisor
        except ZeroDivisionError:
            return default
        
        if return_int:
            return int(res)
        else:
            return res
    
    def compute(self):
        self.wr = self.save_divide(self.wins, self.battles, default=0.0) * 100
        self.ac = self.save_divide(self.hits, self.shots, default=0.0) * 100
        self.avg_dmg = self.save_divide(self.damage_dealt, self.battles, return_int=True, default=0)
        self.avg_xp = self.save_divide(self.xp, self.battles, return_int=True, default=0)
        
    def update(self, replay_data):
        self.battles += 1
        self.wins += 1 if replay_data.winner_team_number == replay_data.author.team_number else 0
        self.damage_dealt += replay_data.author.damage_dealt
        self.hits += replay_data.author.n_hits
        self.shots += replay_data.author.n_shots
        for result in replay_data.player_results:
            if result.info.account_id == replay_data.author.account_id:
                if _settings['font']['premium']:
                    if _settings['font']['base_xp_only']:
                        self.xp += result.info.base_xp * 1.5
                    else:
                        self.xp += replay_data.author.total_xp
                    break
                else:
                    if _settings['font']['base_xp_only']:
                        self.xp += result.info.base_xp
                    else:
                        self.xp += replay_data.author.total_xp
                    break
        self.compute()

class SessionStorage:
    battles: int = 0
    wins: int = 0
    damage_dealt: int = 0
    hits: int = 0
    shots: int = 0
    xp: int = 0

    wr: float = 0.0
    ac: float = 0.0
    avg_dmg: int = 0
    avg_xp: int = 0

    tank_sessions: dict = {}

    def serialize_tank_sessions(self):
        serialized_sessions = {}
        for tank_id, session in self.tank_sessions.items():
            serialized_sessions[tank_id] = {
                "battles": session.battles,
                "wins": session.wins,
                "damage_dealt": session.damage_dealt,
                "hits": session.hits,
                "shots": session.shots,
                "xp": session.xp,
                "wr": f"{session.wr:2.2f} %",
                "ac": f"{session.ac:2.2f} %",
                "avg_dmg": f"{int(session.avg_dmg)}",
                "avg_xp": f"{int(session.avg_xp)}"
            }
        return serialized_sessions

    def update_tank_session(self, tank_id, replay_data):
        if tank_id not in self.tank_sessions:
            self.tank_sessions[tank_id] = TankSession()
        self.tank_sessions[tank_id].update(replay_data)

    def save_divide(self, dividend: int, divisor: int, return_int: bool = False, default: float = 0.0):
        try:
            res = dividend / divisor
        except ZeroDivisionError:
            return default
        
        if return_int:
            return int(res)
        else:
            return res
    
    def compute(self):
        self.wr = self.save_divide(self.wins, self.battles, default=0.0) * 100
        self.ac = self.save_divide(self.hits, self.shots, default=0.0) * 100
        self.avg_dmg = self.save_divide(self.damage_dealt, self.battles, return_int=True, default=0)
        self.avg_xp = self.save_divide(self.xp, self.battles, return_int=True, default=0)
        
    def delete_session(self):
        #print('Core: Session cleared')
        self.battles = 0
        self.wins = 0
        self.damage_dealt = 0
        self.hits = 0
        self.shots = 0
        self.wr = 0.0
        self.ac = 0.0
        self.avg_dmg = 0
        self.xp = 0
        self.avg_xp = 0
        self.tank_sessions = {}

class StatsLabelContainer(CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.btls_container = CTkFrame(self, height=30)
        self.wr_container = CTkFrame(self, height=30)
        self.ac_container = CTkFrame(self, height=30)
        self.avg_dmg_container = CTkFrame(self, height=30)
        self.avg_xp_container = CTkFrame(self, height=30)
        
        self.btls_container.pack(side="top", fill="x")
        self.wr_container.pack(side="top", fill="x")
        self.ac_container.pack(side="top", fill="x")
        self.avg_dmg_container.pack(side="top", fill="x")
        self.avg_xp_container.pack(side="top", fill="x")

_session_storage = SessionStorage()



# main application class
class App(CTk):
    def __init__(self, fg_color: Optional[Union[str, Tuple[str, str]]] = None, **kwargs):
        super().__init__(fg_color, **kwargs)

        self.wm_attributes("-topmost", True)
        win_transp = _settings.db['window'].get('transparency', None)
        if win_transp < 1:
            win_transp = 80
            _settings.db['window']['transparency'] = 80
            _settings.db.commit()
        alpha = float(win_transp) / 100.0
        self.attributes("-alpha", alpha)
        self.minsize(230, 120)
        self.title('TBSession')
        self.iconbitmap(resource_path("assets/ui/app_logo.ico"))
        self.parser = ReplayParser()

        self.hotkey_manager = HotkeyManager(self)
        self.hotkey_manager.start()
 
        self.frame = CTkFrame(self)
        self.stats_container = StatsLabelContainer(self.frame)
        self.frame.pack(fill='both', expand=True)

        self.settings_btn = CTkButton(
            self.stats_container.btls_container,
            width = 28,
            text = "",
            hover = False,
            command = self.open_settings,
            fg_color = "grey",
            image = CTkImage(PIL.Image.open(resource_path("assets/ui/settings_btn_cog.png")), size = (20, 20)),
        )
        self.settings_btn.pack(side = 'right', anchor = 'ne')

        self.sessions_btn = CTkButton(
            self.stats_container.btls_container,
            width = 28,
            text = "",
            hover = False,
            command = self.open_sessions,
            fg_color = "grey",
            image = CTkImage(PIL.Image.open(resource_path("assets/ui/tank_session.png")), size = (20, 20)),
        )
        self.sessions_btn.pack(side = 'right', anchor = 'ne')

        self.olenemer_btn = CTkButton(
            self.stats_container.btls_container,
            width = 28,
            text = "",
            hover = False,
            command = self.open_olenemer,
            fg_color = "grey",
            image = CTkImage(PIL.Image.open(resource_path("assets/ui/olenemer.png")), size = (20, 20)),
        )
        self.olenemer_btn.pack(side = 'right', anchor = 'ne')


        self.static_stats_font = CTkFont(
            family = _settings['font']['static_text'], 
            size = _settings['font']['static_text_size'], 
            weight = "bold"
        )
        self.stats_font = CTkFont(
            family = _settings['font']['dynamic_text'], 
            size = _settings['font']['dynamic_text_size'],
            weight = "bold"
        )

        self.static_btls_label = CTkLabel(
            self.stats_container.btls_container,
            text = _settings['font']['battles_label'],
            font = self.static_stats_font
        )
        self.static_wr_label = CTkLabel(
            self.stats_container.wr_container,
            text = _settings['font']['winrate_label'],
            font = self.static_stats_font
        )
        self.static_ac_label = CTkLabel(
            self.stats_container.ac_container,
            text = _settings['font']['accuracy_label'],
            font = self.static_stats_font
        )
        self.static_avg_dmg_label = CTkLabel(
            self.stats_container.avg_dmg_container,
            text = _settings['font']['avg_damage_label'],
            font = self.static_stats_font
        )
        self.static_avg_xp_label = CTkLabel(
            self.stats_container.avg_xp_container,
            text = _settings['font']['avg_xp_label'],
            font = self.static_stats_font
        )

        self.btls_label = CTkLabel(
            self.stats_container.btls_container,
            text=f"{_session_storage.battles}",
            font=self.stats_font,
            text_color=_settings['window']['primary_color']
        )
        
        self.wr_label = CTkLabel(
            self.stats_container.wr_container,
            text=f"{_session_storage.wr:2.2f} %",
            font=self.stats_font,
            text_color=_settings['window']['primary_color']
        )
        
        self.ac_label = CTkLabel(
            self.stats_container.ac_container,
            text=f"{_session_storage.ac:2.2f} %",
            font=self.stats_font,
            text_color=_settings['window']['primary_color']
        )
        
        self.avg_dmg_label = CTkLabel(
            self.stats_container.avg_dmg_container,
            text=f"{int(_session_storage.avg_dmg)}",
            font=self.stats_font,
            text_color=_settings['window']['primary_color']
        )

        self.avg_xp_label = CTkLabel(
            self.stats_container.avg_xp_container,
            text=f"{int(_session_storage.avg_xp)}",
            font=self.stats_font,
            text_color=_settings['window']['primary_color']
        )
        
        self.del_session_btn = CTkButton(
            self.stats_container.avg_xp_container,
            width=28,
            text="",
            hover=False,
            command=self.delete_session,
            fg_color="grey",
            image=CTkImage(PIL.Image.open(resource_path("assets/ui/delete_session.png")), size=(20, 20)),
        )
        
        self.static_btls_label.pack(side='left')
        self.static_wr_label.pack(side='left')
        self.static_ac_label.pack(side='left')
        self.static_avg_dmg_label.pack(side='left')
        self.static_avg_xp_label.pack(side='left')
        
        self.btls_label.pack(side='left', anchor='nw')
        self.wr_label.pack(side='left', anchor='nw')
        self.ac_label.pack(side='left', anchor='nw')
        self.avg_dmg_label.pack(side='left', anchor='nw')
        self.avg_xp_label.pack(side='left', anchor='nw')
        
        self.del_session_btn.pack(side='right', anchor='se')
        
        self.stats_container.pack(side="top", fill="x")
        
        self.x = None
        self.y = None

        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.do_move)

        self.settings_window = None
        self.sessions_window = None
        self.olenemer_window = None
        self.olenemer_window_2 = None

        self.olenemer_data = {}

        self.after(1000, self.run_watcher)
        self.after(1000, self.run_temp_watcher)
        self.after(1000, self.run_folder_watcher)
        self.check_temp_folder_existance()
        self.load_window_position()
        self.start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.protocol("WM_DELETE_WINDOW", self.save_window_position_and_close)

    def load_window_position(self):
        try:
            x = _settings['window']['position']['x']
            y = _settings['window']['position']['y']
            self.geometry(f"+{x}+{y}")
        except Exception:
            traceback.print_exc()

    def save_window_position_and_close(self):
        x = self.winfo_x()
        y = self.winfo_y()
        _settings['window']['position']['x'] = x
        _settings['window']['position']['y'] = y
        _settings.db.commit()
        self.save_session_to_db()
        if hasattr(self, "hotkey_manager"):
            self.hotkey_manager.stop()
        self.destroy()

    def delete_session(self):
        self.save_session_to_db()
        _session_storage.delete_session()
        self.start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.update_values()
        
    def open_settings(self):
        if self.sessions_window and self.sessions_window.winfo_exists():
            self.sessions_window.focus()
        elif self.settings_window is None or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
            self.settings_window.grab_set()
        else:
            self.settings_window.focus()

    def open_sessions(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.focus()
        elif self.sessions_window is None or not self.sessions_window.winfo_exists():
            self.sessions_window = SessionsWindow(self)
            self.sessions_window.grab_set()
        else:
            self.sessions_window.focus()

    def open_olenemer(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.focus()
        elif self.sessions_window and self.sessions_window.winfo_exists():
            self.sessions_window.focus()
        elif self.olenemer_window is None or not self.olenemer_window.winfo_exists():
            left_x = _settings.db["olenemer"]["left_x"]
            left_y = _settings.db["olenemer"]["left_y"]
            right_x = _settings.db["olenemer"]["right_x"]
            right_y = _settings.db["olenemer"]["right_y"]
            self.olenemer_window = OlenemerWindow(self, x=left_x, y=left_y, side="left", teams_data=self.olenemer_data)
            self.olenemer_window_2 = OlenemerWindow(self, x=right_x, y=right_y, side="right", teams_data=self.olenemer_data)
        else:
            # toggle visibility: if any window is withdrawn -> show both, else hide both
            # determine mapped (visible) state using winfo_ismapped to avoid confusion with state strings
            try:
                left_mapped = self.olenemer_window.winfo_ismapped() if self.olenemer_window and self.olenemer_window.winfo_exists() else False
            except Exception:
                traceback.print_exc()
                left_mapped = False
            try:
                right_mapped = self.olenemer_window_2.winfo_ismapped() if self.olenemer_window_2 and self.olenemer_window_2.winfo_exists() else False
            except Exception:
                traceback.print_exc()
                right_mapped = False

            # if either is hidden -> deiconify both and refresh
            if not left_mapped or not right_mapped:
                if self.olenemer_window and self.olenemer_window.winfo_exists():
                    try:
                        self.olenemer_window.deiconify()
                        self.olenemer_window.lift()
                        self.olenemer_window.refresh()
                    except Exception:
                        traceback.print_exc()
                if self.olenemer_window_2 and self.olenemer_window_2.winfo_exists():
                    try:
                        self.olenemer_window_2.deiconify()
                        self.olenemer_window_2.lift()
                        self.olenemer_window_2.refresh()
                    except Exception:
                        traceback.print_exc()
            else:
                # hide both windows and save positions
                if self.olenemer_window and self.olenemer_window.winfo_exists():
                    try:
                        self.olenemer_window.save_position()
                    except Exception:
                        traceback.print_exc()
                    try:
                        self.olenemer_window.withdraw()
                    except Exception:
                        traceback.print_exc()
                if self.olenemer_window_2 and self.olenemer_window_2.winfo_exists():
                    try:
                        self.olenemer_window_2.save_position()
                    except Exception:
                        traceback.print_exc()
                    try:
                        self.olenemer_window_2.withdraw()
                    except Exception:
                        traceback.print_exc()

    def save_session_to_db(self):
        if _session_storage.battles != 0:
            session = {
                'start_time': self.start_time,
                'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'battles': _session_storage.battles,
                'winrate': f"{_session_storage.wr:2.2f} %",
                'accuracy': f"{_session_storage.ac:2.2f} %",
                'damage': f"{int(_session_storage.avg_dmg)}",
                'xp': f"{int(_session_storage.avg_xp)}",
                'tank_sessions': _session_storage.serialize_tank_sessions()
            }
            _settings.db['sessions'].append(session)
            _settings.db.commit()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, _):
        self.x = None
        self.y = None

    def do_move(self, event):
        if self.x is not None and self.y is not None:
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.winfo_x() + deltax
            y = self.winfo_y() + deltay
            self.geometry(f"+{x}+{y}")

    def update_all_widgets(self):
        self.stats_font = CTkFont(
            family=_settings.db['font']['dynamic_text'], 
            size=_settings.db['font']['dynamic_text_size'],
            weight="bold"
        )
        self.static_stats_font = CTkFont(
            family=_settings.db['font']['static_text'], 
            size=_settings.db['font']['static_text_size'],
            weight="bold"
        )

        self.static_btls_label.configure(
            text=_settings.db['font']['battles_label'],
            font=self.static_stats_font
        )
        self.static_wr_label.configure(
            text=_settings.db['font']['winrate_label'],
            font=self.static_stats_font,
        )
        self.static_ac_label.configure(
            text=_settings.db['font']['accuracy_label'],
            font=self.static_stats_font
        )
        self.static_avg_dmg_label.configure(
            text=_settings.db['font']['avg_damage_label'],
            font=self.static_stats_font
        )
        self.static_avg_xp_label.configure(
            text=_settings.db['font']['avg_xp_label'],
            font=self.static_stats_font
        )

        self.btls_label.configure(
            font=self.stats_font,
            text_color=_settings.db['window']['primary_color']
        )
        self.wr_label.configure(
            font=self.stats_font,
            text_color=_settings.db['window']['primary_color']
        )
        self.ac_label.configure(
            font=self.stats_font,
            text_color=_settings.db['window']['primary_color']
        )
        self.avg_dmg_label.configure(
            font=self.stats_font,
            text_color=_settings.db['window']['primary_color']
        )
        self.avg_xp_label.configure(
            font=self.stats_font,
            text_color=_settings.db['window']['primary_color']
        )

        try:
            win_transp = _settings.db['window'].get('transparency', None)
        except Exception:
            win_transp = None
        if win_transp is None:
            # legacy: transparent is bool
            legacy = _settings.db['window'].get('transparent', False)
            alpha = 0.8 if legacy else 1.0
        else:
            try:
                alpha = float(win_transp) / 100.0
            except Exception:
                alpha = 1.0
        self.attributes("-alpha", alpha)

        if self.olenemer_window and self.olenemer_window.winfo_exists():
            self.olenemer_window.attributes("-alpha", alpha)
            self.olenemer_window.refresh()
        if self.olenemer_window_2 and self.olenemer_window_2.winfo_exists():
            self.olenemer_window_2.attributes("-alpha", alpha)
            self.olenemer_window_2.refresh()

        self.update()

    def update_values(self):
        self.btls_label.configure(text=f"{_session_storage.battles}")
        self.avg_dmg_label.configure(text=f"{int(_session_storage.avg_dmg)}")
        self.avg_xp_label.configure(text=f"{int(_session_storage.avg_xp)}")
        self.wr_label.configure(text=f"{_session_storage.wr:2.2f} %")
        self.ac_label.configure(text=f"{_session_storage.ac:2.2f} %")
        self.update()

    def run_watcher(self):
        self.watcher = FileWatchDog(event_handler=self.on_replay_event)

    def run_temp_watcher(self):
        self.temp_watcher = FileWatchDog(event_handler=self.on_temp_replay_event)

    def run_folder_watcher(self):
        self.folder_watcher = FileWatchDog(folder_handler=self._on_folder_event_main)

    def rerun_watcher(self):
        self.watcher = None
        self.run_watcher()

    def _on_folder_event_main(self, event: NewFolderEvent):
        if event.new_folder_path is None:
            # hide olenemer windows instead of destroying to preserve state
            if self.olenemer_window and self.olenemer_window.winfo_exists():
                try:                self.olenemer_window.save_position()
                except Exception:   pass
                try:                self.olenemer_window.withdraw()
                except Exception:   pass

            if self.olenemer_window_2 and self.olenemer_window_2.winfo_exists():
                try:                self.olenemer_window_2.save_position()
                except Exception:   pass
                try:                self.olenemer_window_2.withdraw()
                except Exception:   pass
            return

        # Auto-create or refresh Olenemer windows depending on user setting
        try:
            auto_open = _settings.db['window'].get('auto_open_olenemer', True)
        except Exception:
            auto_open = True

        if auto_open:
            if self.olenemer_window is None or not self.olenemer_window.winfo_exists():
                left_x = _settings["olenemer"]["left_x"]
                left_y = _settings["olenemer"]["left_y"]
                self.olenemer_window = OlenemerWindow(self, x=left_x, y=left_y, side="left", teams_data=self.olenemer_data)
            elif self.olenemer_window.winfo_exists():
                self.olenemer_window.refresh()

            if self.olenemer_window_2 is None or not self.olenemer_window_2.winfo_exists():
                right_x = _settings["olenemer"]["right_x"]
                right_y = _settings["olenemer"]["right_y"]
                self.olenemer_window_2 = OlenemerWindow(self, x=right_x, y=right_y, side="right", teams_data=self.olenemer_data)
            elif self.olenemer_window_2.winfo_exists():
                self.olenemer_window_2.refresh()
        else:
            # auto-open disabled: don't create windows, but refresh existing ones
            if self.olenemer_window and self.olenemer_window.winfo_exists():
                try:
                    self.olenemer_window.refresh()
                except Exception:
                    traceback.print_exc()
            if self.olenemer_window_2 and self.olenemer_window_2.winfo_exists():
                try:
                    self.olenemer_window_2.refresh()
                except Exception:
                    traceback.print_exc()

    def on_temp_replay_event(self, event: NewFileEvent):
        if str(event.new_file_path).endswith('.tbreplay') or str(event.new_file_path).endswith('.wotbreplay'):
            return

        try:
            # parse replay in watcher thread
            replay_data = self.parser.parse_data_replay(event.new_file_path)
        except ReplayParserError:
            # schedule a refresh on main thread and retry after a short sleep
            self.after(0, self._refresh_olenemers)
            time.sleep(1)
            return self.on_temp_replay_event(event)
        except Exception as e:
            print(f"Error in temp replay watcher: {e}")
            return traceback.print_exc()

        # schedule UI work on main thread to avoid tkinter threading issues
        try:
            self.after(0, lambda rd=replay_data: self._on_temp_replay_main(rd))
        except Exception:
            # fallback: call directly (shouldn't be used for tkinter operations)
            self._on_temp_replay_main(replay_data)

    def _refresh_olenemers(self):
        if self.olenemer_window and self.olenemer_window.winfo_exists():
            try:                self.olenemer_window.refresh()
            except Exception:   traceback.print_exc()
        if self.olenemer_window_2 and self.olenemer_window_2.winfo_exists():
            try:                self.olenemer_window_2.refresh()
            except Exception:   traceback.print_exc()

    def _on_temp_replay_main(self, replay_data):
        self.olenemer_data = replay_data
        # If windows are missing (first time after clear), create them so user sees data automatically
        try:                left_exists = self.olenemer_window and self.olenemer_window.winfo_exists()
        except Exception:   left_exists = False
        try:                right_exists = self.olenemer_window_2 and self.olenemer_window_2.winfo_exists()
        except Exception:   right_exists = False

        if not left_exists or not right_exists:
            try:
                left_x = _settings.db['olenemer']['left_x']
                left_y = _settings.db['olenemer']['left_y']
                right_x = _settings.db['olenemer']['right_x']
                right_y = _settings.db['olenemer']['right_y']
            except Exception:
                left_x = left_y = right_x = right_y = 0
            try:
                # create both windows if missing, but only if auto-open is enabled in settings
                try:
                    auto_open = _settings.db['window'].get('auto_open_olenemer', True)
                except Exception:
                    auto_open = True

                if auto_open:
                    # create missing windows
                    if not left_exists:
                        self.olenemer_window = OlenemerWindow(self, x=left_x, y=left_y, side="left", teams_data=self.olenemer_data)
                    if not right_exists:
                        self.olenemer_window_2 = OlenemerWindow(self, x=right_x, y=right_y, side="right", teams_data=self.olenemer_data)
                else:
                    # auto-open disabled: do not create new windows here
                    pass
            except Exception:
                traceback.print_exc()

        # ensure both windows are visible and refreshed
        if self.olenemer_window and self.olenemer_window.winfo_exists():
            try:
                if not self.olenemer_window.winfo_ismapped():
                    self.olenemer_window.deiconify()
                    self.olenemer_window.lift()
                self.olenemer_window.refresh()
            except Exception:   traceback.print_exc()
        if self.olenemer_window_2 and self.olenemer_window_2.winfo_exists():
            try:
                if not self.olenemer_window_2.winfo_ismapped():
                    self.olenemer_window_2.deiconify()
                    self.olenemer_window_2.lift()
                self.olenemer_window_2.refresh()
            except Exception:   traceback.print_exc()
        print("self.olenemer_data: ", self.olenemer_data)

    def check_temp_folder_existance(self):
        replay_path = _settings.db['replays_path']
        folders = [d for d in pathlib.Path(replay_path).iterdir() if d.is_dir() and d.name.endswith('.tbreplay')]
        if not folders and self.olenemer_data is not None:
            self.olenemer_data = None
            print("self.olenemer_data: ", self.olenemer_data)
            # hide windows instead of destroying
            if self.olenemer_window and self.olenemer_window.winfo_exists():
                try:                self.olenemer_window.save_position()
                except Exception:   traceback.print_exc()
                try:                self.olenemer_window.withdraw()
                except Exception:   traceback.print_exc()

            if self.olenemer_window_2 and self.olenemer_window_2.winfo_exists():
                try:                self.olenemer_window_2.save_position()
                except Exception:   traceback.print_exc()
                try:                self.olenemer_window_2.withdraw()
                except Exception:   traceback.print_exc()

            if self.olenemer_window and self.olenemer_window.winfo_exists():
                try:                self.olenemer_window.refresh()
                except Exception:   traceback.print_exc()

            if self.olenemer_window_2 and self.olenemer_window_2.winfo_exists():
                try:                self.olenemer_window_2.refresh()
                except Exception:   traceback.print_exc()
        self.after(1000, self.check_temp_folder_existance)



    def on_replay_event(self, event: NewFileEvent):
        if str(event.new_file_path).endswith('data.replay'):
            return

        try:
            replay_data = self.parser.parse(event.new_file_path)
        except Exception:
            #print(f"Failed to parse {event.new_file_path}")
            if ('ZIP' in traceback.format_exc()) and ('invalid Zip archive' not in traceback.format_exc()):
                self.watcher.set_deferred_replay(event.new_file_path)
            return

        # print(replay_data.model_dump_json(indent=4))
        # ids = [player.account_id for player in replay_data.players]
        # print(ids)

        if replay_data.room_type == 2:
            return

        #print(f"Data successfully loaded from {event.new_file_path}")
        # schedule session update on main thread to avoid tkinter calls from watcher thread
        try:
            self.after(0, lambda rd=replay_data: self._on_replay_parsed_main(rd))
        except Exception:
            self._on_replay_parsed_main(replay_data)

    def _on_replay_parsed_main(self, replay_data: ReplayData):
        if replay_data.room_type not in [1, 7]: # 1 - обычные бои, 7 - рейтинговые
            return None
        _session_storage.battles += 1
        _session_storage.wins += 1 if replay_data.winner_team_number == replay_data.author.team_number else 0
        _session_storage.damage_dealt += replay_data.author.damage_dealt
        _session_storage.hits += replay_data.author.n_hits
        _session_storage.shots += replay_data.author.n_shots

        for result in replay_data.player_results:
            if result.info.account_id == replay_data.author.account_id:
                if _settings['font']['premium']:
                    if _settings['font']['base_xp_only']:
                        _session_storage.xp += result.info.base_xp * 1.5
                    else:
                        _session_storage.xp += replay_data.author.total_xp
                    break
                else:
                    if _settings['font']['base_xp_only']:
                        _session_storage.xp += result.info.base_xp
                    else:
                        _session_storage.xp += replay_data.author.total_xp
                    break

        for result in replay_data.player_results:
            if str(result.info.tank_id) not in TANKS_DICT:
                for player in replay_data.players:
                    if player.account_id == result.info.account_id:
                        print(f"!!! Найден новый танк: {result.info.tank_id} у игрока {player.info.nickname}")

        for result in replay_data.player_results:
            if result.info.account_id == replay_data.author.account_id:
                _session_storage.update_tank_session(str(result.info.tank_id), replay_data)
                break

        _session_storage.compute()
        try:
            self.update_values()
        except Exception:
            pass
        #print('Core: Session calculated')



# main loop
if __name__ == "__main__":
    app = App()
    app.mainloop()
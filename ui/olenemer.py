import os
import json
import pathlib
import traceback
from screeninfo import get_monitors
from customtkinter import (
    CTkToplevel,
    CTkLabel,
    CTkFont,
    CTkFrame
)
from tksheet import Sheet
from settings.settings import _settings
from lib.utils.resources import resource_path


# Загрузка данных о танках
tanks_file_path = resource_path('tanks_names.json')
with open(tanks_file_path, 'r', encoding='utf-8-sig') as f:
    TANKS_INFO = json.load(f)


translations = {
    'en': {
        'olenemer': "Olenemer",
        'nickname': "Nickname",
        'tank': "Tank",
        'battles': "Battles",
        'wins': "Winrate",
        'damage': "Damage",
        'rating': "Rating",
        'team_1': "Allies team",
        'team_2': "Enemies team",
        'no_battle': "You are not in the battle",
        'data_loading': "Data is loading..."
    },
    'ru': {
        'olenemer': "Оленемер",
        'nickname': "Ник",
        'tank': "Танк",
        'battles': "Бои",
        'wins': "Винрейт",
        'damage': "Урон",
        'rating': "Рейтинг",
        'team_1': "Команда союзников",
        'team_2': "Команда противников",
        'no_battle': "Вы не находитесь в бою",
        'data_loading': "Данные загружаются..."
    }
}


class OlenemerWindow(CTkToplevel):
    def __init__(self, master, x: int = 0, y: int = 0, side: str = "right", teams_data: dict = {}, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.side = side
        self.teams_data = teams_data

        # кеш состояния отображаемых колонок (чтобы пропускать перерисовку когда настройки колонок не менялись)
        self._last_columns_state = None
        self.MAGNET_THRESHOLD = 20

        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        win_transp = _settings.db['window'].get('transparency', None)
        if win_transp < 1:
            win_transp = 80
            _settings.db['window']['transparency'] = 80
            _settings.db.commit()
        alpha = float(win_transp) / 100.0
        self.attributes("-alpha", alpha)
        self.minsize(170, 10)
        self.maxsize(580, 1000)
        self.resizable(False, False)

        self.root_layer = CTkFrame(self)
        self.root_layer.pack(fill="both", expand=True)

        self.geometry(f"+{x}+{y}")

        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<Destroy>", lambda e: self.save_position())

        self.table = None

        if self.winfo_exists():
            self.after(0, self.load_olenemer)

    def refresh(self):
        if self.winfo_exists():
            self.load_olenemer()

    def save_position(self):
        x, y = self.winfo_x(), self.winfo_y()
        if self.side == "left":
            _settings.db['olenemer']['left_x'] = x
            _settings.db['olenemer']['left_y'] = y
        elif self.side == "right":
            _settings.db['olenemer']['right_x'] = x
            _settings.db['olenemer']['right_y'] = y
        _settings.db.commit()

    def start_move(self, event):
        self.x = event.x_root - self.winfo_x()
        self.y = event.y_root - self.winfo_y()

    def stop_move(self, _):
        self.x = None
        self.y = None

    def do_move(self, event):
        if self.x is None or self.y is None:
            return
        x = event.x_root - self.x
        y = event.y_root - self.y
        win_w, win_h = self.winfo_width(), self.winfo_height()

        monitor = None
        for m in get_monitors():
            if m.x <= x <= m.x + m.width and m.y <= y <= m.y + m.height:
                monitor = m
                break
        if monitor is None:
            monitor = get_monitors()[0]

        # прилипание
        if x - monitor.x < self.MAGNET_THRESHOLD:
            x = monitor.x
        elif monitor.x + monitor.width - (x + win_w) < self.MAGNET_THRESHOLD:
            x = monitor.x + monitor.width - win_w

        if y - monitor.y < self.MAGNET_THRESHOLD:
            y = monitor.y
        elif monitor.y + monitor.height - (y + win_h) < self.MAGNET_THRESHOLD:
            y = monitor.y + monitor.height - win_h

        self.geometry(f"+{x}+{y}")

        # зеркальное перемещение второй таблицы
        if self.side == "left" and self.master.olenemer_window_2 and self.master.olenemer_window_2.winfo_exists():
            mirror_x = monitor.x + monitor.width - win_w - (x - monitor.x)
            self.master.olenemer_window_2.geometry(f"+{mirror_x}+{y}")
        elif self.side == "right" and self.master.olenemer_window and self.master.olenemer_window.winfo_exists():
            mirror_x = monitor.x + monitor.width - win_w - (x - monitor.x)
            self.master.olenemer_window.geometry(f"+{mirror_x}+{y}")

    def load_olenemer(self):
        lang = _settings.get_by_key('window')['lang']
        base_widths = {
            translations[lang]['nickname']: 220,
            translations[lang]['tank']: 130,
            translations[lang]['battles']: 60,
            translations[lang]['wins']: 60,
            translations[lang]['damage']: 50,
            translations[lang]['rating']: 60
        }

        if not self.master.olenemer_data:
            window_width = 580
            window_width -= (130 if not _settings.db['window'].get('show_col_tank', True) else 0)
            window_width -= (220 if not _settings.db['window'].get('show_col_nick', True) else 0)
            window_width -= (60 if not _settings.db['window'].get('show_col_rating', True) else 0)
            self.minsize(window_width, 10)
            # если нет данных — очистим окно и покажем сообщение
            for widget in self.root_layer.winfo_children():
                widget.destroy()
            self.show_loading_or_no_battle(lang)
            # сбрасываем кеш при отсутствии данных
            self._last_columns_state = None
            return

        team_key = "team_1" if self.side == "left" else "team_2"
        team_data = self.master.olenemer_data.get(team_key, [])

        # далее — очищаем окно и строим интерфейс заново
        for widget in self.root_layer.winfo_children():
            widget.destroy()

        # сохраняем новое состояние колонок
        data = self.prepare_table_data(team_data, lang)

        headers = data[0]
        rows = data[1:]

        # рассчитаем ширины колонок и минимальную ширину окна по видимым заголовкам
        col_widths = [base_widths.get(h, 60) for h in headers]
        table_width = max(sum(col_widths), 200)
        # обновим минимальный размер окна в зависимости от видимых столбцов
        try:
            self.minsize(table_width, 10)
        except Exception:
            pass

        # таблица без скроллбаров
        self.table = Sheet(
            self.root_layer,
            headers=None,
            show_header=False,
            data=rows + [headers],
            width=table_width,
            show_vertical_grid=False,
            show_horizontal_grid=False
        )

        # убираем индекс строк и все биндинги
        self.table.hide("row_index")
        self.table.hide("x_scrollbar")
        self.table.hide("y_scrollbar")
        self.table.disable_bindings()
        self.table.basic_bindings(False)

        # задаём фон и убираем вертикальные линии
        self.table.set_options(
            table_bg="#242424",
            header_bg="#242424",
            header_fg="white",
            font=("Jost", 10, "bold"),
        )

        # widths already рассчитаны выше в col_widths
        for i, w in enumerate(col_widths):
            try:
                self.table.column_width(i, width=w)
            except Exception:
                traceback.print_exc()

        # высота строк = 30
        for r in range(len(rows)):
            self.table.row_height(r, height=26)

        # подгоняем высоту окна под количество строк, ширина — рассчитанная выше
        table_height = min(len(rows) * 26 + 26, 1000)
        try:
            self.geometry(f"{table_width}x{table_height}+{self.winfo_x()}+{self.winfo_y()}")
        except Exception:
            # fallback to previous fixed size
            self.geometry(f"580x{table_height}+{self.winfo_x()}+{self.winfo_y()}")

        self.table.pack(expand=True, fill="both")

        self.after(50, lambda: self.apply_cell_alignment(headers, lang))
        self.after(100, lambda: self.apply_colors(data, lang))
        self.after(110, lambda: self.table.highlight_rows(rows = self.table.total_rows() - 1, fg = "white", redraw = True))

    def apply_cell_alignment(self, headers, lang):
        total_rows = self.table.get_total_rows()
        cols_to_center = []
        for key in ('battles', 'wins', 'damage', 'rating', ): # 'nickname', 'tank'
            h = translations[lang][key]
            if h in headers:
                try:
                    cols_to_center.append(headers.index(h))
                except Exception:
                    pass

        for col in cols_to_center:
            cells_to_align = [(r, col) for r in range(total_rows)]  # все строки в этом столбце
            self.table.align_cells(cells=cells_to_align, align="center")

    def show_loading_or_no_battle(self, lang):
        for widget in self.root_layer.winfo_children():
            widget.destroy()

        replay_path = _settings.db['replays_path']
        folders = [d for d in pathlib.Path(replay_path).iterdir() if d.is_dir() and d.name.endswith('.tbreplay')]
        if not folders:
            label = CTkLabel(self.root_layer, text=translations[lang]['no_battle'],
                             font=CTkFont(weight="bold", size=16), text_color="red")
        else:
            label = CTkLabel(self.root_layer, text=translations[lang]['data_loading'],
                             font=CTkFont(weight="bold", size=16), text_color="orange")
        label.pack(expand=True, pady=20)

    def prepare_table_data(self, team_data, lang):
        sorted_team = sorted(team_data, key=lambda p: (-int(p.get("tank_level", 0) if str(p.get("tank_level", "")).isdigit() else 0), p.get("tank_name", "").lower()))
        # build headers according to settings for visible columns
        win_settings = _settings.db['window']
        show_nick = win_settings.get('show_col_nick', True)
        show_tank = win_settings.get('show_col_tank', True)
        show_rating = win_settings.get('show_col_rating', True)

        headers = []
        if show_nick:
            headers.append(translations[lang]['nickname'])
        if show_tank:
            headers.append(translations[lang]['tank'])
        headers.append(translations[lang]['battles'])
        headers.append(translations[lang]['wins'])
        headers.append(translations[lang]['damage'])
        if show_rating:
            headers.append(translations[lang]['rating'])
        if self.side == "right":
            headers = headers[::-1]
        data = [headers]

        author_clan_tag = None
        author_nickname = self.master.olenemer_data.get("author_nickname", "")
        for player in sorted_team:
            if player.get("nickname") == author_nickname:
                author_clan_tag = player.get("clan_tag")
                break

        for player in sorted_team:
            battles = player.get("battles", 0)
            wins = player.get("wins", 0)
            winrate = f"{(wins / battles * 100):.2f}%" if battles else "0%"
            avg_damage = int(player.get("damage_dealt", 0) / battles) + 1 if battles else 0
            rating_display = "0" if not player['calibrated'] else ("<=3000" if player['rating'] <= 3000 else str(player['rating']))
            raw_nickname = player.get("nickname", "N/A")
            # сохранить оригинал для сравнения с автором
            original_nickname = raw_nickname
            # усечь ник до 16 символов и добавить '...' если длиннее
            if len(raw_nickname) > 16:
                display_nick = raw_nickname[:16] + "..."
            else:
                display_nick = raw_nickname

            # добавить тег клана, если есть
            clan_tag = player.get("clan_tag")
            if clan_tag:
                display_nick = f"[{clan_tag}] {display_nick}"

            player['_display_nick'] = display_nick
            player['_clan_tag'] = clan_tag
            player['_is_author'] = original_nickname == author_nickname
            player['_same_clan_as_author'] = clan_tag and clan_tag == author_clan_tag and original_nickname != author_nickname

            #platoon = player.get("platoon_index", 0)
            #if platoon:
            #    display_nick = f"[{platoon}]" + f" {display_nick}"
            if original_nickname == self.master.olenemer_data.get("author_nickname", ""):
                display_nick = "⭐ " + display_nick
            
            raw_tank_name = player.get("tank_name", "N/A")
            if len(raw_tank_name) > 16:
                tank_name = player.get("tank_name", "N/A")[:15] + "..."
            else:
                tank_name = raw_tank_name

            row = []
            if show_nick:
                row.append(display_nick)
            if show_tank:
                row.append(tank_name)
            row.extend([f"{battles:,}".replace(",", " "), winrate, avg_damage])
            if show_rating:
                row.append(rating_display)
            if self.side == "right":
                row = row[::-1]
            data.append(row)
        return data

    def apply_colors(self, data, lang):
        if not self.table:
            return
        headers = data[0]
        # compute indices for present headers, otherwise None
        def idx_for(key_name):
            h = translations[lang][key_name]
            return headers.index(h) if h in headers else None

        col_winrate = idx_for('wins')
        col_damage = idx_for('damage')
        col_rating = idx_for('rating')
        col_tank = idx_for('tank')
        col_names = idx_for('nickname')
        col_battles = idx_for('battles')

        team_key = "team_1" if self.side == "left" else "team_2"
        team_data = self.master.olenemer_data.get(team_key, [])
        sorted_team = sorted(team_data, key=lambda p: (-int(p.get("tank_level", 0) if str(p.get("tank_level", "")).isdigit() else 0), p.get("tank_name", "").lower()))

        for i, row in enumerate(data[1:], start=0):
            is_author_nick = False
            is_same_clan_nick = False
            
            if i < len(sorted_team):
                player_data = sorted_team[i]
                is_author_nick = player_data.get('_is_author', False)
                is_same_clan_nick = player_data.get('_same_clan_as_author', False)

            # safe extraction with defaults
            try:
                winrate = float(str(row[col_winrate]).replace('%', '').strip()) if col_winrate is not None else 0.0
            except Exception:
                winrate = 0.0
            try:
                damage = int(row[col_damage]) if col_damage is not None else 0
            except Exception:
                damage = 0
            try:
                rating_str = str(row[col_rating]).replace('<=', '').strip() if col_rating is not None else '0'
                rating = int(rating_str) if rating_str.isdigit() else 0
            except Exception:
                rating = 0

            # determine tank type only if tank column present
            tank_type = ''
            if col_tank is not None:
                try:
                    team_key = "team_1" if self.side == "left" else "team_2"
                    team_data = self.master.olenemer_data.get(team_key, [])
                    sorted_team = sorted(team_data, key=lambda p: (-int(p.get("tank_level", 0) if str(p.get("tank_level", "")).isdigit() else 0), p.get("tank_name", "").lower()))
                    player_data = sorted_team[i]
                    tank_id = player_data.get('tank_id', '')
                    tank_type = TANKS_INFO.get(str(tank_id), {}).get('type', '')
                except Exception:
                    tank_type = ''

            row_bg = self.get_color_tank_type(tank_type)

            # highlight cells only for columns that exist
            if col_names is not None:
                if is_author_nick:
                    # Желтый цвет для автора
                    self.table.highlight_cells(row=i, column=col_names, fg='yellow', bg=None)
                elif is_same_clan_nick:
                    # Зеленый цвет для одноклассников
                    self.table.highlight_cells(row=i, column=col_names, fg='#00FF00', bg=None)
                else:
                    self.table.highlight_cells(row=i, column=col_names, fg='white', bg=None)
                    self.table.highlight_cells(row=i, column=col_names, fg='white', bg=None)
            if col_battles is not None:
                self.table.highlight_cells(row=i, column=col_battles, fg='white', bg=None)
            if col_tank is not None:
                self.table.highlight_cells(row=i, column=col_tank, fg=row_bg, bg=None)
            if col_winrate is not None:
                self.table.highlight_cells(row=i, column=col_winrate, fg=self.get_color_winrate(winrate), bg=None)
            if col_damage is not None:
                self.table.highlight_cells(row=i, column=col_damage, fg=self.get_color_damage(damage), bg=None)
            if col_rating is not None:
                self.table.highlight_cells(row=i, column=col_rating, fg=self.get_color_rating(rating), bg=None)

    # ---- цветовые функции ----
    def get_color_winrate(self, number) -> str:
        if number < 50: return "#fffffd"
        elif number < 60: return "#b9e497"
        elif number < 70: return "#9ec3cf"
        else: return "#ac9eee"

    def get_color_rating(self, number) -> str:
        if number < 3000: return "#fffffd"
        if number < 4000: return "#c4b453"
        elif number < 5000: return "#83c1ca"
        else: return "#b236b8"

    def get_color_damage(self, number) -> str:
        if number < 2000: return "#fffffd"
        elif number < 2500: return "#b9e497"
        elif number < 3000: return "#9ec3cf"
        else: return "#ac9eee"

    def get_color_tank_type(self, type_str) -> str:
        if type_str in ("ЛТ", "СТ"): return "#BFE08B"
        elif type_str == "ТТ": return "#E68E6F"
        elif type_str == "ПТ": return "#6678db"
        else: return "#ffffff"

import os
import json
from customtkinter import (
    CTkToplevel, 
    CTkLabel, 
    CTkScrollableFrame, 
    CTkFont, 
    CTkButton
)
from CTkTable import CTkTable
from settings.settings import _settings
from datetime import datetime
from lib.utils.resources import resource_path
from ui.tank_sessions_window import TankSessionsWindow

# Загрузка данных о танках из файла tanks_id.json
base_dir = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/').replace('ui', '')
tanks_file_path = resource_path('tanks_names.json')

with open(tanks_file_path, 'r', encoding='utf-8-sig') as f:
    TANKS_DICT = json.load(f)

translations = {
    'en': {
        'last_sessions': "Last Sessions",
        'date': "Start date\nEnd date",
        'level': "Average\nlevel",
        'battles': "Battles",
        'wins': "Winrate",
        'damage': "Damage",
        'xp': "XP",
        'accuracy': "Accuracy",
        'no_sessions': "No sessions available",
        'tank_session': "Tanks\nsession",
        'delete': "Delete\nsession"
    },
    'ru': {
        'last_sessions': "Последние сессии",
        'date': "Начало\nКонец",
        'level': "Средний\nуровень",
        'battles': "Бои",
        'wins': "Винрейт",
        'damage': "Урон",
        'xp': "Опыт",
        'accuracy': "Точность",
        'no_sessions': "Сессий нет",
        'tank_session': "Сессия\nпо танкам",
        'delete': "Удалить\nсессию"
    }
}

class SessionsWindow(CTkToplevel):
    def __init__(self, master, x: int = 0, y: int = 0, **kwargs):
        super().__init__(master, **kwargs)
        self.minsize(1500, 400)
        self.title(translations[_settings.get_by_key('window')['lang']]['last_sessions'])
        self.after(250, lambda: self.iconbitmap(resource_path('assets/ui/app_logo.ico')))
        self.root_layer = CTkScrollableFrame(self)
        self.root_layer.pack(fill="both", expand=True)

        if x != 0 or y != 0:
            self.geometry(f"+{x}+{y}")

        self.tank_sessions_windows = {}

        self.load_sessions()

    def load_sessions(self):
        for widget in self.root_layer.winfo_children():
            widget.destroy()

        sessions = _settings.db['sessions'][::-1]
        lang = _settings.get_by_key('window')['lang']

        if not sessions:
            no_sessions_label = CTkLabel(
                self.root_layer, 
                text=translations[lang]['no_sessions'], 
                font=CTkFont(weight="bold", size=16),
                text_color="red"
            )
            no_sessions_label.pack(pady=20)
            return

        headers = [
            translations[lang]['date'],
            translations[lang]['level'],
            translations[lang]['battles'],
            translations[lang]['wins'],
            translations[lang]['accuracy'],
            translations[lang]['damage'],
            translations[lang]['xp'],
            translations[lang]['tank_session'],
            translations[lang]['delete']
        ]

        data = []
        data.append(headers)
        
        for session in sessions:
            session: dict
            average_level: float = 0
            total_average_level_counter: int = 0
            total_level_counter: int = 0
            start_time = session.get('start_time', 'N/A')
            end_time = session.get('date', 'N/A')
            
            if start_time != 'N/A':
                start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S").strftime('%d.%m.%Y %H:%M:%S')
            if end_time != 'N/A':
                end_time = datetime.strptime(session['date'], "%Y-%m-%d %H:%M:%S").strftime('%d.%m.%Y %H:%M:%S')
            
            for tank_id in list(session['tank_sessions'].keys()):
                if tank_id in TANKS_DICT:
                    total_average_level_counter += int(TANKS_DICT[tank_id]['level'])
                    total_level_counter += 1
            average_level = total_average_level_counter / total_level_counter if total_level_counter > 0 else 0

            row = [
                f"{start_time}\n{end_time}",
                f"{average_level:.2f}",
                session.get('battles', 'N/A'),
                session.get('winrate', 'N/A'),
                session.get('accuracy', 'N/A'),
                session.get('damage', 'N/A'),
                session.get('xp', 'N/A'),
                translations[lang]['tank_session'],
                translations[lang]['delete']
            ]
            data.append(row)

        self.table = CTkTable(self.root_layer, values=data, font=CTkFont(size=16, family=_settings.get_by_key('font')['static_text']))
        self.table.edit_row(0, font=CTkFont(size=20, weight="bold", family=_settings.get_by_key('font')['static_text']))
        self.table.pack(fill="both", expand=True, padx=20, pady=20)

        for i in range(1, len(data)):
            winrate = float(data[i][3].replace('%', '').strip())
            accuracy = float(data[i][4].replace('%', '').strip())
            damage = int(data[i][5])
            self.table.edit(i, 3, text_color=self.get_color_winrate(winrate))
            self.table.edit(i, 4, text_color=self.get_color_accuracy(accuracy))
            self.table.edit(i, 5, text_color=self.get_color_damage(damage))
            self.table.edit(i, 7, text_color="#ffff00", command=lambda row=i: self.open_tank_sessions(self.table.get(row, 0).split('\n')[0]))
            self.table.edit(i, 8, text_color="#ff3d00", command=lambda row=i: self.delete_session({"row": row}))

    def get_color_winrate(self, number) -> str:
        if number < 50:
            return "#fffffd"
        elif number < 60:
            return "#b9e497"
        elif number < 70:
            return "#9ec3cf"
        else:
            return "#ac9eee"
    
    def get_color_accuracy(self, number) -> str:
        if number < 85:
            return "#fffffd"
        elif number < 90:
            return "#b9e497"
        elif number < 95:
            return "#9ec3cf"
        else:
            return "#ac9eee"

    def get_color_damage(self, number) -> str:
        if number < 2000:
            return "#fffffd"
        elif number < 2500:
            return "#b9e497"
        elif number < 3000:
            return "#9ec3cf"
        else:
            return "#ac9eee"

    def delete_session(self, data):
        row_index = data["row"]
        session_date = self.table.get(row_index, 0).split('\n')[0]
        _settings.db['sessions'] = [s for s in _settings.db['sessions'] if 'start_time' in s if datetime.strptime(s['start_time'], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M:%S") != session_date]
        _settings.db.commit()
        self.load_sessions()

    def open_tank_sessions(self, session_date):
        if session_date not in self.tank_sessions_windows or not self.tank_sessions_windows[session_date].winfo_exists():
            self.tank_sessions_windows[session_date] = TankSessionsWindow(self, session_date)
        self.grab_release()
        self.tank_sessions_windows[session_date].grab_set()
        self.tank_sessions_windows[session_date].focus()
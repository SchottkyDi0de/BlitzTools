from customtkinter import (
    CTkToplevel, 
    CTkLabel, 
    CTkScrollableFrame, 
    CTkFont
)
from CTkTable import CTkTable
from settings.settings import _settings
from datetime import datetime
from lib.utils.resources import resource_path
import json
import os

# Загрузка данных о танках из файла tanks_id.json
base_dir = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/').replace('ui', '')
tanks_file_path = resource_path('tanks_names.json')

with open(tanks_file_path, 'r', encoding='utf-8-sig') as f:
    TANKS_DICT = json.load(f)

translations = {
    'en': {
        'tank_sessions': "Tank Sessions",
        'level': "Level",
        'tank': "Tank",
        'battles': "Battles",
        'wins': "Winrate",
        'damage': "Damage",
        'xp': "XP",
        'accuracy': "Accuracy",
        'no_sessions': "No sessions available"
    },
    'ru': {
        'tank_sessions': "Сессии по танкам",
        'level': "Уровень",
        'tank': "Танк",
        'battles': "Бои",
        'wins': "Винрейт",
        'damage': "Урон",
        'xp': "Опыт",
        'accuracy': "Точность",
        'no_sessions': "Сессий нет"
    }
}

class TankSessionsWindow(CTkToplevel):
    def __init__(self, master, session_date, x: int = 0, y: int = 0, **kwargs):
        super().__init__(master, **kwargs)
        self.minsize(1200, 400)
        self.title(translations[_settings.get_by_key('window')['lang']]['tank_sessions'])
        self.after(250, lambda: self.iconbitmap(resource_path('assets/ui/app_logo.ico')))
        self.root_layer = CTkScrollableFrame(self)
        self.root_layer.pack(fill="both", expand=True)

        if x != 0 or y != 0:
            self.geometry(f"+{x}+{y}")

        self.load_tank_sessions(session_date)

    def load_tank_sessions(self, session_date):
        for widget in self.root_layer.winfo_children():
            widget.destroy()

        sessions = _settings.db['sessions']
        lang = _settings.get_by_key('window')['lang']

        session = next((s for s in sessions if datetime.strptime(s['start_time'], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M:%S") == session_date), None)
        if not session or 'tank_sessions' not in session:
            no_sessions_label = CTkLabel(
                self.root_layer, 
                text=translations[lang]['no_sessions'], 
                font=CTkFont(weight="bold", size=16),
                text_color="black"
            )
            no_sessions_label.pack(pady=20)
            return

        headers = [
            translations[lang]['level'],
            translations[lang]['tank'],
            translations[lang]['battles'],
            translations[lang]['wins'],
            translations[lang]['accuracy'],
            translations[lang]['damage'],
            translations[lang]['xp']
        ]

        data = []
        data.append(headers)
        
        tank_sessions = session['tank_sessions']
        for tank_id, stats in tank_sessions.items():
            tank_info = TANKS_DICT.get(tank_id, {'name': tank_id, 'level': '0'})
            row = [
                tank_info['level'],
                tank_info['name'],
                stats['battles'],
                stats['wr'],
                stats['ac'],
                stats['avg_dmg'],
                stats['avg_xp']
            ]
            data.append(row)

        data[1:] = sorted(data[1:], key=lambda x: int(x[0]), reverse=True)  # Сортировка по уровню танка

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

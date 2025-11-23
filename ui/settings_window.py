from typing import TYPE_CHECKING
from tkinter import font, BooleanVar
from CTkColorPicker import AskColor

from customtkinter import (
    CTkToplevel,
    CTkFrame,
    CTkLabel,
    CTkEntry,
    CTkImage,
    StringVar,
    CTkButton,
    filedialog,
    CTkComboBox,
    CTkScrollableFrame,
    CTkSwitch,
    CTkSlider,
    CTkCheckBox,
    CTkFont
)
from PIL import Image

from lib.utils.resources import resource_path
from settings.settings import _settings

if TYPE_CHECKING:
    from main import App

import colorsys

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb_color):
    return '#{:02x}{:02x}{:02x}'.format(*rgb_color)

def desaturate_color(hex_color, factor=0.5):
    rgb_color = hex_to_rgb(hex_color)
    
    h, l, s = colorsys.rgb_to_hls(*[x/255.0 for x in rgb_color])
    
    s *= factor
    
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    
    return rgb_to_hex((int(r*255), int(g*255), int(b*255)))

def adjust_brightness(hex_color, factor=1.0):
    rgb_color = hex_to_rgb(hex_color)
    
    h, l, s = colorsys.rgb_to_hls(*[x/255.0 for x in rgb_color])
    
    l = max(0, min(1, l * factor))
    
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    
    return rgb_to_hex((int(r*255), int(g*255), int(b*255)))

translations = {
    'en': {
        'settings': "Settings",
        'current_folder': "Current folder",
        'choose_folder': "Choose replays folder",
        'edit_color': "Edit Primary Color",
        'switch_lang': "Switch to Russian",
        'static_font_size': "Static text font size",
        'dynamic_font_size': "Dynamic text font size",
        'static_font': "Static font",
        'dynamic_font': "Dynamic font",
        'transparency': "Transparency",
        'premium_account': "Premium account?",
        'count_xp': "Count XP without multi?",
        'enabled': "Enabled",
        'disabled': "Disabled",
        'yes': "Yes",
        'no': "No",
        'battles_label': "Battles label text",
        'winrate_label': "Winrate label text",
        'accuracy_label': "Accuracy label text",
        'avg_damage_label': "Average damage label text",
        'avg_xp_label': "Average XP label text",
        'region': "Region",
        'wargaming': "Wargaming",
        'lesta': "Lesta",
        'nickname': "Nickname",
        'tank': "Tank",
        'rating': "Rating",
        'olenemer_chekmarks': "Olenemer columns toggles",
        'auto_open_olenemer': "Auto-open Olenemer windows"
    },
    'ru': {
        'settings': "Настройки",
        'current_folder': "Текущая папка",
        'choose_folder': "Выбрать папку с реплеями",
        'edit_color': "Изменить основной цвет",
        'switch_lang': "Переключить на английский",
        'static_font_size': "Размер шрифта постоянного текста",
        'dynamic_font_size': "Размер шрифта динамического текста",
        'static_font': "Шрифт постоянного текста",
        'dynamic_font': "Шрифт динамического текста",
        'transparency': "Прозрачность окна",
        'premium_account': "Премиум аккаунт?",
        'count_xp': "Считать опыт без множителей?",
        'enabled': "Включено",
        'disabled': "Отключено",
        'yes': "Да",
        'no': "Нет",
        'battles_label': "Текст заголовка боёв",
        'winrate_label': "Текст заголовка винрейта",
        'accuracy_label': "Текст заголовка точности",
        'avg_damage_label': "Текст заголовка среднего урона",
        'avg_xp_label': "Текст заголовка среднего опыта",
        'region': "Регион",
        'wargaming': "Wargaming",
        'lesta': "Lesta",
        'nickname': "Ник",
        'tank': "Танк",
        'rating': "Рейтинг",
        'olenemer_chekmarks': "Переключение столбцов оленемера",
        'auto_open_olenemer': "Авто-открытие окон оленемера"
    }
}

class SettingsWindow(CTkToplevel):
    def __init__(self, master: 'App', x: int = 0, y: int = 0, **kwargs):
        super().__init__(master, **kwargs)
        self.minsize(400, 800)
        self.after(250, lambda: self.iconbitmap(resource_path('assets/ui/app_logo.ico')))
        self.title(translations[_settings.get_by_key('window')['lang']]['settings'])
        self.root_layer = CTkScrollableFrame(self)
        self.root_layer.pack(fill="both", expand=True)
        
        
        if x != 0 or y != 0:
            self.geometry(f"+{x}+{y}")
        

        self.folder_frame = CTkFrame(self.root_layer)
        self.folder_frame.pack(side="top", expand=True, fill="both")

        self.region_frame = CTkFrame(self.root_layer)
        self.region_frame.pack(side="top", expand=True, fill="both")

        self.region_label = CTkLabel(
            self.region_frame,
            text=translations[_settings.get_by_key('window')['lang']]['region'],
            font=CTkFont(weight="bold", size=16)
        )
        self.region_label.pack(side="top")

        self.region_input_field = CTkComboBox(
            self.region_frame,
            values=[translations[_settings.get_by_key('window')['lang']]['wargaming'], translations[_settings.get_by_key('window')['lang']]['lesta']],
            command=self.set_region
        )
        self.region_input_field.pack(side="top", pady=(0, 15))
        self.region_input_field.set("Lesta" if _settings.db['window']['region'] == "ru" else "Wargaming")

        self.curr_folder_label = CTkLabel(
            self.folder_frame,
            text=f"{translations[_settings.get_by_key('window')['lang']]['current_folder']}: {_settings.get_by_key('replays_path')}",
            wraplength=280,
            font=CTkFont(weight="bold", size=16)
        )
        self.curr_folder_label.pack(side="top")


        self.choose_folder_btn = CTkButton(
            self.folder_frame,
            text=translations[_settings.get_by_key('window')['lang']]['choose_folder'],
            command=self.choose_folder,
            fg_color=_settings.db['window']['primary_color'],
            hover_color=adjust_brightness(desaturate_color(_settings.db['window']['primary_color'], factor=0.5), factor=0.8)
        )
        self.choose_folder_btn.pack(side='top', pady=(0, 15))


        self.color_picker_button = CTkButton(
            self.folder_frame,
            text=translations[_settings.get_by_key('window')['lang']]['edit_color'],
            command=self.choose_color,
            fg_color=_settings.db['window']['primary_color'],
            hover_color=adjust_brightness(desaturate_color(_settings.db['window']['primary_color'], factor=0.5), factor=0.8)
        )
        self.color_picker_button.pack(side="top", pady=(0, 15))


        self.language_btn = CTkButton(
            self.folder_frame,
            text=translations[_settings.get_by_key('window')['lang']]['switch_lang'],
            command=self.switch_language,
            fg_color=_settings.db['window']['primary_color'],
            hover_color=adjust_brightness(desaturate_color(_settings.db['window']['primary_color'], factor=0.5), factor=0.8)
        )
        self.language_btn.pack(side='top', pady=(0, 15))


        self.font_settings_frame = CTkFrame(self.root_layer)
        self.font_settings_frame.pack(side="top", expand=True, fill="both")

        self.static_font_label = CTkLabel(
            self.font_settings_frame,
            text=translations[_settings.get_by_key('window')['lang']]['static_font'],
            font=CTkFont(weight="bold", size=16)
        )
        self.static_font_label.pack(side="top")


        fonts = ['Arial', 'Calibri', 'Cambria', 'Candara', 'Comic Sans MS', 'Consolas', 'Courier New', 'Ebrima', 'Franklin Gothic Medium', 'Georgia', 'Impact', 'Ink Free', 'Javanese Text', 'Leelawadee UI', 'Lucida Console', 'Lucida Sans Unicode', 'Malgun Gothic', 'Microsoft Sans Serif', 'Nirmala UI', 'Palatino Linotype', 'Segoe UI', 'Segoe UI Black', 'Segoe UI Light', 'Segoe UI Semibold', 'Segoe UI Semilight', 'Tahoma', 'Times New Roman', 'Trebuchet MS', 'Verdana', 'Yu Gothic']


        self.static_font_input_field = CTkComboBox(
            self.font_settings_frame,
            values=fonts,
            command=self.set_static_font
        )
        self.static_font_input_field.pack(side="top", pady=(0, 15))


        self.dynamic_font_label = CTkLabel(
            self.font_settings_frame,
            text=translations[_settings.get_by_key('window')['lang']]['dynamic_font'],
            font=CTkFont(weight="bold", size=16)
        )
        self.dynamic_font_label.pack(side="top")


        self.dynamic_font_input_field = CTkComboBox(
            self.font_settings_frame,
            values=fonts,
            command=self.set_dynamic_font
        )
        self.dynamic_font_input_field.pack(side="top", pady=(0, 15))


        self.font_size_settings_frame = CTkFrame(self.root_layer)
        self.font_size_settings_frame.pack(side="top", expand=True, fill="both")


        self.dynamic_font_size_label = CTkLabel(
            self.font_size_settings_frame,
            text=translations[_settings.get_by_key('window')['lang']]['dynamic_font_size'],
            font=CTkFont(weight="bold", size=16)
        )
        self.dynamic_font_size_label.pack(side="top")


        self.dynamic_font_size_input_field = CTkComboBox(
            self.font_size_settings_frame,
            values=['12', '14', '16', '18', '20', '22', '24', '26', '28'],
            command=self.set_dynamic_font_size
        )
        self.dynamic_font_size_input_field.pack(side="top", pady=(0, 15))
        self.dynamic_font_size_input_field.set(_settings.db['font']['dynamic_text_size'])


        self.static_font_size_label = CTkLabel(
            self.font_size_settings_frame,
            text=translations[_settings.get_by_key('window')['lang']]['static_font_size'],
            font=CTkFont(weight="bold", size=16)
        )
        self.static_font_size_label.pack(side="top")


        self.static_font_size_input_field = CTkComboBox(
            self.font_size_settings_frame,
            values=['12', '14', '16', '18', '20', '22', '24', '26', '28'],
            command=self.set_static_font_size
        )
        self.static_font_size_input_field.pack(side="top", pady=(0, 15))
        self.static_font_size_input_field.set(_settings.db['font']['static_text_size'])


        self.switch_settings_frame = CTkFrame(self.root_layer)
        self.switch_settings_frame.pack(side="top", expand=True, fill="both")


        self.transparency_label = CTkLabel(
            self.switch_settings_frame,
            text=translations[_settings.get_by_key('window')['lang']]['transparency'],
            font=CTkFont(weight="bold", size=16)
        )
        self.transparency_label.pack(side="top")

        # slider for transparency (0..100 percent)
        initial_transp = _settings.db['window'].get('transparency', None)
        if initial_transp is None:
            # fallback to legacy float or bool
            legacy_float = _settings.db['window'].get('transparency', 0.8)
            try:
                initial_percent = int(float(legacy_float) * 100)
            except Exception:
                legacy_bool = _settings.db['window'].get('transparent', False)
                initial_percent = 80 if legacy_bool else 100
        else:
            initial_percent = int(initial_transp)

        self.transparency_slider = CTkSlider(
            self.switch_settings_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.update_transparency_value,
            progress_color=_settings.db['window']['primary_color'],
            button_color = adjust_brightness(desaturate_color(_settings.db['window']['primary_color'], factor=0.5), factor=0.8),
            button_hover_color = adjust_brightness(desaturate_color(_settings.db['window']['primary_color'], factor=0.5), factor=0.8)
        )
        self.transparency_slider.set(initial_percent)
        self.transparency_slider.pack(side="top", pady=(0, 5), fill='x', padx=10)

        self.transparency_value_label = CTkLabel(self.switch_settings_frame, text=f"{int(initial_percent)}%")
        self.transparency_value_label.pack(side="top", pady=(0, 10))

        # Columns visibility checkboxes
        self.columns_frame = CTkFrame(self.root_layer)
        self.columns_frame.pack(side="top", expand=True, fill="both", pady=(10,0))

        self.columns_label = CTkLabel(
            self.columns_frame,
            text=translations[_settings.get_by_key('window')['lang']]['olenemer_chekmarks'],
            font=CTkFont(weight="bold", size=16)
        )
        self.columns_label.pack(side="top")

        self.col_nick_var = BooleanVar(value=_settings.db['window'].get('show_col_nick', True))
        self.col_tank_var = BooleanVar(value=_settings.db['window'].get('show_col_tank', True))
        self.col_rating_var = BooleanVar(value=_settings.db['window'].get('show_col_rating', True))

        self.col_nick_cb = CTkCheckBox(
            self.columns_frame,
            text=translations[_settings.get_by_key('window')['lang']]['nickname'],
            variable=self.col_nick_var,
            command=self.update_columns_settings,
            fg_color = _settings.db['window']['primary_color'],
            hover_color = adjust_brightness(desaturate_color(_settings.db['window']['primary_color'], factor=0.5), factor=0.8)
        )
        self.col_tank_cb = CTkCheckBox(
            self.columns_frame,
            text=translations[_settings.get_by_key('window')['lang']]['tank'],
            variable=self.col_tank_var,
            command=self.update_columns_settings,
            fg_color = _settings.db['window']['primary_color'],
            hover_color = adjust_brightness(desaturate_color(_settings.db['window']['primary_color'], factor=0.5), factor=0.8)
        )
        self.col_rating_cb = CTkCheckBox(
            self.columns_frame,
            text=translations[_settings.get_by_key('window')['lang']]['rating'],
            variable=self.col_rating_var,
            command=self.update_columns_settings,
            fg_color = _settings.db['window']['primary_color'],
            hover_color = adjust_brightness(desaturate_color(_settings.db['window']['primary_color'], factor=0.5), factor=0.8)
        )

        self.col_nick_cb.pack(side="top", pady=(0, 15))
        self.col_tank_cb.pack(side="top", pady=(0, 15))
        self.col_rating_cb.pack(side="top", pady=(0, 15))


        self.premium_acc_label = CTkLabel(
            self.switch_settings_frame,
            text=translations[_settings.get_by_key('window')['lang']]['premium_account'],
            font=CTkFont(weight="bold", size=16)
        )
        self.premium_acc_label.pack(side="top")


        self.premium_acc_switch = CTkSwitch(
            self.switch_settings_frame,
            text="No" if _settings.get_by_key('window')['lang'] == 'en' else "Нет",
            command=self.update_premium_text,
            progress_color=_settings.db['window']['primary_color']
        )
        if _settings.db['font']['premium']:
            self.premium_acc_switch.toggle()
        self.premium_acc_switch.pack(side="top", pady=(0, 15))


        self.base_xp_only_label = CTkLabel(
            self.switch_settings_frame,
            text=translations[_settings.get_by_key('window')['lang']]['count_xp'],
            font=CTkFont(weight="bold", size=16)
        )
        self.base_xp_only_label.pack(side="top")


        self.base_xp_only_switch = CTkSwitch(
            self.switch_settings_frame,
            text="No" if _settings.get_by_key('window')['lang'] == 'en' else "Нет",
            command=self.update_base_xp_only_text,
            progress_color=_settings.db['window']['primary_color']
        )
        if (_settings.db['font']['base_xp_only']):
            self.base_xp_only_switch.toggle()
        self.base_xp_only_switch.pack(side="top", pady=(0, 15))


        # Auto-open Olenemer windows switch
        self.auto_open_label = CTkLabel(
            self.switch_settings_frame,
            text=translations[_settings.get_by_key('window')['lang']]['auto_open_olenemer'],
            font=CTkFont(weight="bold", size=16)
        )
        self.auto_open_label.pack(side="top")

        self.auto_open_switch = CTkSwitch(
            self.switch_settings_frame,
            text="Disabled" if _settings.get_by_key('window')['lang'] == 'en' else "Отключено",
            command=self.update_auto_open_text,
            progress_color=_settings.db['window']['primary_color']
        )
        if _settings.db['window'].get('auto_open_olenemer', True):
            self.auto_open_switch.toggle()
        self.auto_open_switch.pack(side="top", pady=(0, 15))


        self.dynamic_font_input_field.set(_settings.db['font']['dynamic_text'])
        self.static_font_input_field.set(_settings.db['font']['static_text'])


        self.text_settings_frame = CTkFrame(self.root_layer)
        self.text_settings_frame.pack(side="top", expand=True, fill="both")


        self.btls_label_text = CTkLabel(
            self.text_settings_frame,
            text=translations[_settings.get_by_key('window')['lang']]['battles_label'],
            font=CTkFont(weight="bold", size=16)
        )
        self.btls_label_text.pack(side="top")


        self.btls_label_val = StringVar(self, value='')
        self.btls_input_field = CTkEntry(
            self.text_settings_frame,
            textvariable=self.btls_label_val
        )
        self.btls_input_field.pack(side="top", pady=(0, 15))
        self.btls_input_field.insert(0, _settings.db['font']['battles_label'])


        self.wr_label_text = CTkLabel(
            self.text_settings_frame,
            text=translations[_settings.get_by_key('window')['lang']]['winrate_label'],
            font=CTkFont(weight="bold", size=16)
        )
        self.wr_label_text.pack(side="top")


        self.wr_label_val = StringVar(self, value='')
        self.wr_input_field = CTkEntry(
            self.text_settings_frame,
            textvariable=self.wr_label_val
        )
        self.wr_input_field.pack(side="top", pady=(0, 15))
        self.wr_input_field.insert(0, _settings.db['font']['winrate_label'])


        self.ac_label_text = CTkLabel(
            self.text_settings_frame,
            text=translations[_settings.get_by_key('window')['lang']]['accuracy_label'],
            font=CTkFont(weight="bold", size=16)
        )
        self.ac_label_text.pack(side="top")


        self.ac_label_val = StringVar(self, value='')
        self.ac_input_field = CTkEntry(
            self.text_settings_frame,
            textvariable=self.ac_label_val
        )
        self.ac_input_field.pack(side="top", pady=(0, 15))
        self.ac_input_field.insert(0, _settings.db['font']['accuracy_label'])


        self.avg_dmg_label_text = CTkLabel(
            self.text_settings_frame,
            text=translations[_settings.get_by_key('window')['lang']]['avg_damage_label'],
            font=CTkFont(weight="bold", size=16)
        )
        self.avg_dmg_label_text.pack(side="top")


        self.avg_dmg_label_val = StringVar(self, value='')
        self.avg_dmg_input_field = CTkEntry(
            self.text_settings_frame,
            textvariable=self.avg_dmg_label_val
        )
        self.avg_dmg_input_field.pack(side="top", pady=(0, 15))
        self.avg_dmg_input_field.insert(0, _settings.db['font']['avg_damage_label'])


        self.avg_xp_label_text = CTkLabel(
            self.text_settings_frame,
            text=translations[_settings.get_by_key('window')['lang']]['avg_xp_label'],
            font=CTkFont(weight="bold", size=16)
        )
        self.avg_xp_label_text.pack(side="top")


        self.avg_xp_label_val = StringVar(self, value='')
        self.avg_xp_input_field = CTkEntry(
            self.text_settings_frame,
            textvariable=self.avg_xp_label_val
        )
        self.avg_xp_input_field.pack(side="top", pady=(0, 15))
        self.avg_xp_input_field.insert(0, _settings.db['font']['avg_xp_label'])


        self.save_btn = CTkButton(
            self.root_layer,
            text='',
            image=CTkImage(Image.open(resource_path("assets/ui/save_btn.png"))),
            width=28,
            command=self.save_settings,
            fg_color=_settings.db['window']['primary_color'],
            hover_color=adjust_brightness(desaturate_color(_settings.db['window']['primary_color'], factor=0.5), factor=0.8)
        )
        self.save_btn.pack(side='bottom', anchor='se')

    def set_region(self, value: str):
        _settings.db['window']['region'] = value

    def choose_folder(self):
        path = filedialog.askdirectory(initialdir = _settings.db['replays_path'])
        
        if path != '':
            self.curr_folder_label.configure(text=f"{translations[_settings.get_by_key('window')['lang']]['current_folder']}: {path}")
            
    def set_static_font(self, value: str):
        _settings.db['font']['static_text'] = value
        
    def set_dynamic_font(self, value: str):
        _settings.db['font']['dynamic_text'] = value
        
    def set_static_font_size(self, value: str):
        _settings.db['font']['static_text_size'] = int(value)
        
    def set_dynamic_font_size(self, value: str):
        _settings.db['font']['dynamic_text_size'] = int(value)
        
    # Removed toggle_transparency which used legacy switch widget
        
    def update_switch_text(self, switch: CTkSwitch, en_text, ru_text):
        switch.configure(text=translations[_settings.get_by_key('window')['lang']][en_text[0]] if switch.get() else translations[_settings.get_by_key('window')['lang']][en_text[1]])

    def update_premium_text(self):
        self.update_switch_text(self.premium_acc_switch, ("yes", "no"), ("yes", "no"))

    def update_base_xp_only_text(self):
        self.update_switch_text(self.base_xp_only_switch, ("yes", "no"), ("yes", "no"))

    def update_auto_open_text(self):
        # use enabled/disabled labels for the auto-open switch
        self.update_switch_text(self.auto_open_switch, ("enabled", "disabled"), ("enabled", "disabled"))

    def choose_color(self):
        pick_color = AskColor(title=translations[_settings.get_by_key('window')['lang']]['edit_color'])
        color = pick_color.get()
        if color:
            desaturated_color = desaturate_color(color, factor=0.5)
            darker_color = adjust_brightness(desaturated_color, factor=0.8)

            self.color_picker_button.configure(fg_color=color, hover_color=darker_color)
            self.choose_folder_btn.configure(fg_color=color, hover_color=darker_color)
            self.save_btn.configure(fg_color=color, hover_color=darker_color)
            self.premium_acc_switch.configure(progress_color=color)
            self.base_xp_only_switch.configure(progress_color=color)
            try:
                self.auto_open_switch.configure(progress_color=color)
            except Exception:
                pass
            self.language_btn.configure(fg_color=color, hover_color=darker_color)
            self.transparency_slider.configure(progress_color=color, button_color=darker_color, button_hover_color=darker_color)
            self.col_nick_cb.configure(fg_color=color, hover_color=darker_color)
            self.col_tank_cb.configure(fg_color=color, hover_color=darker_color)
            self.col_rating_cb.configure(fg_color=color, hover_color=darker_color)

    def switch_language(self):
        current_lang = _settings.get_by_key('window')['lang']
        new_lang = 'ru' if current_lang == 'en' else 'en'
        _settings.db['window']['lang'] = new_lang
        _settings.db.commit()
        
        x, y = self.winfo_x(), self.winfo_y()
        
        self.destroy()
        
        SettingsWindow(self.master, x, y)

        # handler for transparency slider
    def update_transparency_value(self, v):
        try:
            val = float(v)
        except Exception:
            return
        # show percent
        try:
            # slider now gives percent directly
            self.transparency_value_label.configure(text=f"{int(val)}%")
        except Exception:
            pass
        # save to settings
        try:
            _settings.db['window']['transparency'] = int(val)
        except Exception:
            _settings.db['window']['transparency'] = 100
        _settings.db.commit()

    def update_columns_settings(self):
        _settings.db['window']['show_col_nick'] = bool(self.col_nick_var.get())
        _settings.db['window']['show_col_tank'] = bool(self.col_tank_var.get())
        _settings.db['window']['show_col_rating'] = bool(self.col_rating_var.get())
        _settings.db.commit()


    def save_settings(self):
        if _settings.db['replays_path'] != self.curr_folder_label.cget('text').split(': ')[1]:
            _settings.db['replays_path'] = self.curr_folder_label.cget('text').split(': ')[1]
            self.master.rerun_watcher()
        _settings.db['font']['battles_label'] = self.btls_input_field.get()
        _settings.db['font']['winrate_label'] = self.wr_input_field.get()
        _settings.db['font']['accuracy_label'] = self.ac_input_field.get()
        _settings.db['font']['avg_damage_label'] = self.avg_dmg_input_field.get()
        _settings.db['font']['avg_xp_label'] = self.avg_xp_input_field.get()
        # save transparency as integer percent
        try:
            _settings.db['window']['transparency'] = int(self.transparency_slider.get())
        except Exception:
            pass
        _settings.db['font']['premium'] = self.premium_acc_switch.get()
        _settings.db['font']['base_xp_only'] = self.base_xp_only_switch.get()
        # save auto-open olenemer setting
        try:
            _settings.db['window']['auto_open_olenemer'] = bool(self.auto_open_switch.get())
        except Exception:
            # if switch missing for some reason, default to True
            _settings.db['window']['auto_open_olenemer'] = _settings.db['window'].get('auto_open_olenemer', True)
        _settings.db['window']['primary_color'] = self.color_picker_button.cget('fg_color')
        _settings.db['window']['region'] = "ru" if self.region_input_field.get() == translations[_settings.get_by_key('window')['lang']]['lesta'] else "eu"
        _settings.db.commit()
        
        self.master: 'App'
        self.master.update_all_widgets()
        self.destroy()
        #print('Core: Settings saved')
        #print('UI: Settings window closed')
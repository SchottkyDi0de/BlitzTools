import elara
import os
from pathlib import Path

from lib.data_classes.config_struct import ConfigStruct

_documents = Path(os.path.expanduser('~')).joinpath('Documents')
_tbpath = _documents / "TanksBlitz" / "replays"
_path = _tbpath if _tbpath.exists() else _documents

_default_settings = {
    "replays_path": str(_path),
    "window": {
        "size_x": 200,
        "size_y": 100,
        "transparency": 80,
        "primary_color": "#9D89E6",
        "lang": "ru",
        "position": {"x": 0, "y": 0},
        "region": "ru"
    },
    "olenemer": {
        "left_x": 100,
        "left_y": 100,
        "right_x": 800,
        "right_y": 100
    },
    "font": {
        "static_text": "Consolas",
        "dynamic_text": "Consolas",
        "static_text_size": 21,
        "dynamic_text_size": 21,
        "static_text_color": "white",
        "battles_label": "BTLS: ",
        "winrate_label": "WR:   ",
        "accuracy_label": "AC:   ",
        "avg_damage_label": "DMG:  ",
        "avg_xp_label": "XP:   ",
        "premium": True,
        "base_xp_only": True
    },
    "sessions": [],
    "tanks_data": {},
    "license_key": ""
}

documents = Path(os.path.expanduser('~'))\
    .joinpath('Documents')\
    .joinpath('TBSession')\
    .joinpath('Settings')\
    .joinpath('settings.eldb')

if not documents.exists():
    documents.parent.mkdir(exist_ok=True, parents=True)

os.chmod(documents.parent, 0o777, follow_symlinks=True)

class Settings:
    def __init__(self) -> None:
        self.db = elara.exe(documents)
        _ = self.db['window']

        if _ is not None:
            try:
                _ = ConfigStruct.model_validate(self.db.retdb())
            except Exception:
                self.db['window'] = _default_settings['window']
                self.db['replays_path'] = _default_settings['replays_path']
                self.db['font'] = _default_settings['font']
                self.db['sessions'] = _default_settings['sessions']
                self.db['olenemer'] = _default_settings['olenemer']
                self.db['tanks_data'] = _default_settings['tanks_data']
                self.db['license_key'] = _default_settings['license_key']
                self.db.commit()
            else:
                print(f'Core: Settings loaded from {documents}')
        else:
            self.db['window'] = _default_settings['window']
            self.db['replays_path'] = _default_settings['replays_path']
            self.db['font'] = _default_settings['font']
            self.db['sessions'] = _default_settings['sessions']
            self.db['olenemer'] = _default_settings['olenemer']
            self.db['tanks_data'] = _default_settings['tanks_data']
            self.db['license_key'] = _default_settings['license_key']
            self.db.commit()
            print('Core: Loaded default settings')

    def get(self) -> ConfigStruct:
        return ConfigStruct.model_validate(self.db.retdb())

    def get_by_key(self, key):
        return self.db.get(key)

    def set(self, key, value):
        self.db.set(key, value)
        self.db.commit()

    def get_raw(self) -> dict:
        return self.db.retdb()

    def __setitem__(self, key, value):
        self.set(key, value)
        self.db.commit()

    def __getitem__(self, key):
        return self.get_by_key(key)

_settings = Settings()

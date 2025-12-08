from yaml import safe_load
from kivy.logger import Logger

from utils.resource_path import get_current_directory
from lib.dataclasses.locales.struct import LocaleStruct


_log = Logger

def get_supported_locales() -> list[str]:
    paths_map = get_current_directory().joinpath('locales/').glob('*.yaml')
    return [i.stem for i in paths_map]


class Locales:
    def __init__(self):
        self.locales = get_supported_locales()
        self.data: dict[LocaleStruct] = {}
        if len(self.locales) == 0:            
            _log.critical('Locales: locales not found!')
            raise ValueError('Locales: locales not found!')

        for locale in self.locales:
            with open(get_current_directory().joinpath(f'locales/{locale}.yaml'), 'r', encoding='utf-8') as f:
                self.data[locale] = LocaleStruct.model_validate(safe_load(f.read()))
                
locales = Locales()

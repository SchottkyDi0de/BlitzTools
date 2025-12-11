import re

import yaml
from kivy.logger import Logger
from pydantic_core import ValidationError

from lib.dataclasses.configs.main_config import ConfigStruct
from utils.resource_path import get_current_directory, get_files_path
from utils.singleton_factory import singleton

_log = Logger

@singleton
class ConfigHandler:
    def __init__(self):
        self.config_path = get_files_path().joinpath('config/config.yaml')
        self.default_config_path = get_current_directory().joinpath('config/default_config.yaml')
        self.dump_options = {'default_flow_style': None, 'sort_keys': False, 'indent': 2, 'encoding': 'utf-8'}
        self.config_file_exists = self.config_path.exists()
        self.raw_config: str = ''
        
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.raw_config = f.read()
                try:
                    self.config = ConfigStruct.model_validate(yaml.safe_load(self.raw_config))
                except (ValidationError, yaml.YAMLError) as e:
                    _log.error(f'Config: Failed to load config file: {e.__class__.__name__}')
                    _log.info(f'Config: Using default config')
                    self.raw_config = self.default_config_path.read_text(encoding='utf-8')
                    self.config = ConfigStruct.model_validate(
                        yaml.safe_load(self.raw_config)
                    )
                    self.config_path.write_text(self.raw_config, encoding='utf-8')

        else:
            _log.warning('Config: Config file not found!')
            _log.info(f'Config: Config file not found, using default config')
            with open(self.config_path, 'w', encoding='utf-8') as config_file:
                self.raw_config = self.default_config_path.read_text(encoding='utf-8')
                config_file.write(self.raw_config)
                self.config = ConfigStruct.model_validate(yaml.safe_load(self.raw_config))
    
    def _rewrite_config(self):
        self.config_path.unlink()
        self.__init__()
            
    def get_config(self) -> ConfigStruct:
        return self.config

import re

import yaml
from kivy.logger import Logger
from pydantic_core import ValidationError

from lib.config.main_config import ConfigStruct
from utils.resource_path import get_default_config_path, get_files_path
from utils.singleton_factory import singleton
from utils.window_geometry import migrate_clusters_config, migrate_window_config, sanitize_window_config

_log = Logger


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


@singleton
class ConfigHandler:
    def __init__(self):
<<<<<<< HEAD
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
=======
        self.config_path = get_files_path().joinpath("config/config.yaml")
        default_path = get_default_config_path()
        with open(default_path, "r", encoding="utf-8") as default_config_file:
            self.default_config_data = yaml.safe_load(default_config_file.read())
        self.default_config = ConfigStruct.model_validate(self.default_config_data)
        self.config = self._load_or_create_config()

    def _load_or_create_config(self) -> ConfigStruct:
        _log.info(f"Config: user config path is {self.config_path}")

        if not self.config_path.exists():
            _log.info("Config: config file not found, creating from defaults...")
            self._write_config(self.default_config)
            return self.default_config.model_copy(deep=True)

        try:
            with open(self.config_path, "r", encoding="utf-8") as config_file:
                user_data = yaml.safe_load(config_file.read()) or {}
            merged_data = _deep_merge(self.default_config_data, user_data)
            config = ConfigStruct.model_validate(merged_data)
        except (ValidationError, yaml.YAMLError, OSError, TypeError) as exc:
            _log.warning(
                f"Config: error while loading config ({exc}), falling back to defaults..."
            )
            self._write_config(self.default_config)
            return self.default_config.model_copy(deep=True)

        changed = False
        if sanitize_window_config(
            config.app_global.window,
            self.default_config.app_global.window,
        ):
            changed = True
        if migrate_window_config(config, self.default_config):
            changed = True
        if migrate_clusters_config(config, self.default_config):
            changed = True
        if changed:
            _log.info("Config: defaults migrated, saving config")
            self.config = config
            self.write_config()
        return config

    def _write_config(self, config: ConfigStruct) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as config_file:
            config_file.write(yaml.dump(config.model_dump(), sort_keys=False, indent=2))

    def get_config(self) -> ConfigStruct:
        return self.config

    def write_config(self) -> None:
        self._write_config(self.config)
>>>>>>> 35887a35760c3d003b7693017bf138bc89650345

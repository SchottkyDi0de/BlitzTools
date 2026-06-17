import yaml
from kivy.logger import Logger

from pydantic_core import ValidationError

from lib.dataclasses.configs.main_config import ConfigStruct
from utils.resource_path import get_current_directory, get_files_path
from utils.singleton_factory import singleton
from utils.window_geometry import migrate_clusters_config, migrate_window_config, sanitize_window_config

_log = Logger

@singleton
class ConfigHandler:
    def __init__(self):
        self.config_path = get_files_path().joinpath('config/config.yaml')
        default_path = get_current_directory().joinpath('config/default_config.yaml')
        with open(default_path, 'r', encoding='utf-8') as default_config_file:
            default_config_data = yaml.safe_load(default_config_file.read())
        self.default_config = ConfigStruct.model_validate(default_config_data)
        self.config = self._load_or_create_config()

    def _load_or_create_config(self) -> ConfigStruct:
        if not self.config_path.exists():
            _log.info('Config: config file not fount, loading default config...')
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as config_file:
                config_file.write(yaml.dump(self.default_config.model_dump(), sort_keys=False, indent=2))
            _log.info('Config: config created successfully!')
            return self.default_config.model_copy(deep=True)

        try:
            with open(self.config_path, 'r', encoding='utf-8') as config_file:
                config = ConfigStruct.model_validate(yaml.safe_load(config_file.read()))
        except (ValidationError, FileNotFoundError, yaml.YAMLError, OSError, TypeError) as exc:
            _log.warning(f'Config: error while loading config ({exc}), resetting to default...')
            try:
                if self.config_path.exists():
                    self.config_path.unlink()
            except OSError:
                pass
            with open(self.config_path, 'w', encoding='utf-8') as config_file:
                config_file.write(yaml.dump(self.default_config.model_dump(), sort_keys=False, indent=2))
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
            _log.info("Config: window defaults migrated, saving config")
            self.config = config
            self.write_config()
        return config
                        
    def _load_config(self) -> None:
        with open(self.config_path, 'r', encoding='utf-8') as config_file:
            self.config = ConfigStruct.model_validate(yaml.safe_load(config_file.read()))
                        
    def get_config(self) -> ConfigStruct:
        """
        Return the current configuration.

        Returns:
            ConfigStruct: The current configuration.
        """
        return self.config
    
    def write_config(self) -> None:
        """
        Write the given configuration to the config file.

        Args:
            config (ConfigStruct): The configuration to write.
        """
        with open(get_files_path().joinpath('config/config.yaml'), 'w', encoding='utf-8') as f:
            f.write(yaml.dump(self.config.model_dump(), sort_keys=False, indent=2))

import yaml
from kivy.logger import Logger

from pydantic_core import ValidationError

from lib.dataclasses.configs.main_config import ConfigStruct
from utils.resource_path import get_current_directory, get_files_path
from utils.singleton_factory import singleton
from utils.window_geometry import sanitize_window_config

_log = Logger

@singleton
class ConfigHandler:
    def __init__(self):
        self.config_path = get_files_path().joinpath('config/config.yaml')
        with open(get_current_directory().joinpath('config/default_config.yaml'), 'r', encoding='utf-8') as default_config_file:
            default_config_data = yaml.safe_load(default_config_file.read())
            self.default_config = ConfigStruct.model_validate(default_config_data)
        
            if not self.config_path.exists():
                self.config: ConfigStruct = self.default_config
                _log.info('Config: config file not fount, loading default config...')
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(self.config_path, 'w', encoding='utf-8') as config_file:
                    config_file.write(yaml.dump(default_config_data))
                    
                _log.info('Config: config created successfully!')
                
            else:
                with open(self.config_path, 'r', encoding='utf-8') as config_file:
                    try:
                        self.config: ConfigStruct = ConfigStruct.model_validate(yaml.safe_load(config_file.read()))
                        if sanitize_window_config(
                            self.config.app_global.window,
                            self.default_config.app_global.window,
                        ):
                            _log.warning('Config: invalid window geometry, restored defaults')
                            self.write_config()
                    except (ValidationError, FileNotFoundError, yaml.YAMLError):
                        _log.warning('Config: Error while loading config, loading default config...')
                        self.config = self.default_config
                        config_file.close()
                        self.config_path.unlink()
                        self.__init__()
                        
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

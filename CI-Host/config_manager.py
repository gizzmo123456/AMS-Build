import common
import DEBUG
_print = DEBUG.LOGS.print

class ConfigManager:

    __CONFIG__ = {}
    __loaded = []

    @staticmethod
    def get(config_name, default_value=None):
        """Gets the config data for name
        :param config_name: name of config value
        :param default_value: default value to return if config does not exist
        """
        config_name = config_name.lower()

        if config_name in ConfigManager.__CONFIG__:
            return ConfigManager.__CONFIG__[config_name]

        return default_value

    @staticmethod
    def set(config_name, data):
        """Sets or adds (if not exist) to the global config"""
        ConfigManager.__CONFIG__[config_name.lower()] = data

    @staticmethod
    def set_from_json( file_path, reload=False ):

        if not reload and file_path in ConfigManager.__loaded:
            _print("config already loaded, skipping...")
            return

        config = common.get_dict_from_json(file_path, lock_file=True)

        _print("Loaded config '", file_path, "'", len(config), "keys Added")

        for conf in config:
            ConfigManager.set( conf, config[conf] )

        ConfigManager.__loaded.append( file_path )

    @staticmethod
    def is_set(config_name):
        return config_name in ConfigManager.__CONFIG__

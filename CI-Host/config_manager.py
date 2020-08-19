import common


class ConfigManager:

    __CONFIG__ = {}

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
    def set_from_json( file_path ):

        config = common.get_dict_from_json(file_path, lock_file=True)

        for conf in config:
            ConfigManager.set( conf, config[conf] )

    @staticmethod
    def is_set(config_name):
        return config_name in ConfigManager.__CONFIG__
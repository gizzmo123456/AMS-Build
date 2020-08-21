import config_manager

config_manager.ConfigManager.set_from_json("./data/configs/ams_path_conf.json")

APP_NAME = "ams-ci"
APP_VERSION             = 0.1

# AMS-CI setup
DEFAULT_SHELL = config_manager.ConfigManager.get( "default_shell", "sh" )
BASE_DIRECTORY = config_manager.ConfigManager.get( "base_directory", "${HOME}/ams-build")

DOCKER_ROOT_DIRECTORY = "/root/AMS-CI"              # Should be in the pipeline?? # This is the directory that the CI-config and CI-Root are mounted
PROJECT_DIRECTORY = BASE_DIRECTORY + "/CI-projects"
RELEVENT_PROJECT_PATH = "../CI-projects"        # relevant to the CI-Host folder

import config_manager
import urllib

APP_NAME    = "ams-ci"
APP_VERSION = "1.0.0"

# AMS-Build setup
DEFAULT_SHELL = config_manager.ConfigManager.get( "default_shell", "sh" )
BASE_DIRECTORY = config_manager.ConfigManager.get( "base_directory", "${HOME}/ams-build")

DOCKER_ROOT_DIRECTORY = "/root/AMS-CI"              # Should be in the pipeline?? # This is the directory that the CI-config and CI-Root are mounted
PROJECT_DIRECTORY = BASE_DIRECTORY + "/CI-projects"
RELEVENT_PROJECT_PATH = "../CI-projects"            # relevant to the CI-Host folder

# Web Const
WEB_ADDRESS = config_manager.ConfigManager.get( "web_address", "localhost" )
WEB_PATH = config_manager.ConfigManager.get( "web_path", "/ams-build" )

if config_manager.ConfigManager.get( "use_ssl", False ):
    WEB_PROTOCOL = "https"
else:
    WEB_PROTOCOL = "http"


def GET_BASE_WEB_ADDRESS(port):
    return f"{WEB_PROTOCOL}://{WEB_ADDRESS}:{port}{WEB_PATH}"


def GET_WEB_ADDRESS(port, path):
    """

    :param port:    target port
    :param path:    request path, within ams-build.
                    ie if requesting api '/api' -> output http://MyDomain.com:8080/ams-buid/api
    :return:
    """
    return f"{GET_BASE_WEB_ADDRESS( port )}{path}"

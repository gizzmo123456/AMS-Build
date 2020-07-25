# general project function used in ci and www interface

from const import *
import common
import os.path
import json

PATHS = {
    "PROJECT":  RELEVENT_PROJECT_PATH+"/{project_name}",
    "INFO":     RELEVENT_PROJECT_PATH+"/{project_name}/projectInfo.json",
    "PIPELINE": RELEVENT_PROJECT_PATH+"/{project_name}/master/config/pipeline.json"
}

def project_exist( project_name ):

    project_path = "{relevent_proj_path}/{project_name}".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                 project_name=project_name )

    return os.path.exists( project_path );

def get_project_list( ):
    """ Get a list of all projects
        :returns: list of dict [ {"name", "base_path"}, ... ]
    """

    projects = [ { "name": directory,
                   "base_path": "{abs_project_path}/{directory}".format( abs_project_path=PROJECT_DIRECTORY, directory=directory ) }
                 for directory in os.listdir( RELEVENT_PROJECT_PATH )
                 if os.path.isdir( "{relev_path}/{directory}".format( relev_path=RELEVENT_PROJECT_PATH, directory=directory ) ) ]

    return projects

def get_project_info( project_name ):
    """ Returns None if project doest not exist otherwise project info """
    # Project info can be accessed from anywhere, but it should only be updated/saved from build_task.

    project_path = "{relevent_proj_path}/{project_name}".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                 project_name=project_name )

    project_info_default = {
        "ProjectName": project_name,
        "latest_build_index": 0,
        "latest_build_key": "",
        "last_created_time": 0,
        "last_deploy_time": 0,
        "last_complete_time": 0
    }

    return common.get_or_create_json_file( project_path, "projectInfo.json", project_info_default )


def get_project_build( project_name ):
    # Project Build info can be accessed from anywhere, but it should only be updated/saved from build_task.

    project_path = "{relevent_proj_path}/{project_name}".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                 project_name=project_name )

    project_build_info_default = []

    return common.get_or_create_json_file( project_path, "projectBuildInfo.json", project_build_info_default )

def get_project_pipeline( project_name ):
    """Gets the project pipeline. None if project or file does not exist does not exist. """

    pipeline_path = "{relevent_proj_path}/{project_name}/master/config/pipeline.json".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                                       project_name=project_name )

    if not os.path.exists( pipeline_path ):
        return None

    return common.get_dict_from_json( pipeline_path )

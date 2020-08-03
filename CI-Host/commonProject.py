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
    """ Check if a project exist, Does not guarantee that the user can access the project"""

    project_path = "{relevent_proj_path}/{project_name}".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                 project_name=project_name )

    return os.path.exists( project_path )


def get_project_list( uac ):                        # TODO: add UAC
    """ Get a list of all projects
        :returns: list of dict [ {"name", "base_path"}, ... ]
    """

    projects = [ { "name": directory,
                   "base_path": "{project_path}/{directory}".format( project_path=RELEVENT_PROJECT_PATH, directory=directory ) }
                 for directory in os.listdir( RELEVENT_PROJECT_PATH )
                 if os.path.isdir( "{relev_path}/{directory}".format( relev_path=RELEVENT_PROJECT_PATH, directory=directory ) ) and uac.has_project_access( directory ) ]

    return projects


def get_all_project_info( project_name ):       # TODO: add UAC
    """ get all project and build info """

    if not project_exist( project_name ):
        return None  # project not found

    return { "name": project_name,
             "base_path": "{abs_project_path}/{directory}".format( abs_project_path=RELEVENT_PROJECT_PATH, directory=project_name ),
             "project_info": get_project_info( project_name ),
             "builds": get_project_build_info( project_name ),
             "tasks": get_project_tasks( project_name )
    }

def get_project_tasks( project_name ):          # TODO: add UAC.    If the user do not have project acceess, the active or pending task, the name should be hidden
    """gets a dict of active and queued tasks"""

    if not project_exist( project_name ):
        return None

    tasks = common.get_dict_from_json( "./data/tasks.json" )
    print(tasks)
    for task in tasks[ "active" ]:
        print( task["project"] )

    project_tasks = {
        "active":  [ task for task in tasks["active" ] if task["project"] == project_name ],
        "pending": [ task for task in tasks["pending"] if task["project"] == project_name ]
    }

    return project_tasks

def get_project_info( project_name ):           # TODO: add UAC
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

    return common.get_or_create_json_file( project_path, "projectInfo.json", project_info_default )[1]


def get_project_build_info( project_name ):     # TODO: add UAC
    # Project Build info can be accessed from anywhere, but it should only be updated/saved from build_task.

    project_path = "{relevent_proj_path}/{project_name}".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                 project_name=project_name )

    project_build_info_default = []

    return common.get_or_create_json_file( project_path, "projectBuildInfo.json", project_build_info_default )[1]

def get_project_pipeline( project_name ):       # TODO: add UAC (Also this should verifi webhook access, as its defined in the pipeline file)
    """Gets the project pipeline. None if project or file does not exist does not exist. """

    pipeline_path = "{relevent_proj_path}/{project_name}/master/config/pipeline.json".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                                              project_name=project_name )

    if not os.path.exists( pipeline_path ):
        return None

    return common.get_dict_from_json( pipeline_path )

def get_project_output_log( project, build_name ):      # TODO: add UAC
    """Get the output log for build in project, None if not found"""

    output_path = "{relevent_proj_path}/{project_name}/builds/{build_name}/output.txt".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                                               project_name=project,
                                                                                               build_name=build_name )

    if os.path.exists( output_path ):
        return common.read_file( output_path, True )

    return None

def get_project_build_7z( project, build_name ):        # TODO: add UAC

    """ returns the binaryFileStream """

    zip_path = "{relevent_proj_path}/{project_name}/builds/{build_name}/{build_name}.7z".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                                               project_name=project,
                                                                                               build_name=build_name )
    if os.path.exists( zip_path ):
        return common.BinaryFileStream( zip_path )

    return None

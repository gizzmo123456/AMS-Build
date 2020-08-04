# common project function that can be access at a user level.
# All public methods require a uac


from const import *
import common
import os.path
import json

PATHS = {
    "PROJECT":  RELEVENT_PROJECT_PATH+"/{project_name}",
    "INFO":     RELEVENT_PROJECT_PATH+"/{project_name}/projectInfo.json",
    "PIPELINE": RELEVENT_PROJECT_PATH+"/{project_name}/master/config/pipeline.json"
}


# use project_exist outside of commonProject.py
def __project_exist( project_name ): # Private
    """ (Private) Check if a project exist, Avoiding the UAC check """

    project_path = "{relevent_proj_path}/{project_name}".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                 project_name=project_name )

    return os.path.exists( project_path )


def project_exist( uac, project_name ):
    """ Check if a project exist """

    return uac.has_project_access( project_name ) and __project_exist( project_name )


def get_project_list( uac ):
    """ Get a list of all projects
        :returns: list of dict [ {"name", "base_path"}, ... ]
    """

    projects = [ { "name": directory,
                   "base_path": "{project_path}/{directory}".format( project_path=RELEVENT_PROJECT_PATH, directory=directory ) }
                 for directory in os.listdir( RELEVENT_PROJECT_PATH )
                 if os.path.isdir( "{relev_path}/{directory}".format( relev_path=RELEVENT_PROJECT_PATH, directory=directory ) ) and uac.has_project_access( directory ) ]

    return projects


def get_all_project_info( uac, project_name ):
    """ get all project and build info """

    if not __project_exist( project_name ) or not uac.has_project_access( project_name ):
        return None  # project not found or no access

    return { "name": project_name,
             "base_path": "{abs_project_path}/{directory}".format( abs_project_path=RELEVENT_PROJECT_PATH, directory=project_name ),
             "project_info": get_project_info( uac, project_name ),
             "builds": get_project_build_info( uac, project_name ),
             "tasks": get_project_tasks( uac, project_name )
    }


def get_project_tasks( uac, project_name ):          # TODO: If the user do not have project acceess, the active or pending task, the name should be hidden (this needs to be applied to all tasks.)
    """gets a dict of active and queued tasks"""

    if not __project_exist( project_name ) or not uac.has_project_access( project_name ):
        return None

    tasks = common.get_dict_from_json( "./data/tasks.json" )

    # extract all task the beloge to project
    project_tasks = {
        "active":  [ task for task in tasks["active" ] if task["project"] == project_name ],
        "pending": [ task for task in tasks["pending"] if task["project"] == project_name ]
    }

    return project_tasks

def get_project_info( uac, project_name ):
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

    if not __project_exist( project_name ) or not uac.has_project_access( project_name ):
        return project_info_default

    return common.get_or_create_json_file( project_path, "projectInfo.json", project_info_default )[1]


def get_project_build_info( uac, project_name ):
    # Project Build info can be accessed from anywhere, but it should only be updated/saved from build_task.

    project_path = "{relevent_proj_path}/{project_name}".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                 project_name=project_name )

    project_build_info_default = []

    if not __project_exist( project_name ) or not uac.has_project_access( project_name ):
        return project_build_info_default

    return common.get_or_create_json_file( project_path, "projectBuildInfo.json", project_build_info_default )[1]


def get_project_pipeline( project_name ):       # TODO: add UAC (Also this should verifi webhook access, as its defined in the pipeline file)
    """ Gets the project pipeline. None if project or file does not exist does not exist or the user does not have access. """

    pipeline_path = "{relevent_proj_path}/{project_name}/master/config/pipeline.json".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                                              project_name=project_name )

    if not os.path.exists( pipeline_path ):
        return None

    pipeline = common.get_dict_from_json( pipeline_path )

    #if not uac.has_project_access( project_name, pipeline ):
    #    return None

    return pipeline


def get_project_output_log( uac, project, build_name ):
    """Get the output log for build in project, None if not found"""

    if not __project_exist( project ) or not uac.has_project_access( project ):
        return None

    output_path = "{relevent_proj_path}/{project_name}/builds/{build_name}/output.txt".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                                               project_name=project,
                                                                                               build_name=build_name )

    if os.path.exists( output_path ):
        return common.read_file( output_path, True )

    return None

def get_project_build_7z( uac, project, build_name ):

    """ returns the binaryFileStream """

    if not __project_exist( project ) or not uac.has_project_access( project ):
        return None

    zip_path = "{relevent_proj_path}/{project_name}/builds/{build_name}/{build_name}.7z".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                                               project_name=project,
                                                                                               build_name=build_name )
    if os.path.exists( zip_path ):
        return common.BinaryFileStream( zip_path )

    return None

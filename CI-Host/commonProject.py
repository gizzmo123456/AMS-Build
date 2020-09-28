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

    project_build_info_path = "{relevent_proj_path}/{project_name}/projectBuildInfo.json".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                                                  project_name=project_name )

    project_build_info_default = []

    if not __project_exist( project_name ) or not uac.has_project_access( project_name ):
        return project_build_info_default

    if not os.path.exists( project_build_info_path ):
        return project_build_info_default
    else:
        # wrap the contents on the json file in [] as there not included in the file,
        # so we can just quickly append new entries to the end of the file :)
        project_info_string = common.read_file( project_build_info_path, lock=True )
        if project_info_string[0] == ",": # also not forgetting to remove the lazy ',' at the start.
            project_info_string = project_info_string[1:]

        project_info_string = '[{file}]'.format( file=project_info_string )

        return json.loads( project_info_string )


def get_project_pipeline( uac, project_name ):
    """ Gets the project pipeline. None if project or file does not exist does not exist or the user does not have access. """

    pipeline_path = "{relevent_proj_path}/{project_name}/master/project_source/pipeline.json".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                                              project_name=project_name )

    if not os.path.exists( pipeline_path ):
        return None

    pipeline = common.get_dict_from_json( pipeline_path )

    if not uac.has_project_access( project_name, get_project_config( uac, project_name, "webhooks") ):
        return None

    return pipeline


def get_project_config( uac, project_name, config_name):

    if config_name == "pipeline":
        return get_project_pipeline( uac, project_name)

    config_path = "{relevent_proj_path}/{project_name}/master/config/{config_name}.json".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                                                 project_name=project_name,
                                                                                                 config_name=config_name )

    if not os.path.exists( config_path ):
        return None

    config = common.get_dict_from_json( config_path )

    if config_name != "webhooks":   # prevent a recursive nightmare
        webhook_access = get_project_config( uac, project_name, "webhooks")
    else:
        webhook_access = config

    if not uac.has_project_access( project_name, webhook_access ):
        return None

    return config


def get_project_webhook_fields( project_name ):
    """ Gets the inbound data fields
        This does not require UAC, since it defines the path to data field in inbound json string.
        And therefor give no access to the project. in-fact we use this data to verify the actors and project.
        The default values are ALWAYS returned regardless of the project existing
    """

    default = {} # BitBucket.
    default["test"]         = ["test"]
    default["actor"]        = ["actor", "display_name"]
    default["repository"]   = ["repository", "name"]
    default["hash"]         = [ "push", "changes", 0, "new", "target", "hash" ] # Todo: Same as below?
    default["branch"]       = ["push", "changes", 0, "new", "name"]    # TODO. this might need improving. 0 refers to n amount of changes and we only check the first :|

    config_path = "{relevent_proj_path}/{project_name}/master/config/webhook_fields.json".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                                                  project_name=project_name )

    if not os.path.exists( config_path ):
        return default

    config = common.get_dict_from_json( config_path )

    return { **default, **config }  # make sure that all values are supplied.

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


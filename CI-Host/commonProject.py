# general project function used in ci and www interface

from const import *
import common
import os.path

def project_exist( project_name ):

    project_path = "{relevent_proj_path}/{project_name}".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                 project_name=project_name )

    return os.path.exists( project_path );

def get_project_info( project_name ):
    """Returns None if project doest not exist otherwise project info"""


    project_path = "{relevent_proj_path}/{project_name}".format( relevent_proj_path=RELEVENT_PROJECT_PATH,
                                                                 project_name=project_name )

    project_info_path = "{project_path}/projectInfo.json".format( project_path=project_path )
    if not os.path.exists( project_path ):
        return None

    if not os.path.exists( project_info_path ):
        # create new project info if one does not exist
        project_info = {
            "ProjectName": project_name,
            "latest_build_index": 0,
            "latest_build_key": "",
            "last_created_time": 0,
            "last_deploy_time": 0,
            "last_complete_time": 0
        }

        common.create_json_file( project_info_path, project_info )

        return project_info
    else:
        return common.get_dict_from_json( project_info_path )
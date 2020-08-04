from const import *
import common
import commonProject
import json
from datetime import datetime
import time
import DEBUG
_print = DEBUG.LOGS.print


class BuildTask:
    "Build tasks..."

    def __init__( self, uac, project_name, build_hash ):
        """
        :param uac:             The UAC of the user that triggered the build
        :param project_name:    name of project
        :param build_hash:      build hash
        """

        # load config file,
        self.config = commonProject.get_project_pipeline( uac, project_name )
        self.valid = self.config is not None

        if not self.valid:
            _print( "Task not valid, ignoring. Either no pipeline or no access ", project_name, message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
            return

        webhook = uac.access_level == uac.WEBHOOK   # TODO: move webhook commands to its own section

        self.format_values = {  # values are public to the pipeline file    # it might be worth passing this into the contatiner.
            # directorys
            "project_dir": PROJECT_DIRECTORY,
            "relv_proj_dir": RELEVENT_PROJECT_PATH,
            "master_dir": "",
            "build_dir": "",
            "master_source_dir": "",
            "build_source_dir": "",
            # project
            "project": project_name,
            "master_build_name": "master",
            # build
            "build_name": "",
            "build_hash": build_hash,
            "build_index": 0,
            # util
            "container_name": project_name+build_hash,
            "actor": uac.username,
            "created": datetime.now().strftime( "%d/%m/%Y @ %H:%M:%S" ),
            "started_build": -1
        }

        self.project_info = None
        # TODO: lock project info during update (on all 3)
        self._update_project_info()

        if self.project_info == None:
            _print( "Bad Task: Project does not exist", message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
            return

        # Update Project info.
        self.format_values[ "build_index" ] = self.project_info[ "latest_build_index" ] + 1

        self.project_info[ "latest_build_index" ] = self.format_values[ "build_index" ]
        self.project_info[ "latest_build_key" ] = build_hash
        self.project_info[ "last_created_time" ] = time.time()

        self._save_project_info()

        # create build name, and define corresponding directories
        self.format_values["build_name"] = "{project}_{build_hash}_build_{build_index}".format( **self.format_values )
        self.format_values["master_dir"] = "{project_dir}/{project}/{master_build_name}".format( **self.format_values )
        self.format_values["build_dir"]  = "{project_dir}/{project}/builds/{build_name}".format( **self.format_values )
        self.format_values["master_source_dir"] = self.format_values["master_dir"] + "/project_source"
        self.format_values["build_source_dir"] = self.format_values["build_dir"] + "/project_source"

        # output
        self.stdout_filepath = "{relv_proj_dir}/{project}/builds/{build_name}/output.txt".format( **self.format_values )

        # Note: until the master directory is copied, the output does not exist,
        #       So _print calls with output_filename defined are queued, until the file does exist
        _print("Starting master/pre-build commands for project '{project}' @ {created}: LOG OUTPUT FILE PATH: {stdout}".format( stdout=self.stdout_filepath, **self.format_values), self.stdout_filepath)

        # prepare the build.
        # - run master commands in project source
        # - copy master directory to build directory
        # - run pre build commands
        _print( "..::Executing master commands::..", output_filename=self.stdout_filepath, console=False )
        if webhook and "master-commands" in self.config["webhook"] and len(self.config["webhook"]["master-commands"]) > 0:
            master_commands = [ mc.format( **self.format_values ) for mc in self.config["webhook"]["master-commands"] ]     # add format values to commands
            for line in common.run_process( ( "cd {master_source_dir}; " + '; '.join( master_commands ) ).format( **self.format_values ), shell="bash"):
                _print(line, output_filename=self.stdout_filepath, console=False)

        _print( "Copying Master To Build Directory", output_filename=self.stdout_filepath, console=False )
        _print( "{master_dir} -> {build_dir}".format( **self.format_values ), output_filename=self.stdout_filepath, console=False )
        for line in common.run_process( "sudo cp -r {master_dir} {build_dir}; "
                                        "cd {build_dir}; ".format( **self.format_values ), shell="bash" ):
            _print(line, output_filename=self.stdout_filepath, console=False)   # Note: Queued _print message are now dumped to file.

        _print( "..::Executing Pre-Build Commands::..", output_filename=self.stdout_filepath, console=False )
        if webhook and "pre-build-commands" in self.config["webhook"] and len(self.config["webhook"]["pre-build-commands"]) > 0:
            pre_build_commands = [ mc.format( **self.format_values ) for mc in self.config["webhook"]["pre-build-commands"] ]   # add format values to commands
            for line in common.run_process( ( "cd {build_source_dir}; " + '; '.join( pre_build_commands ) ).format( **self.format_values ), shell="bash"):
                _print(line, output_filename=self.stdout_filepath, console=False)

        # create the local and docker configs
        # to map local to docker
        self.local_cof = {
            "ci-root": "{root_dir}/CI-root/".format( root_dir=BASE_DIRECTORY ),
            "ci-config": self.format_values["build_dir"] + "/config",
            "project": self.format_values["build_source_dir"],
            "build-output": self.format_values["build_dir"] + "/build"
        }

        self.docker_cof = {
            "ci-root-dest": DOCKER_ROOT_DIRECTORY + "/CI-root:ro",                  # ci-tool mouth point as read only
            "ci-config-dest": DOCKER_ROOT_DIRECTORY + "/CI-config:ro",              # config mouth point as read only
            "project-dest": self.config[ "docker" ][ "project-dest" ],              # project source mount point
            "build-output-dest": self.config[ "docker" ][ "build-output-dest" ],    # build output mount point
            "image": self.config[ "docker" ][ "image" ],
            "args": self.config[ "docker" ][ "args" ]
        }

        _print( "="*25, output_filename=self.stdout_filepath, console=False )
        _print( "SUCCESSFULLY INITIALIZED BUILD TASK", output_filename=self.stdout_filepath, console=False )
        _print( "Waiting to start task...", output_filename=self.stdout_filepath, console=False )
        _print( "="*25, output_filename=self.stdout_filepath, console=False )

    def _update_project_info( self ):
        self.project_info = commonProject.get_project_info( self.format_values[ "project" ] )

    def _save_project_info( self ):

        if self.project_info is None:
            _print( "Unable to update project info for project {project}".format( **self.format_values ) )
            return

        project_info_path = "{relv_proj_dir}/{project}/projectInfo.json".format( **self.format_values )
        common.write_file( project_info_path, json.dumps( self.project_info ), lock=True )

    def get_config_value( self, *keys ):    ## Todo this needs to be replaced with common.get_value_at_key
        """Gets the config value at keys
        :param keys: each key of the config value ie.
                    keys "webhook", "name" would return config[webhook][name]
                    or "pipeline", "commands", 0 would return config[pipeline][commands][0]
                    Returns None if no set.
        """
        value = self.config
        for key in keys:
            # key is not valid if not a dict or list or if the key is an int and the value is not a list
            if (type(value) is not list and type(value) is not dict) or (type(value) is list and type(key) is not int):
                return None
            # if value is a list, this key is an int and in range
            elif type(value) is list and type(key) is int and key >= 0 and key < len(key):
                value = value[key]
            # if the key is the dict
            elif key in value:
                value = value[key]
            else: # not defined.
                return None

        return value


    def local_image_exist( self ):
        """check if the docker image in config exist locally"""
        for line in common.run_process( "sudo docker image inspect {image}".format(image=self.docker_cof["image"]), shell=DEFAULT_SHELL ):
            return not (line == "[]")  # if the first line is an empty list (ie. [] ) no image exist

    def pull_image( self ):
        """attempts to pull the docker image from index.docker.io"""
        for line in common.run_process( "sudo docker pull {image}".format(image=self.docker_cof["image"]), shell=DEFAULT_SHELL ):          # if the fist word of the first line is error this image does not exist in the repo.
            if line.split( " " )[ 0 ].lower() == "error":   # if the first word of the first line is error the image does not exist
                return False
            _print(line, output_filename=self.stdout_filepath, console=False)
        return True

    def deploy_container( self ):
        """deploys the docker container to run the build"""

        dockerRun = "sudo docker run " \
                    "{args} " \
                    "-v {project_path}:{project_dest} " \
                    "-v {ci_root_path}:{ci_root_dest} " \
                    "-v {ci_config_path}:{ci_config_dest} " \
                    "-v {ci_build_path}:{ci_build_dest} " \
                    "{image} --name {container_name}" \
                    "{cmd}".format( args=self.docker_cof[ "args" ],
                                    project_path=self.local_cof[ "project" ], project_dest=self.docker_cof[ "project-dest" ],
                                    ci_root_path=self.local_cof[ "ci-root" ], ci_root_dest=self.docker_cof[ "ci-root-dest" ],
                                    ci_config_path=self.local_cof[ "ci-config" ], ci_config_dest=self.docker_cof[ "ci-config-dest" ],
                                    ci_build_path=self.local_cof[ "build-output" ], ci_build_dest=self.docker_cof[ "build-output-dest" ],
                                    image=self.docker_cof["image"], container_name=self.format_values["container_name"],
                                    cmd="python3 {docker_ci_root}/CI-root/main-ci-root.py".format( docker_ci_root=DOCKER_ROOT_DIRECTORY ) )


        for line in common.run_process( dockerRun, shell=DEFAULT_SHELL ):
            _print(line, output_filename=self.stdout_filepath, console=False)

        # TODO: this should be locked from when we update till the end of save.
        self._update_project_info()  # make sure that we have the current version loaded.
        self.project_info[ "last_complete_time" ] = time.time()
        self._save_project_info()

    def cleanup( self ):

        zip = self.get_config_value( "cleanup", "7z_build" )
        cleanup = self.get_config_value( "cleanup", "remove_build_source" )

        # Zip file
        if zip is not None and zip is True:
            _print( "Zipping build...", output_filename=self.stdout_filepath, console=False )
            # zip the build, removing zipped files
            for line in common.run_process( "cd {build_dir}; sudo 7z a {build_name}.7z ./build/ -sdel;".format( **self.format_values ),
                                            "bash" ):
                _print( line, output_filename=self.stdout_filepath, console=False )
            _print( "Zipping Complete", output_filename=self.stdout_filepath, console=False )
        else:
            _print( "Skipping Zipping", output_filename=self.stdout_filepath, console=False )

        # Clean up
        if cleanup is not None and cleanup is True:
            _print( "Cleaning Source...", output_filename=self.stdout_filepath, console=False )
            # remove the (copied) source folder
            for line in common.run_process( "cd {build_dir}; sudo rm -r {build_source_dir}".format( **self.format_values ), "bash" ):
                _print( line, output_filename=self.stdout_filepath, console=False )
            _print( "Build Source Removed", output_filename=self.stdout_filepath, console=False )
        else:
            _print( "Skipping Clean up", output_filename=self.stdout_filepath, console=False )

    def append_build_info( self ):

        # TODO: It might be worth not formating the json file in the list so
        # we can just append the build info to the end of the file

        build_info = {  "name": self.format_values["build_name"],
                        "hash": self.format_values["build_hash"],
                        "build_id": self.format_values["build_index"],
                        "status": "pass",
                        "created_by": self.format_values["actor"],
                        "created_at": self.format_values["created"],
                        "7z_link": "dl/{project}/{build_name}".format( **self.format_values ),
                        "output_log": "output/{project}/{build_name}".format( **self.format_values )
                      }

        project_builds = commonProject.get_project_build_info( self.format_values["project"] )
        project_builds.append( build_info )

        project_build_info_path = "{relv_proj_dir}/{project}/projectBuildInfo.json".format( **self.format_values )
        common.write_file( project_build_info_path, json.dumps( project_builds ), lock=True )

    def execute( self ):

        if not self.valid:
            _print("Invalid task, ignoring...", output_filename=self.stdout_filepath)
            return

        # update the project info last execute time
        # TODO: this should be locked from when we update till the end of save.
        self._update_project_info()     # make sure that we have the current version loaded.
        self.project_info[ "last_execute_time" ] = time.time()
        self._save_project_info()

        _print( "Local Config:", self.local_cof, output_filename=self.stdout_filepath, console=False )
        _print( "Docker Config:", self.docker_cof, output_filename=self.stdout_filepath, console=False )
        _print( "=" * 24, output_filename=self.stdout_filepath, console=False )

        _print( "Verifying image exist...", output_filename=self.stdout_filepath, console=False )
        image_exist = self.local_image_exist()
        if not image_exist:
            _print("Image does not exist locally", output_filename=self.stdout_filepath, console=False)
            image_exist = self.pull_image()
            if not image_exist:
                _print("Image does not exist on index.docker.io (must be public)", output_filename=self.stdout_filepath, console=False)
                return 1
            else:
                _print("Pulled Image!", output_filename=self.stdout_filepath, console=False)
        else:
            _print("Image Found!", output_filename=self.stdout_filepath, console=False)

        _print( "=" * 24, output_filename=self.stdout_filepath, console=False )

        _print( "Deploying docker container, please wait...", output_filename=self.stdout_filepath, console=False )

        self.deploy_container()
        self.cleanup()
        self.append_build_info()

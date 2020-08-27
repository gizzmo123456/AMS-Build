from const import *
import hashlib
import common
import commonProject
import out_webhook
import json
import os.path
from datetime import datetime
import time
import re
import DEBUG
_print = DEBUG.LOGS.print


class BuildTask:
    "Build tasks..."

    BUILD_STATUS_FAIL   = "fail"
    BUILD_STATUS_PASS   = "pass"
    BUILD_STATUS_WARN   = "warning"
    BUILD_STATUS_CANCEL = "cancel"
    BUILD_STATUS_SKIP   = "skip"
    BUILD_STATUS_DUMMY  = "DEBUG-DUMMY-BUILD"

    TASK_STATE_CANCELED      = -1
    TASK_STATE_INIT          = 0
    TASK_STATE_CREATED       = 1
    TASK_STATE_EXECUTING     = 2
    TASK_STATE_CLEANING      = 3
    TASK_STATE_COMPLETE      = 4

    CONTAINER_STATE_PENDING      = 0
    CONTAINER_STATE_PULL         = 1
    CONTAINER_STATE_RUNNING      = 2
    CONTAINER_STATE_EXITED       = 3

    def __init__( self, uac, project_name, git_hash="", complete_callback=None ):
        """
        :param uac:             The UAC of the user that triggered the build
        :param project_name:    name of project
        :param git_hash:      build hash
        """

        self.complete_callback = complete_callback      # callback params: build_task, successful

        self.task_state = BuildTask.TASK_STATE_INIT
        self.container_state = BuildTask.CONTAINER_STATE_PENDING
        self.build_status = BuildTask.BUILD_STATUS_PASS

        self.uac = uac
        # load config file,
        self.config = commonProject.get_project_pipeline( uac, project_name )

        # make sure that the config file contains the bare minimal
        # Use the IsValid Method to check if the task is in a valid state
        self.__valid = self.config is not None and \
                       "docker"        in self.config and \
                       "prepare-build" in self.config and \
                       "pipeline"      in self.config

        if not self.__valid:
            _print( "Task not valid, ignoring. Either no pipeline, Invalid pipeline or no access ", project_name, message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
            return

        build_name_str = "{project}_{build_hash}_build_{build_index}"

        if "build-name-format" in self.config:
            build_name_str = self.config[ "build-name-format" ]

        trigger_method = "webhook"

        if uac.access_level != uac.WEBHOOK:
            trigger_method = "www_interface"

        # values are public to the pipeline file
        # it might be worth passing this into the contatiner.
        # also might be worth moving directories into its own dict.
        self.format_values = {
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
            "build_index": 0,
            # hashes
            "build_hash": BuildTask.__create_build_hash( project_name ),
            "git_hash": git_hash,
            "7z_hash": None,
            # util
            "trigger_method": trigger_method,
            "actor": uac.username,
            "created": datetime.now().strftime( "%d/%m/%Y @ %H:%M:%S" ),
            "started_build": -1
        }

        self.__format_values = {

        }

        self._project_info_path = "{relv_proj_dir}/{project}/projectInfo.json".format( **self.format_values )
        self.project_info = None

        self._update_project_info() # this must be called at least once

        if self.project_info == None:
            self.valid = False
            _print( "Bad Task: Project does not exist", message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
            return

        # Update Project info.
        with common.LockFile( self._project_info_path, mode='r+' ) as file:     # lock the file during update
            self.project_info = json.loads( file.read() )                       # ensure that we have the latest version

            # update build info
            self.format_values[ "build_index" ] = self.project_info[ "latest_build_index" ] + 1

            # update project info
            self.project_info[ "latest_build_index" ] = self.format_values[ "build_index" ]
            self.project_info[ "latest_build_key"] = self.format_values[ "build_hash" ]
            self.project_info[ "last_created_time" ] = time.time()

            self._overwrite_json_file( file, self.project_info )

        # create build name, and define corresponding directories
        self.format_values["build_name"] = build_name_str.format( **self.format_values )
        self.format_values["master_dir"] = "{project_dir}/{project}/{master_build_name}".format( **self.format_values )
        self.format_values["build_dir"]  = "{project_dir}/{project}/builds/{build_name}".format( **self.format_values )
        self.format_values["master_source_dir"] = self.format_values["master_dir"] + "/project_source"
        self.format_values["build_source_dir"] = self.format_values["build_dir"] + "/project_source"

        # output
        self.stdout_filepath = "{relv_proj_dir}/{project}/builds/{build_name}/output.txt".format( **self.format_values )

        # Note: until the master directory is copied, the output does not exist,
        #       So _print calls with output_filename defined are queued, until the file does exist
        _print("\nStarting master/pre-build commands for project '{project}' @ {created}: LOG OUTPUT FILE PATH: {stdout}".format( stdout=self.stdout_filepath, **self.format_values), self.stdout_filepath)

        # prepare the build.
        # - run master dir commands in the master project source
        # - update git hash if required.
        # - copy master directory to build directory
        # - run build dir commands in copied project source
        _print( "--- Executing Master Dir Prepare Commands ---", output_filename=self.stdout_filepath, console=False )
        if "master-dir-commands" in self.config[ "prepare-build" ] and len( self.config[ "prepare-build" ][ "master-dir-commands" ] ) > 0:

            master_commands = [ mc.format( **self.format_values ) for mc in self.config[ "prepare-build" ][ "master-dir-commands" ] ]
            for line in common.run_process( ( "cd {master_source_dir}; " + '; '.join( master_commands ) ).format( **self.format_values ), shell="bash"):
                _print(line, output_filename=self.stdout_filepath, console=False)

        # -

        _print( "--- Updating Git-hash ---", output_filename=self.stdout_filepath, console=False )
        update_git_hash = "get-git-hash" in self.config[ "prepare-build" ] and self.config[ "prepare-build" ]["get-git-hash"] is True
        if (git_hash == "" or git_hash is None) and update_git_hash:
            cmd = "cd {master_source_dir};".format( **self.format_values )
            git_cmd = cmd + "cd git rev-parse HEAD" # use HEAD to get the repos current hash, after the prepare-build (master)
            temp_git_hash = ""
            for line in common.run_process( git_cmd, shell="bash" ):
                temp_git_hash += line

            _print( "GitHash: {0}".format( temp_git_hash ), output_filename=self.stdout_filepath, console=False )
            self.format_values[ "git_hash" ] = temp_git_hash

        else:
            _print( "Skipped. Pipeline update: {0} git_hash: {1}".format(update_git_hash, self.format_values["git_hash"]), output_filename=self.stdout_filepath, console=False )

        # -

        _print( "--- Copying Master To Build Directory ---", output_filename=self.stdout_filepath, console=False )
        _print( "{master_dir} -> {build_dir}".format( **self.format_values ), output_filename=self.stdout_filepath, console=False )
        for line in common.run_process( "sudo cp -r {master_dir} {build_dir}; "
                                        "cd {build_dir}; ".format( **self.format_values ), shell="bash" ):
            _print(line, output_filename=self.stdout_filepath, console=False)   # Note: Queued _print message are now dumped to file.

        # -

        _print( "--- Executing Build Dir Prepare Commands ---", output_filename=self.stdout_filepath, console=False )
        if "build-dir-commands" in self.config[ "prepare-build" ] and len( self.config[ "prepare-build" ][ "build-dir-commands" ] ) > 0:

            build_commands = [ bc.format( **self.format_values ) for bc in self.config[ "prepare-build" ][ "build-dir-commands" ] ]
            for line in common.run_process( ( "cd {build_source_dir}; " + '; '.join( build_commands ) ).format( **self.format_values ), shell="bash"):
                _print(line, output_filename=self.stdout_filepath, console=False)

        # create the local and docker configs
        # to map local to docker
        self.local_cof = {
            "ci-root": "{root_dir}/CI-root/".format( root_dir=BASE_DIRECTORY ),
            "project": self.format_values["build_source_dir"],
            "build-output": self.format_values["build_dir"] + "/build"
        }

        self.docker_cof = {
            "container_name": project_name.lower() + self.format_values["build_hash"].lower(),
            "stop_timeout": self.get_config_value( "docker", "stop-timeout", default_value=10 ),                                     # the amount of time to wait until SIGKILL is sent after SIGTERM is sent (can be None)
            "ci-root-dest": self.get_config_value( "docker", "ams-container-dest", default_value="/root/AMS-Build"),                 # ci-tool mouth point as read only
            "project-dest": self.config[ "docker" ][ "project-dest" ],                                                               # project source mount point
            "build-output-dest": self.config[ "docker" ][ "build-output-dest" ],                                                     # build output mount point
            "image": self.config[ "docker" ][ "image" ],
            "args": self.config[ "docker" ][ "args" ]
        }

        self.task_state = BuildTask.TASK_STATE_CREATED

        _print( "="*25, output_filename=self.stdout_filepath, console=False )
        _print( "SUCCESSFULLY INITIALIZED BUILD TASK", output_filename=self.stdout_filepath, console=False )
        _print( "Waiting to start task...", output_filename=self.stdout_filepath, console=False )
        _print( "="*25, output_filename=self.stdout_filepath, console=False )

    def is_valid( self ):
        """ A task is considered valid if the pipeline contains all required field
            and the task has not been canceled, and the container has not exited
        """
        return self.__valid and \
               self.task_state != BuildTask.TASK_STATE_CANCELED and \
               self.container_state != BuildTask.CONTAINER_STATE_EXITED

    def can_execute( self ):
        return self.is_valid() and self.task_state < BuildTask.TASK_STATE_EXECUTING

    @staticmethod
    def __create_build_hash( project_name ):
        s = hashlib.sha1()
        s.update( "{name}-{time}".format( name=project_name, time=time.time() ).encode() )
        return s.hexdigest()

    def _update_project_info( self ):

        project_info_default = {
            "ProjectName": self.format_values[ "project" ],
            "latest_build_index": 0,
            "latest_build_key": "",
            "last_created_time": 0,
            "last_execute_time": 0,
            "last_complete_time": 0
        }

        project_info_path = "{relv_proj_dir}/{project}".format( **self.format_values )
        self.project_info = common.get_or_create_json_file( project_info_path, "projectInfo.json", project_info_default )[ 1 ]

    def _overwrite_json_file( self, file, json_dict ):
        """ Overwrites file when in r+ mode """
        file.seek( 0 )
        file.write( json.dumps( json_dict ) )
        file.truncate()

    def get_config_value( self, *keys, default_value=None ):    ## Todo this needs to be replaced with common.get_value_at_key
        """Safely gets the config value at keys
        :param keys:            each key of the config value ie.
                                keys "docker", "image" would return config[docker][image]
                                or "pipeline", "commands", 0 would return config[pipeline][commands][0]
                                Returns None if no set.
        :param default_value:   The default value to be returned if the key is not found
        """
        value = self.config
        for key in keys:
            # key is not valid if not a dict or list or if the key is an int and the value is not a list
            if (type(value) is not list and type(value) is not dict) or (type(value) is list and type(key) is not int):
                return default_value
            # if value is a list, this key is an int and in range
            elif type(value) is list and type(key) is int and key >= 0 and key < len(key):
                value = value[key]
            # if the key is the dict
            elif key in value:
                value = value[key]
            else: # not defined.
                return default_value

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
                    "--name {container_name} {args} " \
                    "-v {project_path}:{project_dest} " \
                    "-v {ci_root_path}:{ci_root_dest}:ro " \
                    "-v {ci_build_path}:{ci_build_dest} " \
                    "{image} " \
                    "{cmd}".format( container_name=self.docker_cof["container_name"].lower(), args=self.docker_cof[ "args" ],
                                    project_path=self.local_cof[ "project" ], project_dest=self.docker_cof[ "project-dest" ],
                                    ci_root_path=self.local_cof[ "ci-root" ], ci_root_dest=self.docker_cof[ "ci-root-dest" ],
                                    ci_build_path=self.local_cof[ "build-output" ], ci_build_dest=self.docker_cof[ "build-output-dest" ],
                                    image=self.docker_cof["image"],
                                    cmd="python3 {docker_ci_root}/main-ci-root.py".format( docker_ci_root=self.docker_cof[ "ci-root-dest" ] ) )

        _print( "DOCKER RUN:\n", dockerRun, output_filename=self.stdout_filepath, console=False )

        self.container_state = BuildTask.CONTAINER_STATE_RUNNING

        last_line = ""
        for line in common.run_process( dockerRun, shell=DEFAULT_SHELL ):
            _print(line, output_filename=self.stdout_filepath, console=False)
            last_line = line

        self.container_state = BuildTask.CONTAINER_STATE_EXITED
        _print("--- Container Exited ---", output_filename=self.stdout_filepath, console=False)

        # check the last line for the build status message.
        STATUS_LINE_BEGIN = "@AMS-PIPELINE-STATUS:"
        STATUS_LINE_LEN = len(STATUS_LINE_BEGIN)
        is_status_line = last_line.find(STATUS_LINE_BEGIN) == 0

        if self.build_status != BuildTask.BUILD_STATUS_CANCEL:  # cancel_task deals with status if the build is canceled.
            if is_status_line:
                pipeline_status = json.loads( last_line[STATUS_LINE_LEN:] )
                final_status = None
                for stage in pipeline_status:   # TODO: Convert the status to BuildTask status and append it to the Build info.
                    stage_status = self.get_stage_status( pipeline_status[ stage ] )
                    final_status = self.get_combin_stage_status( final_status, stage_status )

                    # if the status becomes a Warning we can exit as there is a mixture of passes and fails
                    if final_status == BuildTask.BUILD_STATUS_WARN:
                        break

                if final_status is None:
                    self.build_status = BuildTask.BUILD_STATUS_FAIL
                else:
                    self.build_status = final_status

            else:
                # fail by default if the last line is not the status line.
                # this would indicate that the container crashed :(
                self.build_status = BuildTask.BUILD_STATUS_FAIL

        with common.LockFile( self._project_info_path, mode='r+' ) as file:  # lock the file during update
            self.project_info = json.loads( file.read() )                    # ensure that we have the latest version
            self.project_info[ "last_complete_time" ] = time.time()
            self._overwrite_json_file( file, self.project_info )

    def get_stage_status( self, stage_passed ):

        if stage_passed:
            return BuildTask.BUILD_STATUS_PASS
        else:
            return BuildTask.BUILD_STATUS_FAIL

    def get_combin_stage_status( self, current_status, stage_status ):

        if current_status is None:
            return stage_status
        elif current_status == stage_status:        # Still passing or failing
            return current_status
        elif current_status != stage_status:        # Mixed statues
            return BuildTask.BUILD_STATUS_WARN

    def stop_container( self ):
        """ Stops the tasks container using the docker stop command.
            The main process inside the container will initially receive a 'SIGTERM' signal,
            Once the grace period (or stop timeout) [default 10sec] is reached a SIGKILL is sent,
            to kill the container once and for all :D.
            The stop_timeout can be added as an optional attribute in the docker section of the
            pipeline json file
        """

        docker_stop = "sudo docker stop -t {stop_timeout} {container_name}".format( **self.docker_cof )

        _print("="*25, output_filename=self.stdout_filepath, console=False)
        _print("--- Stopping Container ---", output_filename=self.stdout_filepath, console=False)

        for line in common.run_process( docker_stop, shell=DEFAULT_SHELL ):
            _print( line, output_filename=self.stdout_filepath, console=False )

        self.container_state = BuildTask.CONTAINER_STATE_EXITED

        _print("--- Container Stopped ---", output_filename=self.stdout_filepath, console=False)

    def cleanup( self ):

        self.task_state = BuildTask.TASK_STATE_CLEANING

        zip = self.get_config_value( "cleanup", "7z_build", default_value=False )
        zip_hash = self.get_config_value( "cleanup", "7z_hash" )
        cleanup = self.get_config_value( "cleanup", "remove_build_source", default_value=False )

        accepted_7z_hashes = [ "crc32", "crc64", "sha1", "sha256", "blake2sp" ]

        _print( "="*25, output_filename=self.stdout_filepath, console=False )

        # Zip file
        if self.task_state != BuildTask.TASK_STATE_CANCELED and zip is True:
            _print( "--- Zipping build ---", output_filename=self.stdout_filepath, console=False )
            # zip the build, removing zipped files
            for line in common.run_process( "cd {build_dir}; sudo 7z a {build_name}.7z ./build/ -sdel;".format( **self.format_values ),
                                            "bash" ):
                _print( line, output_filename=self.stdout_filepath, console=False )
            _print( "--- Zipping Complete ---", output_filename=self.stdout_filepath, console=False )

            if zip_hash.lower() in accepted_7z_hashes:
                _print("--- Generating 7z hash ---", output_filename=self.stdout_filepath, console=False)
                hash_cmd = "cd {build_dir}; 7z h -scrc{hash_type} {build_name}.7z | grep -oP '(?<=for data:).*'".format(hash_type=zip_hash.lower(),
                                                                                                                        **self.format_values)
                temp_7z_hash = ""
                for line in common.run_process( hash_cmd, "bash" ):
                    temp_7z_hash += line

                temp_7z_hash = re.sub( r'\s', "", temp_7z_hash )    # remove the white space
                self.format_values["7z_hash"] = temp_7z_hash
                _print("7z hash:", temp_7z_hash, output_filename=self.stdout_filepath, console=False)
                _print("--- 7z hash Complete ---", output_filename=self.stdout_filepath, console=False)


        else:
            _print( "--- Skipping Zipping ---", output_filename=self.stdout_filepath, console=False )

        # Clean up
        if cleanup is True:
            _print( "--- Cleaning Source ---", output_filename=self.stdout_filepath, console=False )
            # remove the (copied) source folder
            for line in common.run_process( "cd {build_dir}; sudo rm -r {build_source_dir}".format( **self.format_values ), "bash" ):
                _print( line, output_filename=self.stdout_filepath, console=False )
            _print( "Build Source Removed", output_filename=self.stdout_filepath, console=False )
            _print( "--- clean source complete ---", output_filename=self.stdout_filepath, console=False )
        else:
            _print( "--- Skipping Clean up ---", output_filename=self.stdout_filepath, console=False )

    def append_build_info( self ):

        project_build_info_path = "{relv_proj_dir}/{project}/projectBuildInfo.json".format( **self.format_values )
        build_info = {  "name": self.format_values["build_name"],
                        "hash": self.format_values["build_hash"],
                        "build_id": self.format_values["build_index"],
                        "status": self.build_status,
                        "trigger_method": self.format_values["trigger_method"],
                        "git_hash": self.format_values[ "git_hash" ],
                        "created_by": self.format_values["actor"],
                        "canceled_by": None,
                        "created_at": self.format_values["created"],
                        "7z_link": "dl/{project}/{build_name}".format( **self.format_values ),
                        "7z_hash": self.format_values["7z_hash"],
                        "output_log": "output/{project}/{build_name}".format( **self.format_values )
                      }

        if not os.path.exists( project_build_info_path ):
            common.write_file( project_build_info_path, "" )

        with common.LockFile( project_build_info_path, 'a' ) as file:
            file.write( "," + json.dumps( build_info ) )

        return build_info

    def execute( self ):

        if not self.can_execute():
            _print("Unable to execute task. Config valid:", self.__valid, "Current State:", self.task_state, output_filename=self.stdout_filepath)
            return

        self.task_state = BuildTask.TASK_STATE_EXECUTING

        # update the project info last execute time
        with common.LockFile( self._project_info_path, mode='r+' ) as file:  # lock the file during update
            self.project_info = json.loads( file.read() )                    # ensure that we have the latest version
            self.project_info[ "last_execute_time" ] = time.time()
            self._overwrite_json_file( file, self.project_info )

        _print( "Local Config:", self.local_cof, output_filename=self.stdout_filepath, console=False )
        _print( "Docker Config:", self.docker_cof, output_filename=self.stdout_filepath, console=False )
        _print( "=" * 24, output_filename=self.stdout_filepath, console=False )

        self.container_state = BuildTask.CONTAINER_STATE_PULL

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

        # make sure that the task has not ben canceled while we where pulling the image.
        if self.task_state != BuildTask.TASK_STATE_CANCELED:
            _print( "Deploying docker container, please wait...", output_filename=self.stdout_filepath, console=False )
            self.deploy_container()
        else:
            _print( "Skipping container deploy, Task Canceled", output_filename=self.stdout_filepath, console=False )

        self.cleanup()
        build_info = self.append_build_info()
        # trigger outbound webhooks
        out_webhook.handle_outbound_webhook( self.uac, self.format_values["project"], out_webhook.OWHT_BUILD_COMPLETE, {**self.format_values, **build_info})

        self.task_state = BuildTask.TASK_STATE_COMPLETE
        self.trigger_complete_callback( True )

    def trigger_complete_callback( self, finished ):

        if self.complete_callback is not None:
            self.complete_callback( self, finished )

    def cancel( self ):

        if self.task_state == BuildTask.TASK_STATE_CANCELED:
            _print( "Unable to cancel task - Already marked as canceled" )

        _print( "--- Canceling Task ---", output_filename=self.stdout_filepath, console=False )

        state_when_canceled = self.task_state
        self.task_state = BuildTask.TASK_STATE_CANCELED

        if self.build_status == BuildTask.BUILD_STATUS_DUMMY:
            self.build_status += "-"+BuildTask.BUILD_STATUS_CANCEL
        else:
            self.build_status = BuildTask.BUILD_STATUS_CANCEL

        if state_when_canceled < BuildTask.TASK_STATE_EXECUTING:
            self.cleanup()
            self.append_build_info()

        elif self.container_state == BuildTask.CONTAINER_STATE_RUNNING:
            # TODO: NOTE: possible BUG: If the container is launching im not 100% the stop container method will work
            # if the container is running we need to kill it.
            _print( "Attempting to stop container...", output_filename=self.stdout_filepath, console=False )
            self.stop_container()

        _print( "--- Task Canceled ---", output_filename=self.stdout_filepath, console=False )


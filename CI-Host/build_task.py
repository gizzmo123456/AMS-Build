from const import *
import json
import common
from datetime import datetime

# TODO print needs to change to log to file.
# i think it might be worth using the debugger from game_server :)
# As that can handle both print and log to file called from different threads
class BuildTask:
    "Build tasks..."

    def __init__( self, trigger_actor, project_name, build_hash, webhook=False, webhook_name="" ):
        """ if webhook is is True, webhook_name must be set in the project pipeline
            otherwise the task will be ignored on execution.
            TBH this serves as a workaround until the webhook is able to do it own look up :)
        """
        self.format_values = {      # values are public to the pipeline file
            # directorys
            "project_dir":          PROJECT_DIRECTORY,
            "relv_proj_dir":        RELEVENT_PROJECT_PATH,
            "master_dir":           "",
            "build_dir":            "",
            "master_source_dir":    "",
            "build_source_dir":     "",
            # project
            "project":              project_name,
            "master_build_name":    "master",
            # build
            "build_name":           "",
            "build_hash":           build_hash,
            "build_index":          0,
            # util
            "actor":                trigger_actor,
            "now":                  datetime.now().strftime("/%d%m/%Y @ %H:%M:%S")
        }

        # create build name, and define corresponding directories
        self.format_values["build_name"] = "{project}_{build_hash}_build_{build_index}".format( **self.format_values )
        self.format_values["master_dir"] = "{project_dir}/{project}/{master_build_name}".format( **self.format_values )
        self.format_values["build_dir"]  = "{project_dir}/{project}/builds/{build_name}".format( **self.format_values )
        self.format_values["master_source_dir"] = self.format_values["master_dir"] + "/project_source"
        self.format_values["build_source_dir"] = self.format_values["build_dir"] + "/project_source"

        # load config file
        self.config = "{relv_proj_dir}/{project}/master/pipeline.json".format( **self.format_values )
        self.config = common.get_dict_from_json( self.config )

        # just to save the headack
        # valid if not a webhook or is webhook and webhook name is defined in project name and request actor is defined in the webhook auth users
        self.valid = not webhook or ( webhook and "webhook" in self.config and "name" in self.config["webhook"] and
                                      self.config["webhook"]["name"] == webhook_name and "authorized-actors" in self.config["webhook"] and
                                      trigger_actor in self.config["webhook"]["authorized-actors"] )

        if not self.valid:
            return

        # prepare the build.
        # - run master commands in project source
        # - copy master directory to build directory
        # - run pre build commands
        if webhook and "master-commands" in self.config["webhook"] and len(self.config["webhook"]["master-commands"]) > 0:
            master_commands = [ mc.format( **self.format_values ) for mc in self.config["webhook"]["master-commands"] ]     # add format values to commands
            for line in common.run_process( ( "cd {master_source_dir}; " + '; '.join( master_commands ) ).format( **self.format_values ), shell="bash"):
                print(line)

        for line in common.run_process( "sudo cp -r {master_dir} {build_dir}; "
                                        "cd {build_dir}; "
                                        "sudo echo created by {actor} - {now} >> createdBy.txt;".format( **self.format_values ), shell="bash" ):
            print(line)

        if webhook and "pre-build-commands" in self.config["webhook"] and len(self.config["webhook"]["pre-build-commands"]) > 0:
            pre_build_commands = [ mc.format( **self.format_values ) for mc in self.config["webhook"]["pre-build-commands"] ]   # add format values to commands
            for line in common.run_process( ( "cd {build_source_dir}; " + '; '.join( pre_build_commands ) ).format( **self.format_values ), shell="bash"):
                print(line)

        # create the local and docker configs
        # to map local to docker
        self.local_cof = {
            "ci-root": "{root_dir}/CI-root/".format( root_dir=BASE_DIRECTORY ),
            # TODO: master needs to be the name of the copied directory
            "ci-config": self.format_values["build_dir"] + "/pipeline.json",
            "project": self.format_values["build_source_dir"],
            "build-output": self.format_values["build_dir"] + "/build"
        }

        self.docker_cof = {
            "ci-root-dest": DOCKER_ROOT_DIRECTORY + "/CI-root:ro",  # ci-tool mouth point as read only
            "ci-config-dest": DOCKER_ROOT_DIRECTORY + "/pipeline.json:ro",  # config mouth point as read only
            "project-dest": "/root/project",  # project source mount point                                              (TODO user defined)
            "build-output-dest": "/root/project/unityBuild/Builds/StandaloneWindows",  # build output mount point       (TODO user defined)
            "image": self.config[ "docker" ][ "image" ],
            "args": self.config[ "docker" ][ "args" ]
        }

    def local_image_exist( self ):
        """check if the docker image in config exist locally"""
        for line in common.run_process( "sudo docker image inspect {image}".format(image=self.docker_cof["image"]), shell=DEFAULT_SHELL ):
            return not (line == "[]")  # if the first line is an empty list (ie. [] ) no image exist

    def pull_image( self ):
        """attempts to pull the docker image from index.docker.io"""
        for line in common.run_process( "sudo docker pull {image}".format(image=self.docker_cof["image"]), shell=DEFAULT_SHELL ):          # if the fist word of the first line is error this image does not exist in the repo.
            if line.split( " " )[ 0 ].lower() == "error":   # if the first word of the first line is error the image does not exist
                return False
            print( line )
        return True

    def deploy_container( self ):
        """deploys the docker container to run the build"""

        dockerRun = "sudo docker run " \
                    "{args} " \
                    "-v {project_path}:{project_dest} " \
                    "-v {ci_root_path}:{ci_root_dest} " \
                    "-v {ci_config_path}:{ci_config_dest} " \
                    "-v {ci_build_path}:{ci_build_dest} " \
                    "{image} " \
                    "{cmd}".format( args=self.docker_cof[ "args" ],
                                    project_path=self.local_cof[ "project" ], project_dest=self.docker_cof[ "project-dest" ],
                                    ci_root_path=self.local_cof[ "ci-root" ], ci_root_dest=self.docker_cof[ "ci-root-dest" ],
                                    ci_config_path=self.local_cof[ "ci-config" ], ci_config_dest=self.docker_cof[ "ci-config-dest" ],
                                    ci_build_path=self.local_cof[ "build-output" ], ci_build_dest=self.docker_cof[ "build-output-dest" ],
                                    image="gableroux/unity3d:2018.4.2f1-windows",
                                    cmd="python3 {docker_ci_root}/CI-root/main-ci-root.py".format( docker_ci_root=DOCKER_ROOT_DIRECTORY ) )


        for line in common.run_process( dockerRun, shell=DEFAULT_SHELL ):
            print( line )

    def execute( self ):

        if not self.valid:
            print("Invalid task, ignoring...")
            return

        print( "Local Config:", self.local_cof )
        print( "Docker Config:", self.docker_cof )
        print( "=" * 24 )

        print( "Verifying image exist..." )
        image_exist = self.local_image_exist()
        if not image_exist:
            print("Image does not exist locally")
            image_exist = self.pull_image()
            if not image_exist:
                print("Image does not exist on index.docker.io (must be public)")
                return 1
            else:
                print("Pulled Image!")
        else:
            print("Image Found!")

        print( "=" * 24 )

        print( "Deploying docker container, please wait..." )
        self.deploy_container()
        # TODO: clean up...

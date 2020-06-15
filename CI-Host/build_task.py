from const import *
import json
import common

# TODO print needs to change to log to file.
# i think it might be worth using the debugger from game_server :)
# As that can handle both print and log to file called from different threads
class BuildTask:
    "Build tasks..."

    def __init__( self, project_name, build_name ):

        self.build_project_directory = "{project_dir}/{project}/{build}".format( project_dir=PROJECT_DIRECTORY,
                                                                                 project=project_name,
                                                                                 build=build_name )

        self.config = "{relv_proj_dir}/{project}/master/pipeline.json".format( relv_proj_dir=RELEVENT_PROJECT_PATH,
                                                                               project=project_name )
        self.config = self.get_dict_from_json( self.config )

        self.local_cof = {
            "ci-root": "{root_dir}/CI-root/".format( root_dir=BASE_DIRECTORY ),
            # TODO: master needs to be the name of the copied directory
            "ci-config": self.build_project_directory + "/pipeline.json",
            "project": self.build_project_directory + "/project_source/",
            "build-output": self.build_project_directory + "/build",
            "stdout": self.build_project_directory + "/output.txt"
        }

        self.docker_cof = {
            "ci-root-dest": DOCKER_ROOT_DIRECTORY + "/CI-root:ro",  # ci-tool mouth point as read only
            "ci-config-dest": DOCKER_ROOT_DIRECTORY + "/pipeline.json:ro",  # config mouth point as read only
            "project-dest": "/root/project",  # project source mount point    (TODO user defined)
            "build-output-dest": "/root/project/unityBuild/Builds/StandaloneWindows",  # build output mount point      (TODO user defined)
            "stdout-dest": DOCKER_ROOT_DIRECTORY + "/output.txt",  # stdout mount point
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
                    "-v {ci_stdout_path}:{ci_stdout_dest} " \
                    "{image} " \
                    "{cmd}".format( args=self.docker_cof[ "args" ],
                                    project_path=self.local_cof[ "project" ], project_dest=self.docker_cof[ "project-dest" ],
                                    ci_root_path=self.local_cof[ "ci-root" ], ci_root_dest=self.docker_cof[ "ci-root-dest" ],
                                    ci_config_path=self.local_cof[ "ci-config" ], ci_config_dest=self.docker_cof[ "ci-config-dest" ],
                                    ci_build_path=self.local_cof[ "build-output" ], ci_build_dest=self.docker_cof[ "build-output-dest" ],
                                    ci_stdout_path=self.local_cof[ "stdout" ], ci_stdout_dest=self.docker_cof[ "stdout-dest" ],
                                    image="gableroux/unity3d:2018.4.2f1-windows",
                                    cmd="python3 {docker_ci_root}/CI-root/main-ci-root.py".format( docker_ci_root=DOCKER_ROOT_DIRECTORY ) )


        for line in common.run_process( dockerRun, shell=DEFAULT_SHELL ):
            print( line )

    def execute( self ):

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

    def read_file( self, file_name ):

        with open(file_name) as file:
            return ''.join( file.readlines() )

    def get_dict_from_json( self, file_name ):
        return json.loads( self.read_file( file_name ) )

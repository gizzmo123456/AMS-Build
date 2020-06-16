from const import *
import json
import common
import time

# TODO print needs to change to log to file.
# i think it might be worth using the debugger from game_server :)
# As that can handle both print and log to file called from different threads
class BuildTask:
    "Build tasks..."

    def __init__( self, trigger_actor, project_name, build_hash, master_commands=[], pre_build_commands=[] ):

        # load config file
        self.config = "{relv_proj_dir}/{project}/master/pipeline.json".format( relv_proj_dir=RELEVENT_PROJECT_PATH,
                                                                               project=project_name )
        self.config = self.get_dict_from_json( self.config )

        # create build name, and define fine corresponding directories
        self.build_name = "{name}_{hash}_build_{index}".format(name=project_name,
                                                               hash=build_hash,
                                                               index=0 )    # todo index me :)

        self.master_build_directory = "{project_dir}/{project}/{build}".format( project_dir=PROJECT_DIRECTORY,
                                                                                project=project_name,
                                                                                build="master")

        self.build_project_directory = "{project_dir}/{project}/builds/{build}".format( project_dir=PROJECT_DIRECTORY,
                                                                                        project=project_name,
                                                                                        build=self.build_name )

        # prepare the build.
        # - run master commands in project source
        # - copy master directory to build directory
        # - run pre build commands
        for line in common.run_process("cd {master_source_dir}; "
                                       "git pull origin master; "
                                       "sudo cp -r {master_dir} {build_dir}; "
                                       "cd {build_dir}; "
                                       "echo {created} >> createdBy.txt".format(
                master_source_dir=self.master_build_directory+"/project_source/testCIGame",         # note: this should only go as far as project source. testCIGame should e in the pipeline file.
                master_dir=self.master_build_directory,
                build_dir =self.master_build_directory,
                created="Build triggered by "+trigger_actor+" at "+time.time() ), shell="bash"):
            print(line)

        # create the local and docker configs
        # to map local to docker
        self.local_cof = {
            "ci-root": "{root_dir}/CI-root/".format( root_dir=BASE_DIRECTORY ),
            # TODO: master needs to be the name of the copied directory
            "ci-config": self.build_project_directory + "/pipeline.json",
            "project": self.build_project_directory + "/project_source/",
            "build-output": self.build_project_directory + "/build"
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

    def copy_master_directory( self ):

        cmd = "sudo cp -r {master_dir} {build_dir}".format( master_dir=self.master_build_directory,
                                                            build_dir=self.build_project_directory )

        for line in common.run_process( cmd, shell=DEFAULT_SHELL ):
            print( line )


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
        print("Copying master directory")
        self.copy_master_directory()

        print( "Deploying docker container, please wait..." )
        self.deploy_container()
        # TODO: clean up...

    def read_file( self, file_name ):

        with open(file_name) as file:
            return ''.join( file.readlines() )

    def get_dict_from_json( self, file_name ):
        return json.loads( self.read_file( file_name ) )

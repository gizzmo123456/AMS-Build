#!/usr/bin/env python3

import json
import common
import threading

def read_file( file_name ):

    with open(file_name) as file:
        return ''.join( file.readlines() )

def get_dict_from_json( file_name ):
    return json.loads( read_file( file_name ) )

if __name__ == "__main__":

    print( "Loading Config..." )

    project_name = "exampleProject"
    default_shell = "sh"

    base_directory = "${HOME}/unity-ci"
    project_directory = base_directory + "/CI-project"
    build_project_directory = "{project_dir}/{project}/{build}".format(project_dir=project_directory,
                                                                       project="exampleProject",
                                                                       build="master")

    relevant_project_directory = "../CI-projects"   # relevant to the CI-host file :)

    # always use the master config file when queuing builds.
    config = "{relv_proj_dir}/{project}/master/pipeline.json".format(relv_proj_dir=relevant_project_directory, project=project_name)
    config = get_dict_from_json( config )

    local_cof = {
        "ci-root"       : "{root_dir}/CI-root/".format(root_dir=base_directory),
        # TODO: master needs to be the name of the copied directory
        "ci-config"     : build_project_directory+"/pipeline.json",
        "project"       : build_project_directory+"/project_source/",
        "build-output"  : build_project_directory+"/build",
        "stdout"        : build_project_directory+"/output.txt"
    }

    docker_cof = {
        "ci-root-dest"      : "/root/CI-root:ro",                                       # ci-tool mouth point as read only
        "ci-config-dest"    : "/root/CI-conf/pipeline.json:ro",                         # config mouth point as read only
        "project-dest"      : "/root/project",                                          # project source mount point
        "build-output-dest" : "/root/project/unityBuild/Builds/StandaloneWindows",      # build output mount point
        "stdout-dest"       : "/root/CI-output/output.txt",                             # stdout mount point
        "image"             : config["docker"]["image"],
        "args"              : config["docker"]["args"]
    }

    print("Local Config:", local_cof)
    print("Docker Config:", docker_cof)

    print("="*24)

    print("Verifying image exist...")

    # find if we have the docker image locally if not attempt to pull the image from docker
    error = False

    for line in common.run_process( "sudo docker image inspect {image}".format(image=docker_cof["image"]), shell=default_shell ):     # if the first line is an empty list (ie. [] ) no image exist
        if line == "[]":
            error = True
            continue

        if error:
            print(line)
        else:
            print("Image Found Locally!")
            break

    if error:   # attempt to pull the image
        print("Attempting pull image from docker...")
        for line in common.run_process( "sudo docker pull {image}".format(image=docker_cof["image"]), shell=default_shell ):          # if the fist word of the first line is error this image does not exist in the repo.
            if error and line.split( " " )[ 0 ].lower() != "error":
                error = False
                print( "Found!, Pulling image." )
            print( line )


    if error:
        print("Unable to pull docker image. Build Failed, exiting...")
        exit(1)

    print("="*24)
    print("Deploying docker container, please wait...")
    # We must mark the CI-root as read only (:ro) to insure that files are not modified
    # and any files created are not passed back into the host system.
    dockerRun = "sudo docker run " \
                "{args} " \
                "-v {project_path}:{project_dest} " \
                "-v {ci_root_path}:{ci_root_dest} " \
                "-v {ci_config_path}:{ci_config_dest} " \
                "-v {ci_build_path}:{ci_build_dest} " \
                "-v {ci_stdout_path}:{ci_stdout_dest} " \
                "{image} " \
                "{cmd}".format(args=docker_cof["args"],
                               project_path=local_cof["project"],       project_dest=docker_cof["project-dest"],
                               ci_root_path=local_cof["ci-root"],       ci_root_dest=docker_cof["ci-root-dest"],
                               ci_config_path=local_cof["ci-config"],   ci_config_dest=docker_cof["ci-config-dest"],
                               ci_build_path=local_cof["build-output"], ci_build_dest=docker_cof["build-output-dest"],
                               ci_stdout_path=local_cof["stdout"],      ci_stdout_dest=docker_cof["stdout-dest"],
                               image="gableroux/unity3d:2018.4.2f1-windows",
                               cmd="python3 /root/CI-root/main-ci-root.py")

    print("Running docker cmd:", dockerRun)

    for line in common.run_process( dockerRun, shell=default_shell ):  # if the fist word of the first line is error this image does not exist in the repo.
        print(line)


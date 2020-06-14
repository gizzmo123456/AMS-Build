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

    project_name = "example_project"
    default_shell = "sh"


    config = get_dict_from_json( "../CI-projects/exampleProject/master/pipeline.json" )

    local_cof = {
        "ci-root"       : "${HOME}/unity-ci/CI-root/",
        # TODO: master needs to be the name of the copied directory
        "ci-config"     : "${HOME}/unity-ci/CI-projects/exampleProject/master/pipeline.json",
        "project"       : "${HOME}/unity-ci/CI-projects/exampleProject/master/project_source/",
        "build_output"  : "${HOME}/unity-ci/CI-projects/exampleProject/master/build",
        "output"        : "${HOME}/unity-ci/CI-projects/exampleProject/master/output.txt",
    }

    docker_cof = {
        "ci-root-dest"  : "/root/CI-root:ro",                     # ci-tool mouth point as read only
        "ci-config-dest": "/root/CI-config/pipeline.json:ro",     # config mouth point as read only
        "project-dest"  : "/root/project",                        # project mount point
        "build_output"  : "",
        "output"        : "",
        "image"         : config["docker"]["image"],
        "args"          : config["docker"]["args"]
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
                "{image} " \
                "{cmd}".format(args=docker_cof["args"],
                               project_path=local_cof["project"],       project_dest=docker_cof["project-dest"],
                               ci_root_path=local_cof["ci-root"],       ci_root_dest=docker_cof["ci-root-dest"],
                               ci_config_path=local_cof["ci-config"],   ci_config_dest=docker_cof["ci-config-dest"],
                               image="gableroux/unity3d:2018.4.2f1-windows",
                               cmd="python3 /root/CI-root/main-ci-root.py")

    print("Running docker cmd:", dockerRun)

    for line in common.run_process( dockerRun, shell=default_shell ):  # if the fist word of the first line is error this image does not exist in the repo.
        print(line)


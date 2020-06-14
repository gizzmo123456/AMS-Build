#!/usr/bin/env python3

import json
import common

def read_file( file_name ):

    with open(file_name) as file:
        return ''.join( file.readlines() )

def get_dict_from_json( file_name ):
    return json.loads( read_file( file_name ) )

if __name__ == "__main__":

    print("Loading Config...")
    config = get_dict_from_json( "../CI-config/test.json" )

    print("Docker:", config["docker"])
    print("Environment:", config["environment"])
    print("Pipeline", config["pipeline"])

    print("="*24)

    print("Verifying image exist...")

    error = False

    for line in common.run_process( "sudo docker image inspect {image}".format(image="gableroux/unity3d:2018.4.2f1-windows"), shell="sh" ):     # if the first line is an empty list (ie. [] ) no image exist
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
        for line in common.run_process( "sudo docker pull {image}".format(image="gableroux/unity3d:2018.4.2f1-windows"), shell="sh" ):          # if the fist word of the first line is error this image does not exist in the repo.
            if error and line.split( " " )[ 0 ].lower() != "error":
                error = False
                print( "Found!, Pulling image." )
            print( line )


    if error:
        print("Unable to pull docker image. Build Failed, exiting...")
        exit(1)

    print("Deploying docker container, please wait...")
    # We must mark the CI-root as read only (:ro) to insure that files are not modified
    # and any files created are not passed back into the host system.
    dockerRun = "sudo docker run " \
                "{args} " \
                "-v ${HOME}/unity-ci/CI-root:/root/CI-root:ro " \
                "-v ${HOME}/unity-ci/CI-config/test.json:/root/CI-config/pipeline.json " \
                "{image} " \
                "python3 /root/CI-root/main-ci-root.py".format(args="-it --rm -v ${HOME}/project:/root/project",
                                                               image="gableroux/unity3d:2018.4.2f1-windows",
                                                               HOME="{HOME}" )
    print(dockerRun)
    for line in common.run_process( dockerRun, shell="sh" ):  # if the fist word of the first line is error this image does not exist in the repo.
        print(line)

    for line in common.run_process( "echo 'Im the Precess :)' ", shell="sh" ):
        print( line )

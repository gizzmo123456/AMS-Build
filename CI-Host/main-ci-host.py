import json
import subprocess
import os

def run_process( command ):

    process = subprocess.Popen( ['python3', '-c', 'import os;os.system("{0}")'.format(command)], stdout=subprocess.PIPE )

    while True:
        line = process.stdout.readline().decode( "utf-8" )
        if not line:
            break
        else:
            if line[-1:] == '\n':   # remove the new line char so we don't get double new lines :)
                line = line[:-1]
            yield line

    process.kill()

def read_file( file_name ):

    with open(file_name) as file:
        return ''.join( file.readlines() )

def get_dict_from_json( file_name ):
    return json.loads( read_file( file_name ) )


if __name__ == "__main__":

    print("Loading Config...")
    # config = get_dict_from_json( "../CI-config/test.json" )

    #print("Docker:", config["docker"])
    #print("Environment:", config["environment"])
    #print("Pipeline", config["pipeline"])

    print("="*24)

    print("Verifying image exist...")

    error = False

    for line in run_process( "sudo docker image inspect {image}".format(image="gizzmo123456/server_info:0.1") ):     # if the first line is an empty list (ie. [] ) no image exist
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
        for line in run_process( "sudo docker pull {image}".format(image="gizzmo123456/server_info:0.1") ):          # if the fist word of the first line is error this image does not exist in the repo.
            if error and line.split( " " )[ 0 ].lower() != "error":
                error = False
                print( "Found!, Pulling image." )
            print( line )


    if error:
        print("Unable to pull docker image. Build Failed, exiting...")
        exit(1)

    print("Deploying docker container, please wait...")
    dockerRun = "sudo docker run {args} -v ${HOME}/unity-ci/CI-root:/root/CI-root -v ${HOME}/unity-ci/CI-config/test.json:/root/CI-config/pipeline.json {image} python3 /root/CI-root/main-ci-root.py".format(args="-it --rm -v ${HOME}/project:/root/project", image="gizzmo123456/server_info:0.1", HOME="{HOME}" )
    print(dockerRun)
    for line in run_process( dockerRun ):  # if the fist word of the first line is error this image does not exist in the repo.
        print(line)

    for line in run_process( "echo 'Im the Precess :)' " ):
        print( line )

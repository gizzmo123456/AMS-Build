# The CI-root directory needs to mounted to /root/CI-root within the container
#

import subprocess

def run_process( command ):  # Todo: make this common :)

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

if __name__ == "__main__":

    cmd = "cd /root/project/unityBuild\n" \
          "source ./preBuild.sh\n" \
          "./before_build.sh\n" \
          "./build.default2.sh\n"

    print("Start Build Process, Hold Tight...")

    for line in run_process( cmd ):
        print( line )

    print( "Build Complete ")

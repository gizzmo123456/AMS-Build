#!/usr/bin/env python3
# The CI-root directory needs to mounted to /root/CI-root within the container
#

import subprocess
import common

def build_config_sh(config):
    """ builds the sh file for each stage.
    :param config:  the config dict
    """

    env = ["# set up the environment"]
    # build the environment section of the sh file
    for e in config["environment"]:
        line = "export {0}={1}".format(e, config["environment"][e])
        env.append(line)

    stages = []
    stage_names = []

    # build each stage
    for p in config["pipeline"]:
        stage = [ "# stage "+p["name"] ]
        for c in p["commands"]:
            stage.append( c )
        stages.append(stage)

    # it worth noting that if we are going to bind mount directories into the image the configs
    # need to be unique folder, to insure that files are not over writen, before or during use.
    with open("stage.txt", mode="w") as file:
        file.write( '\n'.join( stages[0] ) )

if __name__ == "__main__":

    cmd = "cd /root/project/unityBuild; " \
          "source ./preBuild.sh;" \
          "./before_script.sh;" \
          "./build.default2.sh;"

    print(cmd)
    print("Start Build Process, Hold Tight...")

    for line in common.run_process( cmd, shell="bash" ):
        print( line )

    print( "Build Complete " )

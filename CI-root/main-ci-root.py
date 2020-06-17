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

    pipeline_filepath = "/root/AMS-CI/CI-config/pipeline.json"
    pipeline = common.get_dict_from_json( pipeline_filepath )

    env = "".join( [ "export {var}={value}; ".format(var=e, value=pipeline["environment"][e]) for e in pipeline["environment"] ] )
    stages = pipeline["pipeline"]

    for stage in stages:
        print("Starting pipeline stage ", stage["name"].upper())
        cmd = '; '.join( stage["commands"] )

        print( "Executing ", cmd )
        print( "Start Build Process, Hold Tight..." )

        for line in common.run_process( env + cmd, shell="bash" ):
            print( line )

        print("Pipeline stage ", stage["name"].upper(), "Complete")

    # cmd = "cd /root/project/unityBuild; " \
    #      "source ./preBuild.sh;" \
    #      "./before_script.sh;" \
    #      "./build.default2.sh;"

    print( "All Stages Complete :D" )

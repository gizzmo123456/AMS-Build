#!/usr/bin/env python3
# The CI-root directory needs to mounted to /root/CI-root within the container
#

import common
import json

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

    pipeline_filepath = "/root/project/pipeline.json"
    pipeline = common.get_dict_from_json( pipeline_filepath )

    env = "".join( [ "export {var}={value}; ".format(var=e, value=pipeline["environment"][e]) for e in pipeline["environment"] ] )
    stages = pipeline["pipeline"]
    pipeline_statues = {}

    if len(env) > 0 and env[-1] != ";":  # ensure the last car of env is `;`
        env += "; "

    for stage in stages:
        print("="*25)
        print("Starting pipeline stage ", stage["name"].upper())
        exit_line = "0"                         # By default expect last line (exit-line/exit-code) to be 0 (successful)
        if "exit-line" in stage:
            exit_line = stage["exit-line"]

        cmd = '; '.join( stage["commands"] )

        print( "Executing ", env + cmd )
        print( "Start Build Process, Hold Tight..." )
        last_line = ""
        for line in common.run_process( env + cmd, shell="bash" ):
            print( line )
            last_line = line

        # keep track of each stages status (either True (pass) or False (fail))
        pipeline_status = exit_line is False or last_line == exit_line  # if exit line is False, ignore the exit code/line
        pipeline_statues[ stage["name"] ] = pipeline_status

        print("="*25)
        print("Pipeline stage ", stage["name"].upper(), "Complete")
        print("="*25, "="*25, sep="\n")

    print( "All Stages Complete :D" )
    print( "@AMS-PIPELINE-STATUS:", json.dumps( pipeline_statues ) )

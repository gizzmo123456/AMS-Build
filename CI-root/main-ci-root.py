#!/usr/bin/env python3
# The CI-root directory needs to mounted to /root/CI-root within the container
#

import subprocess
import common

if __name__ == "__main__":

    cmd = "cd /root/project/unityBuild;" \
          "source ./preBuild.sh;" \
          "./before_script.sh;" \
          "./build.default2.sh;"

    print(cmd)
    print("Start Build Process, Hold Tight...")

    for line in common.run_process( cmd, shell="sh" ):
        print( line )

    print( "Build Complete " )

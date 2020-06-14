#!/usr/bin/env python3
# Common function between CI-host and root.

import subprocess

def run_process( command, shell="python3" ):

    process = subprocess.Popen( [shell, '-c', command], stdout=subprocess.PIPE )

    while True:
        line = process.stdout.readline().decode( "utf-8" )
        if not line:
            break
        else:
            if line[-1:] == '\n':   # remove the new line char so we don't get double new lines :)
                line = line[:-1]
            yield line

    process.kill()
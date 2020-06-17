#!/usr/bin/env python3
# Common function between CI-host and root.

import subprocess
import json

def run_process( command, shell="python3" ):

    process = subprocess.Popen( [shell, '-c', command], stdout=subprocess.PIPE, stderr=subprocess.STDOUT )

    while True:

        line_out = process.stdout.readline().decode( "utf-8" )

        if not line_out:
            break
        elif line_out:
            yield line_out

    process.kill()

def read_file( file_name ):

    with open(file_name) as file:
        return ''.join( file.readlines() )


def get_dict_from_json( file_name ):

    return json.loads( read_file( file_name ) )
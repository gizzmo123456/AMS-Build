#!/usr/bin/env python3
# Common function between CI-host and root.

import subprocess
import json

def run_process( command, shell="python3" ):

    process = subprocess.Popen( [shell, '-c', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE )

    while True:
        line_err = process.stderr.readline().decode( "utf-8" )

        if line_err:
            yield line_err

        line_out = process.stdout.readline().decode( "utf-8" )

        if line_out:
            yield line_out

        line_in = process.stdout.readline().decode( "utf-8" )

        if line_in:
            yield line_in

        if not line_out and not line_err and not line_in:
            break

    process.kill()

def read_file( file_name ):

    with open(file_name) as file:
        return ''.join( file.readlines() )


def get_dict_from_json( file_name ):

    return json.loads( read_file( file_name ) )
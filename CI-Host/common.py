#!/usr/bin/env python3
# Common function between CI-host and root.

import subprocess
import json
from filelock import FileLock
import DEBUG
_print = DEBUG.LOGS.print

def run_process( command, shell="python3" ):

    process = subprocess.Popen( [shell, '-c', command], stdout=subprocess.PIPE, stderr=subprocess.STDOUT )

    while True:

        line_out = process.stdout.readline().decode( "utf-8" )

        if not line_out:
            break
        elif line_out:
            # remove the new line char :)
            if len(line_out) > 0 and line_out[-1] == "\n":
                line_out = line_out[:-1]

            if len(line_out) > 0 and line_out[-1] == "\r":
                line_out = line_out[:-1]

            yield line_out

    process.kill()

def read_file( file_name, lock=False ):

    lock_file = FileLock( file_name+".lock" )

    if lock:
        lock_file.acquire()

    with open(file_name) as file:
        data = ''.join( file.readlines() )

    if lock:
        lock_file.release()

    return data

def get_dict_from_json( file_name ):

    return json.loads( read_file( file_name ) )

def write_file( filepath, string, append=False, lock=True ):

    lock_file = FileLock( filepath+".lock" )
    mode = 'w'
    if append:
        mode = 'a'

    if lock:
        lock_file.acquire()

    with open( filepath, mode ) as file:
        file.write( string )

    if lock:
        lock_file.release()

def create_json_file(filepath, data):

    try:
        fwrite = json.dumps( data )
    except Exception as e:
        _print( "Bad Data", e, DEBUG.LOGS.MSG_TYPE_ERROR )
        return

    write_file( filepath, fwrite)
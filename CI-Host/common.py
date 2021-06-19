#!/usr/bin/env python3
# Common functions between host, web interface. webhook

import subprocess
import json
import os
from filelock import FileLock
import DEBUG
_print = DEBUG.LOGS.print

def installed():

    if not os.path.exists( "./data/configs/ams_path_conf.json" ):
        return False

    return True

def run_process( command, shell="python3" ): # TODO: remove. being replace with terminal.py :P

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

    if lock:
        with LockFile( file_name ) as file:
            data = ''.join( file.readlines() )
    else:
        with open(file_name) as file:
            data = ''.join( file.readlines() )

    return data


def get_dict_from_json( file_name, lock_file=False ):
    """returns json string as dict, empty if not valid"""
    try:
        return json.loads( read_file( file_name, lock_file ) )
    except Exception as e:
        _print(e, message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
        return {}


def write_file( filepath, string, append=False, lock=True ):

    mode = 'w'

    if append:
        mode = 'a'

    if lock:
        with LockFile( filepath, mode ) as file:
            file.write( string )
    else:
        with open( filepath, mode ) as file:
            file.write( string )


def create_json_file(filepath, data, lock=True):

    _print( "Dumping json data to file", filepath )

    try:
        fwrite = json.dumps( data )
    except Exception as e:
        _print( "Bad Data", e, DEBUG.LOGS.MSG_TYPE_ERROR )
        return

    write_file( filepath, fwrite, lock=lock)

    _print( "Dumped json data to file: ", filepath, "Complete" )


def get_or_create_json_file( path, file_name, default_dict ):
    """ Gets or creates project info files (info and build info)
        :return: tuple, (file created, json dict or None if path does not exist).
    """

    if not os.path.exists( path ):
        return False, None

    file_path = "{path}/{file}".format( path=path, file=file_name )

    if not os.path.exists( file_path ):
        create_json_file( file_path, default_dict )
        return True, default_dict
    else:
        return False, get_dict_from_json( file_path, lock_file=True )


def get_value_at_key( dict, *keys, noValue=None ):
    """Safely retrieves value from list of dict.
        :param dict:        the dict to retrieve the value from
        :param keys:        the keys to search for
        :param noValue:     the value to return if the key does not exist
        :return:            value at key or noValue if key does not exist
    """
    value = dict

    for key in keys:
        try:
            value = value[key]
        except:
            return noValue

    return value

class LockFile:

    def __init__( self, file_name, mode='r' ):

        self.file_name = file_name
        self.lock_file = FileLock( self.file_name + ".lock" )
        self.mode = mode

        self.file = None

    def __enter__(self):
        self.lock_file.acquire()
        self.file = open( self.file_name, self.mode )

        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()
        self.lock_file.release()
        self.file = None

class BinaryFileStream:

    def __init__( self, file_path, chunks=1024 ):

        self.error = not os.path.exists( file_path )

        self.file_path = file_path
        self.file_size = 0
        self.chunks = chunks

        if self.error:
            _print("Unable to set path for BinaryFileStream, Invalid Path (", file_path,")")
            return

        self.file_size = os.stat( file_path ).st_size       # in bytes

    def read( self ):

        if not self.error:
            with open( self.file_path, "rb" ) as f:
                byte = f.read( self.chunks )
                while byte:
                    yield byte
                    byte = f.read( self.chunks )

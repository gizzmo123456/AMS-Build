import subprocess
import threading
from flask import Flask
from flask import request

app = Flask(__name__)

builds = []
MAX_BUILDS = 1

def process(command):

    proc = subprocess.Popen( [ 'python3', '-c', 'import os;os.system( "' + command + '" )' ], stdout=subprocess.PIPE )

    while True:
        line = proc.stdout.readline().decode( "utf-8" )
        if not line:
            break
        else:
            yield line

    proc.kill()


@app.route('/')
def webhook():

    if len(builds) >= MAX_BUILDS:
        return "Unable to process build max builds reached"

    # this should be inited...
    for line in process( 'export BUILD_TARGET="StandaloneWindows"' ):
        print( line )

    print("-"*10)
    for line in process( 'printenv | grep BUILD' ):
        print( line )
    print("-"*10)

    for line in process( "/root/project/unityBuild/before_script.sh" ):
        print( line )

    # build...

    return "Build Started"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6666)

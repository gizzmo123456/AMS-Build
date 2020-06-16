import baseHTTPServer
from urllib.parse import urlparse, parse_qsl
import build_task
import json
import common

from http.server import BaseHTTPRequestHandler, HTTPServer  # this must be removed when local testing is complete


class Webhook( baseHTTPServer.BaseServer ):

    # set to main task queue
    task_queue = None

    def do_POST( self ):

        request = urlparse( self.path )
        path = request.path
        query = parse_qsl( request.query )

        content_len = int( self.headers[ 'Content-Length' ] )
        post_data = json.loads( self.rfile.read( content_len ) )

        if path != "/request":
            self.process_request( "Error: ...", 404, False )
        else:
            actor = post_data["actor"]["display_name"]
            project_request_name = post_data["repository"]
            build_hash = post_data["push"]["changes"][0]["new"]["target"]["hash"]

            Webhook.task_queue.put( build_task.BuildTask( actor, "exampleProject", build_hash ) )
            print( "Processing POST request" )

            self.process_request( "Ok", 200, False )


    def do_GET( self ):

        request = urlparse( self.path )
        path = request.path
        query = parse_qsl( request.query )

        if path != "/request":
            self.process_request("", 404, True)
        else:
            self.process_request("", 404, True)

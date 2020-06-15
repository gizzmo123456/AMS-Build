import baseHTTPServer
from urllib.parse import urlparse, parse_qsl
import build_task

from http.server import BaseHTTPRequestHandler, HTTPServer  # this must be removed when local testing is complete


class Webhook( baseHTTPServer.BaseServer ):

    # set to main task queue
    task_queue = None

    def do_POST( self ):

        request = urlparse( self.path )
        path = request.path
        query = parse_qsl( request.query )

        content_len = int( self.headers[ 'Content-Length' ] )
        post_data = self.rfile.read( content_len )

        if path != "/request":
            self.process_request( "", 404, True )
        else:
            self.process_request( "Processing GET request...", 200, True )
            Webhook.task_queue.put( build_task.BuildTask( "exampleProject", "master" ) )
            print( "Processing POST request" )
            print( post_data )

    def do_GET( self ):

        request = urlparse( self.path )
        path = request.path
        query = parse_qsl( request.query )

        if path != "/request":
            self.process_request("", 404, True)
        else:
            self.process_request("Processing GET request...", 200, True)
            Webhook.task_queue.put( build_task.BuildTask("exampleProject", "master") )
            print("Processing GET request")

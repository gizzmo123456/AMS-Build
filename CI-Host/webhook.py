import baseHTTPServer
from urllib.parse import urlparse, parse_qsl
import build_task
import json
import commonProject
import DEBUG
_print = DEBUG.LOGS.print

from http.server import BaseHTTPRequestHandler, HTTPServer  # this must be removed when local testing is complete


class Webhook( baseHTTPServer.BaseServer ):

    # set to main task queue
    task_queue = None

    def do_POST( self ):

        request = urlparse( self.path )
        path = request.path
        query = dict(parse_qsl( request.query ))

        content_len = int( self.headers[ 'Content-Length' ] )
        post_data = json.loads( self.rfile.read( content_len ) )

        if path != "/request" and "name" not in query or "project" not in query:
            self.process_request( "Error", 404, False )
            _print( "Bad weebhoock request, maybe name or project not set?" )
        elif not commonProject.project_exist( query["project"] ):
            self.process_request( "Error", 404, False )
            _print( "Bad webhook request, Project does not exist" )
        else:
            actor = post_data["actor"]["display_name"]
            repo_name = post_data["repository"]
            build_hash = post_data["push"]["changes"][0]["new"]["target"]["hash"]

            task = build_task.BuildTask( actor, query["project"], build_hash,
                                         webhook=True, webhook_name=query["name"] )

            if task.valid:
                Webhook.task_queue.put( task )
                _print( "Processing POST request" )
            else:
                _print( "Invalid task")

            self.process_request( "Ok", 200, False )


    def do_GET( self ):

        request = urlparse( self.path )
        path = request.path
        query = parse_qsl( request.query )

        if path != "/request":
            self.process_request("", 404, True)
        else:
            self.process_request("", 404, True)

import baseHTTPServer
from urllib.parse import urlparse, parse_qsl
import build_task
import json
import common
import commonProject
import DEBUG
_print = DEBUG.LOGS.print

from http.server import BaseHTTPRequestHandler, HTTPServer  # this must be removed when local testing is complete


class Webhook( baseHTTPServer.BaseServer ):

    # set to main task queue
    task_queue = None

    def do_POST( self ):

        _print("Processing Webhook :)")
        request = urlparse( self.path )
        path = request.path
        query = dict(parse_qsl( request.query ))

        content_len = int( self.headers[ 'Content-Length' ] )
        post_data = json.loads( self.rfile.read( content_len ) )

        if path != "/request" and "name" not in query or "project" not in query:
            self.process_request( "Error", 404, False )
            _print( "Bad webhook request, maybe name or project not set?", message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
        elif not commonProject.project_exist( query["project"] ):
            self.process_request( "Error", 404, False )
            _print( "Bad webhook request, Project does not exist", message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
        else:
            actor = post_data["actor"]["display_name"]
            repo_name = post_data["repository"]
            build_hash = post_data["push"]["changes"][0]["new"]["target"]["hash"]

            # check the request is defined within the projects webhook config in pipeline
            pipeline = commonProject.get_project_pipeline( query[ "project" ] )

            if pipeline is None:
                _print( "Error: Invalid project, No pipeline found for project ", query[ "project" ], message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
                return

            webhook_name = common.get_value_at_key( pipeline, "webhook", "name" )
            authorized_actor = common.get_value_at_key( pipeline, "webhook", "authorized-actor" )

            if webhook_name != query[ "name" ]:
                _print("Error, Webhook not defined for project ", query[ "project" ], message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
                return

            if authorized_actor is None:
                _print( "Error: No actors defined, for project ", query[ "project" ], message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
                return
            elif actor not in authorized_actor:
                _print( "Error: Invalid actor, for project ", query[ "project" ], message_type=DEBUG.LOGS.MSG_TYPE_ERROR  )
                return

            task = build_task.BuildTask( actor, query["project"], build_hash, webhook=True )

            Webhook.task_queue.put( task )
            _print( "Valid task. Tasked queued" )

            self.process_request( "Ok", 200, False )

    def do_GET( self ):

        request = urlparse( self.path )
        path = request.path
        query = parse_qsl( request.query )

        if path != "/request":
            self.process_request("", 404, True)
        else:
            self.process_request("", 404, True)

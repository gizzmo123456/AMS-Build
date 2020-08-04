import baseHTTPServer
from urllib.parse import urlparse, parse_qsl
import user_access_control
import json
import common
import commonProject
import DEBUG
_print = DEBUG.LOGS.print


class Webhook( baseHTTPServer.BaseServer ):

    # set to main task queue
    shared_task_queue = None


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
        else:
            actor = post_data["actor"]["display_name"]
            repo_name = post_data["repository"]
            build_hash = post_data["push"]["changes"][0]["new"]["target"]["hash"]

            uac = user_access_control.UAC( actor, user_access_control.UAC.WEBHOOK )

            # check the request is defined within the projects webhook config in pipeline
            # and the actor has access
            pipeline = commonProject.get_project_pipeline( uac, query[ "project" ] )

            if pipeline is None:
                _print( "Error: Invalid project or Access, For project ", query[ "project" ], message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
                self.process_request( "Error", 404, False )
                return

            webhook_name = common.get_value_at_key( pipeline, "webhook", "name" )

            if webhook_name != query[ "name" ]:
                _print("Error, Webhook (", query["name"],") not defined for project ", query[ "project" ], message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
                self.process_request( "Error", 404, False )
                return

            Webhook.shared_task_queue.queue_task( "build", uac=uac, project=query["project"], build_hash=build_hash )

            self.process_request( "Ok", 200, False )

    def do_GET( self ):

        request = urlparse( self.path )
        path = request.path
        query = parse_qsl( request.query )

        if path != "/request":
            self.process_request("", 404, True)
        else:
            self.process_request("", 404, True)

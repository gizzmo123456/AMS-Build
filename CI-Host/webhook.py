import baseHTTPServer
from urllib.parse import urlparse, parse_qsl
import user_access_control
import json
import common
import commonProject
import config_manager
import DEBUG
_print = DEBUG.LOGS.print


class Webhook( baseHTTPServer.BaseServer ):

    # set to main task queue
    shared_task_queue = None

    ROOT = config_manager.ConfigManager.get("web_root", "ams-build")
    # Remove any outer slashes
    if ROOT[1] == "/":
        ROOT = ROOT[1:]
    if ROOT[-1] == "/":
        ROOT = ROOT[:-1]

    def do_POST( self ):

        _print("Processing Webhook :)")
        request = urlparse( self.path )
        path = request.path
        query = dict(parse_qsl( request.query ))

        content_len = int( self.headers[ 'Content-Length' ] )
        content_str = self.rfile.read( content_len )
        post_data = json.loads( content_str )

        if path != f"/{Webhook.ROOT}/request" or "name" not in query or "project" not in query:
            self.process_request( "Error", 404, False )
            _print( "Bad webhook request, maybe name or project not set?", message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
        else:

            # _print("WH DATA IN: ", content_str )
            fields = commonProject.get_project_webhook_fields( query["project"] )

            # bit bucket give us an option to test the connection.
            test_conn = common.get_value_at_key( post_data, *fields["test"] )
            if test_conn is not None and test_conn:
                self.process_request( "Ok", 200, False )
                return

            # Get required data from post data.
            actor = common.get_value_at_key( post_data     , *fields["actor"] )
            repo_name = common.get_value_at_key( post_data , *fields["repository"] )
            branch = common.get_value_at_key( post_data    , *fields["branch"] )   # TODO: dont forget to check the data.
            build_hash = common.get_value_at_key( post_data, *fields["hash"] )

            if actor is None or repo_name is None or build_hash is None or branch is None:
                _print("Invalid Webhook Data Supplied", message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
                _print( f"Data Actor: {actor is not None} Repo: {repo_name is not None} Hash {build_hash is not None} Branch {branch is not None}", message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
                self.process_request( "Error", 404, False )
                return

            # we must set the sub name, so we can check that the actor belongs to webhook of name for project
            uac = user_access_control.UAC( actor, user_access_control.UAC.WEBHOOK, query["name"] )

            # check the request is defined within the projects webhooks config
            # and the git actor has access
            webhook_config = commonProject.get_project_config( uac, query[ "project" ], "webhooks" )

            if webhook_config is None:
                _print( "Error: Invalid project or Access, For project ", query[ "project" ], message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
                self.process_request( "Error", 404, False )
                return

            webhooks = common.get_value_at_key( webhook_config, "in-webhooks", noValue=[] )
            webhook_repo = None
            webhook_branch = None
            webhook_actors = None

            # find if the webhook is defined for project and that the git actor has access
            for whi in range( len(webhooks) ):
                webhook_name = common.get_value_at_key( webhook_config, "in-webhooks", whi,  "name" )

                if webhook_name == query[ "name" ]:
                    webhook_repo = common.get_value_at_key( webhook_config  , "in-webhooks", whi, "repository" )
                    webhook_branch = common.get_value_at_key( webhook_config, "in-webhooks", whi, "branch" )
                    webhook_actors = common.get_value_at_key( webhook_config, "in-webhooks", whi, "authorized-actors" )
                    break

            if repo_name != webhook_repo:
                _print("Error, Unreconzied repo has trigger webhook for project", query[ "project" ], message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
                self.process_request( "Error", 404, False )
                return

            # TODO. same for branch

            if webhook_actors is None:
                _print("Error, Webhook (", query["name"],") not defined for project ", query[ "project" ], message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
                self.process_request( "Error", 404, False )
                return
            elif actor not in webhook_actors:
                _print( "Error: Invalid actor (", actor, "), for project ", query[ "project" ], message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
                self.process_request( "Error", 404, False )
                return

            Webhook.shared_task_queue.queue_task( "build", uac=uac, project=query["project"], git_hash=build_hash )

            self.process_request( "Ok", 200, False )

    def do_GET( self ):

        request = urlparse( self.path )
        path = request.path
        query = parse_qsl( request.query )

        if path != "/request":
            self.process_request("", 404, True)
        else:
            self.process_request("", 404, True)

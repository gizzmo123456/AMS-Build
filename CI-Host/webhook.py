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
    job_queue = None

    ROOT = config_manager.ConfigManager.get("web_root", "ams-build")
    # Remove any outer slashes
    if ROOT[1] == "/":
        ROOT = ROOT[1:]
    if ROOT[-1] == "/":
        ROOT = ROOT[:-1]

    def do_POST( self ):

        activity_log_filepath = commonProject.get_activity_log_path(None)

        _print(f"Received Webhook. (path: {self.path})", output_filename=activity_log_filepath )

        request = urlparse( self.path )
        path = request.path
        query = dict(parse_qsl( request.query ))

        content_len = int( self.headers[ 'Content-Length' ] )
        content_str = self.rfile.read( content_len )
        post_data = json.loads( content_str )

        if path != f"/{Webhook.ROOT}/request" or "name" not in query or "project" not in query:
            self.process_request( "Error", 404, False )
            _print( f"Bad webhook request (path: {self.path}). Invalid Path, name or project",
                    message_type=DEBUG.LOGS.MSG_TYPE_ERROR,
                    output_filename=activity_log_filepath )
        else:

            # attempt to redirect the activity log to the projects activity log (if exist)
            activity_log_filepath = commonProject.get_activity_log_path(query["project"])
            _print("Webhook POST data: ", content_str, output_filename=activity_log_filepath, console=False )

            fields = commonProject.get_project_webhook_fields( query["project"] )

            # bit bucket give us an option to test the connection.
            test_conn = common.get_value_at_key( post_data, *fields["test"] )
            if test_conn is not None and test_conn:
                self.process_request( "Ok", 200, False )
                _print("Webhook: Test connection successful ", output_filename=activity_log_filepath, console=False)
                return

            # Get required data from post data.
            actor = common.get_value_at_key( post_data     , *fields["actor"] )
            repo_name = common.get_value_at_key( post_data , *fields["repository"] )
            branch = common.get_value_at_key( post_data    , *fields["branch"] )    # TODO: dont forget to check the data.
            build_hash = common.get_value_at_key( post_data, *fields["hash"] )      # TODO: rename to git hash

            if actor is None or repo_name is None or build_hash is None or branch is None:
                _print("Webhook: required data not supplied",
                       message_type=DEBUG.LOGS.MSG_TYPE_ERROR,
                       output_filename=activity_log_filepath,
                       console=False )
                self.process_request( "Error", 404, False )
                return

            # we must set the sub name, so we can check that the actor belongs to webhook of name for project
            uac = user_access_control.UAC( actor, user_access_control.UAC.WEBHOOK, query["name"] )

            # check the request is defined within the projects webhooks config
            # and the git actor has access
            webhook_config = commonProject.get_project_config( uac, query[ "project" ], "webhooks" )

            if webhook_config is None:
                _print( f"Webhook: Invalid project or Access. Project: { query[ 'project' ] } | Actor: { actor }",
                        message_type=DEBUG.LOGS.MSG_TYPE_ERROR,
                        output_filename=activity_log_filepath,
                        console=False )
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
                _print("Webhook:, Unrecognized repo has trigger webhook for project", query[ "project" ],
                       message_type=DEBUG.LOGS.MSG_TYPE_ERROR,
                       output_filename=activity_log_filepath,
                       console=False )
                self.process_request( "Error", 404, False )
                return

            if branch != webhook_branch:
                _print( f"Webhook: triggered by incorrect branch ({webhook_branch} != {branch}). Project: {query[ 'project' ]}",
                        message_type=DEBUG.LOGS.MSG_TYPE_WARNING,
                        output_filename=activity_log_filepath,
                        console=False )
                self.process_request( "Error", 404, False )
                return

            if webhook_actors is None:
                _print("Webhook: name (", query["name"],") not defined for project ", query[ "project" ],
                       message_type=DEBUG.LOGS.MSG_TYPE_ERROR,
                       output_filename=activity_log_filepath,
                       console=False )
                self.process_request( "Error", 404, False )
                return
            elif actor not in webhook_actors:
                _print( "Webhook: Invalid actor (", actor, "), for project ", query[ "project" ],
                        message_type=DEBUG.LOGS.MSG_TYPE_ERROR,
                        output_filename=activity_log_filepath,
                        console=False )
                self.process_request( "Error", 404, False )
                return

            Webhook.job_queue.create_jobs_from_pipeline( uac, query["project"] ) #, branch=branch, git_hash=build_hash )

            self.process_request( "Ok", 200, False )

    def do_GET( self ):

        request = urlparse( self.path )
        path = request.path
        query = parse_qsl( request.query )

        _print(f"Webhook: No data supplied (path: {self.path})",
               message_type=DEBUG.LOGS.MSG_TYPE_ERROR,
               output_filename=commonProject.get_activity_log_path(None),
               console=False)

        if path != "/request":
            self.process_request("", 404, True)
        else:
            self.process_request("", 404, True)

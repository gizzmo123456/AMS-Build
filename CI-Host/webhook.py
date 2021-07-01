import baseHTTPServer
from urllib.parse import urlparse, parse_qsl
import user_access_control
import json
import common
import commonProject
import config_manager
import jobs.job_queue as job_queue
import DEBUG
_print = DEBUG.LOGS.print


class Webhook( baseHTTPServer.BaseServer ):

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

            fields = commonProject.get_project_webhook_fields( query["project"] )

            # bit bucket give us an option to test the connection.
            test_conn = common.get_value_at_key( post_data, *fields["test"] )
            if test_conn is not None and test_conn:
                self.process_request( "Ok", 200, False )
                return

            hook_name = query["name"]
            project = query["project"]

            # Get required data from post data.
            actor = common.get_value_at_key( post_data     , *fields["actor"] )
            repo_name = common.get_value_at_key( post_data , *fields["repository"] )
            branch = common.get_value_at_key( post_data    , *fields["branch"] )
            git_hash = common.get_value_at_key( post_data  , *fields["hash"] )

            if actor is None or repo_name is None or git_hash is None or branch is None:
                _print("Invalid Webhook Data Supplied", message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
                self.process_request( "Error", 404, False )
                return

            # we must set the sub name, so we can check that the actor belongs to webhook of name for project
            uac = user_access_control.UAC( actor, user_access_control.UAC.TRIGGER, origin="webhook" )
            uac.set_webhook(hook_name, actor, branch, repo_name)

            if not uac.has_project_access( project ):
                _print( f"Webhook does not have access to the requested project '{project}'", message_type=DEBUG.LOGS.MSG_TYPE_WARNING )
                self.process_request( "Error", 404, False )
                return

            #Webhook.shared_task_queue.queue_task( "build", uac=uac, project=query["project"], git_hash=build_hash )
            job_queue.JobQueue.create_jobs_from_pipeline( uac, query["project"],
                                                          git_repo_name=repo_name,
                                                          git_branch=branch,
                                                          git_commit_hash=git_hash )

            self.process_request( "Ok", 200, False )

    def do_GET( self ):

        request = urlparse( self.path )
        path = request.path
        query = parse_qsl( request.query )

        if path != "/request":
            self.process_request("", 404, True)
        else:
            self.process_request("", 404, True)

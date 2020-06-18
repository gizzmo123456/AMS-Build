import threading
import baseHTTPServer
from urllib.parse import urlparse, parse_qsl
import json
import common
import os
from const import *


class WebInterface( baseHTTPServer.BaseServer ):
    """
        Request types: GET | POST
        Pages:                                                          (GET only)
            ams-ci /                                                    [Root]
            ams-ci / project /                                          [retrieves list of projects available to user]
            ams-ci / project / {project_name}                           [retrieves list of builds for project name]
            ams-ci / project / {project_name} / {build_hash}            [retrieves list of data for build]
            ams-ci / project / {project_name} / {build_hash} / log      [retrieves log for build]
            ams-ci / project / {project_name} / {build_hash} / dl       [downloads build]
        Get params:
            data_type:  (default) HTML | Json
        Pages:                                                          (POST only)
            ams-ci / auth                                               [Authorizes user]
    """

    def init( self ):
        self.thr_lock_update_tasks = threading.Lock()

        # TODO: theses should be dicts for json
        self.active_builds = ""
        self.queued_tasks = ""

        self.sessions = {}      # { session key: tuple ( expires, data {} )

    def do_POST( self ):

        request = urlparse( self.path ).split("/")  # ams-ci /
        path = request.path
        query = dict(parse_qsl( request.query ))

        content_len = int( self.headers[ 'Content-Length' ] )
        post_data = json.loads( self.rfile.read( content_len ) )

        if len( request ) > 0 and request[0].lowwer() == "auth":
            self.process_request( "Helloo World", 200, False )
        else:
            self.process_request( "I'm Lost", 404, False )

    def do_GET( self ):

        request = urlparse( self.path ).split("/")  # ams-ci /
        path = request.path
        query = parse_qsl( request.query )

        if len(request) == 0 or request[1].lower() != "ams-ci":
            page = "I'm Lost!"
            page_status = 404
            page_content = {}
        elif len( request ) == 2 and request[1] == "style.css":
            page = self.read_page( "stylesheet", 0 )
            page_status = 200
            page_content = {}
        else:
            page = self.read_page("index", self.get_user_access_level( "g43gdGFwe45ggsd34FG43qtgfrea32gds43" ))
            page_status = 200
            page_content = { "active_tasks": "No Active Task", "queued_tasks": "No Queued Tasks", "projects": "No Projects Available", "builds": "Select a Project to view available builds"}

        self.process_request( page.format( **page_content ), page_status, True )

    def get_user_access_level( self, sess_id ):
        """
            Access levels:
                0: No Access
                1: Default Access
        """
        if sess_id not in self.sessions:
            return 0
        else:
            return 1

    def read_page( self, page_name, user_access_level ):

        root = "./www/"
        pages = { "index": ("index.html", 1), "auth": ("login.html", 0), "stylesheet": ("defaul.css", 0) }   # (page, access level)
        no_access = pages["auth"][0]

        if page_name in pages and user_access_level >= pages[page_name][1]:
            page_to_load = pages[page_name]
        else:
            page_to_load = no_access

        return common.read_file( root + page_to_load )

    def list_projects( self ):
        """ returns list of projects dict { "name": pname }
            Json Friendly
        """
        return [ {"name": directory}
                 for directory in os.listdir( PROJECT_DIRECTORY )
                 if os.path.isdir( os.path.join( PROJECT_DIRECTORY, directory ) ) ]

    def list_builds( self, project ):
        """ dict { "project": { "name": pname, builds: list [ {"name": bname, "status" : status, "created_by": user, "link": url} ] } }
            Json Friendly
        """
        return { "project":
                     { "name": project,
                       "builds": [
                           {"name": build_name}
                           for build_name in os.listdir( PROJECT_DIRECTORY+"/builds" )
                           if os.path.isdir( os.path.join( PROJECT_DIRECTORY+"/builds", build_name ) ) ] } }

    def update_tasks( self, active_tasks, queued_tasks ):
        """ Updates the tasks string,
            This should be called from the same thread that is using the list

        :param active_tasks:    list of active tasks
        :param queued_tasks:    list of queued tasks
        :return:
        """

        if len(active_tasks) == 0:
            active_tasks_str = "None"
        else:
            active_tasks_str = '<br />'.join( [ "{project} - {build_hash} - created @ {created} - By {actor}".format( **task[1].format_values ) for task in active_tasks ] )

        if len(queued_tasks) == 0:
            queued_tasks_str = "None"
        else:
            queued_tasks_str = '<br />'.join( [ "{project} - {build_hash} - created @ {created} - By {actor}".format( **task.format_values ) for task in queued_tasks ] )

        self.thr_lock_update_tasks.acquire()
        self.active_builds = active_tasks_str
        self.queued_tasks = queued_tasks_str
        self.thr_lock_update_tasks.release()


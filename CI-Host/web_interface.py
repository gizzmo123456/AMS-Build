import threading
import baseHTTPServer
from http.cookies import SimpleCookie
from urllib.parse import urlparse, parse_qsl
import json
import common
import os
from const import *
import hashlib
import time
from www_page import WWWPage, WWWUser
import math

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
    DEFAULT_SESSION_LENGTH = 60 * 60 # 1hr

    UAC_NO_AUTH = 0
    UAC_USER    = 1
    UAC_MOD     = 2
    UAC_ADMIN   = 3

    def __init__( self, request, client_address, server ):

        self.thr_lock_update_tasks = threading.Lock()
        self.thr_lock_session_id = threading.Lock()

        self.pages = { }
        self.pages["not_found"] = WWWPage( "not_found",  "not_found.html",   404, None                                               )
        self.pages["auth"]      = WWWPage( "auth",       "login.html",       200, self.auth_user_content                             )
        self.pages["index"]     = WWWPage( "index",      "index.html",       200, None,                      1, self.pages["auth"]   )
        self.pages["content"]   = WWWPage( "content",    "",                 200, None,                      1, self.pages["auth"]   )


        # TODO: theses should be dicts for json
        self.active_builds = ""
        self.queued_tasks = ""

        self.sessions = {}      # { `session key`: `WWWUser` }

        super().__init__(request, client_address, server)   # this MUST be called at the end otherwise the others vars don't initialize

    def do_POST( self ):

        self.do_request( False )

    def do_GET( self ):

        self.do_request( True )

    def do_request( self, GET=True ):

        request = urlparse( self.path )
        path = request.path.split( "/" )  # ams-ci /
        path.pop(0)                       # remove the first element, as every path starts with `/` so the first is always empty

        cookie_data = SimpleCookie( self.headers.get('Cookie') )
        get_data = dict( parse_qsl( request.query ) )
        post_data = {}

        session_id = None
        user = WWWUser()

        if "session_id" in cookie_data:
            session_id = cookie_data[session_id].value
            if session_id in self.sessions:
                user = self.sessions[session_id]

        if not GET:
            content_len = int( self.headers[ 'Content-Length' ] )
            post_data = dict( parse_qsl( self.rfile.read( content_len ).decode("utf-8") ) )

        output_page, status = self.get_page( path, user, get_data, post_data )

        self.process_request( output_page, status, GET, user.cookies )

    def get_page( self, requested_path, user, get_data, post_data ):
        """ returns tuple (name of page template, status, content callback)
            All function require uac, get and post data params and must return final page, json content (as dict)
        """
        page = self.pages["not_found"]
        path_len = len( requested_path )

        if type( requested_path ) is list and path_len > 0:

            if requested_path[0].lower() == "ams-ci":
                if path_len > 1:              # content request (html or json)
                    page = self.pages["content"]
                else:
                    page = self.pages["index"]

        return page.load_page(user, requested_path, get_data, post_data)

    def auth_user_content( self, user, request_path, get_data, post_data ):
        """ returns redirect page, content """

        print( "Auth User..." )
        if not user.authorized() and "user" in post_data and "password" in post_data:
            if post_data["user"] == "admin" and post_data["password"] == "password!2E":
                # auth user
                sess_id = hashlib.md5( math.floor(time.time() * 1000).to_bytes(16, "big") ).hexdigest()

                while sess_id in self.sessions: # ensure that the new session id is unique
                    sess_id = hashlib.md5( math.floor(time.time() * 1000).to_bytes( 16, "big" ) ).hexdigest()

                user.set_cookie("session_id", sess_id)
                user.access_level = self.UAC_USER
                self.sessions[ sess_id ] = user

                # queue the session expiry
                threading.Thread( target=self.expire_session, args=( sess_id, self.DEFAULT_SESSION_LENGTH )).start()

                return self.pages["index"], {"message", "login successful :)"}  # redirect content

        return None, {"message": "Invalid Login"}

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

    def expire_session( self, session_id, ttl ):

        while session_id in self.sessions:
            time.sleep( ttl )
            self.thr_lock_session_id.acquire()

            if time.time() < session_id[ session_id ][0]:
                ttl = self.sessions[ session_id ][0] - time.time()
            else:
                del self.sessions[session_id]

            self.thr_lock_session_id.release()
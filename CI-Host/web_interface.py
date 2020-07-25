import threading
import baseHTTPServer
from http.cookies import SimpleCookie
from http import HTTPStatus
from urllib.parse import urlparse, parse_qsl, unquote
import json
import common
import os
from const import *
import hashlib
import time
from www_page import WWWPage, WWWUser
import math

class WebInterface( baseHTTPServer.BaseServer ):
    """ TODO: doc string needs updating
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
    API_ROOT_PATH_LENGTH = 2    # TODO. the could do with a new name, its used for API, login, CSS, JS and DL paths...

    UAC_NO_AUTH = 0
    UAC_USER    = 1
    UAC_MOD     = 2
    UAC_ADMIN   = 3

    sessions = { }  # { `session key`: `WWWUser` }

    def __init__( self, request, client_address, server ):

        self.thr_lock_update_tasks = threading.Lock()
        self.thr_lock_session_id = threading.Lock()

        self.pages = { }
        self.pages["not_found"] = WWWPage( "not_found",  "not_found.html",   404, None                                               )
        self.pages["auth"]      = WWWPage( "auth",       "login.html",       200, self.auth_user_content                             )
        self.pages["index"]     = WWWPage( "index",      "index.html",       200, self.index_content,        1, self.pages["auth"]   )

        # API html templates, use GET param 'template={template name}' to format json data into a html template.
        # if template is 'none' or not supplied, the raw json is returned
        self.pages["api"] = {}
        self.pages["api"]["raw"]            = WWWPage( "api-raw",          None,                         200, self.api_content, 1, self.pages["auth"] )
        self.pages["api"]["active_task"]    = WWWPage( "api-active-tasks", "api-templates/active_task.html",    200, self.api_content, 1, self.pages["auth"], "No Active Tasks" )
        self.pages["api"]["queued_task"]    = WWWPage( "api-queue-tasks",  "api-templates/queued_task.html",    200, self.api_content, 1, self.pages["auth"], "No Queued Tasks" )
        self.pages["api"]["projects"]       = WWWPage( "api-projects",     "api-templates/project.html", 200, self.api_content, 1, self.pages["auth"], "No Projects" )
        self.pages["api"]["builds"]         = WWWPage( "api-builds",       "api-templates/build.html",   200, self.api_content, 1, self.pages["auth"], "No Builds Found" )

        # TODO: theses should be dicts for json
        self.active_builds = ""
        self.queued_tasks = ""

        super().__init__(request, client_address, server)   # this MUST be called at the end otherwise the others vars don't initialize

    def do_POST( self ):

        self.do_request( False )

    def do_GET( self ):

        self.do_request( True )

    def do_request( self, GET=True ):

        request = urlparse( unquote( self.path ) )
        path = request.path.split( "/" )  # ams-ci /
        path = [ p for p in path if p != "" ]                       # remove the empties

        cookie_data = SimpleCookie( self.headers.get('Cookie') )

        get_data = dict( parse_qsl( request.query ) )
        post_data = {}

        session_id = None
        user = WWWUser()

        print("mmmmmmmmmmmmm cookies: ", cookie_data)

        if "session_id" in cookie_data:
            session_id = cookie_data["session_id"].value
            if session_id in self.sessions:
                user = self.sessions[session_id]
                print("user authorized via session cookie")

        if not GET:
            content_len = int( self.headers[ 'Content-Length' ] )
            post_data = dict( parse_qsl( self.rfile.read( content_len ).decode("utf-8") ) )

        output_page, status, content_type = self.get_page( path, user, get_data, post_data )

        self.process_request( output_page, status, GET, user.cookies, content_type )

    def get_page( self, requested_path, user, get_data, post_data ):
        """ returns tuple (name of page template, status, content callback)
            All function require uac, get and post data params and must return final page, json content (as dict)
        """
        page = self.pages["not_found"]
        path_len = len( requested_path )
        content_type = "text/html"

        if type( requested_path ) is list and path_len > 0:

            if requested_path[0].lower() == "ams-ci":
                if path_len >= self.API_ROOT_PATH_LENGTH:              # content request (html or json)
                    if requested_path[1] == "style.css":
                        return common.read_file( "./www/default.css" ), 200, "text/css"
                    elif len(requested_path) >= self.API_ROOT_PATH_LENGTH+1 and requested_path[1] == "js":
                        try:
                            return common.read_file("./www/js/{page}".format( page='/'.join( requested_path[2:] ) )), HTTPStatus.OK, "text/javascript"
                        except:
                            return "Error", HTTPStatus.NOT_FOUND, "text/html"
                    elif requested_path[1] == "logout":
                        if user.session_id in self.sessions:
                            del self.sessions[ user.session_id ]
                            user.session_id = ""
                            user.set_access_level(0)
                        page = self.pages[ "index" ]
                    elif requested_path[1] == "api":
                        page = self.pages["api"]["raw"]
                        content_type = "application/json"
                        if "template" in get_data:
                            content_type = "text/html"
                            if get_data["template"] in self.pages["api"]:
                                page = self.pages["api"][ get_data["template"] ]
                            else:
                                page = self.pages["not_found"]
                else:
                    page = self.pages["index"]

        content, status = page.load_page(user, requested_path, get_data, post_data)
        return content, status, content_type

# www_page callbacks

    def auth_user_content( self, user, request_path, get_data, post_data ):
        """ returns redirect page, content """

        if not user.authorized() and "user" in post_data and "password" in post_data:
            if post_data["user"] == "admin" and post_data["password"] == "password!2E":
                # auth user
                sess_id = hashlib.md5( math.floor(time.time() * 1000).to_bytes(16, "big") ).hexdigest()

                while sess_id in self.sessions: # ensure that the new session id is unique
                    sess_id = hashlib.md5( math.floor(time.time() * 1000).to_bytes( 16, "big" ) ).hexdigest()

                user.set_cookie("session_id", sess_id, path="/ams-ci" )
                user.session_id = sess_id
                user.set_access_level( self.UAC_USER )
                self.sessions[ sess_id ] = user

                # queue the session expiry
                # threading.Thread( target=self.expire_session, args=( sess_id, self.DEFAULT_SESSION_LENGTH )).start()

                return self.pages["index"], {"message": "login successful :)"}  # redirect content

        return None, {"message": "Invalid Login"}

    def index_content( self, user, request_path, get_data, post_data):

        page_content = {
            "active_tasks": self.get_api_content(user, ["tasks", "active"], "active_task", "No Active Tasks"),
            "queued_tasks": self.get_api_content(user, ["tasks", "pending"], "queued_task", "No Queued Tasks"),
            "projects": self.get_api_content(user, ["projects"], "projects", "No Projects"),
            "builds": "Select a project to view available builds",
            "selected_project": "[None Selected]"
        }

        return None, page_content

    def api_content( self, user, request_path, get_data, post_data):
        """ Gets the json data for api path.
            Path format. /ams-ci/api/{api-path}
            api-paths:
            /projects                        returns all projects  (from projects.json)
            /tasks                           returns all queue and active tasks (from tasks.json)
            ===========================
            The path following '/project' or '/task' filters the data in a linear fashion. starting at root
            The path must be the keys in json file, if the key returns a list, then it returns a list
            for keys=value
            ie.
            path:
            /projects                                                           -> a list of all projects
            /projects/name/{name}                                               -> if >1 project is found a list of projects otherwise a dict with the project info
            /projects/name/{name}/builds                                        -> same as above, except only build data
            /projects/name/{name}/builds/name/{name}                            -> same as above, except only builds with name {name}
            /projects/name/{name}/builds/created_by/ashley sands/status/failed  -> would return all builds in project that where create by ashley sands that failed

        """
        # remove the root from the request path, make it all lower
        request = [ r.lower() for r in request_path[self.API_ROOT_PATH_LENGTH:] ]
        request_length = len( request )
        data = {}
        print("API REQUEST: ", request)

        if request_length > 0:
            if request[0] == "projects" or request[0] == "project":
                data = common.get_dict_from_json("./data/projects.json")
            elif request[0] == "tasks":
                data = common.get_dict_from_json("./data/tasks.json")
            else:
                data = { "status": 404, "message": "Data not found in api (Request: {request}) :(".format( request='/'.join( request ) ) }
                request_length = 0  # set the request length to zero to avoid filtering
        else:
            data = {"status": 404, "message": "Data not found in api (No Data Requested) :("}
            request_length = 0  # set the request length to zero to avoid filtering

        # filter the data.
        filter_key = None
        if request_length > 1:
            for f in request[1:]:
                if isinstance( data, dict ):
                    if f in data:
                        data = data[f]
                    else:
                        data = {}
                        break
                elif isinstance( data, list ):
                    if filter_key is None:
                        # remove all elements that do not have a key of f
                        for i in range( len(data)-1, -1, -1 ):
                            if f not in data[i]:
                                data.pop(i)
                        filter_key = f
                    else:
                        # remove all elements where filter_key value does not equal f
                        for i in range( len(data)-1, -1, -1 ):
                            if data[i][filter_key] != f:
                                data.pop(i)
                        if len(data) == 1:      # it no longer needs to be a list :)
                            data = data[0]
                        elif len(data) == 0:    # no data left to filter :)
                            data = []
                            break
                        filter_key = None

        return None, data

# end of www_page callbacks

    def get_api_content( self, user, request_path, template, default_message ):
        """ Use to get the API content locally
            `Request path` is the json filtering, see path in api_content for more info
        """

        if template not in self.pages["api"]:
            print("Error: template not found")
            return "Error: Template not found"

        # we must add elements to make up the pre API path, as they are removed, in api_content
        # if not we have a invalid request.
        pre_path_path = [""] * self.API_ROOT_PATH_LENGTH

        content, status = self.pages["api"][ template ].load_page(user, pre_path_path + request_path, [], [])

        return content

# Is any of this used
# i think this was all replaced by the use of projects.json

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

# End of is used?

    def expire_session( self, session_id, ttl ):    # Note the use has been commented out

        while session_id in self.sessions:
            time.sleep( ttl )
            self.thr_lock_session_id.acquire()

            if time.time() < session_id[ session_id ][0]:
                ttl = self.sessions[ session_id ][0] - time.time()
            else:
                del self.sessions[session_id]

            self.thr_lock_session_id.release()
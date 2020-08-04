import threading
import baseHTTPServer
from http.cookies import SimpleCookie
from http import HTTPStatus
from urllib.parse import urlparse, parse_qsl, unquote
import json
import common
import commonProject
import os
from const import *
import hashlib
import time
from www_page import WWWPage, WWWUser
import user_manager
import math

import DEBUG
_print = DEBUG.LOGS.print

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
    API_ROOT_PATH_LENGTH = 2    # TODO. the could do with a new name, its used for API, login, CSS, JS, DL and output log paths...

    sessions = { }  # { `session key`: WWWUser }
    shared_queue = None

    def __init__( self, request, client_address, server ):

        self.thr_lock_update_tasks = threading.Lock()
        self.thr_lock_session_id = threading.Lock()

        self.pages = { }

        self.pages["not_found"] = WWWPage( "not_found",  "error_page.html", self.not_found_callback )
        self.pages["auth"]      = WWWPage( "auth",       "login.html",      self.auth_user_content )
        self.pages["logout"]    = WWWPage( "logout",      None,             self.logout_callback )
        self.pages["index"]     = WWWPage( "index",      "index.html",      self.index_content,      WWWUser.UAC_USER, self.pages["auth"] )

        # API html templates, use GET param 'template={template name}' to format json data into a html template.
        # if template is 'none' or not supplied, the raw json is returned

        self.pages["api"] = {}
        self.pages["api"]["raw"]           = WWWPage( "api-raw",           None,                                self.api_content, WWWUser.UAC_USER, self.pages["auth"], no_content_template=None )
        self.pages["api"]["message"]       = WWWPage( "api-user-messages", "api-templates/message.html",        self.api_content, WWWUser.UAC_USER, self.pages["auth"], no_content_template=None )
        self.pages["api"]["active_task"]   = WWWPage( "api-active-tasks",  "api-templates/active_task.html",    self.api_content, WWWUser.UAC_USER, self.pages["auth"], "No Active Tasks"        )
        self.pages["api"]["queued_task"]   = WWWPage( "api-queue-tasks",   "api-templates/queued_task.html",    self.api_content, WWWUser.UAC_USER, self.pages["auth"], "No Queued Tasks"        )
        self.pages["api"]["projects"]      = WWWPage( "api-projects",      "api-templates/project.html",        self.api_content, WWWUser.UAC_USER, self.pages["auth"], "No Projects"            )
        self.pages["api"]["builds"]        = WWWPage( "api-builds",        "api-templates/build.html",          self.api_content, WWWUser.UAC_USER, self.pages["auth"], "No Builds Found"        )
        self.pages["api"]["builds"].list_order = WWWPage.LO_DESC    # display newest build on top

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

        if "session_id" in cookie_data:
            session_id = cookie_data["session_id"].value
            if session_id in self.sessions:
                user = self.sessions[session_id]
                _print("user authorized via session cookie")

        if not GET:
            content_len = int( self.headers[ 'Content-Length' ] )
            post_data = dict( parse_qsl( self.rfile.read( content_len ).decode("utf-8") ) )

        page = self.get_page( path, user, get_data, post_data )

        output_page = "404 Not Found"
        status = HTTPStatus.NOT_FOUND
        content_type = "text\html"
        headers = None

        if len( page ) == 3:
            output_page, status, content_type = page
        elif len( page ) == 4:
            output_page, status, content_type, headers = page
        else:
            _print("Unknown page output...")

        self.process_request( output_page, status, GET, user.cookies, content_type, headers )

    def get_page( self, requested_path, user, get_data, post_data ):
        """ returns tuple (name of page template, status, content callback)
            All function require uac, get and post data params and must return final page, json content (as dict)
        """
        page = self.pages["not_found"]
        path_len = len( requested_path )

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
                    elif requested_path[1] == "api":
                        page = self.pages["api"]["raw"]
                        if "template" in get_data:
                            content_type = "text/html"  # this need to be implermented in the json api callback.
                            if get_data["template"] in self.pages["api"]:
                                page = self.pages["api"][ get_data["template"] ]
                            else:
                                page = self.pages["not_found"]
                    elif requested_path[1] == "action":
                        return self.process_action_request( user, requested_path[1:] )
                    elif requested_path[1] == "dl":
                        return self.get_7z_file( user, requested_path[1:] )
                    elif requested_path[1] == "output":
                        return self.get_output_file( user, requested_path[1:] )
                    elif requested_path[1] in self.pages:
                        page = self.pages[ requested_path[1] ]
                else:
                    page = self.pages["index"]

        content, status, content_type, headers = page.load_page(user, requested_path, get_data, post_data)
        return content, status, content_type, headers

# www_page callbacks

    def auth_user_content( self, user, request_path, get_data, post_data ):
        """ returns redirect page, content """

        if not user.authorized() and "user" in post_data and "password" in post_data:

            user_man = user_manager.UserManager()
            # redirect user when login info send received, to prevent resubmit data on refresh
            redirect_header = { "location": '/ams-ci/' }
            user_access = user_man.authorize_user(post_data["user"], post_data["password"])

            if user_access > WWWUser.UAC_NO_AUTH:

                sess_id = hashlib.md5( math.floor(time.time() * 1000).to_bytes(16, "big") ).hexdigest()

                while sess_id in self.sessions: # ensure that the new session id is unique
                    sess_id = hashlib.md5( math.floor(time.time() * 1000).to_bytes( 16, "big" ) ).hexdigest()

                # set the loged in user
                self.sessions[ sess_id ] = user.set_user( post_data["user"], sess_id, user_access )

                user.set_message( "Login Successful!" )

                # queue the session expiry
                # threading.Thread( target=self.expire_session, args=( sess_id, self.DEFAULT_SESSION_LENGTH )).start()

                return None, {"message": "login successful :)"}, HTTPStatus.SEE_OTHER, "text/html", redirect_header  # redirect content
            else:
                return None, { "message": "Invalid Login" }, HTTPStatus.OK, "text/html", None

        return None, {"message": "Login Required"}, HTTPStatus.OK, "text/html", None

    def logout_callback( self, user, request_path, get_data, post_data ):

        # remove the users session
        if user.session_id in self.sessions:
            del self.sessions[ user.session_id ]
            user.session_id = ""
            user.set_access_level( 0 )

        redirect_header = { "location": '/ams-ci/' }
        return None, None, HTTPStatus.SEE_OTHER, "text/html", redirect_header

    def index_content( self, user, request_path, get_data, post_data):

        page_content = {
            "messages":     self.get_api_content(user, ["user_messages"], "message", post_data={"clear": "true"} ),
            "active_tasks": self.get_api_content(user, ["tasks", "active"], "active_task"),
            "queued_tasks": self.get_api_content(user, ["tasks", "pending"], "queued_task"),
            "projects": self.get_api_content(user, ["projects"], "projects"),
            "builds": "<p>Select a project to view available builds</p>",
            "selected_project": "[None Selected]"
        }

        return None, page_content, HTTPStatus.OK, "text/html", None

    def api_content( self, user, request_path, get_data, post_data):
        """ Gets the json data for api path.
            Path format. /ams-ci/api/{api-path}
            api-paths:
            /projects                        returns all projects in CI-project
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
        request = [ r for r in request_path[self.API_ROOT_PATH_LENGTH:] ]
        request_length = len( request )
        data = {}
        _print("API REQUEST: ", request)

        if request_length > 0:
            if request[0] == "projects" or request[0] == "project":
                # if a project name is supplied, get ALL project info
                # otherwise just display all basic project info
                if len(request) > 2 and request[1] == "name":
                    data = commonProject.get_all_project_info( user.get_uac(), request[2] )
                    if data is None:
                        _print("www_interface: Project (", request[2], ") not found")
                        data = {}
                    else:
                        data = [ data ] # data must be wrapped in a list to prevent filtering
                else:
                    data = commonProject.get_project_list( user.get_uac() )
            elif request[0] == "tasks":
                data = common.get_or_create_json_file("./data/", "tasks.json", { "active":[], "pending": [] } )[1] # ensure that the file exist
            elif request[0] == "user_message" or request[0] == "user_messages": # gets a list of the all pending messages for logged in user
                data = user.get_messages()
                if "clear" in post_data and post_data["clear"].lower() == "true":     # Only clear message with POST, so they are now cleared by api request
                    user.clear_messages()
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

        api_header = { "cache-control": "no-store" }
        return None, data, HTTPStatus.OK, "application/json", api_header   # TODO: support html templates.

    def not_found_callback( self, user, request_path, get_data, post_data ):
        content = {"title:": "Not Found", "message": "404, Not Found"}
        return None, content, HTTPStatus.NOT_FOUND, "text/html", None

# end of www_page callbacks

    def get_api_content( self, user, request_path, template, get_data={}, post_data={} ):
        """ Use to get the API content locally
            `Request path` is the json filtering, see path in api_content for more info
        """

        if template not in self.pages["api"]:
            print("Error: template not found")
            return "Error: Template not found"

        # we must add elements to make up the pre API path, as they are removed, in api_content
        # if not we have a invalid request.
        pre_path_path = [""] * self.API_ROOT_PATH_LENGTH

        content, status, content_type, headers = self.pages["api"][ template ].load_page(user, pre_path_path + request_path, get_data, post_data)

        return content

    def get_7z_file( self, user, request_path ):
        """ Returns the 7zip file in bytes
            requestPath: list -> output/{project}/{build_name}
        """

        if not user.authorized(WWWUser.UAC_USER):
            return "404 Not Found", HTTPStatus.NOT_FOUND, "text/html", None

        if len(request_path) >= 3:
            project = request_path[1]
            build = request_path[2]
            zip_file = commonProject.get_project_build_7z( user.get_uac(), project, build )

            if zip_file is not None:

                headers = {
                    'Content-Disposition': 'attachment; filename="{filename}.7z"'.format( filename=build ),
                    'Content-Length': str( zip_file.file_size )
                }

                return zip_file, HTTPStatus.OK, "application/x-7z-compressed", headers

        return "404 Not Found", HTTPStatus.NOT_FOUND, "text/html", None

    def get_output_file( self, user, request_path ):
        """ Returns the raw output log
            requestPath: list -> output/{project}/{build_name}
        """

        if not user.authorized(WWWUser.UAC_USER):
            return "404 Not Found", HTTPStatus.NOT_FOUND, "text/html", None

        if len(request_path) >= 3:
            project = request_path[1]
            build = request_path[2]
            output = commonProject.get_project_output_log( user.get_uac(), project, build )

            if output is not None:
                return output, HTTPStatus.OK, "text/plain", None

        return "404 Not Found", HTTPStatus.NOT_FOUND, "text/html", None

    def process_action_request( self, user, request_path ):

        user_uac = user.get_access_level()
        request_path_len = len( request_path )

        if user_uac < WWWUser.UAC_USER:
            return "Login Required", HTTPStatus.OK, "text/html", None
        elif user_uac < WWWUser.UAC_MOD:
            return "Insufficient privileges", HTTPStatus.OK, "text/html", None
        elif request_path_len <= 1:
            return "404, Not Found", HTTPStatus.NOT_FOUND, "text/html", None

        if request_path[1].lower() == "cancel" and request_path_len >= 4:   # action/{action_type}/{project}/{build_hash}
            WebInterface.shared_queue.queue_task( "cancel", actor=user.get_uac().username, project=request_path[2], build_hash=request_path[3] )
            return "Canceling task", HTTPStatus.ok, "text/html", None
        else:
            return "404, Not Found", HTTPStatus.NOT_FOUND, "text/html", None




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
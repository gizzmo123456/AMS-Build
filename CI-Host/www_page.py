import common
import time
from http.cookies import SimpleCookie
from http import HTTPStatus
import web_interface
import user_access_control as uac
import re
import json
import DEBUG
_print = DEBUG.LOGS.print

class WWWUser:

    # User Access Control Const # TODO, replace const with UAC versions
    UAC_NO_AUTH         = 0             # No permissions
    UAC_USER            = 1             # View/download assigned project only
    UAC_MOD             = 2             # UAC_USER + Can trigger builds
    UAC_PROJECT_ADMIN   = 3             # UAC_MOD + Can Add/Assigned new user to project                (TODO)
    UAC_SERVER_ADMIN    = 4             # All permissions on all projects. # Can also add new projects  (TODO)

    # Message Status Types
    MSG_STATUS_OK       = "message"
    MSG_STATUS_WARN     = "warning"
    MSG_STATUS_ERROR    = "error"
    MSG_STATUS_FATAL    = "fatal"

    def __init__( self ):

        self.__uac = uac.UAC()

        self.session_id = ""
        self.cookies = SimpleCookie()
        self.expires = time.time() + web_interface.WebInterface.DEFAULT_SESSION_LENGTH # Only used if authorized
        self.__messages = []

    def authorized(self, min_auth_value=UAC_USER):
        return self.get_access_level() >= min_auth_value

    def set_user( self, username, session_id, access_level ):

        self.__uac.set_user( username, access_level)

        self.session_id = session_id
        self.set_cookie( "session_id", session_id, path="/"+web_interface.WebInterface.ROOT )

        return self

    def set_access_level( self, level ):
        self.__uac.access_level = level

    def set_cookie( self, key, value, path="/" ):
        self.cookies[key] = value
        self.cookies[key]["path"] = path

    def set_message( self, message, message_status=MSG_STATUS_OK ):

        msg = {
            "status": message_status,
            "message": message
        }

        self.__messages.append( msg )

    def get_messages( self ):

        return self.__messages

    def clear_messages( self ):
        self.__messages = []

    def get_uac( self ):
        return self.__uac

    def get_access_level( self ):

        # update the expire time
        self.expires = time.time() + web_interface.WebInterface.DEFAULT_SESSION_LENGTH  # in 1hr

        return self.__uac.access_level

    def get_cookie( self, key ):

        if key in self.cookies:
            return self.cookies[key].value
        else:
            return ""

    def queue_action_callback( self, queue_item, successful ):

        action_status = WWWUser.MSG_STATUS_OK
        message = "{task} task for {project} with hash {build_hash}, has completed successful".format( task=queue_item.action,
                                                                                                       build_hash=queue_item.build_hash,
                                                                                                       project=queue_item.project_name )

        if not successful:
            action_status = WWWUser.MSG_STATUS_ERROR
            message = "{task} task for {project} with hash {build_hash}, has completed unsuccessfully".format( task=queue_item.action,
                                                                                                               build_hash=queue_item.build_hash,
                                                                                                               project=queue_item.project_name )

        self.set_message( message, action_status )

    def build_action_callback( self, build_task, successful ):

        if successful:
            action_status = WWWUser.MSG_STATUS_OK
            message = "Build task for {project} with hash {build_hash}, has completed successful".format( **build_task.format_values )
        else:
            action_status = WWWUser.MSG_STATUS_ERROR
            message = "Failed to process task (task valid? {valid})".format( valid=build_task.is_valid() )

        self.set_message( message, action_status )

class WWWPage:

    # List Orders
    LO_ASC = 1
    LO_DESC = -1

    def __init__( self, page_name, file_name, content_callback, minimal_user_access_level=WWWUser.UAC_NO_AUTH, no_access_www_page=None, no_content_message="", no_content_template="noContent.html" ):

        self.page_name = page_name
        self.file_name = file_name

        self.content_callback = content_callback
        self.minimal_user_access_level = minimal_user_access_level
        self.no_access_www_page = no_access_www_page
        self.content_dict = self._build_content_dict()  # all values in dict are required on the page.
        self.no_content_message = no_content_message
        self.no_content_template = no_content_template

        self.list_order = WWWPage.LO_ASC    # order of list when content json is a list

    def set_headers( self, headers ):
        """ sets a list of headers

        :param headers: a list of dicts, where dict key is header name
        """
        self.headers = headers

    def _build_content_dict( self ):

        if self.file_name is None:
            return {}

        page = self.load_template()
        keys = re.findall(r"{([a-zA-Z_][a-zA-Z0-9-_]*)}", page)
        content = {}

        for k in keys:
            content[ k ] = ""

        return content

    def extract_get_content(self, get_data):
        """Extracts GET params that can be used as content"""
        content = {"page_redirect": ""}
        # if the params in this list exist the will be formated as &{key}={value}
        # and stored in content as "get_{key}'
        get_params = ["page_redirect"]

        # make sure we only use keys that can be used in content
        # and in a useable format :)
        for k in get_data:
            if k in content:
                if k in get_params:
                    content[f"get_{k}"] = f"&{k}={get_data[k]}"

                content[k] = get_data[k]

        return content

    def build_content( self, content, get_data ):
        return { **self.content_dict, **self.extract_get_content( get_data ), **content, "www_root": web_interface.WebInterface.ROOT }    # overwrite the values in content dict

    def access( self, user ):
        return user.get_access_level() >= self.minimal_user_access_level

    def get_access_page( self, user ):
        """returns this page if user has access otherwise returns no access page (ie login)"""
        if self.access( user ):
            return self
        else:
            return self.no_access_www_page

    def load_template( self, no_content_template=False ):

        root = "./www/"
        file_path = root + self.file_name

        if no_content_template:
            file_path = root + self.no_content_template

        return common.read_file( file_path )

    def __get_list_order_range( self, list_len ):

        if self.list_order == WWWPage.LO_DESC:
            return range( list_len-1, -1, -1 )
        else:
            return range( list_len )

    def load_page( self, user, requested_path, get_data, post_data ):

        # find and display the correct content for user access level,

        www_page = self.get_access_page( user )

        if www_page is None:
            return "Its dark down here.", 200

        redirect = None

        # default content return values
        content =  {"message": ""}
        status = HTTPStatus.OK
        content_type = "text/html"
        page_headers = None

        if www_page.content_callback is not None:
            redirect, content, status, content_type, page_headers = www_page.content_callback( user, requested_path, get_data, post_data )

        while redirect is not None:
            www_page = redirect

            if www_page.content_callback is not None:
                redirect, content, status, content_type, page_headers = www_page.content_callback( user, requested_path, get_data, post_data )
            else:
                break

        # status See Other redirects the page,
        # so there is no point rendering the content
        if status == HTTPStatus.SEE_OTHER:
            return "Loading...", status, content_type, page_headers

        # Render Content
        page_output = ""

        if self.file_name is None:          # return the raw json data
            page_output = json.dumps( content )
        elif isinstance( content, list ):   # if content is list, we need to return the template for all elements
            for i in self.__get_list_order_range( len(content) ):
                page_output += www_page.load_template().format( **www_page.build_content( content[i], get_data ) )
        elif len(content) > 0 and isinstance( content, dict):    # if content is dict, we only have to format it into the template
            page_output = www_page.load_template().format( **www_page.build_content( content, get_data ) )
        else:
            _print("WWWPage: Bad content format for page:", self.page_name)

        if page_output == "" :
            page_headers = None
            if self.no_content_message != "":
                if self.no_content_template is not None:
                    page_output = www_page.load_template( True ).format( no_content_message=www_page.no_content_message )
                else:
                    page_output = self.no_content_message
            else:
                status = HTTPStatus.NO_CONTENT

        return page_output, status, content_type, page_headers

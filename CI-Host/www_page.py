import common
import time
from http.cookies import SimpleCookie
from http import HTTPStatus
import web_interface
import re
import json

class WWWUser:

    # User Access Control Const
    UAC_NO_AUTH = 0
    UAC_USER    = 1
    UAC_MOD     = 2
    UAC_ADMIN   = 3

    def __init__( self ):

        self.session_id = ""
        self.cookies = SimpleCookie()
        self.expires = time.time() + web_interface.WebInterface.DEFAULT_SESSION_LENGTH # Only used if authorized

        self.__access_level = 0

    def authorized(self, min_auth_value=UAC_USER):
        return self.get_access_level() >= min_auth_value

    def get_access_level( self ):

        # update the expire time
        self.expires = time.time() + web_interface.WebInterface.DEFAULT_SESSION_LENGTH  # in 1hr

        return self.__access_level

    def set_access_level( self, level ):
        self.__access_level = level

    def set_cookie( self, key, value, path="/" ):
        self.cookies[key] = value
        self.cookies[key]["path"] = path

    def get_cookie( self, key ):

        if key in self.cookies:
            return self.cookies[key].value
        else:
            return ""

class WWWPage:

    def __init__( self, page_name, file_name, status, content_callback, minimal_user_access_level=WWWUser.UAC_NO_AUTH, no_access_www_page=None, no_content_message="", no_content_template="noContent.html" ):

        self.page_name = page_name
        self.file_name = file_name

        self.status = status
        self.content_callback = content_callback
        self.minimal_user_access_level = minimal_user_access_level
        self.no_access_www_page = no_access_www_page
        self.content_dict = self._build_content_dict()  # all values in dict are required on the page.
        self.no_content_message = no_content_message
        self.no_content_template = no_content_template

    def _build_content_dict( self ):

        if self.file_name is None:
            return {}

        page = self.load_template()
        keys = re.findall(r"{([a-zA-Z_][a-zA-Z0-9-_]*)}", page)
        content = {}

        for k in keys:
            content[ k ] = ""

        return content

    def build_content( self, content ):
        return { **self.content_dict, **content }    # overwrite the values in content dict

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
        file_path = root + self.file_name;

        if no_content_template:
            file_path = root + self.no_content_template;

        return common.read_file( file_path )

    def load_page( self, user, requested_path, get_data, post_data ):

        # find and display the correct content for user access level,

        www_page = self.get_access_page( user )

        if www_page is None:
            return "Its dark down here.", 200

        redirect, content, status = None, {"message": ""}, www_page.status

        if www_page.content_callback is not None:
            redirect, content = www_page.content_callback( user, requested_path, get_data, post_data )

        while redirect is not None:
            www_page = redirect

            if www_page.content_callback is not None:
                redirect, content = www_page.content_callback( user, requested_path, get_data, post_data )
            else:
                break

        page_output = ""

        if self.file_name is None:          # return the raw json data
            page_output = json.dumps( content )
        elif isinstance( content, list ):   # if content is list, we need to return the template for all elements
            for c in content:
                page_output += www_page.load_template().format( **www_page.build_content( c ) )
        elif len(content) > 0 and isinstance( content, dict):    # if content is dict, we only have to format it into the template
            page_output = www_page.load_template().format( **www_page.build_content( content ) )

        if page_output == "":
            if self.no_content_message != "":
                if self.no_content_template is not None:
                    page_output = www_page.load_template( True ).format( no_content_message=www_page.no_content_message )
                else:
                    page_output = self.no_content_message
            else:
                status = HTTPStatus.NO_CONTENT

        return page_output, status

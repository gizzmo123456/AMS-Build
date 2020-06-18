import common
import time
from http.cookies import SimpleCookie
import web_interface

class WWWUser:

    def __init__( self ):

        self.session_id = ""
        self.cookies = SimpleCookie()
        self.expires = time.time() + web_interface.WebInterface.DEFAULT_SESSION_LENGTH # Only used if authorized

        self.__access_level = 0

    def authorized(self):
        return self.get_access_level() > 0

    def get_access_level( self ):

        # update the expire time
        self.expires = time.time() + web_interface.WebInterface.DEFAULT_SESSION_LENGTH  # in 1hr

        return self.__access_level

    def set_cookie( self, key, value ):
        self.cookies[key] = value

    def get_cookie( self, key ):

        if key in self.cookies:
            return self.cookies[key].value
        else:
            return ""

class WWWPage:

    def __init__( self, page_name, file_name, status, content_callback, minimal_user_access_level=0, no_access_www_page=None ):

        self.page_name = page_name
        self.file_name = file_name

        self.status = status
        self.content_callback = content_callback
        self.minimal_user_access_level = minimal_user_access_level
        self.no_access_www_page = no_access_www_page

    def access( self, user ):
        return user.get_access_level() >= self.minimal_user_access_level

    def get_access_page( self, user ):
        """returns this page if user has access otherwise returns no access page (ie login)"""
        if self.access( user ):
            return self
        else:
            return self.no_access_www_page

    def load_template( self ):

        root = "./www/"
        return common.read_file( root + self.file_name )

    def load_page( self, user, requested_path, get_data, post_data ):

        # find and display the correct content for user access level,

        www_page = self.get_access_page( user )

        if www_page is None:
            return "Its dark down here.", 200, []

        redirect, content = None, {"message": ""}

        if www_page.content_callback is not None:
            redirect, content = www_page.content_callback( user, requested_path, get_data, post_data )

        while redirect is not None:
            www_page = redirect

            if www_page.content_callback is not None:
                redirect, content = www_page.content_callback( user, requested_path, get_data, post_data )

        return www_page.load_template().format( **content ), www_page.status

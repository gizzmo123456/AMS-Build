import common

class WWWPage():

    def __init__( self, page_name, file_name, status, content_callback, minimal_user_access_level=0, no_access_www_page=None ):

        self.page_name = page_name
        self.file_name = file_name
        self.status = status
        self.content_callback = content_callback
        self.uac = minimal_user_access_level
        self.no_access_www_page = no_access_www_page

    def access( self, user_access_level ):
        return user_access_level >= self.uac

    def get_access_page( self, user_access_level ):
        """returns this page if user has access otherwise returns no access page (ie login)"""
        if self.access( user_access_level ):
            return self
        else:
            return self.no_access_www_page

    def load_template( self ):

        root = "./www/"
        return common.read_file( root + self.file_name )

    def load_page( self, user_access_level, requested_path, get_data, post_data ):

        # find and display the correct content for user access level,

        www_page = self.get_access_page( user_access_level )

        if www_page is None:
            return "An error has happened :(", 200, []

        all_cookies = []
        redirect, content, cookies = None, {"message": ""}, None

        if www_page.content_callback is not None:
            redirect, content, cookies = www_page.content_callback( user_access_level, requested_path, get_data, post_data )

        while redirect is not None:
            www_page = redirect
            if type( cookies ) is list:
                all_cookies.extend( cookies )
            if www_page.content_callback is not None:
                redirect, content, cookies = www_page.content_callback( user_access_level, requested_path, get_data, post_data )

        return www_page.load_template().format( **content ), www_page.status, all_cookies

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

        if self.access( user_access_level ):
            return self.file_name
        else:
            return self.no_access_www_page.file_name

    def load_template( self, user_access_level ):

        root = "./www/"
        return common.read_file( root + self.get_access_page( user_access_level ) )

    def load_page( self, user_access_level, requested_path, get_data, post_data ):

        www_page = self
        redirect, content = None, {"message": ""}

        if www_page.content_callback is not None:
            www_page.content_callback( user_access_level, requested_path, get_data, post_data )

        while redirect is not None:
            www_page = redirect
            if www_page.content_callback is not None:
                redirect, content = www_page.content_callback( user_access_level, requested_path, get_data, post_data )

        return www_page.load_template( user_access_level ).format( **content )

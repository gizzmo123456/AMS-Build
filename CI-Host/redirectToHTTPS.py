import baseHTTPServer
from http import HTTPStatus
import config_manager
import DEBUG
_print = DEBUG.LOGS.print

class RedirectToHTTPS( baseHTTPServer.BaseServer ):

    def __init__( self, request, client_address, server  ):
        """

        :param web_address:     The web address used (ip or host name)
        :param port:            The port to use
        :param path:            path to direct to
        """

        config = config_manager.ConfigManager
        self.path = "/"

        super().__init__( request, client_address, server )

        _print("Redirecting request", request.getsockname(), self.path)

        self.headers = {
            'Location': f'https://${config.get("web_address", "127.0.0.1")}:${request.getsockname()[1]}${self.path}' # redirect back to localhost if incorrectly setup.
        }

    def do_POST( self ):
        self.process_request( content="", status=HTTPStatus.MOVED_PERMANENTLY, GET=False, headers=self.headers )

    def do_GET( self ):
        self.process_request( content="", status=HTTPStatus.MOVED_PERMANENTLY, GET=True,  headers=self.headers )

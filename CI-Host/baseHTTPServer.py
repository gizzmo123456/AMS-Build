from http.server import BaseHTTPRequestHandler, HTTPServer      # we use this lib so we dont have to install flask :)
import socketserver
import DEBUG
from const import *

_print = DEBUG.LOGS.print

host = "0.0.0.0"
port = 8081


class BaseServer(BaseHTTPRequestHandler):

    def version_string( self ):
        return "{app_name}/{version}".format( app_name=APP_NAME, version=APP_VERSION )

    def do_POST( self ):
        self.process_request(GET=False)

    def do_GET( self ):
        self.process_request()

    def process_request( self, content="i'm a teapot", status=418, GET=True, cookies=None, content_type="text/html" ):
        _print( "GET:", GET, "POST", not GET, "request: ", self.path )

        # send headed
        self.send_response( status, 'OK' )
        self.send_header( 'Content-type', content_type )
        self.send_header( 'Access-Control-Allow-origin', '*' )

        if cookies is not None:
            cookies["test"] = "helloo"
            cookies["test"]["path"] = "/HellooWorld"

            #cookies = cookies.output( header='Set-Cookie:', sep=";" )
            for c in cookies:
                header = str(cookies[c]).split(":")
                print( "Setting cookies...", header )
                if len( header ) > 1:
                    self.send_header( *header )

        self.end_headers()

        if content == "" and status is not 200:
            content = "Error " + str( status )
        # reply
        self.wfile.write( content.encode() )


class ThreadHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    def finish_request(self, request, client_address):
        request.settimeout(30)
        # "super" can not be used because BaseServer is not created from object
        HTTPServer.finish_request(self, request, client_address)

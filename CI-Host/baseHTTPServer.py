from http.server import BaseHTTPRequestHandler, HTTPServer      # we use this lib so we dont have to install flask :)
import socketserver
import DEBUG
from const import *
import common

_print = DEBUG.LOGS.print

class BaseServer(BaseHTTPRequestHandler):

    BLOCK_CORS = False
    ACCEPTED_CORS_ORIGINS = []

    def version_string( self ):
        return "{app_name}/{version}".format( app_name=APP_NAME, version=APP_VERSION )

    def do_POST( self ):
        self.process_request(GET=False)

    def do_GET( self ):
        self.process_request()

    def process_request( self, content="i'm a teapot", status=418, GET=True, cookies=None, content_type="text/html", headers=None ):

        if headers is None:
            headers = { "Content-Disposition": 'inline' }
        elif "Content-Disposition" not in headers:
            headers = { "Content-Disposition": 'inline', **headers }

        _print( "GET:", GET, "POST", not GET, "request: ", self.path )

        # Treat any request with origin header set as a CORS request.
        # for now ALL CORS request are blocked
        origin_header = self.headers.get("origin")

        if BaseServer.BLOCK_CORS and origin_header not in BaseServer.ACCEPTED_CORS_ORIGINS and\
           origin_header is not None and origin_header != "None" and origin_header != "null":
            self.send_response( 406, 'CORS Not Accepted' )
            self.send_header( 'Content-type', "text/html" )
            self.end_headers()
            self.wfile.write( "CORS Not Accepted".encode() )
            _print("Blocked CORS from origin: ", origin_header)
            return

        # send headed
        self.send_response( status, 'OK' )
        self.send_header( 'Content-type', content_type )
        # self.send_header( 'Access-Control-Allow-origin', '*' )    # for now reject all CORS request.
                                                                    # There may be a time where we allow CORS request to the api

        for header_key in headers:
            self.send_header( header_key, headers[header_key] )

        if cookies is not None:
            for c in cookies:
                header = str(cookies[c]).split(":")
                print( "Setting cookies...", header )
                if len( header ) > 1:
                    self.send_header( *header )

        self.end_headers()

        if content == "" and status is not 200:
            content = "Error " + str( status )

        # reply
        if isinstance( content, common.BinaryFileStream ):
            for data in content.read():
                self.wfile.write( data )
        else:
            content = content.encode()
            self.wfile.write( content )


class ThreadHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    def finish_request(self, request, client_address):
        request.settimeout(30)
        # "super" can not be used because BaseServer is not created from object
        HTTPServer.finish_request(self, request, client_address)

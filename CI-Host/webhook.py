import baseHTTPServer
from urllib.parse import urlparse, parse_qsl
from http.server import BaseHTTPRequestHandler, HTTPServer  # this must be removed


class Webhook( baseHTTPServer.BaseServer ):

    def do_GET( self ):

        request = urlparse( self.path )
        path = request.path
        query = parse_qsl( request.query )

        if path != "/request":
            self.process_request("", 404, True)
        else:
            self.process_request("Processing request...", 200, True)


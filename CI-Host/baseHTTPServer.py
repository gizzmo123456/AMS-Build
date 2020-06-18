from http.server import BaseHTTPRequestHandler, HTTPServer      # we use this lib so we dont have to install flask :)
import DEBUG
_print = DEBUG.LOGS.print

host = "0.0.0.0"
port = 8081


class BaseServer(BaseHTTPRequestHandler):

    def do_POST( self ):
        self.process_request(GET=False)

    def do_GET( self ):
        self.process_request()

    def process_request( self, content="i'm a teapot", status=418, GET=True, cookies=[] ):
        _print( "GET:", GET, "POST", not GET, "request: ", self.path )

        # send headed
        self.send_response( status, 'OK' )
        self.send_header( 'Content-type', 'text/html' )
        self.send_header( 'Access-Control-Allow-origin', '*' )

        for c in cookies:
            self.send_header("Set-Cookie", c.output(header='', sep=''))

        self.end_headers()

        if content == "" and status is not 200:
            content = "Error " + str( status )
        # reply
        self.wfile.write( content.encode() )


if __name__ == "__main__":

    server = HTTPServer( (host, port), BaseServer )

    while True:
        server.serve_forever()

    server.server_close()

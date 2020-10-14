import threading
from http.server import HTTPServer
from baseHTTPServer import ThreadHTTPServer
import socket
import ssl

import DEBUG
_print = DEBUG.LOGS.print

# performs basic checks to help prevent unwanted connections.
# and bans badly behaving clients/IP.
# IE. if a request for HTTP/0.9 comes in. Ban!
class SocketWrapper:

    def __init__( self, ip, port, max_connections, http_class, ssl=None, threaded=True ):

        self.alive = True

        self.outer_sock = None
        self.www_handler = None

        self.http_class = http_class
        self.threaded = threaded

        self.ip = ip
        self.port = port
        self.max_connections = max_connections

        #self.ssl_cert = ssl[0]
        #self.ssl_ca   = ssl[1]
        #self.ssl_priv = ssl[2]

        self.thread_lock = threading.Lock()

        self.accept_thread = None
        self.http_thread = None

        self.banned_request = [
            b"http/0.9"
            b"http/1.0"
            b"rds"
        ]

        self.banned_ips = [

        ]

    def is_alive( self ):

        with self.thread_lock:
            return self.alive

    def set_alive( self, ali ):

        with self.thread_lock:
            self.alive = ali

    def ban_ip( self, ip_address ):

        with self.thread_lock:
            self.banned_ips.append( ip_address )

    def serve( self ):

        if self.outer_sock is not None:
            _print( "Socket already created", message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
            return

        self.outer_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )  # the socket that the client connects to.
        self.outer_sock.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )  # alow the socket to be reused onces idled for a long period
        self.outer_sock.bind( (self.ip, self.port) )
        self.outer_sock.listen( self.max_connections + 1 )  # allow 1 extra connection to prevent connections queueing

        # only allow local connections to the http server,
        if self.threaded:
            self.www_handler = ThreadHTTPServer( ("127.0.0.1", 9998), self.http_class )
        else:
            self.www_handler = HTTPServer( ( "127.0.0.1", 9998 ), self.http_class )

        self.http_thread = threading.Thread( target=self.http_serve_thread, args=[self.www_handler] )
        self.http_thread.start()

        self.accept_thread = threading.Thread( target=self.accept_www_thread, args=[self.outer_sock] )
        self.accept_thread.start()

    def http_serve_thread( self, www_handler ):

        while self.is_alive():
            www_handler.serve_forever()

    def accept_www_thread( self, _socket ):

        while self.is_alive():
            client_socket, address = _socket.accept()

            # TODO. check banned list.
            if address[0] in self.banned_ips:
                _print("Rejected banned ip", address[0], message_type=DEBUG.LOGS.MSG_TYPE_WARNING)
                client_socket.shutdown(socket.SHUT_RDWR)
                continue

            _print( address )

            threading.Thread( target=self.process_www_request_thread, args=[ client_socket, address[0] ] ).start()


    def process_www_request_thread( self, client_socket, ip_address ):

        # Read all incoming data from the socket and
        # forward it onto the http server.

        data = self._receive_data( client_socket, False )

        _print("IN", data)
        # close any connections that sent us zero bytes.
        if len( data ) == 0:
            client_socket.close()
            return

        http_header = data.split(b'\r\n')

        # TODO: check request line


        # open the connection the http server and send data from client
        http_con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        http_con.connect( ("127.0.0.1", 9998) )

        http_con.send( data )

        http_data = self._receive_data( http_con, True )

        _print("SEND", http_data)

        # and return the data to the client
        if len( http_data ) > 0:
            client_socket.send( http_data )
        else:    # ban um', no seconds
            self.ban_ip( ip_address )   # TODO: we need a better way

        client_socket.close()

    def _receive_data( self, sock, close_on_timeout ):

        sock.settimeout(0.5)
        data = b''

        while True:
            try:
                byte = sock.recv( 1024 )
                if len( byte ) == 0:    # zero bytes are returned then the connection has been closed by the http server.
                    break
                data += byte
            except socket.timeout as e:
                if close_on_timeout:
                    sock.close()
                break
            except Exception as e:
                _print( "Bad http socket connection" )
                sock.close()
                break

        return data

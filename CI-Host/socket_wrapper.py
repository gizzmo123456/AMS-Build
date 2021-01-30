import threading
from http.server import HTTPServer
from baseHTTPServer import ThreadHTTPServer
import socket
import re
import ssl

import DEBUG
_print = DEBUG.LOGS.print

# performs basic checks to help prevent unwanted connections.
# and bans badly behaving clients/IPs.
# Also redirects http requrest to https
# IE. if a request for HTTP/0.9 comes in. Ban!
# ALSO this is not a intended as a perminent solution
class SocketPassthrough:

    def __init__( self, ip, port, passthrough_ip, passthrough_port, max_connections ):

        self.alive = True

        self.ip = ip
        self.port = port
        self.max_connections = max_connections

        self.passthrough_ip = passthrough_ip
        self.passthrough_port = passthrough_port

        self.socket = None
        self.thread_lock = threading.RLock()

        self.banned_ips = [
            #"127.0.0.1"
        ]

        # if any of the following strings are found in any request
        # the user will be banned this should only be used when ssl
        # socket is in use. Any plan text should be rejected or if its
        # valid http we should probably redirect them but this is not
        # a permanent solution. so i cant be asked.
        self.banRegex = [
            r"HTTP/0.9"
        ]

        self.redirectRegex = [
            r"HTTP/1.1"
        ]

    def is_alive(self):
        ''' Thread safe method to get is alive '''
        self.thread_lock.acquire()
        a = self.alive
        self.thread_lock.release()

        return a

    def ip_is_banned(self, ip):

        self.thread_lock.acquire()
        banned = ip in self.banned_ips
        self.thread_lock.release()

        return banned

    def create_socket(self):

        self.socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )    # the socket that the client connects to.
        self.socket.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )  # alow the socket to be reused onces idled for a long period
        self.socket.bind((self.ip, self.port))

        tred = threading.Thread(target=self.wait_for_connections, args=[self.socket])
        tred.start()

    def wait_for_connections(self, sock):

        sock.listen()
        i = 0

        while self.is_alive():

            s_sock, address = sock.accept()

            _print( i, "New con from", address )

            # Reject the client if there IP has been banned
            if self.ip_is_banned( address[0] ):
                _print("Rejected banned ip", address[0], message_type=DEBUG.LOGS.MSG_TYPE_WARNING)
                s_sock.shutdown(socket.SHUT_RDWR)
                s_sock.close()
                continue

            # Create a client socket so that data can be passed onto the ssl or http socket
            p_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            p_sock.connect( (self.passthrough_ip, self.passthrough_port) )

            # Create a send and receive thread, to pass the connections onto the ssl socket
            recv_thr = threading.Thread( target=self.receive_thread, args=[ s_sock, p_sock, address[0], i ] )
            snd_thr = threading.Thread( target=self.send_thread, args=[ s_sock, p_sock, address[0], i ] )

            i += 1

            recv_thr.start()
            snd_thr.start()

    def receive_thread(self, s_client_socket, p_client_socket, client_ip, idx):   # received from the server socket
        """
        :param s_client_socket:     The socket the client connected to
        :param p_client_socket:     The socket that passes the connection data on
        """

        # TODO: NOTE: Might be worth checking if the ip was banned while this socket was open

        _print("Start Receive", idx)
        #while self.is_alive():

        s_client_socket.settimeout(30)

        banIP = False
        message_bytes = ""    # store the inbound message, so it can be logged in the client gets baned

        while True:
            try:
                data = s_client_socket.recv( 1024 )
                if len( data ) == 0:
                    _print("EXIT rev LOOP", idx)
                    break
            except Exception as e:
                # TODO: if a message has been received, we should consider banning the ip, as this could mean that the SSL is not resolving.
                _print(e)
                break

            data_str = ""

            try:
                for bv in self.banRegex:
                    match = re.search( bv, data.decode("utf-8") )

                    if match:
                        banIP = True
                        break
            except Exception as e:
                _print( e )
                # if the exception is raised the client should be rejected unless in ssh mode
                pass

            if banIP:
                _print( "ban ip triggered!" )
                self.banned_ips.append( client_ip )
                break
            else:
                _print( "Valid request" )

            _print (idx, "request Data:\n", data)

            try:
                p_client_socket.sendall( data )
            except Exception as e:
                _print(e)

            break

        _print("Exit Receive", idx)

        # shutdown the receive stream on servers socket to prevent any more messages coming in.
        # send thread will close the connection fully on the socket when the time comes :)
        try:
            if not banIP:
                s_client_socket.shutdown(socket.SHUT_RD)
            else:   # if the ip is getting baned we must shutdown both sockets in both directions
                p_client_socket.shutdown(socket.SHUT_RDWR)
                s_client_socket.shutdown(socket.SHUT_RDWR)
                _print("BAN HAS SHUTDOWN BOTH P & S SOCKETS")
        except Exception as e:
            _print( e )

    def send_thread(self, s_client_socket, p_client_socket, client_ip, idx):      # send from the server socket
        """
        :param s_client_socket:     The socket the client connected to
        :param p_client_socket:     The socket that passes the connection data on
        """

        # TODO: NOTE: Might be worth checking if the ip was banned while this socket was open

        _print("Start Send", idx)

        while self.is_alive():

            try:
                data = p_client_socket.recv( 1024 )

                #_print(idx, "HTTP DATA:\n",data)

                if len( data ) == 0:
                    _print("EXIT Send LOOP", idx)
                    break

                s_client_socket.sendall( data )
            except Exception as e:
                _print( e )
                break

        pass

        try:
            # finish closing the 2 sockets
            p_client_socket.close()
            s_client_socket.close()
        except Exception as e:
            _print("Error closing sockets", idx)
            _print(e)

        _print( "Sockets Closed!" )
        _print("Exit Send", idx)

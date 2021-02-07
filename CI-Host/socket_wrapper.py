import common
import threading
import socket
import re


import DEBUG
_print = DEBUG.LOGS.print

# performs basic checks to help prevent unwanted connections.
# and bans badly behaving clients/IPs.
# Also redirects http requrest to https
# IE. if a request for HTTP/0.9 comes in. Ban!
# ALSO this is not a intended as a perminent solution
class SocketPassthrough:

    def __init__( self, ip, port, passthrough_ip, passthrough_port, max_connections, using_ssl=False ):

        self.alive = True

        self.ip = ip
        self.port = port
        self.max_connections = max_connections
        self.using_ssl = using_ssl

        self.passthrough_ip = passthrough_ip
        self.passthrough_port = passthrough_port

        self.socket = None
        self.thread_lock = threading.RLock()


        # TODO: banRegex, redirectRegex and banned ip need implementing correctly
        #    1: banned ip need writing to file.
        #    2: redirect stuff needs rediringing
        #    3: banRegex should load from file
        #    And so far its all a bit half asked tbh.
        #    The main focus was to prevent the ssh socket from locking up due to
        #    HTTP request and other plan text messages from the wild-west of the internet :|

        self.banned_ips = [

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

        sock.listen(0)
        connection_id = 0

        while self.is_alive():

            s_sock, address = sock.accept()

            _print( connection_id, "New con from", address )

            # Reject the client if there IP has been banned
            if self.ip_is_banned( address[0] ):
                _print("Rejected banned ip", address[0], message_type=DEBUG.LOGS.MSG_TYPE_WARNING)
                s_sock.shutdown(socket.SHUT_RDWR)
                s_sock.close()
                continue

            _print("Connecting to P...")
            # Create a client socket so that data can be passed onto the ssl or http socket
            # p_sock = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
            try:
                p_sock = socket.create_connection( (self.passthrough_ip, self.passthrough_port), 1 )
            except:
                _print("Unable to connect to HTTP :( ", message_type=DEBUG.LOGS.MSG_TYPE_WARNING)
                s_sock.shutdown(socket.SHUT_RDWR)
                s_sock.close()
                return
            # Create a send and receive thread, to pass the connections onto the ssl socket
            recv_thr = threading.Thread( target=self.receive_thread, args=[ s_sock, p_sock, address[0], connection_id ] )
            snd_thr = threading.Thread( target=self.send_thread, args=[ s_sock, p_sock, address[0], connection_id ] )

            connection_id += 1

            recv_thr.start()
            snd_thr.start()

    def receive_thread(self, s_client_socket, p_client_socket, client_ip, idx):   # received from the server socket
        """
        :param s_client_socket:     The socket the client connected to
        :param p_client_socket:     The socket that passes the connection data on
        """

        # TODO: NOTE: Might be worth checking if the ip was banned while this socket was open

        _print("Start Receive", idx)

        s_client_socket.settimeout(30)

        banIP = False
        reject = False

        message_bytes = ""    # store the inbound message, so it can be logged in the client gets baned

        i = 0
        expected_received_messages = 1

        if self.using_ssl:
            expected_received_messages = 2

        while i <= expected_received_messages:

            # reduce the sockets timeout
            # it appears that it is not need any more.
            #if i == 1:
            #    s_client_socket.settimeout(3)

            # Receive message from client
            try:
                data = s_client_socket.recv( 1024 )
                if len( data ) == 0:
                    break
            except Exception as e:
                #_print("SRECV:", e)
                break

            data_str = ""

            # check the message for know banned message
            try:
                de_data = data.decode("utf-8")     # this will most likely raise an error if an ssl connection comes in

                # reject the connect if the data can be decoded with utf-8
                # while using ssl. And we'll check the banned regex so there ip
                # can be logged if necessary
                if self.using_ssl:
                    reject = True
                    common.write_file("./data/logs/http-request.logs.txt", f"\n{'='*55}\n{client_ip}\n{'='*55}\n" + de_data, append=True )   # Log the header to file


                for bv in self.banRegex:
                    match = re.search( bv, de_data )

                    if match:
                        banIP = True
                        break

            except Exception as e:
                #_print( "RE:", e )
                # if the exception is raised the client should be rejected unless in ssh mode
                if not self.using_ssl:
                    reject = True
                    break
                    pass

            # ban client if necessary
            if banIP:
                _print( "ban ip triggered!" )
                self.banned_ips.append( client_ip )
                common.write_file( "./data/logs/http-bad-ips.txt", "\n"+client_ip, append=True ) # Log ip to file
                break

            else:
                _print( "Valid request" )

            if reject:
                break

            #_print (idx, "request Data:\n", data)

            # pass the message onto the http socket
            try:
                p_client_socket.sendall( data )
            except Exception as e:
                _print("PSND:",e)

            i += 1

        _print("Exit Receive", idx)

        # shutdown the receive stream on servers socket to prevent any more messages coming in.
        # send thread will close the connection fully on the socket when the time comes :)
        try:
            if not banIP and not reject:
                s_client_socket.shutdown(socket.SHUT_RD)
            else:   # if the client is rejected or getting baned we must shutdown both sockets in both directions
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
                    break

                s_client_socket.sendall( data )
            except Exception as e:
                # _print( e )
                break

        pass

        # shudown the sockets so the receive methods stop blocking
        # and make sure there completely closed before exiting
        try:
            p_client_socket.shutdown(socket.SHUT_RDWR)
            s_client_socket.shutdown(socket.SHUT_RDWR)
        except:
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

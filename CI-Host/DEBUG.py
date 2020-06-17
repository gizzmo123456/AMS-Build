import queue as q
import threading
import datetime
import time
import os.path

QUEUE_UNBLOCK_MESSAGE = "[Unblock message]"

# treat as if static :)
class LOGS:

    MSG_TYPE_DEFAULT = 1
    MSG_TYPE_WARNING = 2
    MSG_TYPE_ERROR   = 3
    MSG_TYPE_FATAL   = 4

    debug_mode = True

    que_pre_init_msg = True

    inited = False
    active = False
    print_que = q.Queue()    # Queue of tuples (type, message)
    debug_thread = None

    file_queue = {}

    @staticmethod
    def init():
        """This must be called to start the debug thread
        The thread wll not start unless debug_mode is set to True
        """
        if LOGS.inited or not LOGS.debug_mode:
            return

        LOGS.debug_thread = threading.Thread(target=LOGS.debug_print_thread)

        LOGS.inited = True
        LOGS.print("DEBUG Inited Successfully")
        LOGS.debug_thread.start()

    @staticmethod
    def print( *argv, message_type=1, sept=' ', output_filename="", console=True ):
        """

        :param argv:
        :param message_type:
        :param sept:
        :param output_filename:
        :param console:
        :return:
        """

        if not LOGS.debug_mode or (not LOGS.que_pre_init_msg and not LOGS.inited):
            print("Warning, Debug Log not initilized")
            return

        now = datetime.datetime.utcnow()
        time_str = now.strftime("%m/%d/%Y @ %H:%M:%S.%f")

        # make sure all the values in argv are strings
        argv = [ str( a ) for a in argv ]


        if message_type == LOGS.MSG_TYPE_WARNING:
            message_type_name = "WARNING"
        elif message_type == LOGS.MSG_TYPE_ERROR:
            message_type_name = "ERROR  "
        elif message_type == LOGS.MSG_TYPE_FATAL:
            message_type_name = "FATAL"
        else:
            message_type_name = "MESSAGE"

        LOGS.print_que.put( (time_str, message_type_name, sept.join(argv), output_filename, console) )

    @staticmethod
    def debug_print_thread( ):

        if not LOGS.inited or not LOGS.debug_mode:
            return

        print("started debug thread")

        LOGS.active = True

        while LOGS.active:

            log = LOGS.print_que.get(block=True, timeout=None)

            if len(log) == 5:
                log_time, log_type, message, output_file, console = log
            elif len(log) == 1 and log[0] == QUEUE_UNBLOCK_MESSAGE:
                print("Error: DEAD!")
                break
            else:
                print("Error: Invalid Log Message (", log, ") ")
                continue

            if console:
                print( " | {0} | {1} | {2} ".format( log_time, log_type, message ) )

            if output_file:
                LOGS.add_to_logs(output_file, " | {0} | {1} ".format( log_time, message ))

        LOGS.active = False
        print("dead debug thread")

    @staticmethod
    def add_to_logs( file_path, message ):

        # queue any messages that are outputed to files that do not exist.
        # The master commands are triggered before the master directory has been copied
        # with the builds stdout log :)
        # should proberly add some form of expire time to it.
        if not os.path.exists( file_path ):
            if file_path in LOGS.file_queue:
                LOGS.file_queue[file_path].append(message)
            else:
                LOGS.file_queue[file_path] = [ message ]
            print("message Queued for writing")
            return
        else:
            if file_path in LOGS.file_queue:
                message = '\n'.join( LOGS.file_queue[file_path] ) + "\n" + message
                del LOGS.file_queue[file_path]

        with open(file_path, "a") as log:
            log.write( message+"\n" )

    @staticmethod
    def close():

        LOGS.active = False

        # we must put an message into the que to make sure it gets un blocked
        LOGS.print_que.put( [ QUEUE_UNBLOCK_MESSAGE ] )


import queue as q
import threading
import datetime
import time
import os.path


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
    print_debug_intervals = 0 #1

    __log_messages_to_file = False
    __log_warning_to_file = False
    __log_errors_to_file = True
    __log_fatal_to_file = True


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
    def print( *argv, message_type=1, sept=' ', output_filename="" ):

        if not LOGS.debug_mode or (not LOGS.que_pre_init_msg and not LOGS.inited):
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

        LOGS.print_que.put( (time_str, message_type_name, sept.join(argv), output_filename) )

    @staticmethod
    def debug_print_thread( ):

        if not LOGS.inited or not LOGS.debug_mode:
            return

        print("started debug thread")

        LOGS.active = True

        while LOGS.active:

            time, type, message, output_file = LOGS.print_que.get(block=True, timeout=None)

            if output_file == "":
                print( " | {0} | {1} | {2} ".format( time, type, message ) )
            else:
                LOGS.add_to_logs(output_file, " | {0} | {1} ".format( time, message ))

        LOGS.active = False
        print("dead debug thread")

    @staticmethod
    def set_log_to_file( message=False, warning=False, error=True, fatal=True ):
        LOGS.__log_messages_to_file = message
        LOGS.__log_warning_to_file = warning
        LOGS.__log_error_to_file = error
        LOGS.__log_fatal_to_file = fatal

    @staticmethod
    def add_to_logs( file_path, message ):

        if os.path.exists(file_path):
            file_mode = 'a'
        else:
            file_mode = 'w'

        with open(file_path, file_mode) as log:
            log.write( "\n"+message )

    @staticmethod
    def close():

        LOGS.active = False

        # we must put an message into the que to make sure it gets un blocked
        LOGS.print_que.put( (LOGS.MSG_TYPE_DEFAULT, "| | Closing Debug (Unblock message)" ) )

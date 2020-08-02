import DEBUG
_print = DEBUG.LOGS.print


class SharedQueue:
    """shares a queue, with a dict of objects that the module can queue"""

    def __init__( self, queue ):

        self.__queue = queue    # the shared queue
        self.ACTIONS = {}       # dict of method/objects that can be shared

    def set_action( self, action_name, method ):
        self.ACTIONS[ action_name ] = method

    def set_actions( self, dict_of_actions ):
        self.ACTIONS = { **self.ACTIONS, **dict_of_actions }

    def clone( self, action_names ):
        """ clones the shared queue with only the required actions

        :param action_names:    list of action names that should be cloned with the queue
        :return:                the cloned shared queue
        """

        s_queue = SharedQueue( self.__queue )
        for a in action_names:
            if a in self.ACTIONS:
                s_queue.set_action( a, self.ACTIONS[a] )

        return s_queue

    def queue_task( self, action_name, **params ):

        if self.__queue is None:
            _print( "Unable to que web task, queue not set.", message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
            return

        if action_name not in self.ACTIONS:
            _print( "Action no found for shared queue", message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
            return

        self.__queue.put( self.ACTIONS[ action_name ]( **params ) )

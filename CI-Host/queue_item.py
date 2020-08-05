import DEBUG
_print = DEBUG.LOGS.print

class QueueItem:
    """Single use Queue Items"""

    __ACTIONS = {}

    def __init__(self, uac, project_name, action, build_hash=None, complete_callback=None, complete_message=None):

        self.uac = uac
        self.project_name = project_name
        self.build_hash = build_hash

        self.action = action
        self.item_action = None
        self.complete_callback = complete_callback  # callback must contain params for QueueItem, Successful
        self.complete_message = "Action {0} Complete".format( action )

        self.__executed = False

        if complete_message is not None:
            self.complete_message = complete_message

        if action in QueueItem.__ACTIONS:
            self.item_action = QueueItem.__ACTIONS[ action ]

    @staticmethod
    def add_action( action_name, action_callback ):
        """ Add and action to the queue items
            Callback must return successful status and have QueueItem param
        """
        QueueItem.__ACTIONS[action_name] = action_callback

    def execute( self ):

        if not self.__executed:
            _print("Queue item already executed")
            return

        self.__executed = True

        if self.item_action is not None:
            successful = self.item_action( self )
        else:
            _print("No Action assigned")
            successful = False

        if self.complete_callback is not None:
            self.complete_callback( self, successful )
        else:
            _print( "Queue Task", self.action, "Completed successful? ", successful )

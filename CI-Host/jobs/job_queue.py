import queue
import time

import DEBUG

_print = DEBUG.LOGS.print

class JobQueue:

    MAX_ACTIVE = 3

    def __init__(self):

        self.alive = False

        self.queue   = queue.Queue()    # thread safe queue.
        self.active  = []               # active jobs
        self.pending = []               # pending execution.

    def queue_job(self, job):
        pass

    def queueCount(self):
        """

        :return: (active count, pending count, queued count)
        """

        return len( self.active ), len( self.pending ), self.queue.qsize()

    def process_forever(self):
        """
            Processes the job queue until exited.
            (blocks thread)
        """

        self.alive = True

        #
        while self.alive:

            # wait for new job to be queued.
            new_job = self.queue.get( block=True )
            _print( "JobQueue: Collected new job!", console=True )

            # move the new job into the pending queue.
            # ...

            # process the pending and active queues,
            # unless theres a new job to be collected from the queue.
            while len( self.pending ) > 0 and self.queue.empty():
                # clean up any active jobs that have completed.
                for i in range( len(self.active)-1, -1, -1 ):
                    pass

                # promote pending tasks, while there are active slots available.
                while len( self.pending ) > 0 and len( self.active ) < JobQueue.MAX_ACTIVE:
                    pass

                # while theres no jobs to collect sleep for a second.
                if self.queue.empty():
                    time.sleep(1)

        self.alive = False

    def exit(self):

        self.alive = False
        _print( "JobQueue: exiting")

    # static methods
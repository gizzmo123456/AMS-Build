import DEBUG
import threading
import queue
import job

_print = DEBUG.LOGS.print

class JobQueue:

    def __init__(self):

        self.process = True
        self.__queue = queue.Queue()

        self.__active = []
        self.__pending = []

        self.thread_lock = threading.RLock()

    @property
    def active_jobs(self):
        return [ *self.__active ]   # make a copy of the list so the original cant be modified

    @property
    def pending_jobs(self):
        return [ *self.__pending ]  # make a copy of the list so the original cant be modified

    def queue_job(self, job_to_queue):
        """
            Thread safe method to queue a job
        :param job_to_queue: job object to be queued
        :return: None
        """
        if not isinstance( job_to_queue, job.Job ):
            _print( "Unable to queue item. Not a job", message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
            return

        self.__queue.put( job_to_queue )

    def process_forever(self):
        """ Processes the job queue until exited """
        while self.process:
            pass

    def exit(self):
        """
            Exits the job queue, without canceling any active or pending jobs.
            Once exited jobs can not progress until process_forever is call again
        :return: None
        """

        with self.thread_lock:
            self.process = False
            active_count = len( self.__active )
            pending_count = len( self.__pending )

        _print( f"Job queue exited. with {active_count} active jobs and {pending_count} pending jobs", message_type=DEBUG.LOGS.MSG_TYPE_WARNING )

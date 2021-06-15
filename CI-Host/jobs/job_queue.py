import DEBUG
import threading
import queue
import job
import time

_print = DEBUG.LOGS.print

class JobQueue:

    MAX_ACTIVE_JOBS = 2

    def __init__(self):

        self.process = True
        self.__queue = queue.Queue()

        self.__active = []
        self.__pending = []

        self.update_queue_file = False

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

            # wait for a new job to arrive while theres no jobs pending.
            new_job = self.__queue.get( block=True, timeout=None )
            _print("Collected new job")

            # process the active and pending queues
            # 1. when a new job arrives
            # 2. there are jobs pending to become active
            # 3. temporarily stop processing the active and pending queues if
            #    theres a new job waiting to progress into the pending queue
            while new_job is not None or len( self.pending_jobs ) > 0 and self.__queue.empty():
                # TODO: check that the job is valid.

                # move the new job to the pending queue.
                if new_job is not None:
                    self.__pending.append( new_job )
                    new_job = None

                # Clean up active tasks that have completed.
                for i in range( len( self.__active )-1, -1, -1 ):
                    if self.__active[i].status >= job.Job.STATUS["COMPLETE"]:
                        self.__active.pop( i )
                        self.update_queue_file = True
                        _print( f"Job completed with status {self.__active[i].status_name} ({ self.__active[i].status})" )

                # promote any pending tasks, if there is an active slot available.
                while len( self.__active ) < JobQueue.MAX_ACTIVE_JOBS and len( self.__pending ) > 0:
                    for i in range( len( self.__pending) ):
                        # make sure the status is pending.
                        # otherwise the job is waiting for the completion of another task.
                        if self.__pending[i].compare_status("PENDING"):
                            promoted_task = self.__pending.pop(i)
                            self.__active.append( promoted_task )
                            promoted_task.execute()
                            self.update_queue_file = True
                            _print( "promoted pending task to active." )

                if self.update_queue_file:
                    # TODO: update queue file.
                    _print( f"active tasks: {len(self.__active)}; pending tasks: {len(self.__pending)}")  # TODO: this should print out the name of the status rather than status code.

                # take a nap.
                time.sleep(1)

        _print(f"Job queue exited. with { len( self.__active ) } active jobs and { len( self.__pending ) } pending jobs", message_type=DEBUG.LOGS.MSG_TYPE_WARNING)

    def exit(self):
        """ (Thread safe method)
            Exits the job queue, without canceling any active or pending jobs.
            Once exited jobs can not progress until process_forever is call again
        :return: None
        """

        with self.thread_lock:
            self.process = False

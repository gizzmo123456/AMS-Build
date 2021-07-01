import queue
import time
import jobs.job as job

import DEBUG

_print = DEBUG.LOGS.print

class JobQueue:

    MAX_ACTIVE = 3
    __queue_job = None

    def __init__(self):

        self.alive = False

        self.queue   = queue.Queue()    # thread safe queue.
        self.active  = []               # active jobs
        self.pending = []               # pending execution.

        JobQueue._queue_job = self.queue_job

    def queue_job(self, job):

        if not isinstance( job, job.Job ):
            _print( "JobQueue: Unable to queue job. Item is not an instance of job.")
            return

        self.queue.put( job )


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
        update_queue_file = False

        #
        while self.alive:

            # wait for new job to be queued.
            new_job = self.queue.get( block=True )
            _print( "JobQueue: Collected new job!", console=True )

            # move the new job into the pending queue.
            if isinstance( new_job, job.Job ) :
                if new_job.status == job.Job.STATUS["CREATED"]:
                    self.pending.append( new_job )
                    update_queue_file = True
                else:
                    _print( f"JobQueue: Unable to queue job. Status is not CREATED. (status: {new_job.status} )" )

            # process the pending and active queues,
            # unless theres a new job to be collected from the queue.
            while len( self.pending ) > 0 and self.queue.empty():
                # clean up any active jobs that have completed.
                for i in range( len(self.active)-1, -1, -1 ):
                    if self.active[ i ].is_complete:
                        completed_job = self.active.pop( i )
                        update_queue_file = True
                        _print(f"JobQueue: Job Complete: {completed_job.name} ({completed_job.hash})")

                # promote pending tasks, while there are active slots available.
                while len( self.pending ) > 0 and len( self.active ) < JobQueue.MAX_ACTIVE:
                    promoted_job = self.pending.pop( 0 )
                    promoted_job.execute()
                    self.active.append( promoted_job )
                    update_queue_file = True
                    _print(f"JobQueue: Promoted job {promoted_job.name} ({promoted_job.hash})")

                if update_queue_file:
                    update_queue_file = False

                # while theres no jobs to collect sleep for a second.
                if self.queue.empty():
                    time.sleep(1)

        self.alive = False

    def exit(self):

        self.alive = False
        _print( "JobQueue: exiting")

    # static methods
    @staticmethod
    def create_jobs_from_pipeline( uac, project, **kwargs ):
        """
            Creates and queues jobs from pipeline file.
        :param uac:     user access controle object
        :param project: project to create jobs for
        :param kwargs:  additional data to be set into the job.
        """
        pass

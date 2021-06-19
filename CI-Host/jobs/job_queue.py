import DEBUG
import commonProject
import threading
import queue
import jobs.job as job_obj
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
        if not isinstance( job_to_queue, job_obj.Job ):
            _print( "Unable to queue item. Not a job", message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
            return

        self.__queue.put( job_to_queue )

    def create_jobs_from_pipeline( self, uac, project ):
        """
            Creates and queues jobs from the project pipeline config file
            if the uac permits ALL jobs
        :param uac:
        :param project:
        :param complete_callback:
        :return: True if successful full otherwise False
        """

        # authorize the activity by attempting to load the pipeline config.
        # if None is returned, either the project does not exist or the user
        # does not have access.
        pipeline_config = commonProject.get_project_pipeline( uac, project, v2_config=True )    # TODO: remove v2_config once change is complete.

        if pipeline_config is None:
            _print( "Unable to create job. Failed to load pipeline config." ) # TODO: find out if its an access or project issue
            return False

        if "jobs" not in pipeline_config:
            _print( "Unable to create jobs. Jobs not defined in pipeline config" )
            return False

        output_message = ""             # output message to be pushed into the complete callback.
        jobs_to_queue = []
        jobs = pipeline_config["jobs"]
        job_names = list(jobs)

        for job in job_names:
            # check stages has been defined and it contains at least one stage.
            if "stages" not in jobs[job]:
                output_message += f"Skipping job '{job}' stages not defined in pipeline\n"
                continue    # skip job. stages not defined in pipeline.
            elif len( jobs[job]["stages"] ) == 0:
                output_message += f"Skipping job '{job}' contains no stages\n"
                continue

            stages = jobs[job]["stages"]
            created_job, message = job_obj.Job.create_job_of_tasks( uac, project, stages )

            output_message += message

            if created_job is None:
                _print( output_message )
                return False

            jobs_to_queue.append( created_job )
            # TODO: Set the new job into the previous job, so it can be released once the previous job is released

            # premote the first job.
            jobs_to_queue[0].promote_to_pending()

        # queue jobs.
        for j in jobs_to_queue:
            self.queue_job( j )

        return True

    def process_forever(self):
        """ Processes the job queue until exited """
        while self.process:

            print_queue_stats = False

            # wait for a new job to arrive while theres no jobs pending.
            new_job = self.__queue.get( block=True, timeout=None )
            _print(f"Collected new job (jov status code: {new_job.status})")

            # process the active and pending queues
            # 1. when a new job arrives
            # 2. there are jobs pending to become active
            # 3. temporarily stop processing the active and pending queues if
            #    theres a new job waiting to progress into the pending queue
            while new_job is not None or len( self.pending_jobs ) > 0 and self.__queue.empty():
                # TODO: check that the job is valid.

                # move the new job to the pending queue.
                if new_job is not None:
                    if new_job.activity_count > 0:
                        self.__pending.append( new_job )
                    else:
                        _print("skipping new job. No activities set. (Unblock Task)")
                    new_job = None

                # Clean up active tasks that have completed.
                for i in range( len( self.__active )-1, -1, -1 ):
                    if self.__active[i].status >= job_obj.Job.STATUS["COMPLETE"]:
                        self.__active.pop( i )
                        self.update_queue_file = True
                        print_queue_stats = True
                        _print( f"Job completed with status {self.__active[i].status_name} ({ self.__active[i].status})" )

                # promote any pending tasks, if there is an active slot available.
                if len( self.__active ) < JobQueue.MAX_ACTIVE_JOBS:
                    for i in range( len( self.__pending) ):
                        # make sure the status is pending.
                        # otherwise the job is waiting for the completion of another task.
                        if self.__pending[i].compare_status("PENDING"):
                            promoted_task = self.__pending.pop(i)
                            self.__active.append( promoted_task )
                            promoted_task.execute()
                            self.update_queue_file = True
                            _print( "promoted pending task to active." )
                        print_queue_stats = True    # TODO: this needs to be tabbed over. (here for debuging)

                if self.update_queue_file:
                    # TODO: update queue file.
                    pass

                if print_queue_stats:
                    _print( f"active tasks: {len(self.__active)}; pending tasks: {len(self.__pending)}")  # TODO: this should print out the name of the status rather than status code.
                    print_queue_stats = False

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

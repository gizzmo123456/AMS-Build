import DEBUG
import threading
from jobs.base_activity import BaseActivity as Activity, BaseTask as Task, BaseAction as Action

# this must be here, even if the editor says otherwise.
import jobs.activity_import  # imports subclasses from tasks and actions file. (See notes in import)

_print = DEBUG.LOGS.print


class Job:
    """

    """

    STATUS = {
        "STARTING": -1,  # Job is currently being created
        "CREATED":   0,  # The job has been created but waiting to progress to pending
        "PENDING":   1,  # Pending to be promoted to an active task
        "RUNNING":   2,  # job is currently running
        "COMPLETE":  3,  # job has complete
        "FAILED":    4,  # job has failed
        "INVALID":   5,  # job is invalid
        "NO_AUTH":   6   # user does not have access to preform the job
    }

    JOB_TYPES = {"actions": Action.__get_subclasses_dict__(), "tasks": Task.__get_subclasses_dict__()}
    complete_callback = None    # params: job

    @property
    def access_level(self):
        """
            required access level to perform the job.
            (highest access level of the activities)
        """
        return self.__minimal_access_level

    def __init__(self, uac, project, **kwargs): # not sure if kwargs is necessary
        """

        :param uac:
        :param project:
        :param complete_callback:
        :param kwargs:
        """

        self.__status = Job.STATUS["STARTING"]
        self.__minimal_access_level = 2  # webhook and above

        self.uac = uac
        self.project = project

        self.data = kwargs

        self.job_worker = None
        self.job_lock = threading.RLock()   # TODO: make thread safe.

        self.current_activity_id = 0
        self.activities = []

        self.next_job = None

        self.__status = Job.STATUS["CREATED"]

    @property
    def status_name(self):
        for key in Job.STATUS:
            if Job.STATUS[key] == self.__status:
                return key

    @property
    def status(self):
        return self.__status

    def compare_status(self, status_name):
        """
            Compares the status with the jobs status
            :param status_name:
            :return True if status match otherwise false
        """
        return Job.STATUS[ status_name ] == self.__status

    def append_activity(self, activity):
        # Update the minimal access level.
        if activity.access_level() > self.__minimal_access_level:
            self.__minimal_access_level = activity.access_level

        self.activities.append( activity )

    @property
    def activity_count(self):
        return len( self.activities )

    def promote_to_pending(self):
        """Promotes the pending task to idle"""
        if self.status == Job.STATUS["CREATED"]:
            self.__status = Job.STATUS["PENDING"]
        else:
            _print("Unable to promote the job to IDLE. Task is not pending.")

    def execute(self):
        """
            executes the activities on a new thread
        """

        if self.status != Job.STATUS["PENDING"]:
            _print( f"Unable to start job. Status is not pending. (current status: {self.status})", message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
        elif self.job_worker is not None:
            _print( f"Unable to start job. Job worker is already set.")

        _print( "Starting job worker..." )

        self.job_worker = threading.Thread( target=self.execute_worker, args=() )
        self.job_worker.start()

    def execute_worker(self):

        while self.status < Job.STATUS["COMPLETE"]:

            _print( f"starting activity { self.current_activity_id + 1 } of {len( self.activities )} ")

            act = self.activities[ self.current_activity_id ]
            status, msg = act.execute()

            if status != Activity.STATUS["COMPLETE"]:
                self.__status = Job.STATUS["FAILED"]
                _print( f"Unable to complete job. The current activity has not exited with status COMPLETE (exit code: {status}, message: {msg}). Exiting job" )
                break

            _print("Attempting to clean up activity.")

            try:
                act.cleanup()
            except Exception as e:
                _print( "Unable to clean up activity.", e )

            self.current_activity_id += 1

            if self.current_activity_id == len( self.activities):
                self.__status = Job.STATUS["COMPLETE"]
                _print("All Activities are complete for current job")

                if self.next_job is not None:
                    self.next_job.promote_to_pending()
                    _print("promoting next job")

        self.__job_complete()

        _print("Exiting job...")

    def __job_complete(self):
        if Job.complete_callback is not None:
            Job.complete_callback(self)

    #########
    # Static Methods.
    # The static methods should be preferred over using the constructor directly.
    # Furthermore, mixing tasks and action should be avoided, since actions
    # usually required elevated privileges.

    # TODO: I think these static methods should be in the job queue.

    @staticmethod
    def create_job_of_tasks( uac, project, stages, complete_callback=None ):    # TODO: NOTE: im sure about this complete callback!
        """
            Creates a job of tasks to be performed on the project
        :param uac:
        :param project:
        :param stages: List of stages containing task. any stages containing actions will be skipped
        :return: tuple ( job, message ). Failed to create job if job is None, See message for details
        """
        job = Job( uac, project, complete_callback )
        output_message = ""

        for stage in stages:
            # check that a task has been defined and the task exists
            if "task" not in stage:
                return None, "Failed to create job, task not defined in stage"
            elif stage["task"] not in Job.JOB_TYPES["tasks"]:
                return None, f"Failed to create job. Task '{stage['task']}' does not exist"

            # create and authorize the task, appending it to the job if authorization was successful
            # otherwise reject the job.
            task = Job.JOB_TYPES["tasks"][ stage["task"] ](job, **stage)

            if uac.access_level < task.access_level():    # TODO: UAC Update.
                return None, "Failed to create job. User does not have permission to run task."

            job.append_activity( task )
            output_message += f"Added { stage['task'] } to job\n"

        return job, f"Successfully created job for {project}\n"+output_message

    @staticmethod
    def create_job_of_actions( uac, project, actions, complete_callback=None):
        """
            Creates a job of actions to be performed on the project and inserts
            it into the queue if uac permits.
        :param uac:
        :param project:
        :param actions:             list of actions
        :param complete_callback:
        :return: True if successful full otherwise False
        """
        return False

    @staticmethod
    def __create_job( uac, project, stages, task_type):
        # TODO:
        pass

import DEBUG
import threading
import common
import commonProject
from datetime import datetime
import time
import const
import cipher
import json
from jobs.base_activity import BaseActivity as Activity, BaseTask as Task, BaseAction as Action

# this must be here, even if the editor says otherwise.
import jobs.activity_import  # imports subclasses from tasks and actions file. (See notes in import)

_print = DEBUG.LOGS.print


class Job:
    """

    """

    STATUS = {
        "UNBLOCK":  -2,  # This job is be used to solely unblock the job queue.
                         # As a result the job is not fully initialized and therefore
                         # will be discarded without execution.
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

    @property
    def hash(self):
        try:
            return self.info["hash"]
        except:
            if self.__status == Job.STATUS["UNBLOCK"]:
                return "Unblock Task."
            else:
                return "Job hash not set! (None)"

    def __init__(self, uac, project, queue_unblock=False): # not sure if kwargs is necessary
        """

        :param uac:
        :param project:
        :param queue_unblock: if true, the job is discarded without execution.
        """

        self._activity_log_filepath = commonProject.get_activity_log_path( project )
        _print( f"Creating new job for project '{project}'. (Actor: {uac.username})",
                console=False, output_filename=self._activity_log_filepath )

        self.__status = Job.STATUS["STARTING"] if not queue_unblock else Job.STATUS["UNBLOCK"]
        self.__minimal_access_level = 2  # webhook and above

        self.uac = uac
        self.project = project

        if self.__status == Job.STATUS["UNBLOCK"]:
            _print(f"Created Unblock tast from project '{project}'. (Actor: {uac.username})",
                   console=False, output_filename=self._activity_log_filepath)
            return

        self.__project_paths = {
            "root": f"{const.PROJECT_DIRECTORY}/{project}"
        }

        self.info = {
            "index": None,
            "hash": None,
            "created_at": None,
            "executed_at": None,
            "completed_at": None
        }

        self.update_job_info()
        _print(f"Job index: {self.info['index']}; hash: {self.info['hash']}",
               console=False, output_filename=self._activity_log_filepath)

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

    def update_job_info(self):
        """
            Gets and update the project job information.
            (Creates the job info file if does not already exist)
        """

        # load or create a new job info file.

        default = {
            "ProjectName": self.project,
            "latest_job_index": -1,
            "latest_job_hash": "NONE",
            "last_job_created_time": -1,
            "last_job_execute_time": -1,
            "last_job_complete_time": -1
        }

        created, job_info = common.get_or_create_json_file(self.__project_paths["root"], "projectJobInfo.json", default)

        # Lock job info file, to minimize another job attempting to update the project info at the same time.
        # TODO: this should include the get or create json file.
        with common.LockFile( f"{self.__project_paths['root']}/projectJobInfo.json", "r+" ) as file:

            # update the basic job information, if not already set.
            if self.info["index"] is None:
                job_info["latest_job_index"] += 1
                self.info["index"] = job_info["latest_job_index"]

            if self.info["hash"] is None:
                self.info["hash"] = job_info["latest_job_hash"] = Job.__create_job_hash( self.project, self.info["index"] )

            if self.info["created_at"] is None:
                self.info["created_at"] = job_info["last_job_created_time"] = datetime.now().strftime( const.DATE_TIME_FORMAT )

            # Only update the executed and complete times if they have been set into the job.
            if self.info["executed_at"] is not None:
                job_info["last_job_execute_time"] = self.info["executed_at"]

            if self.info["completed_at"] is not None:
                job_info["last_job_complete_time"] = self.info["completed_at"]

            # update the job info file.
            file.seek(0)
            file.write( json.dumps( job_info ) )
            file.truncate()

    def promote_to_pending(self):
        """Promotes the pending task to idle"""
        if self.status == Job.STATUS["CREATED"]:
            self.__status = Job.STATUS["PENDING"]
            _print( f"Job {self.info['hash']}: Promoting job to IDLE. Task is not pending.",
                    console=False, output_filename=self._activity_log_filepath)
        else:
            _print( f"Job {self.info['hash']}: Unable to promote job to IDLE. Task is not pending.",
                    console=False, output_filename=self._activity_log_filepath)

    def execute(self):
        """
            executes the activities on a new thread
        """

        if self.status != Job.STATUS["PENDING"]:
            _print( f"Job {self.info['hash']}: Unable to start job. Status is not pending. (current status: {self.status})",
                    message_type=DEBUG.LOGS.MSG_TYPE_ERROR, console=False, output_filename=self._activity_log_filepath )
        elif self.job_worker is not None:
            _print( f"Job {self.info['hash']}: Unable to start job. Job worker is already set.",
                    console=False, output_filename=self._activity_log_filepath)

        _print( f"Job {self.info['hash']}: Starting job worker...", console=False, output_filename=self._activity_log_filepath )

        self.job_worker = threading.Thread( target=self.execute_worker, args=() )
        self.job_worker.start()

    def execute_worker(self):

        while self.status < Job.STATUS["COMPLETE"]:

            _print( f"Job {self.info['hash']}: starting activity { self.current_activity_id + 1 } of {len( self.activities )} ",
                    console=False, output_filename=self._activity_log_filepath)

            act = self.activities[ self.current_activity_id ]
            status, msg = act.execute()

            if status != Activity.STATUS["COMPLETE"]:
                self.__status = Job.STATUS["FAILED"]
                _print( f"Job {self.info['hash']}: Unable to complete job. The current activity has not exited with status COMPLETE (exit code: {status}, message: {msg}). Exiting job",
                        console=False, output_filename=self._activity_log_filepath )
                break

            _print( f"Job {self.info['hash']}: Attempting to clean up activity.",
                    console=False, output_filename=self._activity_log_filepath)

            try:
                act.cleanup()
            except Exception as e:
                _print( f"Job {self.info['hash']}: Unable to clean up activity.", e,
                        console=False, output_filename=self._activity_log_filepath )

            self.current_activity_id += 1

            if self.current_activity_id == len( self.activities):
                self.__status = Job.STATUS["COMPLETE"]
                _print( f"Job {self.info['hash']}: All Activities are complete for current job",
                        console=False, output_filename=self._activity_log_filepath)

                if self.next_job is not None:
                    self.next_job.promote_to_pending()
                    _print( f"Job {self.info['hash']}: promoting next job", console=False, output_filename=self._activity_log_filepath)

        self.__job_complete()

        _print(f"Exiting job {self.info['hash']}")

    def __job_complete(self):
        if Job.complete_callback is not None:
            Job.complete_callback(self)

    #########
    # Static Methods.

    @staticmethod
    def __create_job_hash( project_name, job_id ):
        return cipher.Hash.sha1(f"JOB-{project_name}-{job_id}-{time.time()}")

    # The static methods should be preferred over using the constructor directly.
    # Furthermore, mixing tasks and action should be avoided, since actions
    # usually required elevated privileges.

    # TODO: I think these static methods should be in the job queue.

    @staticmethod
    def create_job_of_tasks( uac, project, stages, **kwargs ):
        """
            Creates a job of tasks to be performed on the project
        :param uac:
        :param project:
        :param stages: List of stages containing task. any stages containing actions will be skipped
        :param kwargs: any additional data to be passed into the activities.
        :return: tuple ( job, message ). Failed to create job if job is None, See message for details
        """
        job = Job( uac, project )
        output_message = ""

        for stage in stages:
            # check that a task has been defined and the task exists
            if "task" not in stage:
                return None, "Failed to create job, task not defined in stage"
            elif stage["task"] not in Job.JOB_TYPES["tasks"]:
                return None, f"Failed to create job. Task '{stage['task']}' does not exist"

            # create and authorize the task, appending it to the job if authorization was successful
            # otherwise reject the job.
            task = Job.JOB_TYPES["tasks"][ stage["task"] ](job, **stage, **kwargs)

            if uac.access_level < task.access_level():    # TODO: UAC Update.
                return None, "Failed to create job. User does not have permission to run task."

            job.append_activity( task )
            output_message += f"Added { stage['task'] } to job\n"

        return job, f"Successfully created job for {project}\n"+output_message

    @staticmethod
    def create_job_of_actions( uac, project, actions ):
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

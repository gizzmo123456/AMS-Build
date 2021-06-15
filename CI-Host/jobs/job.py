import commonProject
import DEBUG

_print = DEBUG.LOGS.print


class Job:
    """

    """

    # TODO: change to a dict. to make it easier to print out the names rather than code.
    STATUS = {
        "STARTING": -1,# Job is currently being created
        "CREATED":   0,# The job has been created but waiting to progress to pending
        "PENDING":   1,# Pending to be promoted to an active task
        "RUNNING":   2,# job is currently running
        "COMPLETE":  3,# job has complete
        "FAILED":    4,# job has failed
        "INVALID":   5,# job is invalid
        "NO_AUTH":   6 # user does not have access to preform the job
    }

    JOB_TYPES = {"actions": {}, "tasks": {}}

    @property
    def access_level(self):
        """
            required access level to perform the job.
            (highest access level of the activities)
        """
        return self.__minimal_access_level

    def __init__(self, uac, project, complete_callback=None, **kwargs):
        """

        :param uac:
        :param project:
        :param complete_callback:
        :param kwargs:
        """

        self.__status = Job.STATUS["STARTING"]
        self.__minimal_access_level = 1

        self.uac = uac
        self.project = project
        self.complete_callback = complete_callback

        self.data = kwargs
        self.activities = []

        self.next_job = None

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
        if activity.access_level > self.__minimal_access_level:
            self.__minimal_access_level = activity.access_level

        self.activities.append( activity )

    def promote_to_idle(self):
        """Promotes the pending task to idle"""
        if self.status == Job.STATUS["CREATED"]:
            self.__status = Job.STATUS["PENDING"]
        else:
            _print("Unable to promote the job to IDLE. Task is not pending.")

    def execute(self):
        pass

    def release_next_job(self):
        if self.next_job is not None:
            self.next_job.promote_to_idle()

    #########
    # Static Methods.
    # The static methods should be preferred over using the constructor directly.
    # Furthermore, mixing tasks and action should be avoided, since actions
    # usually required elevated privileges.

    # TODO: I think these static methods should be in the job queue.

    @staticmethod
    def create_jobs_from_pipeline( uac, project, complete_callback=None ):
        """
            Creates a list of jobs from the project pipeline config file
            and inserts them into the queue if uac permits ALL jobs
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
            complete_callback( False, "Unable to create job. Failed to load pipeline config." ) # TODO: find out if its an access or project issue
            return False

        if "jobs" not in pipeline_config:
            complete_callback( False, "Unable to create jobs. Jobs not defined in pipeline config" )
            return False

        output_message = ""             # output message to be pushed into the complete callback.
        jobs_to_queue = []
        jobs = pipeline_config["jobs"]
        job_names = list(jobs["jobs"])

        for job in job_names:
            # check stages has been defined and it contains at least one stage.
            if "stages" not in jobs[job]:
                output_message += f"Skipping job '{job}' stages not defined in pipeline\n"
                continue    # skip job. stages not defined in pipeline.
            elif len( jobs[job]["stages"] ) == 0:
                output_message += f"Skipping job '{job}' contains no stages\n"
                continue

            stages = jobs[job]["stages"]
            created_job, message = Job.create_job_of_tasks( uac, project, stages )

            output_message += message

            if created_job is None:
                complete_callback( False, output_message )
                return False

            jobs_to_queue.append( created_job )
            # TODO: Set the new job into the previous job, so it can be released once the previous job is released

        # TODO: Queue jobs.

        return True

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
                return None, "Failed to create job, task no defined"
            elif stage["task"] not in Job.JOB_TYPES["tasks"]:
                return None, f"Failed to create job. Task '{stage['task']}' does not exist"

            # create and authorize the task, appending it to the job if authorization was successful
            # otherwise reject the job.
            task = Job.JOB_TYPES["tasks"][ stage["task"] ](uac, project, complete_callback, stage)

            if uac.access_level < task.access_level:    # TODO: UAC Update.
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

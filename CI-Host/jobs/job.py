import commonProject

class Job:
    """

    """

    STATUS_STARTING = 0
    STATUS_IDLE     = 1
    STATUS_RUNNING  = 2
    STATUS_COMPLETE = 3
    STATUS_FAILED   = 4
    STATUS_INVALID  = 5
    STATUS_NO_AUTH  = 6

    @property
    def access_level(self):
        """
            required access level to perform the job.
            (highest access level of the activities)
        """
        return 1

    def __init__(self, uac, project, complete_callback=None, **kwargs):
        """

        :param uac:
        :param project:
        :param complete_callback:
        :param kwargs:
        """

        self.__status = Job.STATUS_STARTING

        self.uac = uac
        self.project = project
        self.complete_callback = complete_callback

        self.data = kwargs
        self.activities = []

    @property
    def status(self):
        return self.__status

    def execute(self):
        pass

    #########
    # Static Methods.
    # The static methods should be preferred over using the constructor directly.
    # Furthermore, mixing tasks and action should be avoided, since actions
    # usually required elevated privileges.

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
        pipeline_config = commonProject.get_project_pipeline( uac, project )

        if pipeline_config is None:
            complete_callback( False, "Unable to create job. Failed to load pipeline config." ) # TODO: find out if its an access or project issue
            return False

        # TODO: Create tasks and job from pipeline

        return True

    @staticmethod
    def create_job_of_tasks( uac, project, tasks, complete_callback=None):
        """
            Creates a job of tasks to be performed on the project and inserts
            it into the queue if uac permits.
        :param uac:
        :param project:
        :param tasks:
        :param complete_callback:
        :return: True if successful full otherwise False
        """
        return False

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

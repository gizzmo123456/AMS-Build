import commonProject

class BaseActivity:
    """
    TODO: ...
    """
    # the internal activity status (in priority order)
    ACT_STATUS_STARTING  = 0    # starting the activity
    ACT_STATUS_IDLE      = 1    # waiting to run the activity
    ACT_STATUS_RUNNING   = 2    # running the activity
    ACT_STATUS_COMPLETE  = 3    # activity has complete
    ACT_STATUS_INVALID   = 4    # invalid activity
    ACT_STATUS_NO_AUTH   = 5    # unable to authorize the user who created the activity

    @property
    def access_level(self):
        """ Minimal access level to the project """
        return 2    # webhooks and above

    def __init__(self, uac, project, complete_callback=None, **kwargs):
        """
        Note: the constructor should not be overridden, since it authorizes the
              activity before any potentially sensitive information is loaded in.
              Override init method instead
        :param uac:                 uac for the user who autherize the activity
        :param project:             project to preform the activity on
        :param complete_callback:   method to be called when activity is complete (params: successful, message)
        :param kwargs:              any additional data
        """

        self.__status = BaseActivity.ACT_STATUS_STARTING        # Status of activity

        self.uac = uac
        self.project = project
        self.complete_callback = complete_callback

        self.data = kwargs

        # authorize the activity by attempting to load the pipeline config.
        # if None is returned, either the project does not exist or the user does not have access
        self.pipeline_conf = commonProject.get_project_pipeline( uac, project )

        if self.pipeline_conf is None:
            self.__status = BaseActivity.ACT_STATUS_NO_AUTH
            self.complete( False, "Unable to load pipeline config" ) # TODO: find out if its an access or project issue
            return

        self.__format_values = {}
        self.__private_format_values = {}

        self.init()

        self.__status = BaseActivity.ACT_STATUS_IDLE


    def init(self):
        """(abstract method to initialize activity)"""
        pass

    @property
    def is_valid(self):
        """is the task valid"""
        return self.__status < BaseActivity.ACT_STATUS_INVALID

    @property
    def authorized(self):
        """Is the trigger user authorized to perform this activity"""
        return BaseActivity.ACT_STATUS_STARTING < self.__status < BaseActivity.ACT_STATUS_NO_AUTH

    def get_format_value(self, key):
        return self.__format_values.setdefault( key, None )

    def __get_format_values(self, key): # for internal use only
        """Gets """
        v = self.__private_format_values.setdefault( key, None )
        v = self.__format_values.setdefault( key, None ) if v is None else v
        return v

    def set_format_value(self, key, value, private=False):
        pass

    def execute(self):
        # return (status, promote task)
        self.__status = BaseActivity.ACT_STATUS_RUNNING
        pass

    def cleanup(self):
        pass

    def terminate(self):
        pass

    def complete(self, successful, message):

        if self.__status < BaseActivity.ACT_STATUS_COMPLETE:
            self.__status = BaseActivity.ACT_STATUS_COMPLETE

        self.complete_callback( successful, message )

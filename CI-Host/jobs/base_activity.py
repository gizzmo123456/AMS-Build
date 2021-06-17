from const import *
import commonProject
from datetime import datetime

class BaseActivity:
    """
    TODO: make Thread safe
    """
    # the internal activity status (in priority order)
    STATUS = {
        "CREATING": 0,  # Creating the activity
        "IDLE":     1,  # waiting to run the activity
        "ACTIVE":   2,  # running the activity
        "COMPLETE": 3,  # activity has complete
        "INVALID":  4,  # invalid activity
        "NO_AUTH":  5   # unable to authorize the user who created the activity
    }

    @property
    def activity_name(self):
        """  """
        return "BASE-ACTIVITY"

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
        :param kwargs:              stage/activity data (from config/pipeline file)
        """

        self.__status = BaseActivity.STATUS["CREATING"]   # Status of activity

        self.uac = uac
        self.project = project
        self.complete_callback = complete_callback

        self.activity_data = kwargs     # stage/activity data fro config/pipeline.

        # authorize the activity by attempting to load the pipeline config.
        # if None is returned, either the project does not exist or the user does not have access
        self.pipeline_conf = commonProject.get_project_pipeline( uac, project )

        if self.pipeline_conf is None:
            self.__status = BaseActivity.STATUS["NO_AUTH"]
            self.complete( False, "Unable to load pipeline config" ) # TODO: find out if its an access or project issue
            return

        build_name = "BUILD-NAME-HERE" # TODO: <<

        # NOTE: there should be no overlap in key values between the public and private format values.
        # define default data for all activities
        self.__format_values = {
            "name": build_name,
            # project
            "project": project,
            "branch": "master",
            # hashes
            "activity_hash": "some hash in sha-1",
            # util
            "actor": uac.username,
            "created_at": datetime.now().strftime( DATE_TIME_FORMAT ),
            "completed_at": None,
        }

        # define project directories
        self.__private_format_values = {
            "project_dir":        f"{PROJECT_DIRECTORY}/{project}/master",
            "output_dir":         f"{PROJECT_DIRECTORY}/{project}/builds/{build_name}",
            "project_source_dir": f"{PROJECT_DIRECTORY}/{project}/master/project_source",
            "output_source_dir":  f"{PROJECT_DIRECTORY}/{project}/builds/{build_name}",
            "logs_output_dir":    f"{PROJECT_DIRECTORY}/{project}/logs"                        # TODO: add logs directory
        }

        self.init()

        self.__status = BaseActivity.STATUS["IDLE"]


    def init(self):
        """(abstract method to initialize activity)"""
        pass

    @property
    def is_valid(self):
        """is the task valid"""
        return self.__status < BaseActivity.STATUS["INVALID"]

    @property
    def authorized(self):
        """Is the trigger user authorized to perform this activity"""
        return BaseActivity.STATUS["CREATING"] < self.__status < BaseActivity.STATUS["NO_AUTH"]

    def get_format_value(self, key, default_value=None):
        return self.__format_values.setdefault( key, default_value )

    def __get_format_values(self, key): # for internal use only
        """Gets the private or public format value"""
        v = self.__private_format_values.setdefault( key, None )
        v = self.__format_values.setdefault( key, None ) if v is None else v
        return v

    def set_format_value(self, key, value, private=False):

        if private:
            self.__private_format_values[ key ] = value
        else:
            self.__format_values[ key ] = value

    def execute(self):
        """
        execute the activity ()
        :return: None
        """

        if not self.uac.has_project_access( self.project ):
            self.__status = BaseActivity.STATUS["NO_AUTH"]
            self.complete_callback( False, "Unable to execute activity. User is not authorized.")
            return

        self.__status = BaseActivity.STATUS["ACTIVE"]
        successful, message = self.activity()
        self.__status = BaseActivity.STATUS["COMPLETE"]

        self.complete( successful, message )

    def activity(self):
        """(abstract method) to preform activity
            :returns: successful, Message
        """
        return False, "Activity not implemented"

    def cleanup(self):
        """ Cleans up the activity once complete"""
        raise Exception("Not implemented")

    def terminate(self):
        """ Terminate the activity """
        raise Exception("Not implemented")

    def complete(self, successful, message):

        if self.__status < BaseActivity.STATUS["COMPLETE"]:
            self.__status = BaseActivity.STATUS["COMPLETE"]

        self.complete_callback( successful, message )

from const import *
from datetime import datetime

# NOTE: when adding a new activity, make sure to inherit from 'BaseTask' or 'BaseAction' (or any subclass of the two)
#       The will ensure that the activity is registered into Job.JOB_ACTIVITIES. See base classes at bottom.
class BaseActivity:
    """
    TODO: make Thread safe
    """
    # the internal activity status (in priority order)
    STATUS = {
        "CREATING": 0,  # Creating the activity
        "IDLE":     1,  # waiting to run the activity
        "ACTIVE":   2,  # running the activity
        "COMPLETE": 3,  # activity has complete successfully
        "FAILED":   4,  # activity has failed
        "INVALID":  5   # invalid activity
    }

    @staticmethod
    def __ba_get_all_subclasses__( cls ):
        """
            This method should only be used by classes that directly inherit from BaseActivity
            for instance, BaseTask and BaseActivity.
            Use BaseTask/BaseActivity.__get_subclasses_dict__() instead.
        """
        if not issubclass( cls, BaseActivity ):
            print(cls, "is not a subclass of BaseActivity")
            return []

        direct_sc = cls.__subclasses__()
        indirect_sc = []

        for sc in direct_sc:
            indirect_sc.extend( BaseActivity.__ba_get_all_subclasses__( sc ) )

        return [ *direct_sc, *indirect_sc ]

    @staticmethod
    def __get_subclasses_dict__():
        raise Exception("Not Implemented")

    @staticmethod
    def access_level():
        """ Minimal access level to run the activity"""
        return 2    # webhooks and above

    def __init__(self, job, **kwargs):
        """
        :param job:     the job that owns/created the activity
        :param kwargs:  stage/activity data (from config/pipeline file)
        """

        self.__status = BaseActivity.STATUS["CREATING"]   # Status of activity

        self.job = job                  # the job that owns/created the activity
        self.activity_data = kwargs     # stage/activity data from config/pipeline.

        output_name = "BUILD-NAME-HERE" # TODO: <<

        # NOTE: there should be no overlap in key values between the public and private format values.
        # define default data for all activities
        self.__format_values = {
            "output-name": output_name,
            # project
            "project": job.project,
            "branch": "master",                     # TODO: <<
            # hashes
            "activity_hash": "some hash in sha-1",  # TODO: <<
            # util
            "actor": job.uac.username,
            "created_at": datetime.now().strftime( DATE_TIME_FORMAT ),
            "completed_at": None,
        }

        # define project directories
        base_dir = f"{PROJECT_DIRECTORY}/{job.project}"

        self.__private_format_values = {
            "project_dir":        f"{base_dir}/master",
            "project_source_dir": f"{base_dir}/master/project_source",
            "output_dir":         f"{base_dir}/builds/{output_name}",
            "output_source_dir":  f"{base_dir}/builds/{output_name}",
            "logs_output_dir":    f"{base_dir}/logs/{output_name}"  # TODO: add logs directory
        }

        self.init()

        self.__status = BaseActivity.STATUS["IDLE"]

    def init(self):
        """(abstract method to initialize activity)"""
        pass

    @property
    def status(self):
        return self.__status

    @property
    def is_valid(self):
        """is the task valid"""
        return self.__status < BaseActivity.STATUS["INVALID"]

    def get_format_value(self, key, default_value=None):
        return self.__format_values.setdefault( key, default_value )

    def __get_format_value(self, key): # for internal use only
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
        execute the activity
        :returns: status, message
        """

        # TODO: check job state and permision.

        self.__status = BaseActivity.STATUS["ACTIVE"]

        self.__status, message = self.activity()

        self.set_format_value( "completed_at", datetime.now().strftime( DATE_TIME_FORMAT ) )

        return self.__status, message

    def activity(self):
        """(abstract method) to preform activity
            :returns: status, Message
        """
        return BaseActivity.STATUS["INVALID"], "Activity not implemented"

    def cleanup(self):
        """ Cleans up the activity once complete"""
        raise Exception("Not implemented")

    def terminate(self):
        """ Terminate the activity """
        raise Exception("Not implemented")


class BaseTask( BaseActivity ):

    @staticmethod
    def __get_subclasses_dict__():
        subclasses = BaseActivity.__ba_get_all_subclasses__( BaseTask )
        return dict( zip( [sc.__name__.lower() for sc in subclasses ], subclasses ))


class BaseAction( BaseActivity ):

    @staticmethod
    def __get_subclasses_dict__():
        subclasses = BaseActivity.__ba_get_all_subclasses__(BaseAction)
        return dict(zip([sc.__name__.lower() for sc in subclasses], subclasses))

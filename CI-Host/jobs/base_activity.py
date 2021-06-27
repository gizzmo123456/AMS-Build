from const import *
from datetime import datetime
import time
import commonProject
import hashlib
import DEBUG

_print = DEBUG.LOGS.print

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

        # load in the config file if defined in kwargs
        if "conf" in kwargs:
            conf = commonProject.get_project_config( job.uac, job.project, kwargs["conf"] )
            if conf is not None:
                self.activity_data.update( conf )
            else:
                _print( f"unable to load config file '{kwargs['conf']}' for project {job.project}")

        # NOTE: there should be no overlap in key values between the public and private format values.
        # define default data for all activities
        self._format_values = {
            "job-name": kwargs.get("job-name", "Not-Defined"),
            # project
            "project": job.project,
            "branch": "master",                     # TODO: <<
            "job-index": job.info["index"],
            # hashes
            "job_hash": job.info["hash"],
            "activity_hash": BaseActivity.__create_activity_hash( job.project, self.__class__.__name__ ),
            "git_hash": self.activity_data.get("git_hash", None),
            # util
            "actor": job.uac.username,
            "created_at": datetime.now().strftime( DATE_TIME_FORMAT ),
            "executed_at": None,
            "completed_at": None
        }

        output_name = kwargs.get("output-name-format", DEFAULT_OUTPUT_NAME_FORMAT)
        try:
            output_name = self._format_values["output-name"] =  output_name.format(**self._format_values)
        except KeyError as e:
            _print(f"Unable to format output name. (Key error: {e}) Using default output format instead", message_type=DEBUG.LOGS.MSG_TYPE_WARNING)
            output_name = self._format_values["output-name"] = DEFAULT_OUTPUT_NAME_FORMAT.format(**self._format_values)

        # define project directories
        base_dir = f"{PROJECT_DIRECTORY}/{job.project}"

        self._private_format_values = {
            "root":                  base_dir,
            "project_dir":        f"{base_dir}/master",
            "project_source_dir": f"{base_dir}/master/project_source",
            "project_config_dir": f"{base_dir}/master/config",
            "output_dir":         f"{base_dir}/builds/{output_name}",                       # TODO: change builds to outputs
            "output_source_dir":  f"{base_dir}/builds/{output_name}/project_source",        # TODO: change builds to outputs
            "output_config_dir":  f"{base_dir}/builds/{output_name}/config",                # TODO: change builds to outputs
            "logs_output_dir":    f"{base_dir}/builds/{output_name}/logs"                   # TODO: add logs directory
        }

        self.init()

        self.__status = BaseActivity.STATUS["IDLE"]

    def init(self):
        """(abstract method to initialize activity)"""
        pass

    @property
    def log_header(self):
        return f"{'=' * 24}\n" \
               f"Activity - {self.__class__.__name__}\n" \
               f"{'=' * 24}\n"

    @property
    def status(self):
        return self.__status

    @property
    def is_valid(self):
        """is the task valid"""
        return self.__status < BaseActivity.STATUS["INVALID"]

    def get_format_value(self, key, default_value=None):
        return self._format_values.get( key, default_value )

    def _get_format_value(self, key, default_value=None): # for internal use only
        """Gets the private or public format value"""
        v = self._private_format_values.get( key, None )
        v = self._format_values.get( key, None ) if v is None else v
        return v if v is not None else default_value

    @property
    def _all_format_values(self):
        return { **self._format_values, **self._private_format_values }

    def set_format_value(self, key, value, private=False):

        if private:
            self._private_format_values[ key ] = value
        else:
            self._format_values[ key ] = value

    def execute(self):
        """
        execute the activity
        :returns: status, message
        """

        # TODO: check job state and permision.

        self.__status = BaseActivity.STATUS["ACTIVE"]
        self._format_values["executed_at"] = datetime.now().strftime( DATE_TIME_FORMAT )

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

    @staticmethod
    def __create_activity_hash( project_name, activity_name ):
        s = hashlib.sha1()
        s.update( f"ACTIVITY-{project_name}-{activity_name}-{time.time()}".encode() )
        return s.hexdigest()


class BaseTask( BaseActivity ):

    def __init__(self, job, **kwargs):
        super().__init__(job, **kwargs)

    @staticmethod
    def __get_subclasses_dict__():
        subclasses = BaseActivity.__ba_get_all_subclasses__( BaseTask )
        return dict( zip( [sc.__name__.lower() for sc in subclasses ], subclasses ))


class BaseAction( BaseActivity ):

    def __init__(self, job, **kwargs):
        super().__init__(job, **kwargs)

    @staticmethod
    def __get_subclasses_dict__():
        subclasses = BaseActivity.__ba_get_all_subclasses__(BaseAction)
        return dict(zip([sc.__name__.lower() for sc in subclasses], subclasses))

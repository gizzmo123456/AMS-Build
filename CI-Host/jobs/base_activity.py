import const
import commonProject
import cipher
import time
import datetime
import user_access_control as uac
import helpers

import DEBUG

_print = DEBUG.LOGS.print

class BaseActivity:
    """
        Base activity for Actions and Tasks

        Support stage values for all activities:
          key : description
          -----------------
        - name: (optional) Name of activity or tasks [default: "stage-{index}]
        - conf: (optional) config file to supplement data in the pipeline file. (loc: ../project/msater/config/{file}.json)
                The config file overrides the pipeline stage data.

    """

    STATUS = {
        "INIT"      : -4,
        "CREATED"   : -3,
        "PENDING"   : -2,
        "ACTIVE"    : -1,
        "COMPLETE"  :  0,
        "FAILED"    :  1,
        "NO-AUTH"   :  2
    }

    @property
    def short_hash(self):
        return self.hash[:7]

    @property
    def activity_name(self):
        return self.__class__.__name__.lower()

    @property
    def print_label(self):
        return f"Activity '{self.name}' ({self.short_hash}):"

    @property
    def output_file_header(self):
        return f"\n{'='*24}\n"\
               f"Activity:       {self.activity_name}\n"\
               f"Name:           {self.name}\n"\
               f"Hash:           {self.hash} ({self.short_hash})\n"\
               f"Executed at:    {self.stage_data['executed-at']}\n"\
               f"{'='*24}"

    @property
    def redirect_print(self):
        return {
            "console": False,
            "output_filename": self.job.output_log_path
        }

    @staticmethod
    def access_level():
        return uac.UAC.TRIGGER

    def __init__(self, name, job, stage ):

        self._status = BaseActivity.STATUS["INIT"]

        self.name = name
        self.hash = cipher.Hash.sha1( f"act-{self.activity_name}-{name}-{time.time()}" )

        self.job = job
        self.stage_data = {
            "executed-at": None,
            "completed-at": None
        }

        self._data = {}    # any data that is private/protected to the activity

        self.set_stage_data( stage )
        self.init()

        self._status = BaseActivity.STATUS["CREATED"]

    def init(self):
        """(abstract) Method to extend __init__()"""
        pass

    def set_stage_data(self, data):
        """
            Sets the stage data, also loading in the config file if supplied
            (virtual method intended to set relevent stage data into the self.job.data )
        """

        self.stage_data.update(data)

        if "conf" in data:
            # load in the conf file and update the stage data
            conf = commonProject.get_project_config( self.job.uac, self.job.project, data["conf"] )
            if conf is not None:
                self.stage_data.update( conf )

    def _update_stage_data(self, key, value, append_to_job=False ):

        self.stage_data[key] = value

        if append_to_job:
            self.job.update_data( **{f"{self.name}.{key}": value} )

    def execute(self):

        self._status = BaseActivity.STATUS["ACTIVE"]
        self._update_stage_data( "executed-at",
                                 datetime.datetime.now().strftime( const.DATE_TIME_FORMAT ),
                                 append_to_job=True )

        _print( self.output_file_header, **self.redirect_print )

        successful = self.activity()

        self._status = BaseActivity.STATUS["COMPLETE"] if successful else BaseActivity.STATUS["FAILED"]

        self._update_stage_data( "completed-at",
                                 datetime.datetime.now().strftime( const.DATE_TIME_FORMAT ),
                                 append_to_job=True )

        return successful

    def activity(self):
        raise Exception("Not implemented")

    def terminate(self):
        raise Exception("Not implemented")

    # static methods
    @staticmethod
    def get_subclass_dict():
        raise Exception("Not implemented")


class BaseTask(BaseActivity):

    def __init__(self, name, job, stage_data):
        super().__init__(name, job, stage_data)

    @staticmethod
    def get_subclass_dict():
        subclasses = helpers.get_all_subclasses_of_type( BaseActivity, BaseTask )
        return dict(zip([sc.__name__.lower() for sc in subclasses], subclasses))


class BaseAction(BaseActivity):

    def __init__(self, name, job, stage_data):
        super().__init__(name, job, stage_data)

    @staticmethod
    def get_subclass_dict():
        subclasses = helpers.get_all_subclasses_of_type( BaseActivity, BaseTask )
        return dict(zip([sc.__name__.lower() for sc in subclasses], subclasses))


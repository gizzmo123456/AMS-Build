import commonProject
import cipher
import time
import user_access_control as uac
import helpers

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

    @staticmethod
    def access_level():
        return uac.UAC.TRIGGER

    def __init__(self, name, job, stage ):

        self._status = BaseActivity.STATUS["INIT"]

        self.name = name
        self.hash = cipher.Hash.sha1( f"act-{self.activity_name}-{name}-{time.time()}" )

        self.job = job
        self.stage_data = {}

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

        self.stage_data = data

        if "conf" in data:
            # load in the conf file and update the stage data
            conf = commonProject.get_project_config( self.job.uac, self.job.project, data["conf"] )
            if conf is not None:
                self.stage_data.update( conf )

    def execute(self):
        pass

    def terminate(self):
        pass

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


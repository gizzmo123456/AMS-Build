import cipher
import time
import user_access_control as uac
import helpers

class BaseActivity:

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
    def print_label(self):
        return f"Activity '{self.name}' ({self.hash[:7]}):"

    @staticmethod
    def access_level():
        return uac.UAC.TRIGGER

    def __init__(self, name, job, stage ):

        self._status = BaseActivity.STATUS["INIT"]

        self.name = name
        self.hash = cipher.Hash.sha1( f"act-{self.__class__.__name__}-{name}-{time.time()}" )

        self.job = job
        self.stage_data = {}

        self.__dir = {}

        self.set_stage_data( stage )
        self.init()

        self._status = BaseActivity.STATUS["INIT"]

    def init(self):
        """(abstract) Method to extend __init__()"""
        pass

    def set_stage_data(self, data):
        """
            Sets the stage data
            (virtual method intended to set relevent stage data into the self.job.data )
        """

        self.stage_data = data

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


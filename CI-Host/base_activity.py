import cipher
import time
import user_access_control as uac

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

    @property
    def access_level(self):
        return uac.UAC.TRIGGER

    def __init__(self, name, job):

        self._status = BaseActivity.STATUS["INIT"]

        self.name = name
        self.hash = cipher.Hash.sha1( f"act-{self.__class__.__name__}-{name}-{time.time()}" )

        self.job = job

        self.__dir = {}

        self.init()

        self._status = BaseActivity.STATUS["INIT"]

    def init(self):
        """(abstract) Method to extend __init__()"""
        pass

    def execute(self):
        pass

    def terminate(self):
        pass

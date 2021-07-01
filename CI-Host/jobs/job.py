import threading


class Job:

    STATUS = {
        "UNBLOCK": -99,
        "INIT": -4,
        "CREATED": -3,
        "PENDING": -2,
        "ACTIVE": -1,
        "COMPLETED": 0,
        "FAILED": 1,
        "INVALID": 2,
        "NO-AUTH": 3
    }

    def __init__(self):

        self._status = Job.STATUS["INIT"]
        self.name = ""
        self.hash = ""

        self.activities = {}    # key: user defined name, value: activity. (if the name if undefined auto generated.)

        self.job_thread = None
        self.thread_lock = threading.RLock()

        self.init()

        self._status = Job.STATUS["CREATED"]

    def init(self):
        """(abstract) method to extend init"""
        pass

    @property
    def status(self):
        return self._status

    @property
    def status_name(self):
        for stat_name in Job.STATUS:
            if self._status == Job.STATUS[stat_name]:
                return stat_name

        return "Unknown Status"

    @property
    def is_complete(self):
        return self._status == Job.STATUS["COMPLETE"] and self.job_thread is not None and not self.job_thread.is_alive()

    def execute(self):
        pass

    def execute_thread(self):
        pass

    def terminate(self):
        pass


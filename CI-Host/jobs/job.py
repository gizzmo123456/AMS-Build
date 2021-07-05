import jobs.base_activity as base_activities
import jobs.activities_import  # this import must be here, even if the editor says otherwise.
import cipher
import threading
import time
import datetime
import const
import DEBUG

_print = DEBUG.LOGS.print

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

    ACTIVITIES = {
        "TASKS": base_activities.BaseTask.get_subclass_dict(),
        "ACTIONS": base_activities.BaseAction.get_subclass_dict()
    }

    @property
    def print_label(self):
        return f"Job '{self.name}' ({self.hash[:7]}):"

    @property
    def short_hash(self):
        return self.hash[:7]

    def __init__(self, job_name, uac, project, **data ):
        """

        :param job_name: name of job
        :param uac:      uac object to authorize job
        :param project:  projuect that job belongs to
        :param data:     any public data to be included in self.data
        """

        self._status = Job.STATUS["INIT"] if uac.has_project_access( project ) else Job.STATUS["NO-AUTH"]

        self.name = job_name
        self.project = project
        self.hash = cipher.Hash.sha1( f"job-{job_name}-{time.time()}" )
        self.uac = uac

        _print( f"Job {job_name} ({self.hash[:7]}) Created for project {project}")

        self.current_activity_id = 0
        self.activities = {}    # key: user defined name, value: activity. (if the name if undefined auto generated.)

        # default data, that is available to all activities.
        # Data is extended by the activities that are run.
        self.data = {
            #
            "job-name": job_name,
            "job-hash": self.hash,
            # stats
            "current-activity-id": -1,
            "activity-count": 0,
            # project
            "project": project,
            "project-branch": "master",
            # Actor
            "created-by": uac.username,
            "created-origin": uac.origin,
            # time
            "created-at": datetime.datetime.now().strftime( const.DATA_TIME_FORMAT ),
            "executed-at": None,
            "completed-at": None,
            **data
        }

        self.job_thread = None
        self.thread_lock = threading.RLock()

        if self._status == Job.STATUS["INIT"]:
            self._status = Job.STATUS["CREATED"]

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
        return self._status == Job.STATUS["COMPLETED"] and self.job_thread is not None and not self.job_thread.is_alive()

    def append_activity(self, activity ):

        if not isinstance( activity, base_activities.BaseActivity ):
            _print( f"{self.print_label} Unable to append activity. Activity is not of type BaseActivity" )
            return

        if self._status != Job.STATUS["CREATED"]:
            _print(f"{self.print_label} Unable to append activity. (Status: {self.status_name})")

        self.activities[ activity.name ] = activity
        self.data[ "activity-count"] += 1

        _print( f"{self.print_label} Activity '{activity.activity_name}:{activity.name}' ({activity.short_hash}) appended to job. (activity count: {self.data['activity-count']})")

    def add_unique_data(self, **data ):
        """ Adds data to the to self.data if the values does not already exist."""
        for d in data:
            self.data.setdefault( d, data[d] )

    def update_data(self, **data ):
        """ Updates self.data, overwriting any values that already exist."""
        self.data.update( data )

    def execute(self):

        if self._status != self.STATUS["PENDING"]:
            _print(f"{self.print_label} Unable to execute job status is not pending. (current status: {self._status})")
            return
        elif self.job_thread is not None:
            _print(f"{self.print_label} Unable to execute job. Already executed? ")
            return
        else:
            _print(f"{self.print_label} Starting job thread...")

        self._status = Job.STATUS["ACTIVE"]

        self.job_thread = threading.Thread( target=self.execute_thread )
        self.job_thread.start()

    def execute_thread(self):

        # execute each activity.
        with self.thread_lock:
            activity_keys = list( self.activities )

        successful = False
        current_key = ''

        for key in activity_keys:
            current_key = key
            _print( f"{self.print_label} Starting activity '{self.name}' ({self.short_hash}) [{self.current_activity_id+1} of {len(activity_keys)}] " )
            successful = self.activities[ key ].execute()

            if not successful:
                break

            self.current_activity_id += 1

        self._status = self.STATUS["COMPLETE"] if successful else self.STATUS["FAILED"]

        if successful:
            _print( f"{self.print_label}: All Activities have completed successfully" )
        else:
            _print( f"{self.print_label}: Failed to execute activity '{current_key}'. Job exited with status {self.status_name}")

    def terminate(self):
        pass



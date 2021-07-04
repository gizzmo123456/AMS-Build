import jobs.base_activity as base_activities
import user_access_control as uac

class Prepare( base_activities.BaseTask ):

    @staticmethod
    def access_level():
        return uac.UAC.SERVER_ADMIN

    def init(self):
        pass

    def set_stage_data(self, data):
        pass

    def execute(self):
        pass

    def terminate(self):
        pass

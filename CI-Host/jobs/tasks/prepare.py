import jobs.base_activity as base_activities
import terminal
import DEBUG

_print = DEBUG.LOGS.print


class Prepare( base_activities.BaseTask ):

    def init(self):
        pass

    def activity(self):

        with terminal.Terminal() as console:
            output = console.write( f"cd {self._get_format_value('project_source_dir')}" )
            _print("1) ", output)
            output = console.write( "git status" )
            _print( "2) ", output )

        return base_activities.BaseActivity.STATUS["INVALID"], "Activity not implemented"

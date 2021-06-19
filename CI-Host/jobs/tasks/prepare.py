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
            _print( output[1] )
            output = console.write( "git status" )
            _print( output[1] )

        return base_activities.BaseActivity.STATUS["INVALID"], "Activity not implemented"

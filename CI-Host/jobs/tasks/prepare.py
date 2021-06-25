import jobs.base_activity as base_activities
import terminal
import common
import DEBUG
import const
from datetime import datetime

import time # temp

_print = DEBUG.LOGS.print


class Prepare( base_activities.BaseTask ):

    def init(self):
        pass

    def terminal_write(self, cmd, term, stdout_file):
        success, output = term.write( cmd )
        _print( output, output_filename=stdout_file, console=True )
        return output

    def activity(self):

        output_dir = self._get_format_value('output_dir')
        log_dir = self._get_format_value('logs_output_dir')
        log_output_filepath = f"{log_dir}/output.txt"

        # lock the project directory, to prevent it being modified by another activity.
        with common.LockDirectory( self._get_format_value( 'project_dir' ) ) as lock_dir:
            with terminal.Terminal() as console:

                # create the output and logs directory
                if output_dir is None:
                    return base_activities.BaseActivity.STATUS["FAILED"], "Failed to create output direct. Directory not set."
                elif log_dir is None:
                    return base_activities.BaseActivity.STATUS["FAILED"], "Failed to create logs direct. Directory not set."

                queued_outputs = []

                # create output directory
                output =  console.write( f"mkdir -v '{output_dir}'" )[1]
                queued_outputs.append( output )

                # create logs directory
                output = console.write( f"mkdir -v '{log_dir}'" )[1]
                queued_outputs.append( output )

                # create log files and write the queued outputs.
                common.write_file( f"{log_output_filepath}", f"{'='*24}\n"
                                                             f"Log Output: {self.get_format_value('output-name')}\n"
                                                             f"Created At: {datetime.now().strftime( const.DATE_TIME_FORMAT )}\n"   # use the time the file was created.
                                                             f"{self.log_header}")
                for o in queued_outputs:
                    _print(o, output_filename=f"{log_output_filepath}", console=True)

                # Change to the main project source directory, and run the prepare main commands.
                self.terminal_write( f"cd '{self._get_format_value('project_source_dir')}'", console, log_output_filepath)

                # TODO: Start SSH agent if used.
                # TODO: run prepare main commands.

                # Copy the main config and project source directory to the output directory
                self.terminal_write( "cp -r '{project_config_dir}' '{output_config_dir}'".format(**self._all_format_values), console, log_output_filepath )
                self.terminal_write( "cp -r '{project_source_dir}' '{output_source_dir}'".format(**self._all_format_values), console, log_output_filepath )

                # TODO: From here we can unlock the directory

                # change to the output source directory and run the prepare output commands.
                self.terminal_write( f"cd '{self._get_format_value('output_source_dir')}'", console, log_output_filepath )

                # TODO: run prepare output commands.

        _print("Directory unlocked @ ", time.time())

        return base_activities.BaseActivity.STATUS["COMPLETE"], "Activity not implemented"

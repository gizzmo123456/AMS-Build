import jobs.base_activity as base_activities
import terminal
import common
import DEBUG

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

        with terminal.Terminal() as console:

            # create the output and logs directory
            if output_dir is None:
                return base_activities.BaseActivity.STATUS["FAILED"], "Failed to create output direct. Directory not set."
            elif log_dir is None:
                return base_activities.BaseActivity.STATUS["FAILED"], "Failed to create logs direct. Directory not set."

            output =  console.write( f"mkdir {output_dir} -v" )[1]
            output += console.write( f"mkdir {log_dir} -v" )[1]

            _print( output )

            # create log files and write the output.
            common.write_file( f"{log_output_filepath}", f"{'='*24}\n{self.get_format_value('output-name')}\n{'='*24}\n{self.log_header}")
            _print(output, output_filename=f"{log_output_filepath}", console=False)

            # Change to the main project source directory, and run the prepare main commands.
            self.terminal_write( f"cd {self._get_format_value('project_source_dir')}", console, log_output_filepath)

            # TODO: run prepare main commands.

            # Copy the main config and project source directory to the output directory
            self.terminal_write( "cp -r {project_config_dir} {output_config_dir}".format(**self._all_format_values), console, log_output_filepath )
            self.terminal_write( "cp -r {project_source_dir} {output_source_dir}".format(**self._all_format_values), console, log_output_filepath )

            # change to the output source directory and run the prepare output commands.
            self.terminal_write( f"cd {self._get_format_value('output_source_dir')}", console, log_output_filepath )

            # TODO: run prepare output commands.

        return base_activities.BaseActivity.STATUS["COMPLETE"], "Activity not implemented"

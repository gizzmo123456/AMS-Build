import jobs.base_activity as base_activities
import terminal
import common
import commonProject
import DEBUG
import const
from datetime import datetime
import re

import time # temp

_print = DEBUG.LOGS.print


class Prepare( base_activities.BaseTask ):

    def init(self):

        self._private_format_values["ssh"] = {
            "active": False
        }

        # find if ssh should be used.
        if "ssh" in self.activity_data:
            # attempt to load the ssh config file.
            name = self.activity_data["ssh"]
            ssh_conf = commonProject.get_project_config( self.job.uac, self.job.project, "ssh")

            if name is None or ssh_conf is None:
                _print("Unable to load SSH config", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
                return

            # Check the name of the ssh key exist and load relevant data.
            for conf in ssh_conf:
                if name == conf.get("name", None):
                    key_name = conf.get("key-name", None)
                    self._private_format_values["ssh"]["name"]  = conf["name"]
                    self._private_format_values["ssh"]["active"] = key_name is not None and conf.get("active", False)
                    if conf["active"]:
                        self._private_format_values["ssh"]["key-name"]  = key_name
                        self._private_format_values["ssh"]["key_count"] = 0

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

                # Start SSH agent if used.
                if self._private_format_values["ssh"]["active"]:
                    output = self.terminal_write( "eval $(ssh-agent -s)", console, log_output_filepath )
                    pid = re.findall( r'Agent pid ([0-9]+)', output )
                    if len( pid ) != 1:
                        _print("Failed to capture SSH agent pid. killing agent.", message_type=DEBUG.LOGS.MSG_TYPE_ERROR, output_filename=log_output_filepath, console=True)
                        self.terminal_write("eval $(ssh-agent -k)", console, log_output_filepath)
                    else:
                        self._private_format_values["ssh"]["pid"] = pid[0]

                        # load the required ssh key into the agent.
                        output = self.terminal_write( "ssh-add {BASE_DIR}/CI-Host/data/.secrets/.ssh/"
                                                      "{project}/{key_name}".format( BASE_DIR=const.BASE_DIRECTORY,
                                                                                     project=self.job.project,
                                                                                     key_name=self._private_format_values["ssh"]["key-name"] ),
                                                      console, log_output_filepath )
                        key_added = re.findall( r'^(Identity added:)', output )
                        if len( key_added ) == 1 and key_added[0] == "Identity added:":
                            self._private_format_values["ssh"]["key_count"] += 1
                            _print("Key added successfully!", output_filename=log_output_filepath, console=True )
                        else:
                            _print("Failed to load SSH key", message_type=DEBUG.LOGS.MSG_TYPE_ERROR, output_filename=log_output_filepath, console=True )

                else:
                    _print("SSH Agent not required!", output_filename=log_output_filepath, console=True)

                # load the cmd to run in the main and output source directory
                run_main_cmd = []
                run_output_cmd = []

                if "run" in self.activity_data:
                    if type( self.activity_data["run"] ) is dict:
                        run_main_cmd = self.activity_data["run"].get("main", [])
                        run_output_cmd = self.activity_data["run"].get("output", [])
                    else:
                        _print("run is of an incorrect format. Must be a dict, containing keys 'main' and 'output' with a list of commands for values.",
                               message_type=DEBUG.LOGS.MSG_TYPE_ERROR,
                               output_filename=log_output_filepath, console=True)
                else:
                    _print("run is not defined in pipeline or config file.", message_type=DEBUG.LOGS.MSG_TYPE_WARNING,
                           output_filename=log_output_filepath, console=True)

                # run the main commands
                for cmd in run_main_cmd:
                    self.terminal_write( cmd, console, log_output_filepath )

                # kill the ssh-agent once the prepare commands have been run on the main project source.
                if "pid" in self._private_format_values["ssh"]:
                    output = self.terminal_write( "eval $(ssh-agent -k)", console, log_output_filepath )
                    killed_pid = re.findall( r'Agent pid ([0-9]+) killed', output )
                    if len( killed_pid ) == 1 and killed_pid[0] == self._private_format_values["ssh"]["pid"]:
                        # remove the pid key to show that no ssh agents are running.
                        del self._private_format_values["ssh"]["pid"]
                        _print("SSH Agent killed!", output_filename=f"{log_output_filepath}", console=True)
                    else:
                        _print( f"Failed to kill ssh agent (pid: {self._private_format_values['ssh']['pid']}).")

                # Copy the main config and project source directory to the output directory
                self.terminal_write( "cp -r '{project_config_dir}' '{output_config_dir}'".format(**self._all_format_values), console, log_output_filepath )
                self.terminal_write( "cp -r '{project_source_dir}' '{output_source_dir}'".format(**self._all_format_values), console, log_output_filepath )

                # change to the output source directory and run the prepare output commands.
                self.terminal_write( f"cd '{self._get_format_value('output_source_dir')}'", console, log_output_filepath )

                for cmd in run_output_cmd:
                    self.terminal_write( cmd, console, log_output_filepath )

        _print(f"Directory '{self._get_format_value( 'project_dir' )}' unlocked @ {time.time()}")

        return base_activities.BaseActivity.STATUS["COMPLETE"], f"{self.job.project} has been prepared successfully"

import commonProject
import jobs.base_activity as base_activities
import user_access_control as uac
import terminal
import const
import re

import DEBUG
_print  = DEBUG.LOGS.print

class Prepare( base_activities.BaseTask ):
    """
        Updates the project source directory, ready for build, test or deploy

        Supported stage data (excluding base class(es) data):
          key : description
          -----------------
        - ssh : (optional) name of ssh key config to use.
        - run : List of commands to run in the project source directory

        values registered into job.data (key format '{activity-name}.{key-name}')
          key : description
          -----------------
        - git-hash: The latest git commit hash. (only set if not already)
        -
    """

    def init(self):

        self._data["project_source_path"] = f"{self.job.project_root}/{self.job.data['project-branch']}/project_source"

    def set_stage_data(self, data):
        super().set_stage_data(data)

        if "ssh" in self.stage_data:
            # load in the ssh config file and look up the ssh name
            ssh_conf = commonProject.get_project_config( self.job.uac, self.job.project, "ssh" )

            if ssh_conf is not None:
                found_key = False
                active = False
                # look up the ssh name and set the ssh data if defined/active.
                for ssh_key in ssh_conf:
                    if "name" in ssh_key and ssh_key["name"] == self.stage_data["ssh"]:
                        found_key = True
                        active = ssh_key.get("active", True)

                        # set the ssh data if active.
                        if not active:
                            break

                        self._data["ssh"] = {
                            "active": active,
                            "name": self.stage_data["ssh"],
                            "key-name": ssh_key.get("key-name", None)
                        }
                        _print( self.print_label, f"SSH config '{self.stage_data['ssh']}' loaded.", ssh_key)
                        break

                if not found_key:
                    _print( self.print_label, "SSH key not found in ssh config" )
                elif not active:
                    _print( self.print_label, "Ignoring found ssh key. Not active." )

            else:
                _print( self.print_label, "Unable to load 'ssh' config.")

    def terminal_write(self, term, cmd ):
        """writes to the terminal and prints the output to stdout if supplied otherwise prints directly to console"""
        success, output = term.write( cmd )
        _print( f"{self.print_label} {output} (successful: {success})", **self.redirect_print )
        return output

    def activity(self):

        if "run" not in self.stage_data:
            _print( f"{self.print_label} Unable to run activity. 'run' has not been supplied." )
            return False

        # TODO: should probably "lock" the directory using a lock file.
        with terminal.Terminal( log_filepath=self.job.output_log_path ) as term:

            # change the directory to the project source.
            self.terminal_write( term, f"cd {self._data['project_source_path']}")

            # start start ssh agent and cache the pid
            # TODO: it might be worth moving start SSH agent and Add keys to a terminal helper module/class.
            if "ssh" in self._data:
                output = self.terminal_write(term, "eval $(ssh-agent -s)" )
                pid = re.findall(r'Agent pid ([0-9]+)', output)

                if len( pid ) != 1:
                    _print("Failed to capture SSH agent pid. Killing agent.", message_type=DEBUG.LOGS.MSG_TYPE_ERROR, **self.redirect_print )
                    self.terminal_write( term, "eval $(ssh-agent -k)")
                else:
                    self._data["ssh"]["pid"] = pid[0]

                # load the ssh-key into the agent.
                output = self.terminal_write(term, "ssh-add {BASE_DIR}/CI-Host/data/.secrets/.ssh/{project}/{key_name}"
                                             .format(BASE_DIR=const.BASE_DIRECTORY, project=self.job.project, key_name=self._data["ssh"]["key-name"]))

                key_added = re.findall(r'^(Identity added:)', output)

                if len(key_added) == 1 and key_added[0] == "Identity added:":
                    _print("Key added successfully!", **self.redirect_print)
                else:
                    _print("Failed to load SSH key", message_type=DEBUG.LOGS.MSG_TYPE_ERROR, **self.redirect_print)

            else:
                _print("SSH Agent not required!", **self.redirect_print)

            run_cmd = self.stage_data["run"]

            for cmd in run_cmd:
                self.terminal_write( term, cmd )

            # this assumes that the repo has been updated.
            # if the git hash has not been supplied to job get the latest git hash for this job.
            if "git-hash" not in self.job.data:
                git_hash = self.terminal_write( term, "git rev-parse HEAD" )
                self.job.add_unique_data( **{"git-hash": git_hash} )

            # TODO: Should probably add a method to run this when exiting the with statement, to make sure it is run.
            if "pid" in self._data["ssh"]:
                output = self.terminal_write(term, "eval $(ssh-agent -k)" )
                killed_pid = re.findall(r'Agent pid ([0-9]+) killed', output)
                if len(killed_pid) == 1 and killed_pid[0] == self._data["ssh"]["pid"]:
                    # remove the pid key to show that no ssh agents are running.
                    del self._data["ssh"]["pid"]
                    _print(f"{self.print_label} SSH Agent killed!", **self.redirect_print)
                else:
                    _print(f"{self.print_label} Failed to kill ssh agent (pid: {self._private_format_values['ssh']['pid']}).",
                           message_type=DEBUG.LOGS.MSG_TYPE_ERROR, **self.redirect_print)

        return True

    def terminate(self):
        pass

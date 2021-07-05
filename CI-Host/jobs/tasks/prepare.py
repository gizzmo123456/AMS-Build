import commonProject
import jobs.base_activity as base_activities
import user_access_control as uac
import DEBUG

_print  = DEBUG.LOGS.print

class Prepare( base_activities.BaseTask ):
    """
        Updates the project source directory, ready for build, test or deploy

        Supported stage data:
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
        pass

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
                        _print( self.print_label, f"SSH config '{self.stage_data['ssh']}' loaded.")
                        break

                if not found_key:
                    _print( self.print_label, "SSH key not found in ssh config" )
                elif not active:
                    _print( self.print_label, "Ignoring found ssh key. Not active." )

            else:
                _print( self.print_label, "Unable to load 'ssh' config.")

    def execute(self):
        pass

    def terminate(self):
        pass

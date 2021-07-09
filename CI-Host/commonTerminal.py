# Common commands and helper methods to use with terminal

import DEBUG
import re

_print = DEBUG.LOGS.print


# Helpers
# TODO: I could add this to terminal...
def terminal_print( term, cmd, prefix_label="", **print_options ):
    """
        writes to the terminal and prints the cmd and output to stdout if supplied otherwise prints directly to console
        :param term:         instance of terminal to write to
        :param cmd:          command to run in terminal
        :param prefix_label: label to add to start of print
        :param print_options: options for DEBUG.LOG.print

        :return output
        (if the command is needed use term.last_cmd)
    """
    success, cmd, output = term.write( cmd )
    _print( f"{prefix_label}\n\n{'-'*6} terminal ({term.pid}) {'-'*6}\n\n{cmd}\n{output}\n\n{'-'*4} EOF - success: {success} {'-'*4}\n", **print_options )

    return output


# Common commands
# Git
def git_get_head_commit_hash():
    pass


# SSH
def ssh_agent_start( terminal, prefix_label="", **print_options ):
    pass


def ssh_add_key( terminal, prefix_label="", **print_options ):
    pass


def ssh_agent_close( terminal, prefix_label="", **print_options ):
    pass


# Docker
class Docker:

    def __init__(self, terminal, image_name, print_label="", **print_options):

        self.terminal = terminal
        self.image_name = image_name  # image-name:tag
        self.print_label = print_label
        self.print_options = print_options

        self.container_name = None

    def image_exist_locally( self ):

        output = terminal_print( self.terminal, f"sudo docker image inspect {self.image_name}",
                                 prefix_label=self.print_label, **self.print_options)

        # if the image does not exist, an emtpy array is return followed by an error message.
        # otherwise the array contains the image info

        # so basically we can just check if the first 2 characters of the output are not '[]'

        return output[:2] != "[]"

    def pull_image( self ):

        output = terminal_print( self.terminal, f"sudo docker pull {self.image_name}",
                                 prefix_label=self.print_label, **self.print_options )

        # if the first word of the output is error we have failed to pull the docker image.
        # Note: we only support pulling from public registries.

        return output[:5].lower() != "error"

    def run(self, container_name, args):

        if self.container_name is not None:
            _print( f"{self.print_label} Unable to run container, already running. ", **self.print_options )
            return

        self.container_name = container_name
        output = terminal_print( self.terminal, f"sudo docker run --name {container_name} {args} {self.image_name}",
                                 prefix_label=self.print_label, **self.print_options )  # TODO: <<<

    def stop(self, timeout=10, kill=False):
        """
            sends a SIGTERM to the container. if the container does not exit within the timeout period
            a SIGKILL is send to kill the process.
            if kill is True. Just a SIGKILL is sent.
        """

        method = f"stop" if not kill else "kill"
        timeout = f"-t {timeout}" if not kill else ""

        if self.container_name is None:
            _print( f"{self.print_label} Unable to {method} container. Container name not set.",
                    prefix_label=self.print_label, **self.print_options )

        output = terminal_print( self.terminal, f"sudo docker {method} {timeout} {self.container_name}",
                                 prefix_label=self.print_label, **self.print_options )

        # this should return the container name if stopped successfully

        if output != self.container_name:
            _print( f"{self.print_label} Failed to {method} container {self.container_name}", message_type=DEBUG.LOGS.MSG_TYPE_WARNING, **self.print_options )
            return False

        # now we can remove the container allowing the same name to be used again.
        success = self.remove_container()

        if success:
            self.container_name = None

        return success

    def remove_container(self):

        # remove the container
        output = terminal_print(self.terminal, f"sudo docker container rm {self.container_name}",
                                prefix_label=self.print_label, **self.print_options)

        # this should return the container name if successful
        if output != self.container_name:
            _print(f"{self.print_label} Failed to remove container ({self.container_name})", **self.print_options)
            return False

        return True

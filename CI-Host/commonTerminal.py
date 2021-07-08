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
    _print( f"{prefix_label}\n{cmd}\n{output}\n(command run successfully: {success})", **print_options )
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
def docker_image_exist_locally( terminal, image_name, prefix_label="", **print_options ):

    output = terminal_print( terminal, f"sudo docker image inspect {image_name}", prefix_label=prefix_label, **print_options)

    # if the image does not exist, an emtpy array is return followed by an error message.
    # otherwise the array contains the image info

    # so basically we can just check if the first 2 characters of the output are not '[]'

    return output[:2] != "[]"


def docker_pull_image( terminal, image_name, prefix_label="", **print_options ):

    output = terminal_print( terminal, f"sudo docker pull {image_name}" )

    # if the first word of the output is error we have failed to pull the docker image.
    # Note: we only support pulling from public registries.

    return output[:5].lower() != "error"


def docker_run(terminal, image_name, args, prefix_label="", **print_options):

    output = terminal_print( terminal, f"sudo docker run {args} {image_name}")  # TODO: <<<

def docker_stop(terminal, container_name, prefix_label="", **print_options):
    pass

def docker_kill(terminal, container_name, prefix_label="", **print_options):
    pass
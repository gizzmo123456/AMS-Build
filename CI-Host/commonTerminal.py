# Common commands and helper methods to use with terminal

import DEBUG

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


import pty              # (unix only)
import subprocess
import os
import re
import DEBUG
_print = DEBUG.LOGS.print


class Terminal:

    def __init__(self, input_str="bash-5.0# ", log_filepath="", skip_read=False ):
        """

        :param input_str:       waiting for input string
        :param log_filepath:    log path for prints (this does not log the output of the terminal to file.)
        :param skip_read:       should read be skipped on init
        """

        self.input_str = input_str
        self.redirect_print = {
            "console": True,
            "output_filename": log_filepath
        }

        self.active = True
        self.cmd_queue = []  # change to Queue for thread safeness? # TODO: i think this should be a queue of cmds to run on exit.
        self.print_inputs = True
        self.remove_color_formats = True
        self.waitingForOutput = False

        # Create a new pseudo terminal
        std_master, std_slave = pty.openpty()
        self.stdin = os.fdopen( std_master, 'r')
        self.stdout = self.stdin

        self.last_cmd = ""

        # open the terminal with bash in interactive mode and no rc file.
        cmd = [ "bash", "--norc", "--noediting", "-is" ]
        self.__terminal = subprocess.Popen( cmd, close_fds=False, stdin=std_slave, stdout=std_slave, stderr=std_slave )

        self.pid = self.__terminal.pid

        # read and discard the message printed by bash at the start
        if skip_read:
            self.read() # TODO: Log somewhere..

        _print(f"Opened new terminal -> PID: {self.__terminal.pid} ", **self.redirect_print)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()

    def read(self):
        """
            reads from the stdout until the input string has been printed.
            (blocks until the output has finished)
        :return: command, output (if print inputs is set, the input str is included in the cmd string)
        """

        self.waitingForOutput = True
        cmd = self.last_cmd
        input_cmd = self.last_cmd + "\n\n"
        output = ""

        if self.print_inputs:
            cmd = self.input_str + cmd

        while self.waitingForOutput:
            output += os.read( self.stdout.fileno(), 1024 ).decode()

            if output[ -len(self.input_str): ] == self.input_str:
                # remove the inputted command and end input string from the output
                output = output[ len(input_cmd):-len(self.input_str)-1 ]
                self.waitingForOutput = False

        if self.remove_color_formats:
            output = re.sub( r'(\033\[[0-9]*m)', '', output ) # TODO: this is major improvment. But this will do for git at least. See https://misc.flogisoft.com/bash/tip_colors_and_formatting
                                                              #       NOTE: '\e' (or '^[') is '\033' in regex :)

        return cmd, output   # cmd, output (where cmd can include the input string.)

    def write(self, cmd):
        """
            writes to the stdin and waits for the output.
        :param cmd: command to execute
        :returns: successful, cmd, output (or message if not successful) (if print inputs is set, the input str is included in the cmd string)
        """

        cmd_input_str = cmd

        if self.print_inputs:
            cmd_input_str = self.input_str + cmd_input_str

        if not self.active:
            return False, cmd_input_str, "Unable to write command. Terminal not active."
        elif self.waitingForOutput:
            return False, cmd_input_str, "Unable to write command. Waiting for output"

        self.last_cmd = cmd
        os.write( self.stdin.fileno(), cmd.encode() + b'\n' )

        cmd_input_str, output = self.read()

        return True, cmd_input_str, output

    def queue_cmd(self, cmd="echo ' '"):
        """
            Queues a command to be processed. (must be used with process queue)
        :param cmd: command to executed
        :return: None
        """
        self.cmd_queue.append( cmd )

    def queue_cmds(self, cmds=[] ):
        """
            Queues a list of command to be processed. (must be used with process queue)
        :param cmds: list of commands to be executed
        :return: None
        """
        self.cmd_queue.extend( cmds )

    def process_queue(self):
        """
            processes the command queue until no commands remain.
        :yields: output, per-command
        """
        if len( self.cmd_queue ) == 0:
            _print("Unable to process queue. No commands queued", **self.redirect_print)
            return
        while len( self.cmd_queue ) > 0:
            cmd = self.cmd_queue.pop(0)
            successful, output = self.write( cmd )
            if not successful:
                raise Exception( f"Error: {output}" )
            else:
                yield output

    def terminate(self):
        _print("Terminating terminal with pid:", self.__terminal.pid, **self.redirect_print)
        self.active = False
        self.__terminal.terminate()

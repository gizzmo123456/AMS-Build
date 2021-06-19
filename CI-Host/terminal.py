
import pty  # (unix only?)
import subprocess
import os
import DEBUG
_print = DEBUG.LOGS.print


class Terminal:

    def __init__(self, input_str="bash-5.0$ " ):

        self.input_str = input_str

        self.active = True
        self.cmd_queue = []  # change to Queue?
        self.print_inputs = True
        self.waitingForOutput = False

        # Create a new pseudo terminal
        std_master, std_slave = pty.openpty()
        self.stdin = os.fdopen( std_master, 'r')
        self.stdout = self.stdin

        self.last_cmd = ""

        # open the terminal with bash in interactive mode and no rc file.
        cmd = [ "bash", "--norc", "--noediting", "-is" ]
        self.__terminal = subprocess.Popen( cmd, close_fds=False, stdin=std_slave, stdout=std_slave, stderr=std_slave )

        _print(f"Opened new terminal -> PID: {self.__terminal.pid} ")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()

    def read(self):
        """
            reads from the stdout until the input string has been printed.
            (blocks until the output has finished)
        :return: output
        """

        self.waitingForOutput = True
        start = ""
        input_cmd = self.last_cmd + "\n\n"
        output = ""

        if self.print_inputs:
            start = self.input_str
            input_cmd = ""

        while self.waitingForOutput:
            output += os.read( self.stdout.fileno(), 1024 ).decode()
            _print(">>>", output)
            if output[ -len(self.input_str): ] == self.input_str:
                output = output[ len(input_cmd):-len(self.input_str)-1 ] # remove the inputed command and end input string from the output
                self.waitingForOutput = False

        return start + output

    def write(self, cmd):
        """
            writes to the stdin and waits for the output.
        :param cmd: command to execute
        :returns: successful, output (or message if not successful)
        """

        if not self.active:
            return False, "Unable to write command. Terminal not active."
        elif self.waitingForOutput:
            return False, "Unable to write command. Waiting for output"

        self.last_cmd = cmd
        os.write( self.stdin.fileno(), cmd.encode() + b'\n' )

        return True, self.read()

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
            _print("Unable to process queue. No commands queued")
            return
        while len( self.cmd_queue ) > 0:
            cmd = self.cmd_queue.pop(0)
            successful, output = self.write( cmd )
            if not successful:
                raise Exception( f"Error: {output}" )
            else:
                yield output

    def terminate(self):
        _print("terminating terminal with pid:", self.__terminal.pid)
        self.active = False
        self.__terminal.terminate()

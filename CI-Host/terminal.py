
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
        self.remove_escape_characters = True
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
        if not skip_read:
            self.read() # TODO: Log somewhere..
        else:
            _print("Read Skipped")

        _print(f"Opened new terminal -> PID: {self.__terminal.pid}", **self.redirect_print)

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
            read = os.read( self.stdout.fileno(), 1024 ).decode()

            if self.remove_escape_characters:
                read = self.clean_escape_seq( read )
            _print( read )
            output += read

            if output[ -len(self.input_str): ] == self.input_str:
                # remove the inputted command and end input string from the output
                output = output[ len(input_cmd):-len(self.input_str)-1 ]
                self.waitingForOutput = False

        return cmd, output   # cmd, output (where cmd can include the input string.)

    def write(self, cmd):
        """
            writes to the stdin and waits for the output.
        :param cmd:                 command to execute
        :param new_input_str:   if supplied updates the input string after the command has been run!
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

    def write_expects(self, cmd, expects, new_input_string=None):
        """
            writes to the stdin and waits for the output.
        :param cmd:                 command to run
        :param expects:             what is expected to be return in the output.
                                    dict {} keys: "begins", "contains", "ends". Value: String
                                    is:       the output is equal to value.
                                    begins:   the output begins with value.
                                    contains: the output contains value.
                                    end:     the output ends with value.
                                    flags:    regex flags. See https://docs.python.org/3/library/re.html#module-contents
                                    All keys are optional, but at least 1 key is required. (with the exception of flags which must be supplied with one of the other keys)
                                    if 'is' is supplied, the other keys are ignored, since it looks for an exact match.
        :param new_input_string:    (ignored if None) the new input_str to be used if the expected
                                    output was returned from the command.
        :return:                    successful, inputted command, output
                                    successful if the expected output is returned
        """

        if type(expects) is not dict:
            _print( f"Terminal ({self.pid}): Unable to write command. Expects param must be of type dict", **self.redirect_print )
            return False, cmd, ""

        expects_keys = ["is", "begin", "contains", "end"]  # ignore flags as its a params for the re method.
        found = False

        for k in expects_keys:
            if k in expects_keys:
                found = True
                break

        if not found:
            _print(f"Terminal ({self.pid}) Unable to write command. Expects must contain at least one of the following keys. { expects_keys }")
            return

        successful, cmd, output = self.write( cmd )

        if not successful:
            return successful, cmd, output

        regex = r""

        # build the regex to be used.
        if "is" in expects:
            regex = rf"(^{expects['is']}$)"
        else:   # (^Many)[\s\S]*(bob)[\s\S]*(world$) # TODO: <<
            if "begin" in expects:
                regex += rf"(^{expects['begin']})"
            elif "contains" in expects:
                regex += rf"[\s\S]*({expects['contains']})"
            elif "end" in expects:
                regex += rf"[\s\S]*({expects['end']}$)"

            _print( f"Terminal ({self.pid}): Expects RE: {regex}" )

        match = re.search( regex, output, flags=expects.setdefault( "flags", 0 ) ) is not None

        if not match and new_input_string is not None:
            self.input_str = new_input_string

        return match, cmd, output

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

    # TESTING
    def clean_escape_seq(self, output):
        # See: https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python

        if type( output) is not bytes:
            output = output.encode()

        # TODO: this should be cached statically.
        ansi_escape = re.compile(br'''
            (?: # either 7-bit C1, two bytes, ESC Fe (omitting CSI)
                \x1B
                [@-Z\\-_]
            |   # or a single 8-bit byte Fe (omitting CSI)
                [\x80-\x9A\x9C-\x9F]
            |   # or CSI + control codes
                (?: # 7-bit CSI, ESC [ 
                    \x1B\[
                |   # 8-bit CSI, 9B
                    \x9B
                )
                [0-?]*  # Parameter bytes
                [ -/]*  # Intermediate bytes
                [@-~]   # Final byte
            )
        ''', re.VERBOSE)

        return ansi_escape.sub( b'', output).decode()

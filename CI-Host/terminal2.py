import pty
import subprocess
import os
import re
import time
import select
import DEBUG
_print = DEBUG.LOGS.print

class Terminal:

    ansi_escape_re = None

    def __init__(self, input_prompt="bash-5.0# ", start_cmd=None ):

        self.input_prompt = input_prompt

        self.active = True
        self.cmd_history = []
        self.last_cmd_id = -1   #

        # open the pty file descriptor
        std_master, std_slave = pty.openpty()
        self.stdin = os.fdopen( std_master, 'r')
        self.stdout = self.stdin

        self.poll = select.poll()
        self.poll.register( std_master, select.POLLIN | select.POLLOUT )

        self.poll_stats = {
            "read": False,
            "write": False
        }

        # start the subprocess
        cmd = [ "bash", "--norc", "--noediting", "-is" ] if start_cmd is None else start_cmd

        self.__terminal = subprocess.Popen( cmd, close_fds=False, stdin=std_slave, stdout=std_slave, stderr=std_slave )
        self.__pid = self.__terminal.pid
        self.__return_code = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @property
    def pid(self):
        return self.__pid

    def poll_std_master(self, timeout=1):
        poll = self.poll.poll( timeout )

        if len(poll) == 0:
            return  # no change

        self.poll_stats["read"] |= poll[0][1] & select.POLLOUT > 0
        self.poll_stats["write"] |= poll[0][1] & select.POLLIN > 0

    def write(self, cmd):
        """
            writes to the terminal input
        :param cmd: command to run
        :return: successfully writen to the stdin
        """

        self.poll_std_master()

        if not self.active or not self.poll_stats["write"]:
            return False

        cmd = cmd.encode() + b'\n'

        self.cmd_history.append( cmd )

        os.write( self.stdin.fileno(), cmd )

        return True

    def write_wait(self, cmd):
        """
            writes to the terminal input and waits for the input prompt
        :param cmd: cmd to run
        :returns: successfully writen to the stdin, cmd output
        """

        write_success = self.write( cmd )

        if not write_success:
            return False, ""

        return True, self.read_wait()

    def wait_for_prompt(self):
        """
            waits for the input prompt in the output
        """
        pass

    def read(self, poll_timeout=1):
        """
            yields the output from the stdout
        :param poll_timeout:
        :yields: terminal output
        """

        yield None

    def read_wait(self):
        """
            reads the output from the stdout and waits for the input prompt
        :return: stdout
        """
        pass

    @property
    def return_code(self):
        """
            gets the return code of the process. None if still running
        """
        # attempt to get the return code if not already set.
        if self.__return_code is None:
            self.__terminal.poll()
            self.__return_code = self.__terminal.returncode

        return self.__return_code

    def wait_for_return_code(self, poll_intervals=1, poll_count=-1):
        """
            blocks the thread and waits for the return code from the running process.
        :param poll_intervals:  amount of time to poll the process for a return code.
        :param poll_count:      amount of times to poll the process for a return code. <=0 waits indefinitely
        :return: process return code, None if still active
        """

        return_code = None
        remaining_polls = poll_count

        while return_code is None:

            time.sleep( poll_intervals )

            # poll and attempt to get the return code
            self.__terminal.poll()
            return_code = self.__terminal.returncode

            if poll_count > 0:
                remaining_polls -= 1

                if remaining_polls <= 0:
                    break

        self.__return_code = return_code
        return return_code

    # helpers and statics

    def print(self, method, params, **print_options):
        """
            prints the terminals output to logs (either stdout or file)
            and waits for the input prompt
        :param method:          method to be executed
        :param params:          params to be passed to method
        :param print_options:   print options (optional)
                                    prefix:          prefix to be printed
                                    console:         should the output be printed to console
                                    output_filename: path to output log
        """
        pass

    @staticmethod
    def clean_escape_seq(output):
        # See: https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python

        if type( output) is not bytes:
            output = output.encode()

        # compile and catch the ansi escape regex
        if Terminal.ansi_escape_re is None:
            Terminal.ansi_escape_re = re.compile(br'''
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

        return Terminal.ansi_escape_re.sub( b'', output).decode()

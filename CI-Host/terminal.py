import config_loader    # Loads in all config file.
from constants import PLATFORMS, SHELLS
from app_const import PLATFORM
from subprocess import Popen, PIPE, STDOUT
import os
import re

import DEBUG
_print = DEBUG.LOGS.print

# if we are running on linux/unix its better to use pty
# and pty does not support windows (although included).
# it might work with wsl2
if PLATFORM != PLATFORMS.WINDOWS:
    import pty
    PROMPT_LINE_TERMINATE = "\r\n"
else:
    PROMPT_LINE_TERMINATE = "\n"


class Terminal:

    DEFAULT_PROMPT = "amsCI> "

    if PLATFORM == "WIN":
        SUPPORTED_SHELLS = [SHELLS.WIN_CMD, SHELLS.WIN_PS]
    else:
        SUPPORTED_SHELLS = [SHELLS.LINUX_BASH]

    # At the present time the standard linux Shell is unsupported, for some reason its taking over the current
    # standard input, and failing to read inputs correctly. It might work if we get sh to read from file, and use "-ic"
    # rather then "-is" as we can specify the file to read from.
    UNSUPPORTED_SHELLS = [SHELLS.LINUX_SH]

    def __init__(self, process_and_options, prompt=DEFAULT_PROMPT, prompt_line_terminate=PROMPT_LINE_TERMINATE):
        """
            Creates a sudo-terminal for windows or linux. This must be used in conjunction with the 'with statement'
            to spawn the terminal. This is to help prevent dangling processes
        :param process_and_options:     list [] of cmd and options
                                        the first element of the list should be the shell application to run
                                        On windows we support cmd and powershell where powershell is preferred
                                        On Linux we support sh and bash where bash is preferred. At the present time
                                        there is an issues with running sh where is does not receive keyboard interrupt singles.
                                        You may use other shells or command line application however the prompt must be
                                        an exact match.
        :param prompt:                  the input prompt to wait for.
                                        if using Windows cmd or powershell the prompt is set to the prompt arg
                                        and the same for linux Bash and SH.
        :param prompt_line_terminate:   sequence of characters that terminates the prompt line with an input
        """

        if len( process_and_options ) == 0:
            _print("Error: at least one process and option must be supplied!")
            return

        if process_and_options[0] in Terminal.UNSUPPORTED_SHELLS:
            _print(f"Error: {process_and_options[0]} is not currently supported. please consider using an alturnative { Terminal.SUPPORTED_SHELLS }")
            return
        elif process_and_options[0] not in Terminal.SUPPORTED_SHELLS:
            _print( "WARNING: The requested shell application is not officially supported. Use at your own risk!" )
            _print( ">>", process_and_options[0], Terminal.SUPPORTED_SHELLS )

        if len( prompt ) == 0:
            _print("Warning: Prompt can not be empty. setting to default.")
            prompt = Terminal.DEFAULT_PROMPT

        # TODO: NOTE: We should properly add some form of
        #       limit on what process can be launched so we can have more control
        self.__process_and_options = process_and_options
        self.application = process_and_options[0]

        self.stdin = self.stdout = None

        self.process = None # Popen( process_and_options, close_fds=False, stdin=_popen_stdin, stdout=_popen_stdout, stderr=_popen_stderr)  # None

        # if its a know terminal application add the application to the start of prompt line
        if self.application in Terminal.SUPPORTED_SHELLS:
            self.prompt = f"{self.application}-{prompt}"
        else:
            self.prompt = prompt

        self.prompt_line_terminate = prompt_line_terminate

        self.lines = []
        self.last_cmd = ""
        self.last_prompt = ""
        self.executing_cmd = None

    def __enter__(self):

        # configure popen for windows or linux
        _popen_stdin = PIPE
        _popen_stdout = PIPE
        _popen_stderr = STDOUT

        if PLATFORM != PLATFORMS.WINDOWS:
            std_master, std_slave = pty.openpty()
            self.stdin = os.fdopen(std_master, 'r')
            self.stdout = self.stdin
            _popen_stdin = _popen_stdout = _popen_stderr = std_slave

        self.process = Popen(self.__process_and_options, close_fds=False, stdin=_popen_stdin, stdout=_popen_stdout,
                             stderr=_popen_stderr)  # None

        if self.stdin is None:
            self.stdin = self.process.stdin
            self.stdout = self.process.stdout

        # set the prompt and clear
        self.__set_prompt()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.process.kill()  # ensure that the process has been stoped.

    def __set_prompt(self):

        if self.application not in Terminal.SUPPORTED_SHELLS:
            return

        if PLATFORM == PLATFORMS.LINUX:
            self.execute(f"PS1='{self.prompt}'")
        elif PLATFORM == PLATFORMS.WINDOWS:
            if self.application == SHELLS.WIN_CMD:
                # In CMD we must use $G for the grater than cymbal and $s for space
                # TODO: I should have a look at implementing more of the special chars
                #       https://stackoverflow.com/questions/12028372/how-do-i-change-the-command-line-prompt-in-windows
                #       https://www.hanselman.com/blog/a-better-prompt-for-cmdexe-or-cool-prompt-environment-variables-and-a-nice-transparent-multiprompt
                self.execute(f"set PROMPT={self.prompt.replace('>', '$G').replace(' ', '$s')}") # NOTE: these are the two main ones just to get it working
            elif self.application == SHELLS.WIN_PS:
                self.execute(f"function prompt {{ '{self.prompt}' }}")

    def __read(self):

        line_count = len(self.lines)
        if line_count == 0 or line_count == 1:
            # We must remember the remaining line so it can be finished.
            first_line_start = self.lines[0] if line_count == 1 else ""
            lines_bytes = os.read( self.stdout.fileno(), 1024 )

            # split the bytes into line putting the new line back.
            lines = [f"{line.decode()}\n" for line in lines_bytes.split( b'\n' )]
            line_count = len(lines)
            # we must remove the new line from the last as there was no split!
            lines[line_count-1] = lines[line_count-1][:-1]
            lines[0] = f"{first_line_start}{lines[0]}"

            self.lines = lines

        # only return the line if its complete, otherwise use __peek to view the next line and incomplete line.
        return self.clean_escape_seq( self.lines.pop(0) ) if self.lines[0][-1] == "\n" else None

    def __peek(self):
        if len( self.lines ) == 0:
            return None

        return self.clean_escape_seq( self.lines[0] )

    def __write(self, cmd):
        os.write( self.stdin.fileno(), f"{cmd}\n".encode() )
        # self.process.stdin.write(f"{cmd}\n".encode())
        # self.process.stdin.flush()

    def __expected_input_line(self):
            return f"{self.prompt}{self.last_cmd}{self.prompt_line_terminate}"

    def __expected_prompt(self):
        return self.prompt

    def read(self, return_prompt=False, read_input=True, return_input=True):
        """

        :param return_prompt: Should the input prompt be included in the output string
        :param read_input:    Are we expecting to read the input before the output of the command.
                              This should only be false when initialize the process to clear the initial output
        :param return_input:  Should the input be return in the output string. (ignored if read input is false)
        :return: string:      STD output
        """
        has_read_input = False
        std_output = ""

        while True:

            line = self.__read()

            # the input string should end with just '\n' rather than '\r\n'
            if line is not None and read_input and not has_read_input and line == self.__expected_input_line():
                if return_input:
                    std_output += line
                has_read_input = True

            if has_read_input or not read_input:
                peek_line = self.__peek()

                if peek_line == self.__expected_prompt():

                    if return_prompt:
                        std_output += peek_line

                    self.last_prompt = peek_line

                    self.executing_cmd = None
                    return std_output

                if line is not None:
                    std_output += line

    def execute(self, cmd):
        """
        executes a command on the running process.
        Generally if the method returns false, it singling that read needs to be called first.
        :param cmd: cmd to execute
        :return:    true if executed otherwise false
        """

        if self.executing_cmd is not None:
            return False

        self.last_cmd = cmd
        self.executing_cmd = cmd

        self.__write(cmd)

        return True

    def clean_escape_seq(self, output):
        # See: https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python

        if type(output) is not bytes:
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

        return ansi_escape.sub(b'', output).decode()

if __name__ == "__main__":

    DEBUG.LOGS.init()

    _print( "starting" )
    _print( PLATFORM )

    with Terminal([SHELLS.WIN_PS]) as aaa:

        if aaa is not None:

            std = aaa.read(read_input=False)
            _print(std)

            inp = ""
            while inp != "exit":

                _print(aaa.last_prompt )

                inp = input ()

                if inp == "exit":
                    break
                elif not aaa.execute(inp):
                    exit(-1)

                std = aaa.read()
                _print(std)
OS = "WIN"

from subprocess import Popen, PIPE, STDOUT
import os

# if we are running on linux/unix its better to use pty
# and pty does not support windows (although included).
# it might work with wsl2


class Terminal:

    def __init__(self, process_name, prompt):
        """

        :param process_name: the shell or process to to start
        :param prompt:       the input prompt to wait for
        """

        # TODO: NOTE: We should properly add some form of
        #       limit on what process can be launched so we can have more control
        self.process_name = process_name

        self.process  = Popen( [self.process_name], close_fds=False, stdin=PIPE, stdout=PIPE, stderr=STDOUT )

        self.stdin = self.process.stdin
        self.stdout = self.process.stdout

        self.prompt = prompt
        self.lines = []
        self.last_cmd = ""
        self.last_prompt = ""
        self.executing_cmd = None

    def __enter__(self):
        # self.process = Popen( [self.process_name], stdin=PIPE, stdout=PIPE, stderr=PIPE )
        # self.stdin    = self.process.stdin # None
        # self.stdout = self.process.stdout # None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.process.kill()  # ensure that the process has been stoped.

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

        # only return the line if its complete
        return self.lines.pop(0) if self.lines[0][-1] == "\n" else None

    def __peek(self):
        if len( self.lines ) == 0:
            return None

        return self.lines[0]

    def __write(self, cmd):
        self.process.stdin.write(f"{cmd}\n".encode())
        self.process.stdin.flush()

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
            print( "PEEK: ", self.__peek() )
            line = self.__read()
            print("LINE:", line)

            # the input string should end with just '\n' rather than '\r\n'
            if line is not None and read_input and not has_read_input and line[-2:] != "\r\n" and line[-1:] == "\n":
                print("Read input :)")
                if return_input:
                    std_output += line
                has_read_input = True

            if has_read_input or not read_input:
                peek_line = self.__peek()
                print( "PEEK >>", peek_line )
                # Powershell only. Should this be regex?
                print(f'{peek_line[:2] == "PS"} and {peek_line[-2:] == "> "}')
                if peek_line[:2] == "PS" and peek_line[-2:] == "> ":
                    # print("Next")
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

        # print( f"write cmd {cmd}")

        self.last_cmd = cmd
        self.executing_cmd = cmd

        self.__write(cmd)

        return True

if __name__ == "__main__":

    print( "starting" )

    with Terminal("powershell", "") as aaa:
        std = aaa.read(read_input=False)
        print( std )
        print( aaa.executing_cmd )
        if not aaa.execute("dir"):
            exit(-2)

        std = aaa.read()
        print(std)

        if not aaa.execute("ipconfig"):
            exit(-3)

        std = aaa.read()
        print( std )

        if not aaa.execute( input( aaa.last_prompt ) ):
            exit(-4)

        std = aaa.read()

        if not aaa.execute(input(aaa.last_prompt)):
            exit(-5)

        std = aaa.read()
        print( std )

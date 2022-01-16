import subprocess
from subprocess import Popen, PIPE, STDOUT
subprocess.STD_INPUT_HANDLE

class Terminal:


    def __init__(self, process_name, prompt):
        """

        :param process_name: the shell or process to to start
        :param prompt:       the input prompt to wait for
        """

        # TODO: NOTE: We should properly add some form of
        #       limit on what process can be launched so we can have more control
        self.process_name = process_name
        # TODO: process and stdOut need to be changed to None, this is for intellisense only
        self.process  = Popen( [self.process_name], stdin=PIPE, stdout=PIPE, stderr=STDOUT ) # None
        # NOTE: for some reason we cant set process.stdin into a var,
        #       it seems to prevent it from updating when an input is submited.
        #       So we have to read directly from self.process.stdin
        self.stdout   = self.process.stdout # None

        self.prompt   = prompt
        self.last_cmd = ""
        self.last_prompt = ""
        self.executing_cmd = None

    def __enter__(self):
        self.process = Popen( [self.process_name], stdin=PIPE, stdout=PIPE, stderr=PIPE )
        self.stdout = self.process.stdout # None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.process.kill() # ensure that the process has been stoped.

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
            # print( "<<<<", self.stdout.peek(2))
            line = self.stdout.readline().decode()
            # print( "@@@", line )
            # the input string should end with just '\n' rather than '\r\n'

            if read_input and not has_read_input and line[-2:] != "\r\n" and line[-1:] == "\n":
                # print("Read input :)")
                if return_input:
                    std_output += line
                has_read_input = True

            if has_read_input or not read_input:
                peek_line = self.stdout.peek(1)
                # print( ">>>>", peek_line )
                # Powershell only. Should this be regex?
                # print("####", peek_line[:2] == b"PS", peek_line[-2:] == b"> ")

                if peek_line[:2] == b"PS" and peek_line[-2:] == b"> ":
                    # print("Next")
                    if return_prompt:
                        std_output += line

                    self.last_prompt = peek_line.decode()
                    self.executing_cmd = None
                    return std_output

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

        self.process.stdin.write( f"{cmd}\n".encode() )
        self.process.stdin.flush()

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

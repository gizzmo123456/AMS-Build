import threading
import time
import jobs.base_activity as base_activities
import terminal
import commonTerminal

import DEBUG

_print = DEBUG.LOGS.print


class Build( base_activities.BaseTask ):
    """
        Updates the project source directory, ready for build, test or deploy

        Supported stage data (excluding base class(es) data):
          key             : description
          -----------------
        - output-name     : (optional) format of the output name. (See 'Build.DEFAULT_BUILD_NAME' for default value)
        - docker          : (optional)
        -- image          : name of docker image to use (ie. 'imageName:Tag')
        -- args           : arguments to be used with docker
        - output-location : The location the output of the application will be save.
        - run             : List of commands to run in the process or container

        # NOTE: if docker is not supplied add the command to run the application to 'run'

        values registered into job.data (key format '{self.name}.{key-name}')
          key         : description
          -----------------
        - output-name : name of output
        -
    """

    DEFAULT_BUILD_NAME = "{project}-{name}-{build-id}"
    def __init__(self, name, job, stage):

        super().__init__(name, job, stage)

        self.container_attach_thread = None
        self.thread_lock = threading.RLock()

    def set_stage_data(self, data):

        super().set_stage_data( data )

        # make sure any required values have been supplied
        if "output-location" not in data or "run" not in data:
            self._status = base_activities.BaseActivity.STATUS["INVALID"]
            _print( f"{self.print_label} Invalid stage data passed to activity ({self.activity_name}::{self.name}). "
                    f"Stage data must contain 'output-location' and 'run'", message_type=DEBUG.LOGS.MSG_TYPE_ERROR )
            return

        # Set any default values if not been supplied
        self.stage_data.setdefault( "output-name", Build.DEFAULT_BUILD_NAME)
        self.stage_data.setdefault( "docker", None )

        # check docker has been configured correctly
        if self.stage_data["docker"] is not None:

            if "image" not in self.stage_data["docker"]:
                _print( f"{self.print_label} Invalid docker settings for activity ({self.activity_name}::{self.name})"
                        f"docker must contain 'image'.")
                self._status = base_activities.BaseActivity.STATUS["INVALID"]
                return

            self.stage_data["docker"].setdefault("args", "")

    def activity(self):

        with terminal.Terminal( log_filepath=self.job.output_log_path, n="helloo" ) as term:

            # configure docker if used.
            if self.stage_data["docker"] is not None:

                docker = commonTerminal.Docker( term, self.stage_data["docker"]["image"], self.print_label, **self.redirect_print )

                # check if the docker image exist and pull the image if necessary
                if not docker.image_exist_locally():
                    if not docker.pull_image():
                        return False

                # TODO: Create the volume mounts and append to args.
                # TODO: determine if run was successful or not.
                args = self.stage_data["docker"]["args"]
                args += " -ti " # make sure that the tty and interactive flags are supplied.

                # map volumes
                # args += " -v "

                # before running the container we need to start a new thread and attach to container with a new terminal
                # so we can interact with the containers shell.
                # We must start a new terminal in case the input_str is different from host os.

                self.container_attach_thread = threading.Thread( target=self.container_terminal_thread, args=[self.hash], kwargs={"poll": 1, "max_attempts": 5} )
                self.container_attach_thread.start()
                _print("BobBob....")
                exit_code = docker.run( self.hash, args )

                _print( self.print_label, f"Container exited with code: {exit_code} ", **self.redirect_print )
                _print( f"EXIT CODE: {exit_code}" ) # TODO: remove testing

                if self.container_attach_thread.is_alive():
                    _print("Attached thread has not exited", message_type=DEBUG.LOGS.MSG_TYPE_WARNING)

                return True

            _print( f"{self.print_label} No support for non docker build :(. (TODO: support <<)" )
            return False

    def container_terminal_thread(self, container_name, poll=1, max_attempts=5):

        _print("attaching....")

        # we must wait a sec to get the container chance to start :)
        time.sleep( poll )
        _print("Sleep Done")

        attempt = 0
        attached = False

        # We must skip the read on init since it will be empty
        with terminal.Terminal( input_str="/ # ", skip_read=True, n="thread" ) as term:
            # TODO: turn off console in term.

            attempt += 1

            _print(f"Attaching to container {container_name}")
            while not attached:
                output = commonTerminal.terminal_print( term, f"sudo docker attach {container_name}", console=True, output_filename="")

                if output[:5].lower() == "error":
                    if attempt < max_attempts:
                        _print(f"Unable to attach to container '{container_name}'. Attempting again in {poll} seconds (attempt {attempt} of {max_attempts})")
                        time.sleep(poll)
                    else:
                        _print(f"Failed to attach to container '{container_name}' after {max_attempts} attempts. Exiting.")
                        return
                else:
                    attached = True

            # now we can inject the run commands.
            # TODO: ....
        _print( "Finished running cmds........." )

    def terminate(self):

        with terminal.Terminal( log_filepath=self.job.output_log_path ) as term:

            if self.stage_data["docker"] is not None:
                docker = commonTerminal.Docker( term, self.stage_data["docker"]["image"], self.print_label, **self.redirect_print )
                docker.stop()
            else:
                _print( f"{self.print_label} Unable to stop build. No support for non docker.", **self.redirect_print )

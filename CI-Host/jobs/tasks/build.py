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

        with terminal.Terminal( log_filepath=self.job.output_log_path ) as term:

            # configure docker if used.
            if self.stage_data["docker"] is not None:

                docker = commonTerminal.Docker( term, self.stage_data["docker"]["image"], self.print_label, **self.redirect_print )

                # check if the docker image exist and pull the image if necessary
                if not docker.image_exist_locally():
                    if not docker.pull_image():
                        return False

                # TODO: Create the volume mounts and append to args.
                # TODO: determine if run was successful or not.
                docker.run( self.hash, self.stage_data["docker"]["args"] )

                return True

            _print( f"{self.print_label} No support for non docker build :(. (TODO: support <<)" )
            return False

    def terminate(self):

        with terminal.Terminal( log_filepath=self.job.output_log_path ) as term:

            if self.stage_data["docker"] is not None:
                docker = commonTerminal.Docker( term, self.stage_data["docker"]["image"], self.print_label, **self.redirect_print )
                docker.stop()
            else:
                _print( f"{self.print_label} Unable to stop build. No support for non docker." )
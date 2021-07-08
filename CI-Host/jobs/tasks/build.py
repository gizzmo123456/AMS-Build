import jobs.base_activity as base_activities

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

    def init(self):
        pass

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
        if self._data["docker"] is not None:

            if "image" not in self._data["docker"]:
                _print( f"{self.print_label} Invalid docker settings for activity ({self.activity_name}::{self.name})"
                        f"docker must contain 'image'.")
                self._status = base_activities.BaseActivity.STATUS["INVALID"]
                return

            self._data["docker"].setdefault("args", "")

    def activity(self):
        pass

    def terminate(self):
        pass
import common

import DEBUG
_print = DEBUG.LOGS.print


class DataStore:

    def __init__(self, json_path=None):

        self.data = common.get_dict_from_json(json_path, True) if json_path is not None else {}

        if len(self.data) == 0:
            _print( "Failed to load json ")

    def __getitem__(self, key):
        return self.data[ key ] if key in self.data else None

    def __setitem__(self, key, value):
        self.data[key] = value

    def get_default(self, key, default_value, set_default=False):
        if set_default:
            self.add_default(key, default_value)
        return self.data[ key ] if key in self.data else default_value

    def add_defaults(self, values):
        """
            Adds a dict of default values.
            This should be called to add default value when inheriting
        """

        for key in values:
            self.add_default(key, values[key])

    def add_default(self, key, value):
        """
            Adds a default value if the values does not already exist
        """

        if key not in self.data:
            self.data[key] = value


class PipelineStore( DataStore ):
    """
        parses and validates project pipeline file.
    """

    PIPELINE_TASKS = ["prepare", "build", "run"]
    # All fields defined in REQUIRED, OPTIONAL and DEFAULT must be added to PIPELINE_VALIDATE_METHODS at the bottom
    # Format:
    # {"taskName": [ [value, orValue], [andValue], [andValue, orValue, orValue, ...], ... ]
    PIPELINE_REQUIRED_FIELDS = {
        "prepare": [["main-directory-commands"], ["build-directory-commands"]],
        "build": [["execute", "docker"], ["commands"]],
        "run": [["execute", "docker"], ["commands"]]
    }

    PIPELINE_OPTIONAL_FIELDS = {
        "prepare": [],
        "build": [["name-format"], ["exit-line"], ["package"], ["cleanup"]],
        "run": [["name-format"], ["exit-line"], ["cleanup"]]
    }

    # {"taskName": [ [default, ifNotValue], [default], [default, ifNotValue, ifNotValue, ...], ... ]
    # default: default to add if itself and ifNotValue is not present.
    PIPELINE_DEFAULT_FIELDS = {
        "prepare": [],
        "build": [["name-format"], ["exit-line"], ["package"], ["cleanup"]],
        "run": [["name-format"], ["exit-line"], ["cleanup"]]
    }

    # Set the validate method the first time it is inited, since we cant see them till then
    PIPELINE_VALIDATE_METHODS = None

    def set_pipline_validate_methods(self):
        # methods to validate and set defaults.
        # prams: value, (out) data (ie. dict)
        # return: true if successful
        PipelineStore.PIPELINE_VALIDATE_METHODS = {
            "main-directory-commands": PipelineStore.__verify_pipe_main_dir_commands,
            "build-directory-commands": PipelineStore.__verify_pipe_build_dir_commands,
            "execute": PipelineStore.__verify_pipe_execute,
            "docker": PipelineStore.__verify_pipe_docker,
            "commands": PipelineStore.__verify_pipe_commands,
            "name-format": PipelineStore.__verify_pipe_name_format,
            "exit-line": PipelineStore.__verify_pipe_exit_line,
            "package": PipelineStore.__verify_pipe_package,
            "cleanup": PipelineStore.__verify_pipe_cleanup
        }

    def __init__(self, json_path):

        if PipelineStore.PIPELINE_VALIDATE_METHODS is None:
            self.set_pipline_validate_methods()

        self.valid = True

        super().__init__( json_path ) # load json file.
        if len(self.data) == 0:
            self.valid = False   # prevent us from saving the file if it failded to load.
            return

        # overwrite the defaults and clear the data.
        verified_pipeline = {
            "dummy-build": False,
            "environment": [],
            "pipeline": [],
        }

        # Validate and set defaults

        if "dummy-build" in self.data:
            if type( self.data["dummy-build"] ) is not bool:
                _print("dummy-build is not of valid type bool. Using default (False) ", message_type=DEBUG.LOGS.MSG_TYPE_WARNING)
            else:
                _print("Successfully parsed and verified dummy-build variable")
                verified_pipeline["dummy-build"] = self.data["dummy-build"]

        if "environment" in self.data or len( self.data["environment"] ) == 0 :
            if self._validate_environment_variables( self.data["environment"] ):
                _print("Successfully parsed and verified environment variables")
                verified_pipeline["environment"] = self.data["environment"]
            else:
                self.valid = False
                self.data = {}
                return
        else:
            _print("No environment to parse")

        verified_pipeline_stages = None

        if "pipeline" in self.data and len( self.data["pipeline"] ) > 0:
            verified_pipeline_stages = self._validate_pipeline_stages( self.data["pipeline"] )
            if verified_pipeline_stages is None:
                _print("Failed to verify pipeline stages", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
                self.valid = False
            else:
                _print("Successfully verified pipeline stages!")
                verified_pipeline["pipeline"] = verified_pipeline_stages
        else:
            _print("Failed to validate pipeline stages. Not present", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
            self.valid = False

        self.data = verified_pipeline_stages if verified_pipeline_stages is not None and self.valid else {}

    def _validate_environment_variables(self, variables):

        if type( variables ) is not dict:
            _print("Failed to validate 'environment' of pipeline file. Incorrect format. Must be a dictionary", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
            self.valid = False
            return False

        for key in variables:
            if type(key) is not str:
                _print("Failed to validate environment variable name (key). Must be a string", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
                self.valid = False
            elif type( variables[key] ) is not str and type( variables[key] ) is not int and \
                    type( variables[key] ) is not float and type( variables[key] ) is not bool:
                _print("Failed to validate environment variable value. Must be a string, bool, float or int", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
                self.valid = False

            if not self.valid:
                return False

        return True

    def _validate_pipeline_stages(self, pipeline_stages):

        if type( pipeline_stages ) is not list:
            _print("Failed to validate 'pipeline' of pipeline file. Incorrect format. Must be a List of dictionary, "
                   "where each value in the List is a pipeline stage", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
            return None

        verified_stages = []
        i = 1
        for stage in pipeline_stages:
            _print( f"[Starting pipeline stage {i} of {len(pipeline_stages)}]" )
            if type( stage ) is not dict:
                _print("Failed to validate pipeline stage. Incorrect format. Must be a dictionary", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
                return None

            verified_stage = self._validate_pipeline_stage( stage )
            if verified_stage is None :
                return None
            else:
                verified_stages.append( verified_stage )

            i += 1

        return verified_stages

    def _validate_pipeline_stage(self, stage):

        if "task" not in stage:
            _print("Failed to validate pipeline stage. 'task' not present", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
            return None
        elif type(stage["task"]) is not str:
            _print("Failed to validate pipeline stage. 'task' Incorrect format, must be string", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
            return None
        elif stage["task"] not in PipelineStore.PIPELINE_TASKS:
            _print(f"Failed to validate pipeline stage. Invalid 'task', must be {PipelineStore.PIPELINE_TASKS}", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
            return None

        task = stage["task"]

        # Format: [ [value, orValue], [andValue], [andValue, orValue, orValue, ...], ... ]
        required_fields = PipelineStore.PIPELINE_REQUIRED_FIELDS[ task ]
        optional_fields = PipelineStore.PIPELINE_OPTIONAL_FIELDS[ task ]
        found_fields = []

        # make sure that all the remaining required fields are present.
        for fields in required_fields:

            status, field = self.__find_pipeline_field( fields, stage )

            if status == 2:
                _print( f"Failed to validate pipeline stage required field. pipeline can not contain both '{field[0]}' and '{field[1]}' fields in task `{task}", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
                return None
            elif status == 1:
                _print(f"Failed to validate pipeline stage required field. task `{task}` does not contain a required field. must contain exactly one of {field}")
                return None
            else: # keep track of the found fields.
                _print(f"Found required field {field}")
                found_fields.append( field )

        # Do the same for optionals fields except skip over fields that are not found.
        for fields in optional_fields:

            status, field = self.__find_pipeline_field(fields, stage)

            if status == 2:
                _print( f"Failed to validate pipeline stage optional field. pipeline can not contain both '{field[0]}' and '{field[1]}' fields in task `{task}", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
                return None
            elif status == 0:  # keep track of the found fields.
                _print(f"Found optional field {field}")
                found_fields.append(field)

        _print("Successfully completed searching for required and optional task fields")
        for key in stage:
            if key != "task" and key not in found_fields:
                _print(f"Ignored '{key}' field, not an optional or required field for task '{task}'")

        verified_pipeline_stage = {
            "task": task
        }

        # Validate each of our found fields.
        i = 1
        for field in found_fields:
            _print( f"[{i} of {len(found_fields)}] *** {task}.{field} ***" )
            _print( stage[field] )
            if not PipelineStore.PIPELINE_VALIDATE_METHODS[field]( stage[field], verified_pipeline_stage ):
                _print(f"Failed to validate pipeline field {field}", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
                return None
            else:
                _print(f"Validated pipeline field '{field}'")
            i += 1

        # check the defaults have been added.
        # Format: {"taskName": [ [default, ifNotValue], [default], [default, ifNotValue, ifNotValue, ...], ... ]
        # default is the value to add if itself and ifNotValues are not found.
        for default_sets in PipelineStore.PIPELINE_DEFAULT_FIELDS[ task ]:
            found = False
            for not_value in default_sets:
                if not_value in verified_pipeline_stage:
                    found = True
                    break

            if not found:
                PipelineStore.PIPELINE_VALIDATE_METHODS[default_sets[0]](None, verified_pipeline_stage)
                _print(f"Added default pipeline field '{task}.{default_sets[0]}'")

        _print( f"pipeline stage '{task}'added successfully")
        return verified_pipeline_stage

    def __find_pipeline_field(self, search_fields, fields_to_search):
        """
        Searches a dict for search_fields. successful if exactly one match is found otherwise fails.
        :param search_fields:       The fields to search for using format: [field, orField, ...]
        :param fields_to_search:    The data structure (dict) to search.
        :return:                    (status, field). status 0: successful, 1: not found, 2: found two matches
                                    if status is 0, field is the found field
                                    if status is 1, list of fields not found
                                    if status is 2, tuple of matches

        """

        found_field = None
        for field in search_fields:
            if field in fields_to_search:
                if found_field is None:
                    found_field = field
                else:
                    return 2, (found_field, field)

        if found_field is None:
            return 1, search_fields
        else:
            return 0, found_field

    # Verify pipeline field helpers
    @staticmethod
    def __verify_string_list_helper(value, data, field_name):

        if type(value) is not list:
            _print(f"Failed to validate '{field_name}'. Incorrect format, must be list of strings",
                   message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
            return False

        if len( value ) == 0:
            return False

        for val in value:
            if type(val) is not str:
                _print(f"Failed to validate '{field_name}'. Incorrect format, list contains non-string")
                return False

        data[field_name] = value

        return True

    @staticmethod
    def __verify_string_helper(field_name, value, data, print_name, print_default=""):

        if field_name not in value:
            _print(f"Unable to valid {print_name}. Not present. {print_default}")
            return False

        if type( value[field_name] ) is str:
            data[field_name] = value[field_name]
            return True
        else:
            _print(f"Failed to validate {print_name}. Must be a string. {print_default}")
            return False

    @staticmethod
    def __verify_int_or_float_helper(field_name, value, data, print_name, print_default=""):

        if field_name not in value:
            _print(f"Unable to valid {print_name}. Not present. {print_default}")
            return False

        if type(value[field_name]) is float or type(value[field_name]) is int:
            data[field_name] = value[field_name]
        else:
            _print(f"Failed to validate {print_name}. Must be a int or float. {print_default}")
            return False


    # Verify pipeline field methods
    @staticmethod
    def __verify_pipe_main_dir_commands(value, data):
        """
            Required
            Task: Prepare
            Expecting: List of strings
        """

        return PipelineStore.__verify_string_list_helper( value, data, "main-directory-commands")

    @staticmethod
    def __verify_pipe_build_dir_commands( value, data):
        """
            Required
            Task: Prepare
            Expecting: List of strings
        """

        return PipelineStore.__verify_string_list_helper(value, data, "build-directory-commands")

    @staticmethod
    def __verify_pipe_execute(value, data):
        """
            Required, either execute or docker
            Task: build, run
            Expecting: string
        """

        if type( value ) is str and value:
            _print("Validated execute field successfully")
            data["execute"] = value
            return True

        _print("Failed validated execute", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)

        return False

    @staticmethod
    def __verify_pipe_docker(value, data):
        """
            Required, either execute or docker
            Task: build, run
            Expecting: dict
        """

        verified_docker = {
            # required
            "image": "",
            "args": "",
            # default
            "ams-mount-dest": "/AMSBuild",
            "source-mount-dest": "/projectSource",
            "build-output-dest": "/projectOutput",
            "stop-timeout": 10
        }

        if not PipelineStore.__verify_string_helper( "image", value, verified_docker, "image of docker" ):
            return False

        if not PipelineStore.__verify_string_helper( "args", value, verified_docker, "args of docker" ):
            return False

        PipelineStore.__verify_string_helper( "ams-mount-dest"   , value, verified_docker, "ams-mount-dest of docker", f"using default ({verified_docker['ams-mount-dest']})" )
        PipelineStore.__verify_string_helper( "source-mount-dest", value, verified_docker, "source-mount-dest of docker", f"using default ({verified_docker['source-mount-dest']})" )
        PipelineStore.__verify_string_helper( "build-output-dest", value, verified_docker, "build-mount-dest of docker", f"using default ({verified_docker['build-output-dest']})" )
        PipelineStore.__verify_int_or_float_helper( "stop-timeout", value, verified_docker, "stop-timeout of docker", f"using defualt ({verified_docker['stop-timeout']})" )

        _print( "Successfully verified docker field!" )
        data["docker"] = verified_docker

        return True

    @staticmethod
    def __verify_pipe_commands(value, data):
        """
            Required
            Task: build, run
            Expecting: List of strings
        """

        return PipelineStore.__verify_string_list_helper(value, data, "commands")

    @staticmethod
    def __verify_pipe_name_format(value, data):
        """
            Optional
            Task: build
            Expecting: None or string.
            Has default
        """
        data["name-format"] = "{project}-{build-hash}-build-{build-index}" if value is None or type(value) is not str else value
        return True

    @staticmethod
    def __verify_pipe_exit_line(value, data):
        """
            Optional
            Task: build, run
            Expecting: None or string.
            Has default
        """
        data["exit-line"] = "exit code 0" if value is None or type(value) is not str else value
        return True

    @staticmethod
    def __verify_pipe_package(value, data):
        """
            Optional
            Task: build
            Expecting: dict.
            Has default
        """

        verified_package = {
            "7z-build": False,
            "7z-hash": "sha1"
        }

        accepted_7z_hashes = ["sha1"] # TODO: <<, i cant remember them off the top of my head

        if value is not None:
            if "7z-build" in value and type( value["7z-build"] is bool ):
                verified_package["7z-build"] = value["7z-build"]

            if "7z-hash" in value and value["7z-hash"] in accepted_7z_hashes:
                verified_package["7z-hash"] = value["7z-hash"]

        data["package"] = verified_package

        return True

    @staticmethod
    def __verify_pipe_cleanup(value, data):
        """
            Optional
            Task: build, run
            Expecting: dict.
            Has default
        """

        verified_cleanup = {
            "remove-build-source": True
        }

        if value is not None and "remove-build-source" in value and type(value["remove-build-source"] is bool):
            verified_cleanup["remove-build-source"] = value["remove-build-source"]

        data["cleanup"] = verified_cleanup

        return True

if __name__ == "__main__":
    DEBUG.LOGS.init()
    pipeline_filename = "../CI-Projects/pipline.v2.json"
    pipeline = PipelineStore( pipeline_filename )
    _print( pipeline.data )
    _print("done")
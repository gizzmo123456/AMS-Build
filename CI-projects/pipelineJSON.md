```
> Json Pipeline for AMS-Build
> Example Json file with comments
> this is valid Json if the comments are removed.
```

 The build pipe lines have access to a number of variables  
 all variables must be formatted in curly braces, as if you where using String.format  
 eg. {variable_name}  
 
### Available Variables
#### - Directories
- project_dir               # CI-Project root.
- build_dir                 # Build output
- master_source_dir         # Project master root
- build_source_dir          # Project build root

#### - Project
- project                   # name of project that the pipeline belogs to
- master_build_name         # name of master build

### - build
- build_name                # build full name
- build_hash                # commit hash 
- build_index               # the build index

#### - Utills
- actor                     # the actor how triggered the build (actors must be supplied in the webhook)
- created                   # time the build was triggered


**There are others but there not recommended and may be removed in the future for that reason**

### Example Json File
```

{
  "build-name-format": "{project}_{build_hash}_build_{build_index}",            # [Optional] build name format
  "docker": {                                                                   # Specifies the docker image config
    "image": "dockerUser/mydockerimage:latest",                                 # The docker repo to pull the image from (This must be in a public repo as it stands)
    "args": "-it --rm",                                                         # [Optional] Any args that should be specifies when running the image
    "project-dest": "/root/project",                                            # The destination within the docker image that the project should be mounted
    "build-output-dest": "/root/project/Builds",                                # The destination within the docker image that build directory will be mounted
    "ams-container-dest:" "/root/AMS-Build",                                    # The destination within the docker image to mount AMS-Build
    "stop-timeout": 10                                                          # [Optional] how long until to wait until the container is forcefully stopped.
  },
  "prepare-build": {                                                            # Commands to be run to prepare the build ready for task automation
      "master-dir-commands": [                                                  # A list of command that should be run to prepare the build before the directory is copied to the build directory
          "sudo git pull origin master "
        ],
        "get-git-hash": true,                                                   # Should AMS-Build get the current git hash after the master has updated (non-webhook only, webhooks must always have the git hash supplied)
        "build-dir-commands": [                                                 # List of commands to be run inside the of the build directory after copying
          "sudo git checkout --detach {git_hash}"
        ]
  }
  "environment": {                                                              # Any environment vars that need setting within the docker container.
                                                                                #
  },
  "pipeline": [                                                                 # The build Pipeline. A List of Dicts
                                                                                # Each pipeline is run in its own environment, One after the other.
    {
      "name": "build",                                                          # the name of the stage
      "commands": [                                                             # the list of commands that should be run within the container for to complete the stage.
        "./build.sh",                                                           
      ],
      "exit-line": "exit code 0"                                                # The last line printed in each pipeline should be the status of the pipeline. if false, ignored. if not supplied expects "0"
                                                                                # This line detimins the status of build. ie PASS, FAIL
    }
  ],
  "cleanup": {                                                                  # How should the build directory be cleaned up once the build is complete
    "remove_build_source": true,                                                # Should the build source be removed?
    "7z_build": true                                                            # Should the build directory be wraped up into a 7zip file. (if true the original build output is remove)
    "7z_hash" : "sha1"                                                          # Should we create the hash for the 7z, (using 7z itself), set to 'null' for no hash otherwise you can use
                                                                                # crc32, crc64, sha1, sha256 or blake2ep 
  }
}
```

```
NOTE: Get git hash is skipped if supplied with the constructor (ie from a webhook). Otherwise it is executed directly
after the master folder is updated.
```

```
IMPORTANT NOTE.
If using multiple pipelines its it very important that each pipeline outputs to a 
different sub directory of the build directory.
```

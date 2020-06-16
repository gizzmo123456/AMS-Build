Root Directory for all projects.

File Structure
```
CI-projects                     # All project root
- Project_1                     # Project root
    - master                    # The master copy of the project
        - build                 # build out put folder (should only contain a show file)
        - project_source        # project source
        - output.txt            # empty stdout text file
        - pipeline.json         # pipeline config folder
    - builds                    # folder containing all built and queued builds
        - [project_name]_[build_hash]_build_[build_index]        # copy of the master project ready from building.
        - ...
    - project_build_stats.json  # file to store the build index, key, time ect...
---    
```


```
Pipeline files contain 4 sections.
1. docker       (required)
2. webhook      (optional)
3. environment  (optional)
4. pipeline     (required)

More info to follow....

1.
..

2. Webhoock
- webhook                       # root json node
    - name                      # name of webhook
    - method                    # method to receive json payload
    - project_request_name      # the name of the request that must match the value of request_name field to link to project name
    - data_fields               # names of json fields that we require to extract data from
        - actor                 # field of actor who triggered the build
        - request_name          # field of a name that is used to link the request to the project
        - build_hash            # field of a unique hash that can be used to identify the build ie. git commit hash
    - master-commands           # list of commands to be executed on the master project
        - []
    - pre-build-commands        # list of commands to be executed on copy of the master
        - []
# master-commands are executed before pre-build-commands.
# When a build is triggered it first runs the master-commands, followed by
# copying the master into builds folder and renaming accordingly, then
# executing the pre-build-commands, ready to execute the build.

```
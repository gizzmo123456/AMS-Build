Root Directory for all projects.

File Structure
```
CI-projects                     # All project root
- Project_1                     # Project root
    - master                    # The master copy of the project
        - build                 # build output folder (should only contain a show file)
        - project_source        # project source
        - output.txt            # empty stdout text file
        - config                # config folder 
            - pipeline.json     # project config
    - builds                    # folder containing all built and queued builds
        - [project_name]_[build_hash]_build_[build_index]        # copy of the master project ready for building.
        - ...
    - projectBuildInfo.json    # File to store the build index, key, time ect...
    - projectInfo.json          # File to store basic project stats in.
---    
```
For more info on project info see,
- **./exampleProject/projectBuildInfoJSON.md**
- **./exampleProject/projectInfoJSON.md**


```
Pipeline files contain 5 sections.
1. docker           (required)
2. webhook          (optional)
3. prepare-build    (required)  (docs to do)
4. environment      (optional)
5. pipeline         (required)

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


IMPORTANT NOTE: Prepare-build. If get_git_hash == true. master-dir-commands must be left in the 
git directory that we want to get the git hash from. 
Also Get git hash is skipped if supplied with the constructor. Otherwise it is executed directly
after the master folder is updated.

```
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

# Change Log

## version 1.0.1
Version 1.0.1 has changes that will break the current configuration
1) updating will remove the ```ams_path_config``` file, triggering the 
new not installed check. (It was incorrectly tracked by git)
2) The ```pipeline``` has been moved to the root of the project source, rather
than being in the config file.

### Added features
- Added Outbound Webhooks
    - supports discords
- Added Installed check.

### Changes
- removed ams_path_config from being tracked by git as it auto generated
- Move pipeline file to the root of the project source.


## Initial Release (v1.0.0)
### Features 
- Pull and Run docker containers to automate tasks
- update projects via git
- automatic build packaging into a 7zip
- trigger builds via webhhooks
- Web Interface
    - View projects
    - Trigger builds
    - View build output log
    - Download build 7z
    - View build status, actors ect.
    - View and cancel Active and Queued Tasks
    - All Info is available via the Web Interface API (ams-ci/api) (See TODO. for API plans)
- SSL for webhooks and web user interface
    
### Know Issues
- Pipelines Only have a single output directory.
- Some Users Types are not yet implemented
- Web User Interface display actions not available to users (but they are rejected)
- Delete Output Action not yet implemented
- Pass/Fail status not implemented
- Web Interface Cross-Origin Resource Sharing (CORS) is disabled

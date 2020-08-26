# Change Log

## v1.0.1
- Added outbound Webhooks
    - supports discords
- removed ams_path_config from being tracked by git as it auto generated
- Add installed check.


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

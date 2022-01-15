# Change Log

# Change log since version 1.0.0

## Version 1.1.0
- Updated python version to 3.9
- Updated Requirement version
  - FileLock 3.0.12 to 3.4.2
  - pycryptodome 3.9.8 to 3.12.0

## Version 1.0.4b (09/02/2021)
- Improved socket wrapper prints and redirected to file
- Add page redirect to login->auth

## Version 1.0.4 (07/02/2021)
- Added support for ssh keys  
  See [pipeline-configJSON.md](CI-projects/pipeline-configJSON.md) for more info

## Version 1.0.3 (31-01-21)
- Added a pass through socket to check for a http request when using https (ssl)
  - Fixes the ssl socket locking up when receiving http request
  - Added check for known bad request and bans ip
  - Added Log file for bad ip's and none https request

## Version 1.0.2 (28-09-20)

- Added 'Repository' and 'Branch' fields to in-Webhooks as a requirement
- Added 'webhook_fields.json' to map post data fields to the required webhook fields.
- Moved dummyBuild property in 'main-ci-host' to project pipeline file.
- Fixed *CRASH* when incorrect post data is received for a git webhook
- Created Ubuntu 16 branch
    - Fixed 7z not having '-sdel' switch
    - Known issue: No 7z hash :(
    
## version 1.0.1 (26-08-20))
Version 1.0.1 has changes that will break the current configuration
1) updating will remove the ```ams_path_config``` file, triggering the 
new not installed check. (It was incorrectly tracked by git)
2) The ```pipeline``` has been moved to the root of the project source, rather
than being in the config file.

### Added features
- Added Outbound Webhooks
    - supports discords
- Added Installed check.
- Added Complete Task callback to build tasks 
- Added Build Status
```
    - PASS      All pipeline tasks passed
    - FAIL      All pipeline tasks failed
    - WARN      Some tasks passed, some failed :|
```

### Changes
- removed ams_path_config from being tracked by git as it auto generated
- Move pipeline file to the root of the project source.
- www root/index is now defined in ```web_conf.json```
- moved docker container root path const to the docker def in the pipeline file 

### Fixes
- wrong git hash when building from the www interface


## Initial Release (v1.0.0) (19-08-20)
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

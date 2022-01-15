# Change Log

# Change log since version 1.0.0

# Version 1.1.0b1 (release data)
###### (11/07/21)
- Added write expects to terminal

###### (10/07/21)
- Added 2nd thread to interact with a docker container. 

###### (09/07/21)
- Added commonTerminal.Docker class for common docker commands
  - Image exist locally
  - Pull image
  - Run image
  - Container is running
  - Remove container
  - Stop/Kill container
- Added docker section to build activity


###### (08/07/21)
- Added invalid state to activities
- Added skip job if an invalid activity is created.
- Added rename activity if the name is not unique by append an index.
-

###### (07/07/21)
- Changed Terminal read/write to return tuple containing the last cmd ran and output
- Added option to terminal to remove output colors 
  Tho this requires further improvements. However, it works for 'git' atm
- Fixed git keys in jobs.data to be consistent with other keys
- Add commonTerminal for common terminal functions and classes
  - Moved terminal_print from prepare to commonTerminal


###### (06/07/21)
- Changed project 'build' directory name to 'output'
- Added created output dir and log file to job.
- Added 'display_timestamp' to DEBUG.LOG.print as an optional param (default: True)
- Added activity method to prepare.
  - loads ssh agent if required
  - runs 'run' commands from pipeline/config
  - captures the git commit hash if not already supplied to job.
  
###### (05/07/21)
- Added terminal
- Added method to activity to set relevant data into job
- Added add_unique_data to job to set data if not already set
- Added execute to job and activity
- 

###### (04/07/21)
- Added short hash property to job and BaseActivity
- Added create jobs from pipeline to job queue
- 

###### (02/07/21)
- Changed UAC, to now load in the access level rather than it being supplied to the constructor
  - changed update user projects to update user, now it updates the access level as well.
  - the access level for UAC with origin 'webhook' is now set when set_webhook is called.
- Added helper script
  - with method to get all direct and indirect subclasses of type
- Added base activity and subclasses for BaseAction and BaseTask
  - Added dictionary to job for activities of type Action and Task
  - Added activities import file, so the activities dictionary is filled automatically

###### (01/07/21)
- Moved job queue into its own dedicated module
- Added method to UAC to authorize (inbound) webhooks
  This prevents the need to load in webhook config file outside the UAC module.
  - Fixes possible stack overflow when attempting to load the webhook config file
    without the correct information supplied.
  - Integrated into webhook module and commonProject.get_project_config 
- Renamed access level WEBHOOK to TRIGGER in UAC.
  (WEBHOOK will be removed soon)

## Version 1.0.4f2 (09/02/2021)
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

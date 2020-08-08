# AMS-CI (AMS-Tasks)

AMS-Ci is a tool designed to launch docker containers that build projects,
triggered by webhooks, from GitHub and Bitbucket (and maybe others)

AMS-CI is built in 3 main sections.

- **CI-Host**
- **CI-Projects**
- **CI-Root**       // (Will be renamed to CI-Container.)

## CI-Host
CI-host is the main host of the tool, and has 3 main aspects

#### 1. ci
When a webhooks are received, the docker container is launched, configed to
the pipeline.json, once all pipeline steps are complete the results are 
zipped into a 7z and updates the web-interface (queue and projects).

For details about pipeline.json see CI-Projects/pipelineJSON.md



#### 2. webhook
Triggers Build via webhook from GitHub or BitBucket

###### Webhook Config
```
Port            8081
root path       /request/
Query String (GET)
    name        {webhook name}
    project     {project name}
    
eg. mydomain.com:8081/request?name=example&project=example_project
```

#### 3. web interface
The Web interface lists all queued and active tasks, along with all projects
and builds details (build name/number, download links ect...) 
 
###### Web Interface Config
```
Port            8080
root path       /ams-ci/
Default user    Admin
temp pass       password!2E
```

## CI-Project
Ci-Project is the root for all projects.
All projects are in there own folder, which contains the project master folder,
the builds folder and the project build status (still to do)

See the CI-Project/README.md for further info on folder structure

## CI-Container (Ci-root)
Ci-container is mounted into the docker container along with the pipeline.json file
where it will setup the environment and run each pipeline, along with log the 
container output to file.


========================
Users / UAC note.

When updating users UAC it can take upto 30 seconds to be applied
to all logged in users. The UAC objects caches project data for
UAC.__update_project_TTL seconds (default 30 seconds). 
It is designed to prevent excessive file reads.

Also. its worth noting that a project will display 'Not found'
if the user does not have access.

Also get project info and get build info 
returns the default values if the user does not have access to the project
meaning that get_project_info and get_project_build_info can not be used 
to determin if a project exist or not nor if the user has access to it.


===================
7z hash pipeline Notes.
values can be 
- null              (no hash)
- 'CRC32'
- 'CRC64'
- 'SHA1'
- 'SHA256'
- 'BLAKE2sp'

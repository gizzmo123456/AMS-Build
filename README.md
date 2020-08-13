# AMS-Build 
###### AMS - *Automation Made Simple* 


## Overview
AMS-Build is a simple lightweight automation tool designed run,
build and automate tasks in docker containers and deliver the results to 
a clean and simple to use web user interface.

AMS-Build has capabilities to accept webhooks from BitBucket and GitHub,
along with manual triggers via the web user interface.

AMS-Build is writen in Python, and uses Git to update projects and 
Docker for containerizing tasks.  
AMS-Build is designed to run on Ubuntu 18+ and has NO support for any other 
OS (as it stands, tho the web interface will work on windows, for testing).

## Contents
  1. System Requirements and Dependencies 
     1. Requirements
     2. Dependencies
  2. Modules and Components
  3. Getting Started
  4. Further Reading  
  5. ...
    
## 1. System Requirements and Dependencies 

### Requirements 

###### **Minimal system requirements:**  
- 1 core
- 1GB memory  
###### **Recommended system requirements:**  
- 2 core
- 4GB memory  

### Dependencies  
| Product        | Version |
| :------------: | :-----: |
| Ubuntu (64bit) | 18+     |
| Python         | 3.6     |
| PyCryptodome   | 3.9.8   |
| Git            | [version here] |
| Docker         | [version here] |

## 2. Modules and Components
AMS-Build is made up of several components, across 3 key modules.
1. CI-Host
2. CI-Project
3. CI-Container (or CI-root)

#### CI-Host
CI-Host is the main module that handles automation tasks which is made up
of 3 components in itself.

The main component is the ```Main Ci Host``` which is heart of the system 
and houses the other 2 components, (1) ```Web User Interface``` and
(2) ```Git Events/Webhooks```.

Both the ```Web User Interface``` and ```Git Events/Webhooks``` use a shared 
queue from ```Main Ci Host```, to queue tasks such as Start/Build, 
Stop/Cancel and delete output/build data (todo) ect, from there respected locations.

The ```Main Ci Host``` is then responsible for processing said task accordingly.
Some tasks are executed immediately once received by the main ci host while
others (build tasks) are moved to a 'pending tasks' list, until there is an
available slot in the 'active tasks' list.

**Current Available Tasks include,**
```
- Build task,       # the main task type, handles updating project, 
                    # setting up output folders and handling docker 
                    # containers. 
                    # Build tasks are queued until a build slot is available.
                    
- Cancel task       # If task is pending, removes it from the queue,
                    # Otherwise stops the docker container.
                    # Cancel tasks are executed immediately once received 
                    # by the main ci host.
                    
- Delete output     # Deletes all of a tasks output (TODO, not implemented)
                    # Delete are executed immediately once received 
                    # by the main ci host.
```
##### - Web User Interface
The Web User Interface is the main portal, that allows users to view, create 
and cancel any tasks, along with view project outputs, status and other basic
info, also not forget access to the 7z's of the builds. 

Users must login to the Web User Interface and can only access / preform 
operations on project that they have permission to (and only up to there access level) 

For more info on user types and accounts see, 
- **User Types and Access Levels** 
- **Adding A New User**

##### - Git Events/Webhooks
The Git Events receives a webhook from either GitHub or BitBucket, when an 
event such as PUSH is trigger on the GIT server. When the event is received 
by AMS-Build, a build task is created and queued if the git trigger actor is 
an approved actor in the target project webhook config.

For further info on Webhook Actors see,
- **Approving webhook actors**

###### User Types and Access Levels ( For Web User Interface and Webhooks )

| User Type    | Access Level | Permissions                                                  | Other Info                 |
| :----------- | :----------: | :----------------------------------------------------------- | :------------------------- |
| NO AUTH      | 0            | None. No Access                                              |                            |
| USER         | 1            | View/Download assigned projects                              |                            |
| WEBHOOK      | 2            | Only Triggers Build Tasks                                    | Available to Webhooks only |
| MODERATOR    | 3            | Same as USER + Trigger Tasks for assigned projects           |                            |
| ADMIN        | 4            | Same as MODERATOR + Add/Assigne users to assigned project    | TODO (Not implemented)     |
| SERVER ADMIN | 5            | All Permissions on All Projects                              | TODO (Not implemented)     |

#### CI-Project
Ci-Project directory contains all projects available to AMS-Build.
Each project must contain a 'master' directory for the master copy of the project
and a 'builds' directory for each triggered build. 

The master directory must contain an empty folder for the output build, the 
project source directory, and the config directory along with an empty txt file
for the std-output.

Finally there must be pipeline.json file in the config directory.

The root of each project also contains auto generated files for basic project 
and build info.

For more info on the CI-Projects structure and overview of pipeline files see, 
- **./CI-projects/README.md**
- **./CI-project/pipelineJSON.md**

For more info on auto generated files see,
- **./CI-projects/exampleProject/projectBuildInfoJSON.md**
- **./CI-projects/exampleProject/projectInfoJSON.md**

Also see, (in this readme)
- **Getting started**, for info on setting up a project. 

#### CI-Container (CI-root)
CI-Container, is a simple piece of python that is launched inside the container 
to setup any environment variables set in the Pipeline.json file followed by
running each stage of the defined pipeline. 

Each stage runs in a new environment.

## 3. How The Automation/Build Task work

![image](./.assets-for-git/AMS-Build.jpg)  
[fig 1. System overview]  

When a build task is first triggered and accepted, the ```"prepare-build"```
sections of the projects pipeline.json file is ran.

First it runs the ```master-dir-commands``` inside of the master source directory
(```CI-Project/{project_name}/master/project_source```)  

Followed by copying the master directory into the builds folder also renaming 
the folder to build name

Once the project has been copied, the ```build-dir-commands``` are ran inside
of the copied project source
(```CI-Project/{project_name}/builds/{build_name}/project_source```)

And the task is finally queued for execution.

```
Note.
I decided to update and copy the master directory, to ensure that project
is not modified before or during execution. 
So that the project remains the exact state that it was at trigger time.
```

When the ```Main Ci Host``` receives a build task (on the shared queue),

It first put the task into the ```pending task``` list where it waits for
an available task execution slot in the ```active task``` list.

```
Side Note.
When there are no pending task, the main thread waits for a task to arrive on 
the shared queue. (the queue blocks the thread)
If there are pending tasks the main thread ticks over once every second to monitor
task thread statuses (ie task alive?). Also collects new tasks as they arrive.

The reason for this is to ensure that the queues does not block us from, 
from promoting queue tasks to active tasks. But this no longer the case
as we have methods to unblock the queue when a task is completed.
So this may change in the near future. :)  
```
Once an available task slot becomes available, the task is moved from the 
```pending``` list to the ```active``` list, followed by starting a new 
task worker (thread) with the task passed in and the task is executed.

When the task is executed its starts by pulling the docker image if once 
does not exist locally. Once the docker image has been obtained, the docker
run command is built using the ```docker``` section of the projects pipeline,
and the container is run.

The docker container is configure as follows.
```
# Container name 
'{project_name}{build_hash}'

# Container args 
Are defined in the 'docker' section of the pipeline file.

# Mounted Directories
'.../{build_name}/project_source' -> 'docker.project-dest' defined in pipeline
'.../{build_name}/build'          -> 'docker.build-output-dest' defined in pipeline
'.../{build_name}config'          -> root directory of the container as a READ-ONLY directory
'CI-Root'                         -> root directory of docker as a READ-ONLY directory

# Image
Defined in the 'docker' sections of the pipeline file.

# command
python3 {path_to_ci_root}/main-ci-root.py

Note.
Root needs to be added to the 'docker' section of pipeline.
```
Once all pipeline task has completed, the status is determined and the project 
clean up begins 
```
Note. ATM the system is not suitable for multiple pipeline task, due to the single build directory.
Also Note. Build Status is yet to be implemented, I seem to of forgot about this :/
```

When the clean up begins, it first 7Zips the build folder (also removing it), 
followed by generating the 7z hash, if configured to do so in the 'clean-up'
section of the pipeline file.

```
Note. Builds can only be downloaded from the Web User Interface if they are zipped.
```

7z hash types available
- **null**      (do not hash)
- **CRC32**
- **CRC64**
- **SHA1**
- **SHA256**
- **BLAKE2ep**
```
Note. that 7z is used to generate the hash.
```

And the project source is remove, if also configured to do so in the 'clean-up'
section of the pipeline file 

Once the clean up has finished a ```TASK-COMPLETE``` message is put onto the 
shared queue, to ensure it is unblocked and able to update the task list 
(queue and active)

###### Project Build Statuses

| Status | Discription          | Note              |
| :----- |:-------------------- | :---------------- |
| PASS   | Build was successful | |
| FAIL   | Build failed         | Not Implemented   |
| CANCEL | Build was canceled   | |
| SKIP   | Build was skipped    | Not Implemented   |
| DUMMY  | Dummy fake build     | |


## 4. Getting Started

### Setting up a project 
TODO.

### Using The Web User Interface
#### Setup
```
Web User Interface Config,

Port            8080
root path       /ams-ci/

Default user    admin

eg. mydomain.com:8080/ams-ci/

```

#### Interface

#### API

### Accepting Webhooks
```
Webhook Config,

Port            8081
root path       /request

Query String (GET)
    name        {webhook name}
    project     {project name}
    
POST data:
    data from github or BitBucket webhook
    
eg. mydomain.com:8081/request?name=example&project=example_project

```

### A Bit About Security
As with any private task or automation server, its recommended to host it on 
a private network so it can be accessed internally or via a vpn or proxy.

But this is not always possible especially if using GitHub or (public) BitBucket 
webhooks.
In this case it is recommended to setup a firewall on the webhook port (default 8081)
to only allow connection for trusted git servers.
```
GitHub IPs      : (link)
BitBucket IPs   : (link)
```
And to only allow connects via vpn to the web interface (default port 8080).

## 5. Further Reading 

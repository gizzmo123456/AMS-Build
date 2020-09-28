
[x] Apply const web root path thingy
[x] replace the DOCKER_ROOT_DIR Const with the pipeline version
[x] Fixed test project build sh files 
   
# TODO.

would it be better to store queue and project info in redis?
see https://pypi.org/project/redis/ for py lib

------------------------------------------------------------------------
Release v1.0.0 TODO.
------------------------------------------------------------------------
[x] Update Documents
    - Readme
    - Json description docs
    - Todo Refresh
[x] Clean install
[x] SSL
[x] Push to GitHub

------------------------------------------------------------------------
Urgent v1.0.x
------------------------------------------------------------------------
[x] SSL socket only handles a single connection at a time or hangs for some reason
    - Change the way that sll sockets are initialized which seems to of improved if
      not resolved the issue
[x] Add a short 1 to 2 sec delay before printing status code.
    - Solution is for users to define a short delay in the pipeline or shell script.
    (it is more of an issue cased by the compiler or build tool printing a 
     message just after the status code is printed)  
[x] Add Branch to Webhooks
[x] Fix *crash*, Add some check for data on webhooks... 

[ ] Fix 7zip in ubuntu 16.x
    -[x] add own remove method (-sdel does not seam to work on u16) (for 16 only)
    - hash? (hash does not seem to work on u16)
    
------------------------------------------------------------------------
v1.0.0 Missed tasks TODO. 
------------------------------------------------------------------------

[x] Pass/Fail Status
[x] Move dummy-build option to pipeline.json file

[ ] build cool down  
[ ] Only build latest  
[ ] Build output needs to be moved or build into a folder relating to the pipeline task


[x] Sort console output, mark sure that there are no prints, only _prints  
    [ ] And add some log files :)  
[ ] Allow API CORS (See Web interface API for more info)  
[ ] find out why .secrets are by user 'me' not 'root'  
[ ] Add write stdout to file, in DEBUG.  
[ ] add values to projectBuildInfo.json
    - [c] git hash  
    - [c] 7z hash  
    - [ ] canceled by   

[ ] Find out why we get Can not cancel build, insfficient priv's when a task completes.
    (this is hampering because no user is added for 'task complete' object. Its fine tho as its only a queue un-blocking task )
[ ] Improve WWWUser message feedback when trigger tasks via the web_userInterface.
    - ATM users have to be logged in to receive messages and messages are very
      static.
      I fell that the message should be changed to have a message param rather than
      having the task and successful params.
    - messages should be write to file, so message can be queued for when the user next logs in

------------------------------------------------------------------------
Post v1.0.0 Release TODO.
------------------------------------------------------------------------

[ ] Add test connection for bitBucket
[x] Automatically detect install path
[ ] In init we need to detect if the cd/git commands fail.
    And if a input is required for what ever reason.

[ ] Update Directory names from CI-XXX to AMS-XXX.
    (this is going to be a bit of a pain)
    CI-Host     -> AMS-Build
    CI-Projects -> AMS-Projects
    CI-Root     -> AMS-Container
    
[ ] Auto Build Deletion (for builds older than X amount of time)  
    With the option to keep the first/last build of each month   

[ ] Add Project Storage limits.

[ ] Accept actor name using any case (lower/upper ect...)
[ ] Add config/method for loading key into ssh-agent

[ ] Improve the way that content is loaded into the webpage.
    - At the moment each messages, active and queue sections all auto-
    refresh every X amount of time (i think its set to 60sec for active 
    and queued, and 30sec for messages) The problem is 9 times out 10 
    there's no change in data and when there are changes its laggy, and
    the project and builds dont auto refresh.
    - To make the solution more efficient there two approaches that could 
    be taken.
    
        1. We could turn the request into a single http request, that
        only returns data for each panel (in a single json dict) if its
        changed since the last update.
        This would require a lot of JS and server work tho, but would be 
        the most efficient approach, as there would be a maximum amount of 
        request per min and it would also decrees the overrule payload, 
        since the payload would only return data if there's been a change.
```
    Example JSON response (no change)
    {
        active: [],
        queue: [],
        message: [],
        projects: [],
        builds: []
    }
    Example JSON (message change)
    {
        active: [],
        queue: [],
        message: [{"message", "Queueing Build"}, {"error", "Unable to queue build..."}],
        projects: [],
        builds: []
    }
```

        2. The other would be to add a new request, to check if any of the
        panels have changed sine the last time panel had a content change,
        Then load in the content using the current methods (but only if needed)
        This would require that we make a minimal amount of request, per min
        but would reduce the payload overall, as the main (payload) request
        are only made if needed. This would require minimal JS and server work.
```
    Example JSON response (no change)
    {
        active: false,
        queue: false,
        message: false,
        projects: false,
        builds: false
    }
    Example JSON (message change)
    {
        active: false,
        queue: false,
        message: true,
        projects: false,
        builds: false
    }
```
------------------------------------------------------------------------
Web-pages Todo. No Rush, it can all be done back end :)
------------------------------------------------------------------------
[ ] sort out the css and js paths  
[ ] Add users  
[ ] Add project  
[ ] Pipeline Editor  
[ ] Remove Builds    

[ ] Add method to get empty templates, useful for message output  

[x] Message section.  

[ ] Fixed view overflowing on the X axis
[x] Add AMS-Labs Logo 
[ ] Add Zip hash to builds panel

------------------------------------------------------------------------
API and CORS plans
------------------------------------------------------------------------
[ ] Allow CORS for API/Output Log/Build Download
    - [ ] Add API-keys to allow CORS
        - Add API User Type?
        - Logs and Builds will require additional checks  
        
------------------------------------------------------------------------
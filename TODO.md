# TODO.

- [x] Finishing mapping file path
- [x] Add copy master, to build folder
- [x] Add build log
- [x] redesign the json file.

- [x] Add Basic webhook
- - [x] test 
- [x] add simple webpage

============================================

- [x] Add Job Queue

==========================================
- [x] add clean up
- [x] add lock files
- [x] pipeline
- [ ] build index
- [ ] build cooldown
- [ ] only build lastest in queue
- [ ] multi-project
- [x] Fix debug print to file and output file path 

=========================

- [ ] Make format_values available inside of the contatiner?
      Or at least a subset of usefull values
      (Also if i do this it would be worth breaking FV down into two dicts,
       one that available only on the host and there other available in both
       ie, it does not make sence to share the local paths in the container
       as don't exist, while some like now are dynamic )

==========================

it would be better to store queue and project info in redis?
see https://pypi.org/project/redis/ for py lib

========================================================================
Ignore all of Above :)
========================================================================

[x] Add build to project.json file  ??  
[x] Build index  
[ ] build cool down  
[ ] Only build latest  
[ ] Add Build Now to 'Web_Interface'  
[x] Add refresh functionality  
[x] Add Download to 'Web_interface'  
[x] Add Build naming convention to the pipeline file  
[ ] Add Last complete build index to projectInfo   
[x] make tasks.json untracked by git   
[x] intergrate projects into to the project info file.  
    This will affect the web interface API    
    
[ ] Build output needs to be moved or build into a folder relating to the pipeline task
```
eg.
builds/eProj_hash_build_N/Stage_0/
builds/eProj_hash_build_N/Stage_1/
... 
```
    
========
[x] add auth to output and dl files.  
[x] change BinaryFileStream default chunkSize 1024  

[x] Block all CORS request  
[x] Add Additional headers to process_request,  
    This will mean that filename can be removed.  
[x] remove Cross-Origin header  
[x] Add content-cache no-store http header   
    And or max-age  
[x] Add content length http header  
[x] Add Location http header to redirect login  
  - To achieve this i think it would be worth moving the page status   
    code from WWWPage to the page callback, along with headers.  
    
    This would be that 'None' can be no longer supplied as the callback  
    instead use an inline function.  
    
    The when the user logs in we can send head 303 (See other) and  
    redirect the user using the 'Location' header.  

[x] change logout to its own callback so we can redirect back to root after logout.   
[ ] sort out the css and js paths  

[ ] Build Now  
[x] Cancel task ->   
    [x] this should be added to BuildTask obj so it can preform clean ups and input the data
    [x] pending  
    [x] active  

[x] Fix tasks title heading overflow  
[x] Fix build no zipping :(  
[x] Sort build so newest is top  

[x] Sort console output, mark sure that there are no prints, only _prints  
[ ] And add some log files :)  

[x] Add Project Users  
[ ] Clean the task file on start.  

[x] move the master-commands and pre-build-commands to it own section  
    Also improving the names.  
    
[ ] Allow API CORS  
    
[c] Add check for users file on start,  
    if not present add a setup string.  
    
[c] Add UAC object to bridge the gap between Webhook and web_interface.  
    - Webhooks only have access to create new builds, if the actor is listed in the webhook config  
    - WWWUsers, have a uac access level and project list, to restrict access on the web_interface  
    
With this, we can remove webhook from buildTask constructor and the actor  
can change to the UAC object  

[ ] find out why .secrets are by user 'me' not 'root'  

[ ] Add write stdout to file, in DEBUG.  

[ ] add values to projectBuildInfo.json
    - [c] git hash
    - [c] 7z hash
    - [ ] canceled by 

[ ] Change build hashing system
    - currently we just the git hash for our build hash, and thats a little harder for build now so.
    [c] Change build hash to a simple md5/sha-1 hash based on the build name.
    [c] Add git hash to formatValues
    [c] Add 7z hash to build json.

[ ] Find out why we get Can not cancel build, insfficient priv's when a task completes

[ ] Improve WWWUser message feedback when trigger tasks via the web_userInterface.
    - iv notices that it returns completed successful when a request has only been excepted
      So i think it would be good, if there was a message to say the request has been made,
      Accepted and complete
 
[ ] Fix user manager not adding access level to user    

========================================================================
Release v1.0.0 TODO.
========================================================================
[ ] Update Documents
    - Readme
    - Json description docs
    - Todo Refresh
[ ] Clean install
[ ] SSL
[ ] Push to GitHub

========================================================================
v1.0.0 Missed Features TODO. 
========================================================================
TODO... 

========================================================================
Post v1.0.0 Release TODO.
========================================================================
[ ] Auto Build Deletion (for builds older than X amount of time)  
    With the option to keep the first/last build of each month   

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
========================================================================
Web-pages Todo. No Rush, it can all be done back end :)
========================================================================
[ ] Add users  
[ ] Add project  
[ ] Pipeline Editor
[ ] Remove Builds  

[ ] Add method to get empty templates, useful for message output  

[x] Message section.  

[ ] Fixed view overflowing on the X axis
[ ] Add AMS-Labs Logo 
[ ] Add Zip hash to builds pannel

============== uac server TEST LIST:  
[x] test uac for output  
[x] test uac for dl  

-> Spot test for below has PASSED :)  
[x] test uac for get_project_build_info  
[x] test uac for get_project_info  
[x] test uac for get project pipeline (both wh and www)  

- Remember to remove the project info file. its broken :)   

== NOTES web_interface Content callback change.  

Remove  
status and headers   
from wwwPage  

and add them to the content callback.  

then load_page with return the full stack  
content, status, content_type, page_headers  

this will then alow us to set more dynamic headers   
and will be able to move js, css directorys into its   
own wwwPage, to clean things up a little  
 
========================================================================
Known Issues
========================================================================
- When running a container print messages have a load of white space added 
  for some unknown reason.


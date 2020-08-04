# TODO.

- [x] Finishing mapping file path
- [x] Add copy master, to build folder
- [x] Add build log
- [wip] redesign the json file.

- [x] Add Basic webhook
- - [x] test 
- [wip] add simple webpage

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
[ ] Add Build naming convention to the pipeline file
[ ] Add Last complete build index to projectInfo 
[x] make tasks.json untracked by git 
[x] intergrate projects into to the project info file.
    This will affect the web interface API  
    
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
[ ] Cancel task
    [ ] pending
    [ ] active

[x] Fix tasks title heading overflow
[x] Fix build no zipping :(
[x] Sort build so newest is top

[x] Sort console output, mark sure that there are no prints, only _prints
[ ] And add some log files :)

[ ] Add Project Users
[ ] Clean the task file on start.

[ ] move the master-commands and pre-build-commands to it own section
    Also improving the names.
    
[ ] Allow API CORS
    
[x] Add check for users file on start,
    if not present add a setup string.
    
[ ] Add UAC object to bridge the gap between Webhook and web_interface.
    - Webhooks only have access to create new builds, if the actor is listed in the webhook config
    - WWWUsers, have a uac access level and project list, to restrict access on the web_interface
    
With this, we can remove webhook from buildTask constructor and the actor
can change to the UAC object

========================================================================
Web-pages Todo. No Rush, it can all be done back end :)
========================================================================
[ ] Add users
[ ] Add project
[ ] Remove Builds

[ ] Message section.

============== uac server TEST LIST:
[ ] test uac for output
[ ] test uac for dl

-> Spot test for below has PASSED :)
[ ] test uac for get_project_build_info
[ ] test uac for get_project_info
[ ] test uac for get project pipeline (both wh and www) (still to do.)


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

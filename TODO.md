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
[ ] Add refresh functionality
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
[ ] Add Additional headers to process_request,
    This will mean that filename can be removed.
[x] remove Cross-Origin header
[ ] Add content-cache no-store http header 
    And or max-age
[ ] Add content length http header
[ ] Add Location http header to redirect login


[ ] Fix tasks title heading overflow
[x] Fix build no zipping :(
[ ] Sort build so newest is top

[ ] Sort console output, mark sure that there are no prints, only _prints
[ ] And add some log files :)

[ ] Add Project Users
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

============
Note 23/06/2020
So when i get back to this, we need to find out the the ajax is not working,
from the server perspective, we are receiving the request. from the client tho
there is an error, where we are trying to set the innerHTML of a string (the element id )
and no error is being thrown :( 
 
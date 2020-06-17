# TODO.

- [x] Finishing mapping file path
- [x] Add copy master, to build folder
- [x] Add build log
- [wip] redesign the json file.

- [x] Add Basic webhook
- - [x] test 
- [ ] add simple webpage

============================================

- [x] Add Job Queue

==========================================
- [ ] add clean up
- [ ] add lock files
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

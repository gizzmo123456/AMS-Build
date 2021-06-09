# AMS-Build Version MVP + SSL + SSH  -> 1.1.x Planed Updates
# AMS-Build WWW interface 1.0 -> 2.0 module  

-----------
### Tasks
- [ ] Base Task (see [activites readme](CI-Host/jobs/readme.md) for more info)
  - [ ] Build
  - [ ] Run (A task that run an application until stopped)
- [ ] Add a method to define shell commands for different OS's and methods
  - [ ] Add Shell builder
  - [ ] Add a method to run task without Docker (ie. just on the command line)
  - [ ] Add a method to use linux virtualization to run task rather than docker.
- [ ] Improve SSH, to capture PID so it can force exit the SSH agent if exited without status 0    
- [ ] Add multiple branch support

### Pipeline / Configs
- [ ] Add GitConfig (Might be worth adding a Version control/Git module )
  ```
  This is to remove the git commands form the pipeline file, and should be saved in the config directory
  Also it doent seem locgical to pull the project to find that the pipline has changed.
  ```


### Job Queue, tasks and project
- [ ] Add project task cool down
- [ ] Add active task limits for projects
- [ ] Add method to only build the latest task request.  
  ```  For instance, if a project has a task queue and another request comes in the first task queued should be discarded```
- [ ] Add project storage limit
- [ ] Add Auto output/build deletion

### Job Queue And (inbound) Webhooks
- [ ] Add prepare project job (This should only be one per project at any time)  
This is, so we can remove the prepare from the inbound Webhook witch is causeing it to never respond to the server.

### Message queue
- [ ] Push all user messages to file, so they can be displayed to the user to the user when they log in
- [ ] Add method to link WebHook users to WWWUsers

### WWW interface
- backend redesign
  - [ ] Add public Directory
  - [ ] Add method to add non-HTTPS directory for things such as fav icon  
  - [ ] WWWUser (This should simply be a wrapper for the UAC class, with helper method for WWW)
  - [ ] WWWPage -> Create a base class for pages
    - Index
    - Not Found
    - Log in (auth)
    - Log out
    - Api
    ```
      This will alow the output to be defined in the class rather than setting a callback into the class.
      The (raw) API WWWPage should be set as a singleton, and be availbale to all WWWPages, since it serves
      the content to all pages!.
     
      - Each WWWPage should contain the required UAC code, to view the page.
      - The API page should handle all template request
      - Each WWWPage should must have a method for handler stats such as 'No permission'
    ```
  - [ ] Improve API filtering to handle dictionaries 
  - New Pages
    - [ ] Add/Modify Users
    - [ ] Add Pipeline editor
    - [ ] Add new/modify project
    - [ ] Integrate a view for logs, Rather than just displaying the raw output
      - [ ] Add view active page jobs
  - New Features
    - [ ] Add Delete build

### HTTP Server.
- [ ] Enable CORS (baseHTTPServer.BaseServer)
- [ ] Rename baseHTTPServer.BaseServer To .HTTPRequestHandler

### Pass-through SSL Socket
- [ ] Add auto IP banning (This should not last for longer than 24 hr)
- [ ] Add Auto HTTPS redirect for valid HTTP request

### User Manager and UAC
- [ ] Add Version to UserManager and user file.
- [ ] Update UAC to use sha256 for secretes
- [ ] Update UAC to use a bit mask for permission rather than using access levels.
  (also some access level have not yet been implemented.)  
ie.
```
mask       (hex)        discription
0b00000000 (0x0)      = No auth
0b00000001 (0x1)      = View and download assigned projects
0b00000010 (0x2)      = Trigger build on assigned projects
0b00000100 (0x4)      = Managerment for assigned projects
0b00001000 (0x8)      = User managerment for assigned projects
0b10000000 (0x80)     = Admin access

So a user with access 0b00000011 (0x3) would allow a user to trigger a build 
and view and download build

This would then allow webhoocks to be 0b00000010 (0x2) and prevent the permision override.
```
- [ ] Admin features always requires a password via HTTP/HTTPS

### Platforms
- Add Windows support
- Test on Ubuntu 20 LTS
- Deprecate Ubuntu 16 support 

### (outbound) Webhooks
- Add Slack support
- Add Teams support

### Debugging
- [ ] Add write stdout to file

### Other
- [ ] Need to create the logs directory for the socket wrapper
- [ ] Clean up printing and debugging messages.


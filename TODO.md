# TODO Release 1.1.x

------------------------------------------------------------------------
Release v1.1.x Bug Fixes.
------------------------------------------------------------------------
- [ ] Fix Inbound webhooks blocking thread while updating git repo (See: I-02, for more info)
- [ ] Fix Web-Interface not redirecting users to panel when logging in to download a build (See: I-01, for more info)

------------------------------------------------------------------------
Release v1.1.x Improvements.
------------------------------------------------------------------------
- [ ] (I-01) Re-write Web-Interface.
    - This should have a method to extend the Web-Interface 
- [ ] Add better list and map filter support to Web-Interface API.
- [ ] (I-02) Improve BuildTask, by using a base class
    - [ ] Add BaseTask
      - [ ] Add DummyExecute to BaseTask (This is to make it more generic and so it can be removed from the Main-CI-Module.)
      - [ ] Change execute method to return none or another task if necessary (ie. GitTask would return a new BuildTask)
    - [ ] Change BuildTask to inherit from BaseTask
    - [ ] Add GitTask (Webhook)
    - [ ] Add RunTask (Maybe)
    The Base Task is just required to contain the ``execute()`` method.
    And ``DummyExecute`` Once added.
- [ ] Update method that we use, to interact with process (ie. Update terminal)
  - [ ] Replace common.run_process with a new interactive terminal module
    - This is to give us more control over the terminal process and allow us to run a single
      command at a time rather than batching them all together making it easier to detect errors.
- [ ] Improve UAC module
  - This should use a system similar to rwx (read-write-execute) permissions on a per-project basis
        - Read: Basic Access to project (ie view and download project build)
        - Write: Upload files ?? 
        - Execute: Execute tasks (and update configs)
    Something like this
- [ ] Improve password store
  - [ ] Add SHA1
  - [ ] Move encryption keys to cloud platform (ie. AWS, Azure or GCP) (most likely to only add support for AWS atm)
  - [ ] Add secondary salt
  - [ ] remove space from password store.
  - [ ] And change format so it's the other way around.

- [ ] Add date/time format to const.py
- [ ] Improve install.sh script to detect dependencies (maybe)

------------------------------------------------------------------------
Release v1.1.x New Features.
------------------------------------------------------------------------
- [ ] Add Windows CMD/Powershell support
  - [ ] Add install.bat
  - [ ] Add method to build command depending on platform

------------------------------------------------------------------------
Release v1.1.x From 1.0.x backlog
------------------------------------------------------------------------
[ ] Fix Favicon / Add Public directory
[ ] Re route debug logs to file. 
[ ] find out why .secrets are by user 'me' not 'root' 
[ ] When starting the ssh-agent it should capture the pid in case the shell doent exit cleanly
[ ] Build Deletion (WWW) (maybe auto deletion as well?)
[ ] Add Project Storage limits.

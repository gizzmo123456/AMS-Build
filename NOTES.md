# 1.1.x Notes and Ideas

------------------------------------------------------------------------
Release v1.1.x Notes
------------------------------------------------------------------------
### user_manager.py
- It appears that update user secret relies on auth user first witch does ent seam all that good tbf
- It to add the sha1 cipher to better protect passwords

### User_manager and user_access_control (UAC)
There seems to be a disconnect between the two. I think I originally took this approach since WebHooks 
don't authorize via the user manager. However, it would make a lot more since for the user manager to 
handle the creation of UAC objects. As a result UAC objects are created throughout the Web Interface,
witch requires a total overhaul, so it would make sense to this first.

### User Permission
So I want to do something more along the lines of RWX (read-write-execute).
Read:    View, download & view project logs
Write:   Modify project configs
Execute: Execute Tasks, Actions and Scheduled Actions (Jobs)

I propose this is stored as 4 bits per project. Where the most significant bit is the webhook flag.
Webhooks are only permitted to have 'execute' permission. There for the webhook flag MUST NOT be supplied 
for a user.

ie. hmmm....
0101 (-r-x) would give a users read and write permissions on a project.
1101 (hr-x) would be an invalid webhook
1001 (h--x) would be a valid webhook.

To support different permissions on user the users.json file will require an update.
the ``projects`` field should change to a list of lists (or lis of dicts) with project
with first value as the project name (or ID if I can be asked), and the permissions to that project.
ie.
```
"project": ["Example Project", "rwx"]
```

And access_level should change to platform permissions.

# Web InterFace and www page / www user
- Web interface it kinda fine how it handles things, however the whole generic WWWPage thing
with all the methods as callbacks in the web interface is a bit of head screw. It's got to 
happen, each page needs to be its own class that inherits from (a re-writen) WWWPage.
Furthermore, the api should inherit from APIPage (could maybe  be an extension of WWWPage)
Witch would handle its own supported templates.
This would make it much easier to extend in the future.
- Error page should be static?
- WWWPage need to be able to load content from APIPages. 
- both API and WWW Pages execute methods (current WWWPage.content_callback) return 
``redirects, page content, status, content type, headers`` Its this redirect that is bad.
and when return the value to be sent we just have ``page content, status, content type, headers``
i think it would make more sense to handle errors via the stats code. and the content would be
an additional message to display :)



------------------------------------------------------------------------
Release v1.1.x Ideas
------------------------------------------------------------------------
Thinking that I want to add scheduled tasks such as auto deletion, clean-ups ect.

At the moment we have Actions and Tasks (well a single task atm). 
I think it could add "Jobs" to this for the automated actions and add a job scheduler.

An Action is a single activity (Such as 'Cancel Build' or 'Delete Build') that can occur on any given project
A Task is a configurable series of activities or operation that can occur on any give project
And a Job would be a configurable scheduled Action or Task that can occur on any given project

This is subject to the user having permission to the project.
# Task JSON File

The file is automatically generated.  
The file should only be modified by main-ci-host. (see def update_queue_info)
main-ci-host will overwrite any changes 

the data is used to serve the www API

```
{
  "active": [                                                       # Active Tasks
    {
      "task_name": "Build 1 ExampleProject",                        # Name of task
      "task_hash": "asdf4565yhgrt765uhjte56y456yrgtr7465",          # the task hash
      "project": "exampleProject",                                  # name of project that the task belongs to
      "created_by": "Ashley Sands",                                 # actor who created the task
      "created_at": 346765764757876533475,                          # time task was created
      "start_at": 346765764757876584930                             # time task started to build
    }
  ],
  "pending": [                                                      # Pending/Queued tasks
    {
      "task_name": "name",                                          # Name of task
      "task_hash": "hfatr43tgrvsed6y5tgrfds6y5hgfddfgdf8",          # the task hash
      "project": "exampleProject",                                  # name of project that the task belongs to 
      "created_by": "Ashley Sands",                                 # actor who created task
      "created_at": 346765764757876533475                           # time task was created
    }
  ]
}
```
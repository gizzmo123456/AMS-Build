# Jobs (Queue Items) and Activities 

## Jobs
A job is a wrapper class containing all activities to get the "job done" :P  
A job ensures the user has access to achieve each activity before commencing  

this is a work in progress :P

## Activities

Aa activity is an item that can be queued to be processed by the CI-Host.  
Queue Items come in two main flavors
1. Action
  ``A single action that is preformed within the AMS-Build environment`` 
   
2. Task
  ``A task that is lunched into a new (or its own) environment 
    (such as a docker container) to be executed``
   
```
Queue Items

## 1. Actions
- Cancel Task
- Delete Output
- Task Complete (Queue unblocker to update build information)

## 2. Task
- Prepare
- Build
- Run (Deploy)
```

Furthermore, activities are only exposed to modules that are able to trigger 
the action or task  
For example:
```
main-host
- actions (all)
- tasks (all)
www interface:
- actions
  - cancel task
  - delete output
- tasks (all)
(inbound) webhooks
- tasks (all)
```

# Note: This is a work in progress
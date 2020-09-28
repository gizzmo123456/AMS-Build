
# Changes Since Version 1.0

## Version 1.1.0
    - Added 'Repository' and 'Branch' fields to in-Webhooks as a requirement
    - Added 'webhook_fields.json' to map post data fields to the required webhook fields.
    - Fixed *CRASH* when incorrect post data is received for a git webhook
    - Moved dummyBuild property in 'main-ci-host' to project pipeline file.
    - Created Ubuntu 16 branch
        - Fixed 7z not having '-sdel' switch
        - Known issue: No 7z hash :(
     

## Version 1.0.1
    - Changed hashes. Now generates it own build hash rather then use the git hash
      and add 7z hash for 7z files
    - Added auto detect install path to shell file
    - Added 'pass' status
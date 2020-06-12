Root path for all build pipeline configs  
Config files are passed into the container at runtime  

Config files are writen in json,

```
AmsCiConfig:            Parent node for config file
    docker:             Docker settings.
        image:          name of docker image.
        params:         any params that are required to be passed into the docker image.
    
    environment:        Any environment variables that need to be set within the docker image.
    
    pipeline:           The intirer build pipeline
        stage:          and indervidule stage with in the pipeline
            name:       name of the stage in the pipeline
            commands:   list of commands to exicute.
```
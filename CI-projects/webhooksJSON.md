# Inbound & Outbound Webhooks

## Inbound
AMS-Builds uses webhooks from git servers to trigger builds when an event such as
push occurs.   

At the moment AMS-Build has support from 
- **BitBucket** 
- **GitHub** (I think, probably still needs doing)  

At requires that the project and webhook name is supplied via the query string (GET data) 
and the actor, repo name and git hash is supplied via POST as JSON data

### Data Keys
| Method  | Key                            | Note                       |
| :---    | :---:                          | :---                       |
| GET     | name                           | Webhook name               |
| GET     | project               | Project that the webhook belongs to |
| POST    | actor.display_name             | name of approved git actor |
| POST    | repository                     | name of repo               |
| POST    | push.changes.0.new.target.hash | git hash                   |


Example
```
Query String (GET)
https://mydomain.com/request?name=ExampleHook&project=exampleProject

JSON (POST) (minimal data structure)
{
  ...
  "actor": {
    "display_name": "git actor"
  },
  "repository": "MyRepo",
  "push":{
    "changes": [
      {
        "new": {
          "target": {
            "hash": "SomeGitHash"
          }
        }
      }
    ]
  }
  ...
}

```

### Adding an in-bound webhook
AMS-Build has support for multiple webhooks, per project. Each inbound def is
defined in json list under the ```in-webhook``` section and only requires 2 params.
```name``` the webhook name and ```authorized-actors``` a list of authorized git actors.

example
```
"in-webhooks":[
    {
      "name": "Webhook-one",
      "authorized-actors": [
        "git actor"
      ]
    },
    {
      "name": "Webhook-two",
      "authorized-actors": [
        "git actor one", 
        "git actor two"
      ]
    }
  ]
```

## Outbound
Outbound webhooks are handy for automatically posting message to team messages 
services such as Slack or Discord.

All Webhooks require 5 fields.
1. **"hook-name"** name of inbound webhook
2. **"type** The type of webhook ie discord
3. **"trigger"** the trigger type of the hook. ie build-complete
4. **"url"** The address the webhook is targeting
5. **"data"** The webhooks payload.

The ```data``` fields must contain at least one nested fields called ```"default"```,
which is the default data for the message. (this will very depending on the type)
There may be other nested fields in data, but it will depend on the type.

### Support
Currently AMS-Build only has support for Discord.

The json definition for the web hook almost follows the discord format.  
The supported discord webhook elements
- standard content 
- username overrides
- embeds
  - with Fields
  
See [Discord Webhooks API](https://discord.com/developers/docs/resources/webhook#execute-webhook) for more info  
and See [This Gist on Discord Webhooks](https://gist.github.com/Birdie0/78ee79402a4301b1faf412ab5f1cdcf9) to better understand the structure

(but there is no need to get to deep into it, we only support the standard content, embeds and username overrides)

#### Discords

##### Default Fields
- **content** The standard message field.
- **username** The username override
- **avatar_url** the url to the users avatar

##### Embeds
Discords support up to 10 embeds.

Embeds require a ```title``` and a ```description``` and has an optional
```field``` list. Each field requires a ```name```, ```value``` and an optional ```inline```

```
Note.
They are all the fields that we currently support.
```
Example
```
{
      "hook-name": "Build Complete Discord",
      "type": "discord",
      "trigger": "build-complete",
      "url": "",
      "data": {
        "default": {
          "content": "Helloo World Im A bot"
        },
        "embeds":[
          {
            "title": "{project} - Build Complete",
            "description": "Build {build_index} has completed!",
            "fields": [
              {
                "name": "Build Name",
                "value": "{build_name}",
                "inline": false
              },
              {
                "name": "ID",
                "value": "{build_index}",
                "inline": true
              },
              {
                "name": "Status",
                "value": "{build_status}",
                "inline": true
              }
            ] 
          }
        ]
      }
    }
  ]
}
```

### Formatting.
There is far few string format variables that can be used, but they will very
depending on the trigger type. define format variables using curly braces ie.
```{format_var}```

### Build-Complete string variables (Only the notable ones)
- **Project**
- **build_name**
- **build_index**
- **build_hash**
- **git_hash**
- **7z_hash**
- **trigger_method**
- **actor**
- **created**
- **status**
- **canceled_by**
- **7z_link**
- **output_log**
# Pipeline-config.json
The pipeline-config.json file can be found in the projects master config directory,
and MUST NOT be place in the project itself. ie. 
```CI-projects/exampleProject/master/config/pipeline-config.json```

The file is intended to enable SSH support and other potentially sensitive pieces of information.
(Tho the 'other potentially sensitive pieces' is still to be considered )

The structure of the file mimics that of pipeline.json, tho currently it only has support to enable
SSH "prepare-build" section (ie in both subsections "master-dir-commands" and "build-dir-commands").

## SSH Keys
At the present time adding an SSH key is NOT an automated process and therefore must be done manually.  
Furthermore, the SSH folder is NOT created by AMS-Build and must be created by an admin with 
root privileges.

The SSH agent is started before executing the relevant subsection of ```perpare-build``` in ```pipline.json```
and exited at the end of the subsection.

### SSH Config
1. To begin, navigate to ```CI-Host/data/.secrets``` and add a new directory called ```.ssh/``` with 
   root privileges only.  
   
Example:  
```bash
cd CI-Host/data/.secrets
sudo mkdir .ssh/
sudo chmod 700 .ssh/
```
```
NOTE: this step is only required the first time you add an SSH key
```
2. Add a new directory to the ```.ssh/``` directoy with the exact name of the project 
   (the same as the one in ```CI-project```).
```bash
sudo madir .ssh/exampleProject/
```
```
Currently AMS-build on supports a singal SSH key per defined section
```

3. Create/Move your ssh key into the directory ```Importent the key must have root priviliges```.  
   The name of the SSH key can be specified in the ```pipeline-config.js``` file

## Variables
No variables are available at this time since it only enable SSH

## Example Json File
```
{
  "prepare-build": {
    "master-dir-commands": {
      "ssh": {                
        "use": true,            # should SSH be used on while executing the master-dir-commands (default: false)
        "name": "ams.id.rsa"    # (optinal) the file name of the SSH key. (DO NOT include the path) (default: "id_rsa").
      }
    }
    "build-dir-commands": {
      "ssh": {
        "use": true
      }
    }
  }
}
```
If SSH is not required for the subsection, there no need to include it in the file :P

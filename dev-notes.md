# Dev Notes

### Dev Versions as of 02/06/21
| Dependence     | Version |
| :------------: | :-----: |
| Ubuntu (64bit) | 20.04.2 LTS |
| Git            | 2.25.1      |
| Docker         | 20.10.2     |
| 7Zip           | 16.02       |
| Python         | 3.8.5       |
| pip3           | 20.0.2      |
| PyCryptodome   | 3.9.8       |
| (Py) FileLock  | 3.0.12      |

### Readme update todo:
- Queue Items (Activities)
  - Finalize dedicated readme  
  - Update task in main read me.
    
### TODO:
- commonProject.get_project_pipline needs param v2_config removing
  - this will also need top be done in Job.create_jobs_from_pipeline
  - Also the .v2. will need removing from the pipeline file
  
#### Testing
- Test job
  - create jobs from pipeline
    - [ ] check job is skiped if stages is not defined
    - [ ] check job is skiped if stages contains no stages
  - create job of tasks
    - [ ] check it fails if no task is defined
    - [x] check it fails if the defined task does not exist
    - [ ] check fails if the user (uac) does not have access
      - [ ] www interface
      - [x] webhooks
    - [ ] 
  

##### something something 
- Docker finds image if the image name is empty ie. ```image: "" ```
- Add logs directory to projects

- Needs to add job to unblock queue once a job has finished. 

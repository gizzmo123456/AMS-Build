import queue
import time
import jobs.job as job
import common
import commonProject

import jobs.base_activity # TEMP TODO: remove.

import DEBUG

_print = DEBUG.LOGS.print

class JobQueue:

    MAX_ACTIVE = 3
    __queue_job = None

    def __init__(self):

        self.alive = False

        self.queue   = queue.Queue()    # thread safe queue.
        self.active  = []               # active jobs
        self.pending = []               # pending execution.

        JobQueue.__queue_job = self.queue_job

    def queue_job(self, job_to_queue):

        if not isinstance( job_to_queue, job.Job ):
            _print( "JobQueue: Unable to queue job. Item is not an instance of job.")
            return

        self.queue.put( job_to_queue )
        _print(f"JobQueue: Job '{job_to_queue.name}' ({job_to_queue.short_hash}) queued.")

    def queueCount(self):
        """

        :return: (active count, pending count, queued count)
        """

        return len( self.active ), len( self.pending ), self.queue.qsize()

    def process_forever(self):
        """
            Processes the job queue until exited.
            (blocks thread)
        """

        self.alive = True
        update_queue_file = False
        _print("JobQueue: Starting to process jobs.")

        #
        while self.alive:

            # wait for new job to be queued.
            new_job = self.queue.get( block=True )
            _print( "JobQueue: Collected new job!", console=True )

            # move the new job into the pending queue.
            if isinstance( new_job, job.Job ) :
                if new_job.status == job.Job.STATUS["CREATED"]:
                    if new_job.promote_to_pending():
                        self.pending.append( new_job )
                        update_queue_file = True
                    else:
                        _print(f"JobQueue: Discarding job ({new_job.short_hash}). Unable to promote to a pending state. ")   # TODO: This could be because the job is waiting for the completion of another job
                else:
                    _print( f"JobQueue: Unable to queue job. Status is not CREATED. (status: {new_job.status} )" )

            # process the pending and active queues,
            # unless theres a new job to be collected from the queue.
            while len( self.pending ) > 0 and self.queue.empty():
                # clean up any active jobs that have completed.
                for i in range( len(self.active)-1, -1, -1 ):
                    if self.active[ i ].is_complete:
                        completed_job = self.active.pop( i )
                        update_queue_file = True
                        _print(f"JobQueue: Job Complete: {completed_job.name} ({completed_job.hash})")

                # promote pending tasks, while there are active slots available.
                while len( self.pending ) > 0 and len( self.active ) < JobQueue.MAX_ACTIVE:
                    promoted_job = self.pending.pop( 0 )
                    if promoted_job.execute():
                        self.active.append( promoted_job )
                        _print(f"JobQueue: Successfully promoted job ({promoted_job.short_hash}) from 'PENDING' to 'ACTIVE ")
                    else:
                        _print(f"JobQueue: Failed to execute job ({promoted_job.short_hash})")

                    update_queue_file = True

                if update_queue_file:
                    update_queue_file = False

                # while theres no jobs to collect sleep for a second.
                if self.queue.empty():
                    time.sleep(1)

        self.alive = False
        _print("JobQueue: Ended processing jobs.")


    def exit(self):

        self.alive = False
        _print( "JobQueue: exiting")

    # static methods
    @staticmethod
    def create_jobs_from_pipeline( uac, project, **data ):
        """
            Creates and queues jobs from the projects pipeline file.
        :param uac:     user access controle object
        :param project: project to create jobs for
        :param data:  additional data to be set into the job.
        """

        _print("CREATING JOB FROM PIPELINE ...")

        # load the projects pipeline file.
        # if none is returned either the project does not exist or the user does not have access to the project.
        pipeline_conf = commonProject.get_project_pipeline( uac, project, version2=True )

        if pipeline_conf is None:
            _print(f"JQ-CreateJob: Failed to load pipeline for project '{project}'. "
                   f"(either project does not exist or user does not have access)",
                   message_type=DEBUG.LOGS.MSG_TYPE_WARNING)
            return

        if not pipeline_conf.get( "active", True ):
            _print(f"JQ-CreateJob: Unable to create jobs from project ({project}) pipeline. Pipeline not active")
            return

        if "jobs" not in pipeline_conf:
            _print(f"JQ-CreateJob: Unable to create jobs from project ({project}) pipeline. 'jobs' is not defined")
            return

        pipeline_jobs = pipeline_conf["jobs"]  # Key: job name, Value: stages []
        job_names = list( pipeline_jobs )
        created_job_count = 0

        if len( pipeline_jobs ) == 0:
            _print(f"JQ-CreateJob: Unable to create jobs from project ({project}) pipeline. 'jobs' contains no jobs")
            return

        for job_name in job_names:
            pipeline_job = pipeline_jobs[job_name]

            if "stages" not in pipeline_job:
                _print(f"JQ-CreateJob: Unable to create job ({job_name}) from project ({project}) pipeline. 'stages' not defined for job")
                continue
            elif type( pipeline_job["stages"] ) is not list:
                _print(f"JQ-CreateJob: Unable to create job ({job_name}) from project ({project}) pipeline. stages is not an Array.")
                continue

            new_job = jobs.job.Job( job_name, uac, project, **data )    # TODO: add some of the pipeline data.
            job_stages = pipeline_job["stages"]
            stage_index = 0
            skip_job = False

            for stage in job_stages:

                stage_name = stage.get( "name", f"stage-{stage_index}" )

                if "task" not in stage:
                    _print(
                        f"JQ-CreateJob: Unable to create job ({job_name}). 'task' is not defined in stage ({stage_name}).")
                    skip_job = True
                    break

                task_name = stage["task"]
                stage_task = jobs.job.Job.ACTIVITIES["TASKS"].get( task_name, None )

                if stage_task is None:
                    _print(
                        f"JQ-CreateJob: Unable to create job ({job_name}). The defined task ({stage['task']}) in stage does not exist.")
                    skip_job = True
                    break

                if not uac.can_execute_activity( stage_task ):
                    _print(
                        f"JQ-CreateJob: Unable to create job ({job_name}) for project ({project}). User ('{uac.username}' origin: '{uac.origin}' ) does not have permission to execute task ({task_name}) (stage: {stage_name})")
                    skip_job = True
                    break

                stage_task = stage_task( stage_name, new_job, stage )

                if not stage_task.is_valid:
                    _print( f"JQ-CreateJob: Unable to create job ({job_name}) for project ({project}). Invalid Action ({stage_task.action_name}::{stage_task.name}) created." )
                    skip_job = True
                    break

                new_job.append_activity( stage_task )
                _print(f"JQ-CreateJob: Created job from project ({project}) pipeline")

                stage_index += 1

            if skip_job:
                # discard and move onto the next job.
                del new_job
                continue

            JobQueue.__queue_job( new_job )
            created_job_count += 1

        if created_job_count == 0:
            _print( f"JQ-CreateJob: Failed to create any jobs from project ({project}) pipeline file.", message_type=DEBUG.LOGS.MSG_TYPE_WARNING )
        else:
            _print(f"JQ-CreateJob: Successfully created {created_job_count} of {len( pipeline_jobs )} job from project ({project}) pipeline")

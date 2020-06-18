#!/usr/bin/env python3
import DEBUG
import build_task
import webhook
import web_interface
import threading
import time
from http.server import HTTPServer
import queue
import common


def web_hook():

    wh_server = HTTPServer( ("0.0.0.0", 8081), webhook.Webhook )

    while alive:
        wh_server.serve_forever()

    wh_server.server_close()

def web_interface():

    wi_server = HTTPServer( ("0.0.0.0", 8080), web_interface.WebInterface )

    while alive:
        wi_server.serve_forever()

    wi_server.server_close()

def task_worker(job):

    _print("Starting new task")
    job.execute()

    zip = job.get_config_value( "cleanup", "7z_build" )
    cleanup = job.get_config_value( "cleanup", "remove_build_source")

    if zip is not None and zip is True:
        _print("Zipping build...", output_filename=job.stdout_filepath, console=False)
        # zip the build, removing zipped files
        for line in common.run_process("cd {build_dir}; sudo 7z a {build_name}.7z ./Build/ -sdel;".format( **job.format_values ), "bash"):
            _print( line, output_filename=job.stdout_filepath, console=False)
        _print("Zipping Complete", output_filename=job.stdout_filepath, console=False)
    else:
        _print( "Skipping Zipping", output_filename=job.stdout_filepath, console=False )

    if cleanup is not None and zip is True:
        _print( "Cleaning Source...", output_filename=job.stdout_filepath, console=False )
        # remove the (copied) source folder
        for line in common.run_process( "cd {build_dir}; sudo rm -r {build_source_dir}".format( **job.format_values ), "bash" ):
            _print( line, output_filename=job.stdout_filepath, console=False )
        _print( "Build Source Removed", output_filename=job.stdout_filepath, console=False )
    else:
        _print( "Skipping Clean up", output_filename=job.stdout_filepath, console=False )

    _print("job "+job.format_values["build_hash"]+" complete")


if __name__ == "__main__":

    thr_lock_tasks = threading.Lock()
    alive = True

    DEBUG.LOGS.init()
    _print = DEBUG.LOGS.print

    task_queue = queue.Queue()
    max_running_tasks = 1
    pending_tasks = [] # task object
    active_tasks = []  # tuple (thread, task object)

    webhook.Webhook.task_queue = task_queue

    webhook_thread = threading.Thread( target=web_hook )
    web_interface_thread = threading.Thread( target=web_interface() )

    webhook_thread.start()
    web_interface_thread.start()

    while alive:

        # wait for a task to come in while theres no pending
        task = task_queue.get(block=True, timeout=None)
        _print( "Task de queued :)" )

        # wait to start pending task,  collecting new task as they are submitted
        while task is not None or len(pending_tasks) > 0 and task_queue.empty():
            if task is not None:
                if isinstance( task, build_task.BuildTask ):
                    pending_tasks.append( task )
                    _print("task_pending")
                else:
                    _print("invalid task")
                task = None
            # find if there is any available resources to launch the task
            # - clean up old task
            for i in range(len(active_tasks)-1, -1, -1):
                if not active_tasks[i][0].is_alive():
                    active_tasks.pop(i)
                    _print("complete task removed ({active_tasks}/{max_task})".format(active_tasks=len(active_tasks), max_task=max_running_tasks))
            # - start new tasks
            while len(active_tasks) < max_running_tasks and len(pending_tasks) > 0:
                start_task = pending_tasks.pop(0)
                worker = threading.Thread( target=task_worker, args=(start_task,) )
                worker.start()
                active_tasks.append( (worker, start_task) )
                _print( "Active task {active_tasks} of {max_tasks} | current pending {pending}".format(active_tasks=len(active_tasks),
                                                                                                       max_tasks=max_running_tasks,
                                                                                                       pending=len(pending_tasks) ))
                start_task = None
            # time for a nap
            time.sleep(1)

    #alive = False
    DEBUG.LOGS.close()

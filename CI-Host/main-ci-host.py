#!/usr/bin/env python3

import DEBUG
import build_task
import common
import webhook
import threading
from http.server import HTTPServer
import queue

def web_hook():

    server = HTTPServer( ("0.0.0.0", 8081), webhook.Webhook )

    while alive:
        server.serve_forever()

    server.server_close()

def web_interface():
    pass

def task_worker(job):

    job.execute()


if __name__ == "__main__":

    alive = True

    DEBUG.LOGS.init()
    DEBUG.LOGS.set_log_to_file( message=True, warning=True, error=True, fatal=True )
    _print = DEBUG.LOGS.print

    task_queue = queue.Queue()
    max_running_tasks = 1
    pending_task = [] # task object
    active_tasks = [] # tuple (thread, task object)

    webhook.Webhook.task_queue = task_queue

    webhook_thread = threading.Thread( target=web_hook, args=() )
    webhook_thread.start()

    while alive:

        # wait for a task to come in while theres no pending
        task = task_queue.get(block=True, timeout=None)
        print( "Task de queued :)" )

        # wait to start pending task,  collecting new task as they are submitted
        while task is not None or len(pending_task) > 0 and task_queue.empty():
            if task is not None:
                if isinstance( task, build_task.BuildTask ):
                    pending_task.append( task )
                    print("task_pending")
                else:
                    print("invalid task")
                task = None
            # find if there is any available resources to launch the task
            # - clean up old task
            for i in range(len(active_tasks), -1, -1):
                if not active_tasks[i].is_alive():
                    active_tasks.pop(i)
            # - start new tasks
            while len(active_tasks) < max_running_tasks and len(pending_task) > 0:
                start_task = pending_task.pop(0)
                worker = threading.Thread( target=task_worker, args=(start_task,) )
                worker.start()
                active_tasks.append( worker, start_task )

    #alive = False
    DEBUG.LOGS.close()

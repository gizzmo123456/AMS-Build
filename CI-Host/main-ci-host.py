#!/usr/bin/env python3
import DEBUG
import build_task
import webhook
import web_interface
import threading
import time
from http.server import HTTPServer
from baseHTTPServer import ThreadHTTPServer
import queue
import sharedQueue
import queue_item
import common
import user_manager

SKIP_TASK_EXECUTION = True      # if Runs the task without executing the container
SKIP_TASK_DELAY = 15            # if task execution is skipped how long to halt the worker, to emulate execution

def web_hook():

    # Use the single thread HTTPServer for the web hook,
    # we only want to handle a single connection at a time
    # to ensure that the request are executed in order :)
    wh_server = HTTPServer( ("0.0.0.0", 8081), webhook.Webhook )

    while alive:
        wh_server.serve_forever()

    wh_server.server_close()

def www_interface():

    # Use the threaded HTTPServer for the web interface,
    # so we're not handing around while files are downloaded
    # and pre-sockets are opened
    wi_server = ThreadHTTPServer( ("0.0.0.0", 8080), web_interface.WebInterface )

    while alive:
        wi_server.serve_forever()

    wi_server.server_close()

def update_queue_info( a_tasks, p_tasks ):

    _print( "Building Queue Info File" )
    tasks = { "active": [], "pending": [] }

    for t in a_tasks:
        format_values = t[1].format_values
        values = {
            "task_name":  format_values["build_name"],
            "task_hash":  format_values["build_hash"],
            "project":    format_values["project"],
            "created_by": format_values["actor"],
            "created_at":  format_values["created"],
            "started_at": format_values["started_build"]
        }
        tasks["active"].append ( values )

    for t in p_tasks:
        format_values = t.format_values
        values = {
            "task_name": format_values[ "build_name" ],
            "task_hash": format_values[ "build_hash" ],
            "project": format_values[ "project" ],
            "created_by": format_values[ "actor" ],
            "created_at": format_values[ "created" ]
        }
        tasks[ "pending" ].append( values )

    threading.Thread( target=common.create_json_file, args=( "./data/tasks.json", tasks ) ).start()
    _print( "Building Queue File Compleat" )


def cancel_task( q_item ):

    if q_item.build_hash is None:
        _print( "unable to cancel task. No build hash supplied" )
        return False

    # search pending tasks.
    for i in range(len(pending_tasks)):
        if pending_tasks[i].format_values["build_hash"] == q_item.build_hash:
            pending_tasks.pop(i)
            return True

    # search active tasks.
    for i in range(len(active_tasks)):
        if active_tasks[i][0].format_values["build_hash"] == q_item.build_hash:
            _print("Can not stop active task atm :( ")
            return False


def task_worker(job):

    _print("Starting new task")
    if SKIP_TASK_EXECUTION:
        time.sleep( SKIP_TASK_DELAY )   # simulate build
        job.append_build_info()         # updating build list
    else:
        job.execute()

    _print("job "+job.format_values["build_hash"]+" complete")

    # insert a TASK FINISHED message into the task que to unblock
    # so we can safely update the web_interface without any threading issues
    # it also makes sure that the task is removed from the active task list.
    task_queue.put( queue_item.QueueItem( job.format_values["actor"], job.format_values["project"],
                                          "Task-Finished", build_hash=job.format_values["build_index"] ) )


if __name__ == "__main__":

    thr_lock_tasks = threading.Lock()
    alive = True
    update_queue_file = False

    DEBUG.LOGS.init()
    _print = DEBUG.LOGS.print

    task_queue = queue.Queue()

    # setup queue items
    queue_item.QueueItem.add_action("build_finished", lambda q_item: True )   # queue unblocking task
    queue_item.QueueItem.add_action("cancel_task", cancel_task )

    # Sharded queue, shares the task queue in a controlled manner
    # Only exposing the Queue objects available to the module the
    # queue is shared with.
    sharded_queue = sharedQueue.SharedQueue( task_queue )
    # add all available actions in the shared queue
    sharded_queue.set_action( "build",       lambda uac, project, build_hash: build_task.BuildTask(uac, project, build_hash) )
    sharded_queue.set_action( "cancel_task", lambda uac, project, build_hash, complete_callback=None: queue_item.QueueItem(uac, project, "cancel_task", build_hash=build_hash, complete_callback=complete_callback) )

    # assign the shared queue with only the required objects to the modules
    webhook.Webhook.shared_task_queue = sharded_queue.clone( ["build"] )
    web_interface.WebInterface.shared_task_queue = sharded_queue.clone( ["build", "cancel_task"] )

    # build tasks
    max_running_tasks = 1
    pending_tasks = [] # build task object
    active_tasks = []  # tuple (thread, build task object)

    # start up the www
    webhook_thread = threading.Thread( target=web_hook )
    web_interface_thread = threading.Thread( target=www_interface )

    webhook_thread.start()
    web_interface_thread.start()

    # Initialize
    _print("Initializing, Hold tight...")

    # create an instance of user manager to create user files if not already setup.
    user_manager.UserManager()  # make sure this is last. so the test account details are not berried in the log

    _print("Initializing, Complete!")
    _print("Starting...")

    while alive:

        # wait for a task to come in while theres no pending
        task = task_queue.get(block=True, timeout=None)
        _print( "Task de queued :)" )

        # wait to start pending task,  collecting new task as they are submitted
        while task is not None or len(pending_tasks) > 0 and task_queue.empty():
            if task is not None:
                if isinstance( task, build_task.BuildTask ):
                    pending_tasks.append( task )
                    update_queue_file = True
                    _print("task_pending (total: {pending}) ".format( pending=len(pending_tasks) ) )
                elif isinstance( task, queue_item.QueueItem ):
                    task.execute()
                    update_queue_file = True
                else:
                    _print("invalid task")
                task = None
            # find if there is any available resources to launch the task
            # - clean up old task
            for i in range(len(active_tasks)-1, -1, -1):
                if not active_tasks[i][0].is_alive():
                    active_tasks.pop(i)
                    update_queue_file = True
                    _print("complete task removed ({active_tasks}/{max_task})".format(active_tasks=len(active_tasks), max_task=max_running_tasks))
            # - start new tasks
            while len(active_tasks) < max_running_tasks and len(pending_tasks) > 0:
                start_task = pending_tasks.pop(0)
                worker = threading.Thread( target=task_worker, args=(start_task,) )
                worker.start()
                active_tasks.append( (worker, start_task) )
                update_queue_file = True
                _print( "Active task {active_tasks} of {max_tasks} | current pending {pending}".format(active_tasks=len(active_tasks),
                                                                                                       max_tasks=max_running_tasks,
                                                                                                       pending=len(pending_tasks) ))
                start_task = None

            if update_queue_file:   # this could be threaded, if we copy the list
                update_queue_info( active_tasks, pending_tasks )
                update_queue_file = False

            # time for a nap
            time.sleep(1)

    #alive = False
    DEBUG.LOGS.close()

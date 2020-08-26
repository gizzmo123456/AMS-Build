#!/usr/bin/env python3
import DEBUG
import config_loader    # Loads in all config file.
import config_manager
import build_task
import webhook
import web_interface
import threading
import time
from http.server import HTTPServer
from baseHTTPServer import ThreadHTTPServer
import ssl
import queue
import sharedQueue
import queue_item
import common
import user_manager
import out_webhook

SKIP_TASK_EXECUTION = True      # if Runs the task without executing the container
SKIP_TASK_DELAY = 15            # if task execution is skipped how long to halt the worker, to emulate execution
SKIP_TASK_INTERVALS = 15        # how many times should we check if the tasks state has changed, ie been cnaceled.
SKIP_TASK_CLEAN_UP = True

def web_hook( ip, port, ssl_socket ):
    """
    :param ip:              host ip (string)
    :param port:            host port (int)
    :param ssl_socket:      ssl_socket (SSLContext)
    """

    # Use the single thread HTTPServer for the web hook,
    # we only want to handle a single connection at a time
    # to ensure that the request are executed in order :)
    wh_server = HTTPServer( (ip, port), webhook.Webhook )
    redirect_thread = None

    if ssl_socket is not None:
        wh_server.socket = ssl_socket( wh_server.socket, server_side=True )

    while alive:
        wh_server.serve_forever()

    if redirect_thread is not None and redirect_thread.is_alive():
        redirect_thread.join()

    wh_server.server_close()

def www_interface( ip, port, ssl_socket ):
    """
    :param ip:              host ip (string)
    :param port:            host port (int)
    :param ssl_socket:      ssl_socket (SSLContext) or None if not using ssl
    """

    # Use the threaded HTTPServer for the web interface,
    # so we're not handing around while files are downloaded
    # and pre-sockets are opened
    wi_server = ThreadHTTPServer( (ip, port), web_interface.WebInterface )
    redirect_thread = None

    if ssl_socket is not None:
        wi_server.socket = ssl_socket( wi_server.socket, server_side=True )

    while alive:
        wi_server.serve_forever()

    if redirect_thread is not None and redirect_thread.is_alive():
        redirect_thread.join()

    wi_server.server_close()

def create_ssl_socket_wrapper(cert_filepath, key_filepath, ca_bundle_filepath):
    """ creates an ssl socket

    :param cert_filepath:           file path to certificate
    :param key_filepath:            file path to private key
    :param ca_bundle_filepath:      file path to ca bundle
    :return: warp_socket function to be applied to the HTTP Server.
    """

    ssl_socket = ssl.SSLContext( ssl.PROTOCOL_TLS_SERVER )
    ssl_socket.load_cert_chain( certfile=cert_filepath, keyfile=key_filepath )
    ssl_socket.load_verify_locations( ca_bundle_filepath )

    return ssl_socket.wrap_socket


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
            # remove job from pending tasks list to prevent it progressing onto active
            canceled_job = pending_tasks.pop(i)
            threading.Thread( target=cancel_worker, args=(canceled_job,) ).start()
            return True

    # search active tasks.
    for i in range(len(active_tasks)):
        if active_tasks[i][1].format_values["build_hash"] == q_item.build_hash:
            # leave the task in the active task list,
            # as it will be remove once the container closes and the job worker exits
            # making sure that no other task is launched while its still running.
            canceled_job = active_tasks[ i ]
            threading.Thread( target=cancel_worker, args=(canceled_job[1],) ).start()
            return True

    return False

def cancel_worker(job):
    _print("Canceling task for ", job.format_values["project"] )
    job.cancel()
    _print("Task Canceled")

def task_worker(job):

    _print("Starting new task")
    if SKIP_TASK_EXECUTION:
        _print( "Simulating task task" )
        job.build_status = job.BUILD_STATUS_DUMMY
        slept_time = 0
        interval = SKIP_TASK_DELAY / SKIP_TASK_INTERVALS
        while slept_time < SKIP_TASK_DELAY and job.build_status != job.BUILD_STATUS_CANCEL:
            time.sleep( interval )                       # simulate build
            slept_time += interval

        if job.build_status != job.BUILD_STATUS_CANCEL:         # if its canceled the cancel method will clean up for us.
            if SKIP_TASK_CLEAN_UP:
                job.cleanup()                                   # Clean up the job
            job.append_build_info()                             # updating build list
            out_webhook.handle_outbound_webhook( job.uac, job.format_values[ "project" ], out_webhook.OWHT_BUILD_COMPLETE, job.format_values )  # The task complete does not have the build info when in simulate mode

    else:
        job.execute()

    _print("job "+job.format_values["build_hash"]+" complete")

    # insert a TASK FINISHED message into the task que to unblock
    # so we can safely update the web_interface without any threading issues
    # it also makes sure that the task is removed from the active task list.
    task_queue.put( queue_item.QueueItem( job.uac, job.format_values["project"],
                                          "build_finished", build_hash=job.format_values["build_index"] ) )


if __name__ == "__main__":

    # Set up Debug
    DEBUG.LOGS.init()
    _print = DEBUG.LOGS.print

    # make sure that the install script as been run.
    if not common.installed():
        _print("I would appear that AMS-Build has not been setup", message_type=DEBUG.LOGS.MSG_TYPE_ERROR)
        _print("When your ready please run '../ams-build-setup.sh', Exiting...")
        time.sleep( 1 )  # prevent debug from stopping before all message have been printed.
        DEBUG.LOGS.close()
        exit()

    # Load Config files.
    config = config_manager.ConfigManager

    thr_lock_tasks = threading.Lock()
    alive = True
    update_queue_file = False

    task_queue = queue.Queue()

    # setup queue items
    # All Queue items action (execution) callback functions must container exactly one param, q_item.
    queue_item.QueueItem.add_action("build_finished", lambda q_item: True )   # queue unblocking task
    queue_item.QueueItem.add_action("cancel_task", cancel_task )

    # Sharded queue, shares the task queue in a controlled manner
    # Only exposing the Queue objects available to the module the
    # queue is shared with.
    sharded_queue = sharedQueue.SharedQueue( task_queue )

    # add all available actions in the shared queue
    # Sharded queue actions, must return a constructed instance of either a BuildTask or QueueItem.
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
    webhook_ssl_socket_wrapper = None
    web_interface_ssl_socket_wrapper = None

    # set up ssl (if used)
    if config.get("use_ssl", False):
        ssl_conf = config.get("ssl")
        try:
            webhook_ssl_socket_wrapper = create_ssl_socket_wrapper(       ssl_conf["cert_file"], ssl_conf["private_file"], ssl_conf["ca_bundle_file"] )  # Never redirect webhooks.
            web_interface_ssl_socket_wrapper = create_ssl_socket_wrapper( ssl_conf["cert_file"], ssl_conf["private_file"], ssl_conf["ca_bundle_file"] )
        except Exception as e:
            _print("Failed to Create SSL Sockets", message_type=DEBUG.LOGS.MSG_TYPE_FATAL)
            _print(e, message_type=DEBUG.LOGS.MSG_TYPE_FATAL)
            _print("Please Fix web config file.", "Failed to Start.", "Exiting", message_type=DEBUG.LOGS.MSG_TYPE_FATAL, sept="\n")
            time.sleep(1)   # prevent debug from stopping before all message have been printed.
            DEBUG.LOGS.close()
            exit()

    webhook_thread = threading.Thread(       target=web_hook,      args=( config.get( "webhook_ip"      , "0.0.0.0" ),
                                                                          config.get( "webhook_port",       8081 ),
                                                                          webhook_ssl_socket_wrapper ) )
    web_interface_thread = threading.Thread( target=www_interface, args=( config.get( "web_interface_ip", "0.0.0.0" ),
                                                                          config.get( "web_interface_port", 8080 ),
                                                                          web_interface_ssl_socket_wrapper ) )

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

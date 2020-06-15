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

if __name__ == "__main__":

    alive = True

    DEBUG.LOGS.init()
    DEBUG.LOGS.set_log_to_file( message=True, warning=True, error=True, fatal=True )

    task_queue = queue.Queue()

    webhook.Webhook.task_queue = task_queue

    webhook_thread = threading.Thread( target=web_hook, args=() )
    webhook_thread.start()

    while alive:

        task = task_queue.get(block=True, timeout=None)

        if isinstance( task, build_task.BuildTask ):
            # task.execute()
            print("Task de queued :)")
            pass

    #alive = False
    DEBUG.LOGS.close()

#!/usr/bin/env python3

import DEBUG
import build_task
import common
import threading

if __name__ == "__main__":

    DEBUG.LOGS.init()
    DEBUG.LOGS.set_log_to_file( message=True, warning=True, error=True, fatal=True )

    task = build_task.BuildTask("exampleProject", "master")
    #task.execute()

    DEBUG.LOGS.close()

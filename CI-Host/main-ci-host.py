#!/usr/bin/env python3

import DEBUG
import build_task
import common
import threading

if __name__ == "__main__":

    DEBUG = DEBUG.LOGS().init()

    task = build_task.BuildTask("exampleProject", "master")
    task.execute()

    DEBUG.LOGS().close()

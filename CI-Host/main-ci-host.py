#!/usr/bin/env python3

import build_task
import common
import threading

if __name__ == "__main__":

   task = build_task.BuildTask("exampleProject", "master")
   task.execute()

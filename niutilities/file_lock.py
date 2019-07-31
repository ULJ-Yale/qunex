from __future__ import print_function

import os
import time

def lock(filename, delay=1, identifier="Python process"):
    lock_file = filename + ".lock"

    # wait while file exists
    while True:
        if not os.path.isfile(lock_file):
            # create lock file
            f = open(lock_file, "w")
            f.write(identifier)
            f.close()
            break

        time.sleep(delay)


def lock_and_write(string, filename, delay=1):
    # lock
    lock(filename, delay=delay)

    # open file
    f = open(filename, "a")

    # write
    f.write(string)

    # close file
    f.close()

    # unlock
    unlock(filename)


def unlock(filename):
    lock_file = filename + ".lock"

    if os.path.isfile(lock_file):
        os.unlink(lock_file)

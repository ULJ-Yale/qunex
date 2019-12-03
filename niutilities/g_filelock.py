from __future__ import print_function

import os
import time
import atexit
import random

# create a lock file for a certain file
def lock(filename, delay=0.5, identifier="Python process"):
    lock_file = filename + ".lock"

    # wait while file exists
    locked = True
    while locked:
        time.sleep(delay)

        if not os.path.isfile(lock_file):
            # double check
            time.sleep(random.random() * delay)

            if not os.path.isfile(lock_file):
                # create lock file
                f = open(lock_file, "w")
                f.write(identifier)
                f.close()

                # store lock file
                locks.append(lock_file)

                locked = False

# remove a lock file for a certain file
def unlock(filename):
    lock_file = filename + ".lock"

    if os.path.isfile(lock_file):
        try:
            os.unlink(lock_file)
        except:
            pass

    # remove from storage
    if lock_file in locks:
        locks.remove(lock_file)

# lock a file, write into it, then unlock it
def safe_write(string, filename, delay=1):
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

# delete all lock files on exit
def cleanup():
    for lock_file in locks:
        if os.path.isfile(lock_file):
            os.unlink(lock_file)

# lock storage
locks = []

# clenup on exit
atexit.register(cleanup)

#!/usr/bin/env python3.9
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``filelock.py``

A python filelocking library.
"""

from __future__ import print_function

import os
import shutil
import time
import atexit
import random

# create a lock file for a certain file
def lock(filename, delay=0.5, identifier="Python process"):
    lock_file = filename + ".lock"

    # wait while file exists
    while True:
        # create lock file
        try:
            f = os.open(lock_file, os.O_CREAT|os.O_EXCL|os.O_WRONLY)
            os.write(f, bytes(identifier))
            os.close(f)

            # store lock file
            locks.append(lock_file)

            break
        except:
            pass

        # try again soon
        time.sleep(delay + random.random() * delay)


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

    for status_file in statuses:
        status = open(status_file, 'r').read().strip()
        if 'done' not in status:
            os.unlink(status_file)


# open a locked status file
def open_status(filename, status=""):
    try:
        f = os.open(filename, os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        os.write(f, bytes(status))
        os.close(f)

        # store lock file
        statuses.append(filename)

        return None

    except (OSError, IOError) as e:
        return e.strerror


# write to the status file
def write_status(filename, status="", mode="w"):
    try:
        open(filename, mode).write(status)
        return True
    except:
        return False


# wait for status to be done
def wait_status(filename, status, delay=0.5):
    
    while True:
        try:
            # check content
            content = open(filename, 'r').read()
            if status in content:
                return status

            # try again soon
            time.sleep(delay + random.random() * delay)

        except (OSError, IOError) as e:
            return e.strerror


# remove status file
def remove_status(filename):
    try:
        os.unlink(filename)
        return True
    except:
        return False


# ==================  Safe creation functions

# create folders
def makedirs(folder):
    try:
        os.makedirs(folder)
        return None
    except (OSError, IOError) as e:
        return e.strerror

# create hardlink
def link(source, target):
    try:
        os.link(source, target)
        return None
    except (OSError, IOError) as e:
        return e.strerror

# remove folders
def rmtree(folder):
    try:
        shutil.rmtree(folder)
        return None
    except (OSError, IOError) as e:
        return e.strerror

# remove file
def remove(filename):
    try:
        os.remove(filename)
        return None
    except (OSError, IOError) as e:
        return e.strerror


# lock storage
locks = []
statuses = []

# clenup on exit
atexit.register(cleanup)

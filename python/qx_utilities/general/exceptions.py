#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``exceptions.py``

Definition of exceptions used in gmri.
"""


class CommandError(Exception):
    """There was an error in calling the command."""

    def __init__(self, function=None, error=None, *hints):
        if function is None:
            function = "unknown function"
        if error is None:
            error = "unspecified"
        msg = "Error '%s' occurred in %s" % (error, function)
        super(CommandError, self).__init__(msg)
        self.function = function
        self.error    = error
        self.hints    = hints
        self.report   = (error,) + hints


class CommandFailed(Exception):
    """A command has failed to carry out fully."""

    def __init__(self, function=None, error=None, *hints):
        if function is None:
            function = "unknown function"
        if error is None:
            error = "unspecified"
        msg = "Error '%s' occurred in %s" % (error, function)
        super(CommandFailed, self).__init__(msg)
        self.function = function
        self.error    = error
        self.hints    = hints
        self.report   = (error,) + hints


class CommandNull(Exception):
    """A command has not produced any output."""

    def __init__(self, function=None, error=None, *hints):
        if function is None:
            function = "unknown function"
        if error is None:
            error = "unspecified"
        msg = "%s ended with %s" % (function, error)
        super(CommandNull, self).__init__(msg)
        self.function = function
        self.error    = error
        self.hints    = hints
        self.report   = (error,) + hints


class SpecFileSyntaxError(Exception):
    """There was an error when parsing qunex spec files

    spec files include
      - session file
      - batch file
      - parameter file
      - list file
    """

    def __init__(self, filename=None, error=None, *hints):
        if filename is None:
            filename = "unknown file"
        if error is None:
            error = "unspecified"
        msg = "Error '%s' occurred when parsing %s" % (error, filename)
        super(SpecFileSyntaxError, self).__init__(msg)
        self.filename = filename
        self.error    = error
        self.hints    = hints
        self.report   = (error,) + hints


def report_command_failed(comm, e):
    if e.function == comm:
        e_string = "\n---> ERROR in completing %s:\n     %s\n" % (comm, "\n     ".join(e.report))
    else:
        e_string = "\n---> ERROR in completing %s at %s:\n     %s\n" % (comm, e.function, "\n     ".join(e.report))
    return e_string


def report_command_error(comm, e):
    if e.function == comm:
        e_string = "\nERROR in running %s:\n%s" % (comm, "\n".join(e.report))
    else:
        e_string =  "\nERROR in running %s at %s:\n%s" % (comm, e.function, "\n".join(e.report))
    return e_string


def report_command_null(comm, e):
    if e.function == comm:
        e_string = "\nWhen running %s:\n%s" % (comm, "\n".join(e.report))
    else:
        e_string =  "\nWhen running %s at %s:\n%s" % (comm, e.function, "\n".join(e.report))
    return e_string


def report_syntax_error(comm, e):
    pass
    # if e.filename == comm:
    #     eString = "\nWhen running %s:\n%s" % (comm, "\n".join(e.report))
    # else:
    #     eString =  "\nWhen running %s at %s:\n%s" % (comm, e.function, "\n".join(e.report))
    # return eString
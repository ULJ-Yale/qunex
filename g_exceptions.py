#!/usr/bin/env python
# encoding: utf-8
"""
g_exceptions.py

Definition of exceptions used in gmri
"""


class CommandError(Exception):
    """There was an error in calling the command."""
    
    def __init__(self, function=None, error=None, *hints):
        if function is None:
            function = "unknown function"
        if error is None:
            error = "unspecified"
        msg = "Error '%s' occured in %s" % (error, function)
        super(CommandFailed, self).__init__(msg)
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
        msg = "Error '%s' occured in %s" % (error, function)
        super(CommandFailed, self).__init__(msg)
        self.function = function
        self.error    = error
        self.hints    = hints
        self.report   = (error,) + hints



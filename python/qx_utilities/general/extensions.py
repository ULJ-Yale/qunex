#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``extensions.py``

Loads the python modules an extension asks QuNex to import, and collects what
they declare.

A command is *not* declared here. An extension's function is a QuNex command
because its docstring carries a `.. qx_command:` block and
`qunex build_qx_registry` indexed it, exactly as a core command is. What this
file collects is everything an extension states explicitly: the parameters and
flags its commands take, the deprecations it honours, and the handful of other
lists and dictionaries `process.py` and `commands_support.py` read.
"""

import os
import os.path
import sys
import importlib
from inspect import signature, Parameter

from qx_extension_paths import extension_python_folders


module_names = []
modules      = {}

arglist = []


# -- process extensions
def load_extensions():
    for extensions_path in extension_python_folders():

        # -- append the extension python folder to the path. Done whether or
        #    not the extension has a qx_modules file: a command's registry
        #    path is dotted relative to this folder and nothing else ever
        #    adds it, so gating this on the file left an extension whose
        #    commands were listed and dispatched and then failed to import
        if extensions_path not in sys.path:
            sys.path.append(extensions_path)

        # -- read the module names. The file is optional and says which
        #    modules to import eagerly -- the ones declaring parameters,
        #    flags or deprecations -- not which modules hold commands
        modules_file = os.path.join(extensions_path, 'qx_modules')
        if not os.path.exists(modules_file):
            continue

        with open(modules_file, 'r') as f:
            for line in f:
                if (len(line.strip()) > 0) and (not line.strip().startswith('#')):
                    module_name = line.strip()
                    if os.path.isdir(os.path.join(extensions_path, module_name)):
                        sys.path.append(os.path.join(extensions_path, module_name))
                    try:
                        modules[module_name] = importlib.import_module(module_name)
                        module_names.append(module_name)
                    except Exception:
                        print(f"WARNING: There was an error when trying to import extension module: {extensions_path}/{module_name}!")


def compile_list(list_name):
    '''
    compile_list(list_name)

    Inspects all loaded extension modules for presence of the 'list_name' and
    returns a list compiled across all modules.
    '''
    extensions_list = []
    for module_name in module_names:
        if hasattr(modules[module_name], list_name):
            if type(getattr(modules[module_name], list_name)) is list:
                extensions_list += getattr(modules[module_name], list_name)

    return extensions_list


def compile_dict(dict_name):
    '''
    compile_dict(dict_name)

    Inspects all loaded extensions modules for presence of the 'dict_name' and
    returns a dictionary compiled across all modules.
    '''
    extensions_dict = {}
    for module_name in module_names:
        if hasattr(modules[module_name], dict_name):
            if type(getattr(modules[module_name], dict_name)) is dict:
                extensions_dict.update(getattr(modules[module_name], dict_name))

    return extensions_dict


def qx_process(command_type="parallel", short_name=None, long_name=None, description=None):
    '''
    qx_process(command_type="parallel", short_name=None, long_name=None, description=None)

    Declares the parameters of an extension's processing command.

    It does not register a command, and has not since the command registry
    arrived: a function is a QuNex command because its docstring carries a
    `.. qx_command:` block and `build_qx_registry` indexed it. What is left is
    the conversion of the decorated function's keyword arguments into `arglist`
    entries -- each parameter's default, and the way its value is read -- which
    is the same job a module level `arglist` does, and which the extension
    documentation now teaches directly.

    `command_type`, `short_name`, `long_name` and `description` are no longer
    read. They are still accepted so that an extension written against the
    older decorator imports rather than failing, and taking the whole module's
    declarations down with it.
    '''

    def inner_decorator(f):
        global arglist

        f_signature = signature(f)

        # check arguments
        if (not list(f_signature.parameters.keys())[0] == 'sinfo'):
            first_arg = list(f_signature.parameters.keys())[0]
            print(f"First argument of QuNex processing command must be 'sinfo', but got {first_arg}. Not declaring the parameters of {f.__name__}")
            return f
        if 'overwrite' not in f_signature.parameters:
            print(f'A QuNex extension function must have a keyword argument "overwrite". Not declaring the parameters of {f.__name__}')
            return f
        if 'thread' not in f_signature.parameters:
            print(f'A QuNex extension function must have a keyword argument "thread". Not declaring the parameters of {f.__name__}')
            return f

        # --- add options to arglist ---
        def _check_default(x):
            if x == Parameter.empty:
                return ""
            else:
                return x

        def _check_annotation(x):
            if x == Parameter.empty:
                return str
            else:
                return x

        # `options` is the merged options dictionary the command is handed, not
        # a parameter of its own. It was excluded where these entries used to be
        # read and not where they are written, which did not show while the
        # entries were being dropped for having four elements
        arglist += [
            [arg, _check_default(param.default), _check_annotation(param.annotation), ""]
            for arg, param in f_signature.parameters.items()
            if arg not in ['sinfo', 'options', 'overwrite', 'thread']
        ]

        return f

    return inner_decorator

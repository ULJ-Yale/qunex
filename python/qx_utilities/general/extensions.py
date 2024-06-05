#!/usr/bin/env python2.7
# encoding: utf-8

import os
import os.path
import sys
import importlib
from inspect import signature, Parameter


module_names = []
modules      = {}

commands = {}  # decorator `qx` puts simple commands in here, it is then read out in `general.commands` 
arglist = []
calist = []
lalist = []
malist = []
salist = []

# -- process extensions
def load_extensions():
    if "QXEXTENSIONSPY" in os.environ:
        #print('=> processing extensions')
        extensions_paths = [e.strip() for e in os.environ['QXEXTENSIONSPY'].split(':') if e]
        
        # -- loop through paths and check that we have qx_modules file
        for extensions_path in extensions_paths:
            if os.path.exists(os.path.join(extensions_path, 'qx_modules')):

                # -- append the module python folder to the path
                sys.path.append(extensions_path)

                # -- read the module names
                with open(os.path.join(extensions_path, 'qx_modules'), 'r') as f:
                    for line in f:
                        if (len(line.strip()) > 0) and (not line.strip().startswith('#')):
                            module_name = line.strip()
                            if os.path.isdir(os.path.join(extensions_path, module_name)):
                                sys.path.append(os.path.join(extensions_path, module_name))
                            try:
                                modules[module_name] = importlib.import_module(module_name)
                                module_names.append(module_name)
                            except:
                                print(f"WARNING: There was an error when trying to import extension module: {extensions_path}/{module_name}!")

        # -- load the modules
        # if module_names:
        #     for module_name in module_names:
        #         print(f'   ... importing module {module_name}')
        #         if os.path.isdir(os.path.join(extensions_path, module_name))
        #         modules[module_name] = importlib.import_module(module_name)


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
    # print(f'-> extensions_dict {dict_name}')
    # print(f'   -> modules {module_names}')
    for module_name in module_names:
        # print(f'... module {module_name}')
        if hasattr(modules[module_name], dict_name):
            # print(f'... dict {dict_name}')
            if type(getattr(modules[module_name], dict_name)) is dict:
                # print(f"... adding {getattr(modules[module_name], dict_name)}")
                extensions_dict.update(getattr(modules[module_name], dict_name))

    return extensions_dict


def qx(qx_cmd=None):
    def inner_decorator(f):
        nonlocal qx_cmd
        if qx_cmd is None:
            qx_cmd = f.__name__
        if qx_cmd not in commands:
            commands[qx_cmd] = {'com': f, 'args': list(signature(f).parameters.keys())}
        return f
    return inner_decorator


def qx_process(command_type="parallel", short_name=None, long_name=None, description=None):
    
    def inner_decorator(f):
        global arglist, calist, lalist, malist, salist
        nonlocal command_type, short_name, long_name, description
        
        f_signature = signature(f)
        
        # check arguments
        if (not list(f_signature.parameters.keys())[0] == 'sinfo'):
            first_arg = list(f_signature.parameters.keys())[0]
            print(f"First argument of QuNex processing command must be 'sinfo', but got {first_arg}. Not registering {f.__name__}")
            return f
        if not 'overwrite' in f_signature.parameters:
            print('A QuNex extension function must have a keyword argument "overwrite". Not registering {f.__name__}')
            return f
        if not 'thread' in f_signature.parameters:
            print('A QuNex extension function must have a keyword argument "thread". Not registering {f.__name__}')
            return f
        
        def f_decorated(sinfo, options, overwrite, thread):
            kwargs = {k: options[k] for k in f_signature.parameters if not k in ['sinfo', 'options', 'overwrite', 'thread']}
            return f(sinfo, options, overwrite=overwrite, thread=thread, **kwargs)
        
        f_decorated.__doc__ = f.__doc__
        
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
        
        arglist += [
            [arg, _check_default(param.default), _check_annotation(param.annotation), ""]
            for arg, param in f_signature.parameters.items()
            if not arg in ['sinfo', 'overwrite', 'thread']
        ]

        # --- add function to qunex command list ---
        if short_name is None:
            short_name = f.__name__
        if long_name is None:
            long_name = f.__name__
        if description is None:
            if f.__doc__ is not None:
                description = f.__doc__.splitlines()[0].strip()    
            else:
                description = ""
            
        dict(
            parallel=calist,
            single=salist,
            longitudinal=lalist,
            multisession=malist,
        )[command_type].append(
            [short_name, long_name, f_decorated, description]
        )   
        
        return f
    
    return inner_decorator

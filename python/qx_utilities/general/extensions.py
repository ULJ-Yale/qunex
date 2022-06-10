#!/usr/bin/env python2.7
# encoding: utf-8

import os
import os.path
import sys
import importlib

module_names = []
modules      = {}

# -- process extensions

if "QXEXTENSIONSPY" in os.environ:
    # print('=> processing extensions')
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
                            print(f"WARNING: There was an error when trying to import extension module:\n         {extensions_path}/{module_name}.\n         The module is not loaded and will not be available for use.")                        

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



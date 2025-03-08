#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``config.py``

Config related functions for 'run_qa' Quality Assurance. 
"""

"""
Created by Samuel Brege on 2024-04-19.
"""
import yaml
import general.exceptions as ge

#Valid datatypes for run_qa
valid_datatypes = ['raw_data', 'check_config']

"""
Config template/schema that is used to validate input, consisting of nesting dicts. Each parameter has it's own dict,
and parameters may/must have the follow keys with appropriate values:

default - Unused for types dict, Required otherwise.
    Default value for this parameter. If of type dict, this is not used.

accept_list - Unused for types dict, Required otherwise.
    Whether it will accept a list of values (so long as they are of the defined type) as input. However, it does not 
    require input to be a list.
    eg. 
        accept_list:True and type:[int], the input [1, 2, 3] is accepted.
        accept_list:True and type:[str], the input "T1w" is accepted.
        accept_list:False and type:[bool], the input [True, False] is NOT accepted.

only_valid - Required for types dict, unused otherwise.
    Whether sub-parameters (parameters key) for this parameter must be explicitly defined in the template to be accepted.
    eg.
        scan has only_valid:True, because all subparameters are explicitly used.
        json has only_valid:False, because sub-parameters are matched against the loaded file and not checked.

type - Required
    The expected type of the input. This is defined in a list, allowing multiple types to be specified, though this is 
    not currently used. When used with accept_list:True, it will ensure all values in the list are of correct type.

required - Required
    Whether or not the parameter must be specified in the config in order for the config to parse successfuly.

parameters - Required for types dict, unused otherwise.
    Sub-parameters for this parameter, defined as a dict of dicts. Each parameter must follow the previous guidelines.

ID - Required for type dict with accept_list:True, unused otherwise.
    Special parameter to allow parsing of .yaml sequences without overwriting. The value for this must be a key in the parsed
    dict, and the associated value will be used as the identifying key in the parsed config. Currently the only use-case is
    for parsing the individual scans, designed to work with 'series_description'.

description - Required.
    Description of the parameter, self-explanatory. Also printed to log when config parse fails.
"""
config_template = {"datatypes": {"default":None, "accept_list":False, "only_valid":True, "type":[dict], "required":True,
                "parameters":{
                    "raw_data": {"default":None, "accept_list":True, "only_valid":True, "type":[dict], "required":False,
                    "parameters":{
                        "scan":{"default":None, "accept_list":False, "only_valid":True, "type":[dict], "required":True, "ID":"series_description",
                        "parameters": {
                            "series_description":{"default":None, "accept_list":False, "type":[str], "required":True,
                            "description":"The actual scan name/description, found in the session.txt and the nifti .json"},
                            "required":{"default":True, "accept_list":False, "type":[bool], "required":False,
                            "description":"Whether this scan is required to be present for it to pass"},
                            "dicoms":{"default":None, "accept_list":True, "type":[int], "required":False,
                            "description":"Whether this scan is required to be present for it to pass"},
                            "session":{"default":None, "accept_list":False, "only_valid":True, "type":[dict], "required":False,
                            "parameters":{
                                "scan_index":{"default":None, "accept_list":True, "type":[int], "required":False,
                                "description":"If multiple scans have the same series description, you can specify the index to map (starting from 0)"},
                                "image_count":{"default":None, "accept_list":False, "type":[int], "required":False,
                                "description":"Number of expected scans with this series_description"},
                                "image_number":{"default":None, "accept_list":True, "type":[int], "required":False,
                                "description":"Specify a specific scan using the image number"},
                                "acquisition":{"default":[0], "accept_list":True, "type":[int], "required":False,
                                "description":"The acquisition number for this scan, if not split int"}
                            },
                            "description":"Parameters related to the session.txt file"},
                            "json":{"default":None, "accept_list":False, "only_valid":False, "type":[dict], "required":False,
                            "parameters":{
                                "normalized":{"default":None, "accept_list":True, "type":[bool], "required":False,
                                "description":"Is the scan normalized (ImageType)"},
                            },
                            "description":".json parameters, usually key/value pairs found in the nifti sidecar .json files"
                            },
                            "nifti":{"default":None, "accept_list":False, "only_valid":False, "type":[dict], "required":False,
                            "parameters":{
                                "data_shape":{"default":None, "accept_list":True, "type":[list,int], "required":False,
                                "description":"The shape of the nifti data as a list of ints"}
                            },
                            "description":"Nifti parameters, usually key/value pairs found in the .nifti file header"
                            }
                        },
                        "description":"Scan related parameters, used for mapping and validation. Requires the key series_description"},

                        "other":{"default":None, "accept_list":False, "only_valid":True, "type":[dict], "required":False, "ID":"file_name",
                        "parameters":{
                            "file_name":{"default":None, "accept_list":False, "type":[str], "required":True,
                            "description":"Path to the file for validation from the session's folder."},
                            "file_type":{"default":None, "accept_list":False, "type":[str], "required":False,
                            "description":"How to parse the file, default assumed from file extension. Useful if file has unusual extension (eg. QuNex movement files)."},
                            "deliminator":{"default":None, "accept_list":False, "type":[str], "required":False,
                            "description":"If using deliminated data (eg. .csv), default assumed from file extension. Useful for unusual files."},
                            "data_column":{"default":None, "accept_list":True, "type":[str], "required":False,
                            "description":"If using deliminated data (eg. .csv), you can define specific column(s) to validate. Otherwise will use all columns."},
                            "index_column":{"default":None, "accept_list":False, "type":[str], "required":False,
                            "description":"If using deliminated data (eg. .csv), define a column to use as the index, default is the line index."},
                            "required":{"default":True, "accept_list":False, "type":[bool], "required":False,
                            "description":"Whether this file is required to be present for it to pass"},
                            "values":{"default":None, "accept_list":False, "only_valid":False, "type":[dict], "required":False,
                            "parameters":{
                            },
                            "description":"Actual parameters to check in data, using rules defined under '- other'"
                            }
                            

                        },
                        "description":"Parameters for validation of user-defined files, highly customizable."
                        }  
                    },
                    "description":"run after import_datatype, it allows for QA and mapping validation"},
                    "config":{"default":None, "accept_list":False, "only_valid":False, "type":[dict], "required":False,
                    "parameters":{
                        "data_import":{"default":None, "accept_list":False, "type":[str], "required":False,
                        "description":"The type of the data before import, currently only accepts dicom"}
                    },
                    "description":"Misc config options for all datatypes, also allows for parsing of run_qa flags for all datatypes (eg. datatype, sessions)"
                    }}
                ,
                "description":"run_qa datatype parameters"}
            }

def print_template():
    """
    Print template dict in a human readable format.
    """
    
    #This is similar information to the doc above, but with dev related info removed
    out="Config key descriptions:\n"\
        "Input is validated against a template, consisting of nesting dicts. Each parameter has the follow keys:\n"\
        "\n"\
        "default\n"\
        "    Default value for this parameter. If of type dict, this is not used.\n"\
        "\n"\
        "accept_list\n"\
        "    Whether it will accept a list of values (so long as they are of the defined type) as input. However, it does not \n"\
        "    require input to be a list.\n"\
        "    eg. \n"\
        "        accept_list:True and type:[int], the input [1, 2, 3] is accepted.\n"\
        "        accept_list:True and type:[str], the input 'T1w' is accepted.\n"\
        "        accept_list:False and type:[bool], the input [True, False] is NOT accepted.\n"\
        "\n"\
        "only_valid\n"\
        "    Whether sub-parameters (parameters key) for this parameter must be explicitly defined in the template to be accepted.\n"\
        "    eg.\n"\
        "        scan has only_valid:True, because all sub-parameters are explicitly used.\n"\
        "        json has only_valid:False, because sub-parameters are matched against the loaded file and not checked.\n"\
        "\n"\
        "type\n"\
        "    The expected type of the input. This is defined in a list, allowing multiple types to be specified, though this is \n"\
        "    not currently used. When used with accept_list:True, it will ensure all values in the list are of correct type.\n"\
        "\n"\
        "required\n"\
        "    Whether or not the parameter must be specified in the config in order for the config to parse successfuly.\n"\
        "\n"\
        "parameters\n"\
        "    Sub-parameters for this parameter, defined as a dict of dicts. Each parameter must follow the previous guidelines.\n"\
        "\n"\
        "ID\n"\
        "    Special parameter to allow parsing of .yaml sequences without overwriting. The value for this must be a key in the parsed\n"\
        "    dict, and the associated value will be used as the identifying key in the parsed config. Currently the only use-case is\n"\
        "    for parsing the individual scans, designed to work with 'series_description'.\n"\
        "\n"\
        "description\n"\
        "    Description of the parameter, self-explanatory. Also printed to log when config parse fails.\n\n"\
        "Template Config Parameters:\n"
    
    def rec_print(template, padding):
        """
        Recursively prints out the template in a more readable format than pprint
        """
        out = ""
        if 'description' in template.keys():
            out += f"{padding}description: {template['description']}\n"
        for key in template.keys():
            if isinstance(template[key], dict):

                if key == 'parameters':
                    out += f"{padding}Sub-parameters:\n"
                else:
                    out += f"\n{padding}- {key}\n"
                out += rec_print(template[key], padding + "   ")
            else:
                if key != 'description':
                    out += f"{padding}{key}: {template[key]}\n"

        return out
    
    out += rec_print(config_template, "")
    print(out)
    return

def parse_config(config_file):
    """
    Parses a .yaml config file for QA by checking it against a defined template.
    Outputs a nested dict.
    """
    if config_file == None:
        print("No config yaml file supplied, skipping parse...")
        return None

    print(f"\nParsing configfile {config_file}.")

    print("Config will be parsed with the following template:\n")

    print_template()

    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    parsed_config = {}
    parsed_config = recursive_parse('datatypes', config_template['datatypes'], config['datatypes'])

    return parsed_config

def recursive_parse(name, template, config):
    """
    Helper function for parse_config, allows for the parsing of nested dicts.
    """
    p_config = {}
    #if defined in template as dict of lists (yaml sequence) of dictionaries then must be parsed differently
    if template['type'][0] == dict and template['accept_list'] == True:
        for param in config:
            param_name = list(param.keys())[0]
            list_dict = recursive_parse(param_name, template['parameters'][param_name], param[param_name])
            #If yaml sequence has an ID defined in template, then it is assigned and appended to that id value
            #allows for multiple in the same yaml sequence to be assigned to different values in the parsed dict
            if 'ID' in template['parameters'][param_name].keys():
                id_name = template['parameters'][param_name]['ID']
                try:
                    param_id = list_dict[id_name]
                except:
                    raise ge.CommandError(
                        "run_qa",
                        f"Missing required ID parameter {id_name} for {name}!\nKey Description: {template['description']}",
                        f"Supplied parameter has incorrect type."
                    )
                #ensure all lists have the same length, if so add that length
                num_items = check_lengths(list_dict)
                list_dict['n_items'] = num_items
                list_dict = set_lengths(list_dict, num_items)
                #if the original sequence value (param_name) has not yet been parsed
                if param_name not in p_config.keys():
                    p_config[param_name] = {}
                p_config[param_name][param_id] = list_dict

            #If it does not have an id, will always overwrite. No use-case for now
            else:
                p_config[param_name] = list_dict
    #if defined as a dict it will repeat
    elif template['type'][0] == dict:
        for param_name in config.keys():
            #undefined parameters
            if param_name not in template['parameters'].keys():
                if template['only_valid']:
                    raise ge.CommandError(
                        "run_qa",
                        f"Supplied parameter {param_name} invalid! \nValid parameters are: {list(template['parameters'].keys())}\nKey Description: {template['description']}",
                        f"Supplied parameter invalid."
                    )
                else:
                    #directly assigned because these lack a template to validate against
                    if not isinstance(config[param_name], list):
                        p_config[param_name] = [config[param_name]]
                    else:
                        p_config[param_name] = config[param_name]
            #defined parameters
            else:
                p_config[param_name] = recursive_parse(param_name, template['parameters'][param_name], config[param_name])

    #if not a dict or a list, check type and return the value
    #allows for multiple types to be specified, so long as param is of one valid type it will be accepted
    else:
        #check types are valid
        bad_val, error = check_type(config, template['type'], template['accept_list'])
        if bad_val != None:
            raise ge.CommandError(
                "run_qa",
                f"Parameter {name}: {bad_val} parse error. {error}\nKey Description: {template['description']}",
                f"Incorrect parameter type"
            )
        if template['accept_list']:
            if type(config) != list:
                config = [config]
            elif template['type'][0] == list:
                #if a list is nested, all elements must be lists with same length
                #if not nested, make it nested
                if not check_nested(config):
                    config = [config]

        return config
    
    #keys in template that haven't been parsed
    remaining_keys = set(template['parameters'].keys()).difference(set(p_config.keys()))
    for r_key in remaining_keys:
        if template['parameters'][r_key]['required']:
            raise ge.CommandError(
                "run_qa",
                f"Missing required parameter {r_key}!\nKey Description: {template['parameters'][r_key]['description']}",
                f"Missing required parameter in config."
            )
        else:
            if template['parameters'][r_key]['type'][0] == dict:
                p_config[r_key] = recursive_parse(r_key, template['parameters'][r_key], {})
            else:
                p_config[r_key] = template['parameters'][r_key]['default']
    return p_config

def check_lengths(dictionary):
    """
    Helper function for parsing config. Ensures all lists inside a dict (and all sub dicts)
    have the same length, will error otherwise. Returns the length.
    """
    length = None
    for key, value in dictionary.items():
        if isinstance(value, dict) and len(value.keys()) > 0:
            dict_length = check_lengths(value)
            if dict_length > 1:
                if length is None:
                    length = dict_length
                elif dict_length != length:
                    raise ge.CommandError(
                        "run_qa",
                        f"Invalid config {key}:{value}. If using lists to specify values, all lists for a scan must have the same length!",
                        f"Inconsistent list length."
                    )
        elif isinstance(value, list):
            if len(value) > 1:
                if length is None:
                    length = len(value)
                elif len(value) != length:
                    raise ge.CommandError(
                        "run_qa",
                        f"Invalid config {key}:{value}. If using lists to specify values, all lists for a scan must have the same length!",
                        f"Inconsistent list length."
                    )
    if length == None:
        return 1
    #These values cannot be 1 if length is greater than 1
    length_keys = ['image_number']
    for key in length_keys:
        if key in dictionary.keys():
            if dictionary[key] != None and len(dictionary[key]) != length:
                raise ge.CommandError(
                        "run_qa",
                        f"Invalid config {key}:{dictionary[key]}. This value must have the same number of elements as other defined lists",
                        f"Inconsistent list length."
                    )
    return length

#Once list lengths are checked, set them to length n_items
def set_lengths(dictionary, n_items):
    """
    Helper function for parsing config, sets all lists in the structure to n_items. Used after check_lengths.
    """
    for key, value in dictionary.items():
        if isinstance(value, dict) and len(value.keys()) > 0:
            dictionary[key] = set_lengths(value, n_items)

        elif isinstance(value, list) and len(value) == 1:
            dictionary[key] = value * n_items

    return dictionary

def check_type(value, type_list, accept_list):
    """
    Helper function for parsing config, checks wether param type matches accepted type
    """

    bad_val = None
    error = None
 
    #If data is meant to be a list for each scan (eg. data_shape)
    if type_list[0] == list:
        if type(value) == list:
                for val in value:
                    bad_val, error = check_type(val, type_list[1:], accept_list)
                    if bad_val != None:
                        return bad_val, error
        else:
            return value, "Param value must be a list!"
        
    else:
        if type(value) == list:
            if accept_list:
                for val in value:
                    bad_val, error = check_type(val, type_list, False)
                    if bad_val != None:
                        return bad_val, error

            else:
                return value, "Param value cannot be a list!"
        else:
            if type(value) != type_list[0]:
                return value, f"Param value must be {str(type_list[0])}!"
            
    return bad_val, error

def check_nested(val_list):
    """
    Helper function for config, takes in a list and checks whether it is nested (contains lists)
    If so, ensures all values are lists with the same length, recurses on all contained lists.
    """
    is_nested = False
    length = None
    for val in val_list:
        if type(val) == list:
            is_nested = True
            if length == None:
                length = len(val)
            elif length != len(val):
                pass #FAIL
            check_nested(val)
        elif is_nested:
            pass #FAIL

    return is_nested
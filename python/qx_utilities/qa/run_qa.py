#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``run_qa.py``

Wrapper functions for Quality Assurance, run under the main function 'run_qa'. 
"""

"""
Created by Samuel Brege on 2024-03-19.
"""

import os
import yaml
import numpy as np
import general.exceptions as ge
import general.core as gc
import general.filelock as fl
import general.parser as parser
import qa.core as qa
import qa.config as config
import pprint

def run_qa(
    datatype=None,
    sessionsfolder=".",
    sessions=None,
    configfile=None,
    tag=None,
    overwrite="no"
    ):

    """
    ``run_qa [datatype=None] [sessionsfolder=.] [sessions=None] [configfile=None] [tag=None] [overwrite=no]``

    Runs Quality Assurance on a QuNex study, based off data-type and a user-defined config.

    Parameters:
        --datatype (str):
            The type of data to be run through QA. Currently only supports 'raw_data'.

        --sessionsfolder (str):
            The location of the <study>/sessions folder.

        --sessions (str, default None):
            If provided, only the specified sessions from the sessions folder
            will be processed. They are to be specified as a pipe or comma
            separated list, grob patterns are valid session specifiers. This
            parameter also accepts session .list files.

        --configfile (str, default None):
            The location of a .yaml file providing instructions and key-value 
            pairs for QA to verify. If left blank, minimal QA will be run.

        --tag (str, default None):
            Optional tag to add to output files, useful for preventing overwrite.
            If left blank, the name of the configfile will be used.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

    Notes:
        This command will generate four files. These consist of 2 sessions .list 
        files (pass and fail sessions lists), a report .txt file, and a more detailed 
        report .yaml file. List files will go in processing/lists, reports in 
        processing/reports (a new directory for QA reports).

        The .list files are QuNex compatible, they can be used as input into any 
        datatype using the ``--sessions`` flag, as well as with ``qunex_container``. They 
        are in format ``session id: <id>``, and contain no extra info. Intended use is 
        that the ``passQA`` sessions list will be used as input for futher QuNex datatypes, 
        and ``failQA`` sessions lists will be manually gone over and investigated.

        The .txt report file provides further information for the ``failQA`` sessions list, 
        including what caused the session to fail, why it failed, as well as recommended 
        action.

        The data type:
            
            ``--dataype=raw_data``

            Raw Data QA checks whether found scans are in-line with the scan Protocol, 
            defined by the user in the supplied config. Run after the import datatype, 
            this does various checks to ensure data is valid before processing. The main 
            goal is to identify problematic sessions before you start processing, saving 
            time and resources. It should also prevent users from needing to manually 
            check each session_hcp.txt file for correct mapping, as raw_data will 
            identify missing/misordered scans.

            ``--dataype=check_config``

            Config QA checks if the user-created config can be parsed by run_qa, without
            running QA on any actual data. This can be used to ensure the config is valid
            and visualize how it is parsed before running actual QA.

        The config file:

            In addition to basic checks (such as whether specified session folders exist 
            and have the correct paths), run_qa can do extensive QA through the use of a 
            user created config .yaml file, which can vary from simple to complex.

            Here is a basic config for one scan for 'raw_data' QA:

            ::

                datatypes:
                    raw_data:
                        - scan:
                            series_description: T1w_MPR
                            mapping_name: T1w 
                            dicoms: 208
                            json: 
                                normalized: True 

            This means that run_qa will ensure every sessions has an image with 
            series_description T1w_MPR, 208 dicoms, and is normalized.
            
            It can also be more complicated:

            ::

                        - scan:
                            series_description: T2w|T2w run-*
                            mapping_name: T2w
                            session:
                                image_count: 2
                            nifti:
                                data_shape: (208, 300, 320)
                            json:
                                RepetitionTime: [3.2, 3.3]
                                EchoTime: 0.564
                                normalized: [True, False]

            In series_description, pipes '|' can be used to define multiple valid strings,
            and also accepts unix-style pattern matching (eg. wildcard '*'). There are 
            multiple subcategories (session, nifti, and json) depending on the data source. 
            If there are multiple files with the same description, the QA will adapt. 
            For example, if you specify ``image_count: 2``, it will expect 2 images to match 
            the series_description, and ensure at least 1 matches the parameters. Parameters 
            can also be specified as lists (eg. ``normalized: [True, False]``), so if you expect 
            these images to have different values for certain parameters, you can specifiy that. 
            Or, if you expect the values to be identical, you leave it just as one value 
            (eg. ``EchoTime: 0.564``). Position does matter, so in this above case the normalized 
            scan should have an RT of 3.2, and the non-normalized scan should have an RT of 3.3.

            Scans are defined as a .yaml sequence, so when specifying multiple scans, you 
            simply add another ``- scan:`` block below it:

            ::

                        - scan:
                            series_description: sbref rest run-*
                            mapping_name: boldref1:rest
                            session:
                                image_count: 4
                            nifti:
                                data_shape: (90, 90, 60)
                            json:
                                RepetitionTime: 0.9
                                EchoTime: 0.035
                                PhaseEncodingDirection: [j-, j, j-, j]

                        - scan:
                            series_description: bold rest run-*
                            mapping_name: bold1:rest
                            session:
                                image_count: 4
                            nifti:
                                data_shape: (90, 90, 60, 333)
                            json:
                                RepetitionTime: 0.9
                                EchoTime: 0.035
                                PhaseEncodingDirection: [j-, j, j-, j]

            Here is a list of all possible parameters:

            ::

                datatypes: #Contains run_qa datatypes, currently only raw_data is compatible.
                    raw_data: #Contains params for each scan to run raw_data.
                        - scan: #Multiple can be specified, so long as the series_description is different.
                            series_description: #Name of the scan in the session.txt, accepts pipes for 'or', as well as unix pattern matching.
                            required: #Whether or not the scan is required to pass QA, default is True.
                            dicoms: #Number of dicom files for the scan, recquires dcm2nii logs to function.
                            session: #session.txt related parameters.
                                scan_index: #If multiple scans with the same description, this can be used to specify the relative index.
                                image_count: #If you expect a specific number of images to match the description.
                                image_number: #The scan's image number.
                            json: #Nifti sidecar .json files. Most keys here are directly compared to the .json file and can be anything.
                                normalized: #Whether or not the scan should be normalized.
                            nifti: #Compares keys to the nifti file headers. Similar to .json, any key can be defined so long as it is in the .nii file.
                                data_shape: Expected shape of the data, potential alternative to ``dicoms`` but more complex.
                    config: #Misc config options for raw_data.
                        data_type: #Currently, only dicom is accepted, used for ``dicoms`` parameter.

    """

    out_dir, tag = param_check(datatype, sessionsfolder, configfile, tag, overwrite)
    
    pass_out = f"{out_dir}/lists/QA_pass_{datatype}{tag}.list"
    fail_out = f"{out_dir}/lists/QA_fail_{datatype}{tag}.list"
    report_out = f"{out_dir}/reports/QA_report_{datatype}{tag}.txt"
    yaml_out = f"{out_dir}/reports/QA_report_{datatype}{tag}.yml"

    outputs = [pass_out, fail_out, report_out, yaml_out]
    
    print("\nCreating QA instance...")
    qa_instance = qa.QA(sessions, sessionsfolder, configfile)
    
    print("\nQA instance created successfully! Parsed as:\n")
    pp = pprint.PrettyPrinter(indent=1)
    pp.pprint(qa_instance.config)
    print("\nPlease see above datastructure to see how config was parsed.\n")

    if qa_overwrite(outputs, overwrite):
        print("QA complete due to existing outputs. Change tag, check folders, or use --overwrite=yes to re-run")
        return 
    
    if datatype == 'check_config':
        return

    elif datatype == 'raw_data':
        qa_instance.QA_raw_data()

    create_list_file(qa_instance.slist, pass_out)
    create_list_file(qa_instance.failQA, fail_out)
    fl.safe_write(qa_instance.report, report_out)
    with open(yaml_out, 'w') as f:
        yaml.dump(slist2yaml(qa_instance.failQA), f)

    return

def param_check(datatype, sessionsfolder, configfile, tag, overwrite):
    """
    Helper function for run_qa. Ensures all input parameters are valid and formats specific parameters.
    """
    print("\n")
    print("Beginning parameter check for run_qa.")
    print(f"--datatype: {datatype}")
    print(f"--sessionsfolder: {sessionsfolder}")
    print(f"--configfile: {configfile}")
    print(f"--overwrite: {overwrite}")
    print("\n")

    if datatype not in config.valid_datatypes:
        raise ge.CommandError(
            "run_qa",
            f"Invalid or None datatype provided, check your inputs! Ran with --datatype={datatype}. "\
                f"Valid datatypes for run_qa: {list(config.valid_datatypes)}",
            "Use run_qa --help for more information.",
        )
    
    if sessionsfolder == '.':
        print("WARNING: --sessionsfolder left blank or '.', current directory will be treated as sessionsfolder.")
    else:
        if not os.path.exists(sessionsfolder):
            raise ge.CommandError(
                "run_qa",
                f"Specified sessions folder {sessionsfolder} does not exist! Please check your inputs."
            )
        else:
            print(f"Sessions folder {sessionsfolder} found.")
    
    if datatype == "raw_data":
        if configfile == None:
            print("WARNING: No config file set, only minimal QA will run")
        else:
            if not os.path.exists(configfile):
                raise ge.CommandError(
                    "run_qa",
                    f"Specified config file {configfile} does not exist! Please check your inputs."
            )

    out_dir = sessionsfolder + "/../processing"

    if not os.path.exists(out_dir):
        raise ge.CommandError(
                "run_qa",
                f"ERROR: Processing folder does not exist! Check your paths!"
        )
    
    if not os.path.exists(f'{out_dir}/lists'):
        os.makedirs(f'{out_dir}/lists')
    
    if not os.path.exists(f'{out_dir}/reports'):
        os.makedirs(f'{out_dir}/reports')
    
    if tag == None:
        print("No tag specified...")
        print("   Trying config file name...")
        if configfile != None:
            tag = '_' + os.path.basename(configfile).split('.')[0]
        else:
            print("   No configfile set, leaving tag empty.")
            tag = ""
    else:
        print(f"Tag set to {tag}.")
        tag = "_" + tag
    
    if overwrite.lower() == "no" or overwrite.lower() == "yes":
        print(f"Overwrite set to: {overwrite}.")
    else:
        raise ge.CommandError(
                "run_qa",
                f"Invalid overwrite supplied {overwrite}! --overwrite must be set as 'yes' or 'no'."
        )

    print("Parameter check complete!")
    return out_dir, tag

def qa_overwrite(outputs, overwrite):
    """
    Helper function for run_qa. Checks if output sessions list already exist and deletes if overwrite enabled.
    Returns whether QA should not continue.
    """
    print("Checking for existing QA outputs...")
    for out_file in outputs:
        if os.path.exists(out_file):
            if overwrite.lower() == 'yes':
                os.remove(out_file)
            else:
                return True
    return False

def create_list_file(sessions, outname):
    """
    Helper function for run_qa output. Formats and re-writes slist into a QuNex style sessions .list.
    """
    l = ""
    for session in sessions:
        l += f"session id: {session['id']}\n"
    fl.safe_write(l,outname)

def slist2yaml(slist):
    """
    Helper function for run_qa output. Converts slist into a more yaml friendly format.
    Mainly just converts numpy arrays to lists.
    """
    def rec(s):
        if isinstance(s, dict):
            for key in s.keys():
                s[key] = rec(s[key])
        elif isinstance(s, list):
            for i in range(len(s)):
                s[i] = rec(s[i])
        #extra data from numpy arrays unneccesary
        elif isinstance(s, np.ndarray):
            return s.tolist()
        return s
    
    yaml_slist = []

    for s in slist:
        yaml_slist.append({'session':rec(s)})

    return yaml_slist
#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``core.py``

Main internal functions for 'run_qa' Quality Assurance. 
"""

"""
Created by Samuel Brege on 2024-03-19.
"""

import os
import glob
import numpy as np
import nibabel as nib
import json
import general.core as gc
import general.parser as parser
import general.exceptions as ge
import qa.config as config
import re
from fnmatch import fnmatch
from difflib import SequenceMatcher

class QA:
    """
    QA class, stores functions and variables related to Quality Assurance, primarily used
    in the run_qa function.
    """
    def __init__(self, sessions=None, sessionsfolder='.', configfile=None):
        """
        init function for QA. Sets up internal attributes.

        Parameters:
        --sessions (str, default None)
            List of sessions to run through QA. If not supplied will run on all subfolders

        --sessionsfolder (str, default '.')
            Path to sessions folder

        --configfile (str, default None)
            Path to config.py style config .yaml file

        Notes:
            Session info attributes:
                slist
                    The 'working' list. Each element is a dict pertaining to a session. This dict contains
                    useful info and keys are shared across elements (eg. the 'id' key always refers to the session id).
                    This list contains sessions that have not yet QA, upon failure they are moved to 'failQA'. 
                    Built in the 'build_slist' function.

                failQA
                    List for sessions that have failed QA, follows same conventions as 'slist'. Dicts in this list must
                    additionally have the 'QA_fail/ (failure cause) and 'QA_action' (recommended action) keys. Generally
                    sessions are moved from 'slist' to 'failQA' in the 'fail' function.

            Other attributes:
                'sessionsfolder'
                    String, path to a QuNex style sessions folder

                'report'
                    String, contains human-readable info on sessions that have failed QA

                'config'
                    Dict, contains info on how to run QA based on datatype, parsed in 'config.py'
        """
        #set sessionsfolder to full path rather than local
        if sessionsfolder[0] != '/':
            sessionsfolder = os.path.join(os.getcwd(),sessionsfolder)
        self.sessionsfolder = sessionsfolder

        self.report = "=========================================="
        self.report += "\n              QA report"
        self.report += "\n=========================================="

        
        #List of dictionaries, basically QA slist. Stores sessions that haven't failed QA.
        self.slist = self.build_slist(sessions)
        #dicts in fail QA must have ID and reason/datatype they failed
        self.failQA = []

        self.config = config.parse_config(configfile)


        return

    def build_slist(self, sessions):
        """
        Creates an slist for use in QA. If sessions=None, will run on all subfolders in the sessionsfolder.
        If sessions is specified, uses 'get_sessions_list' function from 'general/core.py'. If sessions are
        specified but not defined as subfolders of sessionsfolder, they will fail QA.
        """
        #directories that may be found in a sessionsfolder but are not sessions
        #currently manually defined here but not ideal 
        non_sessions = ['specs','QC','inbox','archive']
        session_dirs = glob.glob(f"{self.sessionsfolder}/*/")
        #All sessions (None specified)
        if sessions == None:
            print(f"No sessions specified, running on all sessions found in {self.sessionsfolder}")
            slist = []
            #Filter out non-sessions and create an slist
            for session_dir in session_dirs:
                #directory name assumed to be sessionid
                session_id = session_dir.split("/")[-2]
                if session_id not in non_sessions:
                    slist.append({"id":session_id, "QA_sessionfolder":session_dir[:-1]})

        #Specific sessions
        else:
            slist,gpref =gc.get_sessions_list(sessions)
            #Iterating over a copy to allow removal from original list
            #Get only folders that are a specified session
            for s in slist.copy():
                for dn in session_dirs:
                    if s['id'] == dn.split("/")[-2]:
                        s['QA_sessionfolder'] = dn[:-1]
                
                #QA fail
                if 'QA_sessionfolder' not in s.keys():
                    print(f"WARNING: Session {s['id']} not found in {self.sessionsfolder}! Removing from --sessions...")
                    s['QA_sessionfolder'] = None
                    self.fail(s, "Session folder import", f"Session folder {s['id']} missing in {self.sessionsfolder}",
                              f"Check import_dicom log for this session. Are scans present in inbox folder?")
        return slist
    
    def fail(self, session, datatype, reason, action):
        """
        Handles sessions that have failed QA. Removes them from slist, adds diagnositc info, appends to failQA.

        --session (str)
            dict from slist for session that has failed QA
        
        --datatype (str)
            datatype which session failed to pass

        --reason (str)
            why the session failed

        --action (str)
            recommended action to fix problem
        """
        print(f"QA failed for session {session['id']} during datatype {datatype}")
        self.slist.remove(session)
        session['QA_fail'] = reason
        session['QA_action'] = action
        self.failQA.append(session)
        print(f"Failure reason: {reason}")
        print(f"Recommend action: {action}")
        self.report += f"\n\n\n=================================================================="
        self.report += f"\nSession {session['id']} has failed {datatype}"
        self.report += f"\nCause: {reason}\nFix: {action}"
        self.report += f"\n=================================================================="
        return
    
    def QA_raw_data(self):
        """
        Designed to be run after import_dicom/bids but before create_session_info. The goal is to
        identify sessions that: 

        > Are missing required acquisitions
        > Have poor acquisitions (Through quantitative means, eg. frame count)
        > Have unusual/unexpected acquisitions and would require an exotic mapping
        > Failed import_dicom (eg. missing/empty session.txt, incomplete nifti folder)

        This information is found through the session.txt, .nii files, and .json sidecars
        """
        sessions = [s['id'] for s in self.slist]
        print("\n----------------------------------------------------------------------------------")
        print(f"Beginning QA datatype 'raw_data' in {self.sessionsfolder}")
        print("----------------------------------------------------------------------------------\n")
        print(f"Running on sessions: {sessions}")

        if self.config == None:
            minimalQA = True
            print("No config file supplied, running only minimal QA")
        else:
            if 'raw_data' not in self.config.keys():
                minimalQA = True
                print("Config file supplied, but no settings for raw_data detected")
                print("Running with only minimal QA")
            else:
                minimalQA = False
                print("Config file supplied, settings for raw_data found")
                print("Running with full QA")

        #QA for each session. If QA is failed, continue to next session
        for s in self.slist.copy():
            print(f"\nQA start for {s['id']}...")

            #image log, only printed if session fails
            i_log = ""

            #Minimal QA

            #session.txt QA
            if os.path.exists(f"{s['QA_sessionfolder']}/session.txt"):
                i_log += f"\n   session.txt found! Opening..."
                s['QA_sessiontxt'] = os.path.join(s['QA_sessionfolder'], 'session.txt')
                sfile = parser.read_generic_session_file(s['QA_sessiontxt'])
            else:
                s['QA_sessiontxt'] = None
                self.fail(s,'raw_data',  
                            f"Session file session.txt not found in {s['QA_sessionfolder']}",
                            f"Check data import log for this session (eg. import_dicom). Perhaps it was interrupted?")
                continue
    
            #session id check, currently does not check subject
            if sfile['session'] != s['id']:
                self.fail(s,'raw_data',
                            f"session in {s['QA_sessiontxt']} does not match {s['id']}",
                            f"Check your folders match up with the data they contain. Did something get moved or renamed?")
                continue
            else:
                i_log += f"\n      session: {sfile['session']} valid"

            #Check if paths are pointing to the right folder (in case of study move/copy)
            pathFail=False
            for pkey in sfile['paths'].keys():
                if os.path.dirname(sfile['paths'][pkey]) != s['QA_sessionfolder']:
                    pathFail=True
                    self.fail(s,'raw_data',
                                f"{pkey} path in {s['QA_sessiontxt']} does not match {s['QA_sessionfolder']}",
                                f"Ensure the paths are pointing to folders inside the session folder. Did the study get moved or renamed?")
                    break
                else:
                    i_log += f"\n      {pkey}: {sfile['paths'][pkey]} valid"
            if pathFail:
                continue

            #check nii folder exists and add
            niifolder=os.path.join(s['QA_sessionfolder'], 'nii')
            if os.path.exists(niifolder):
                s['QA_niifolder'] = niifolder
            else:
                self.fail(s,'raw_data',
                                f"{niifolder} does not exist!",
                                f"Check the folder for {s['id']}. Did the study get moved or copied? Was something deleted?")
                continue
            
            if minimalQA:
                print('No --config supplied, skipping image QA...')
                continue

            #if data defined as dicom, will check if dicom folder exists
            #use-case is for dicom log QA, but this check is likely unneccesary
            if self.config['config']['data_import'] == 'dicom':
                dicomfolder=os.path.join(s['QA_sessionfolder'], 'dicom')
                if os.path.exists(dicomfolder):
                    s['QA_dicomfolder'] = dicomfolder
                else:
                    self.fail(s,'raw_data',
                                    f"{dicomfolder} does not exist!",
                                    f"Check the folder for {s['id']}. Did the study get moved or copied? Was something deleted?")
                    continue
            else:
                s['QA_dicomfolder'] = None

            #Image QA
            i_log += f"\n   Beginning image QA..."
            s['QA_image'] = {}
            s['QA_image_fail'] = {}

            #Combine session images, numbers, and acquisition into a more usable format
            # [ image id, image description, image acquisition ]
            s_images = []
            for key, value in sfile['images'].items():
                desc = value['series_description'].split(" [")
                if len(desc) > 1:
                    acq = str(key[0])[-1]
                else:
                    #acq 0 means done in one acquisition
                    acq = '0'
                s_images.append([key[0], desc[0], acq])
            s_images = np.asarray(s_images)

            #QA for each image's config
            #Builds numpy arrays for found and expected values for each key, compared at the end
            #Will run full QA for each image so long as an image is found, QA info is stored under 'QA_image' key
            for image_id, image in self.config['raw_data']['scan'].items():
                i_log += f"\n   {image_id} validation..."
                s['QA_image'][image_id] = {}

                #pipe means OR
                id_list = image_id.split('|')

                #Get the relevant images for current image config
                rel_images = []
                for id_str in id_list:
                    #allows unix pattern matching
                    found_images = s_images[np.vectorize(fnmatch)(s_images[:,1],id_str)]
                    rel_images.append(found_images)
                
                rel_images = np.vstack(rel_images)

                num_images = rel_images.shape[0]
                #number of found images
                s['QA_image'][image_id]['n_scans'] = num_images
                #number of configs defined for this image
                s['QA_image'][image_id]['n_configs'] = image['n_items']

                if num_images == 0:
                    i_log += f"\n      No images found matching this description!"
                    i_log += f"\n      Image required: {image['required']}"
                    i_log+="\n      similar images:"
                    for found_images in s_images:
                        #Get series descriptions that are similar, only used for logging/suggested fix
                        ratio = SequenceMatcher(None, image_id, found_images[1]).ratio()
                        if ratio>=0.5:
                            i_log+=f" {found_images[0]}: {found_images[1]}"
                    if image['required']:
                        s['QA_image_fail'][image_id] = "missing"
                    continue
                
                i_log += f"\n      {num_images} images found"
                i_log += f"\n      {image['n_items']} configs found"

                #Holds actual scan values, first row is whether scan has NOT been identified to a config 
                s['QA_image'][image_id]['scan_list'] = [['True'] * num_images]
                #Holds image config values to compare against scan_list
                s['QA_image'][image_id]['im_list'] = [['True'] * image['n_items']]
                #Holds keys, used for report
                s['QA_image'][image_id]['key_list'] = ['matching_scans']

                #If image_count has been specified in config and does not match the number of found images, it fails
                #will still run remaining QA so that matching occurs and user gets a summary of the found images vs. config
                if image['session']['image_count'] != None and image['session']['image_count'] != num_images:
                    s['QA_image_fail'][image_id] = "image_count"
                
                #session QA

                #if scan_index is supplied then image order is considered for matching
                if image['session']['scan_index'] != None:
                    s['QA_image'][image_id]['scan_list'].append(list(range(num_images)))
                    s['QA_image'][image_id]['im_list'].append(image['session']['scan_index'])
                    s['QA_image'][image_id]['key_list'].append('scan_index')

                if image['session']['image_number'] != None:
                    s['QA_image'][image_id]['scan_list'].append(rel_images[:,0].astype(int))
                    s['QA_image'][image_id]['im_list'].append(image['session']['image_number'])
                    s['QA_image'][image_id]['key_list'].append('image_number')

                if image['session']['acquisition'] != None:
                    s['QA_image'][image_id]['scan_list'].append(rel_images[:,2].astype(int))
                    s['QA_image'][image_id]['im_list'].append(image['session']['acquisition'])
                    s['QA_image'][image_id]['key_list'].append('acquisition')

                #dicom log QA, currently only supports 'dicoms' key
                if image['dicoms'] != None:
                    #Get the number of dicoms
                    s['QA_image'][image_id]['scan_list'].append(self.get_dicoms(s, rel_images))
                    value = image['dicoms']
                    s['QA_image'][image_id]['im_list'].append(value)
                    s['QA_image'][image_id]['key_list'].append('dicoms')

                #sidecar json QA
                self.json_qa(s, image_id, rel_images, image)

                #nifti QA
                self.nifti_qa(s, image_id, rel_images, image)
                try:
                    #Create arrays for validation
                    scan_arr = np.vstack(s['QA_image'][image_id]['scan_list'])
                    im_arr = np.vstack(s['QA_image'][image_id]['im_list'])
                    key_arr = np.vstack(s['QA_image'][image_id]['key_list'])
                except:
                    print(f"Unexpected error comparing config to scans! One of the following lists has an inconsistent number of columns:")
                    print(s['QA_image'][image_id]['scan_list'])
                    print(s['QA_image'][image_id]['im_list'])

                    print("Keys:")
                    print(s['QA_image'][image_id]['key_list'])
                    raise ge.CommandError(
                        "run_qa",
                        f"Failed to compare keys!",
                        f"Key comparison failed with image: {image_id}",
                    )
                #Validate configs
                s['QA_image'][image_id]['fail'] = []
                s['QA_image'][image_id]['pass'] = []
                s['QA_image'][image_id]['fail_keys'] = []
                for i in range(image['n_items']):
                    #validation array, compares found and expected values
                    v_arr = (scan_arr == im_arr[:,i].reshape(-1,1))
                    v_indices = np.where(np.all(v_arr,axis=0))[0]
                    if len(v_indices) == 0:
                        s['QA_image_fail'][image_id] = "mismatch"
                        im_arr[0,i] = 0
                        s['QA_image'][image_id]['fail'].append(im_arr[:,i].reshape(-1,1)) #Fail
                        #Assume scan with most correct keys is intended scan, used only for report. Get the keys that do not match this scan
                        s['QA_image'][image_id]['fail_keys'].append(v_arr[:,np.argmax(np.sum(v_arr, axis=0))].reshape(-1,1))
                    else:
                        #set first valid index to unavailable
                        scan_arr[0][v_indices[0]] = False
                        #Replace availability bool with number of matching scans, used for report table
                        im_arr[0,i] = len(v_indices)
                        s['QA_image'][image_id]['pass'].append(im_arr[:,i].reshape(-1,1)) #Found

                remaining_scans = scan_arr[:,np.where(scan_arr[0]=='True')[0]]
                remaining_scans[0] = " "
                s['QA_image'][image_id]['remaining'] = remaining_scans
                s['QA_image'][image_id]['keys'] = key_arr

            #Image QA Report
            if len(s['QA_image_fail'].keys()) > 0:
                #Image log only printed on fail. Could add verbose flag
                print(i_log)
                self.fail(s, 'raw_data',
                    f"Scan(s) {', '.join([key for key in s['QA_image_fail'].keys()])} have failed QA",
                    "Check config and data for this session, see image report for relevant parameters")
                self.update_report(s)
            else:
                print(f"{s['id']} has passed QA!")
        return
    
    def nifti_qa(self, s, image_id, scans, config):
        """
        Runs raw_data QA on .nii files. Runs key-value validation on the header, except for data_shape
        which is extracted.

        --s (dict)
            slist dict

        --scans (list)
            session ids to check

        --config (dict)
            config to check scans against
        """
        niftis = []

        n_list = []
        #attempt to load nifti file headers
        for scan in scans:
            try:
                niftis.append(nib.load(os.path.join(s['QA_niifolder'],f"{scan[0]}.nii.gz")).header)
                n_list.append(True)
            except:
                niftis.append('missing_file')
                n_list.append('Missing!') #Fail

        s['QA_image'][image_id]['scan_list'].append(n_list)
        #if nifti QA is run, config will always require that nifti files can be loaded
        s['QA_image'][image_id]['im_list'].append([True]*config['n_items'])
        s['QA_image'][image_id]['key_list'].append('nifti_file')
            
        for key, value in config['nifti'].items():
            #If config key has a valid defined value
            if value != None:
                #params that are a list of vals for each image
                if key in ["data_shape", "pixdim", "dim", "srow_x", "srow_y", "srow_z"]:
                    value = np.asarray(value).T
                    s['QA_image'][image_id]['im_list'].append(value)
                    #parse each value in the list separately
                    for i in range(len(value)):
                        n_list = []
                        s['QA_image'][image_id]['key_list'].append(f"{key}_{i}")
                        for n in niftis:
                            try:
                                #data_shape is not a key in header
                                if key == "data_shape":
                                    n_list.append(n.get_data_shape()[i])
                                else:
                                    n_list.append(n[key][i])
                            except:
                                n_list.append("Missing!") #Fail if missing
                        s['QA_image'][image_id]['scan_list'].append(n_list)
                #standard key-value comparison
                else:
                    s['QA_image'][image_id]['im_list'].append(value)
                    s['QA_image'][image_id]['key_list'].append(key)
                    n_list = []
                    #get data from headers
                    for n in niftis:
                        try:
                                n_list.append(n[key])
                        except:
                            n_list.append("Missing!") #Fail if missing
                        
                    s['QA_image'][image_id]['scan_list'].append(n_list)
        return 
    
    def json_qa(self, s, image_id, scans, config):
        """
        Runs raw_data QA on sidercar .json files. Runs key-value validation, except for normalized.

        --s (dict)
            slist dict

        --scans (list)
            session ids to check

        --config (dict)
            config to check scans against
        """
        jsons = []
        j_list = []
        for scan in scans:
            try:
                with open(os.path.join(s['QA_niifolder'],f"{scan[0]}.json")) as file:
                    jsons.append(json.load(file))
                    j_list.append(True)
            except:
                jsons.append("missing_file")
                j_list.append("Missing!") 

        s['QA_image'][image_id]['scan_list'].append(j_list)
        s['QA_image'][image_id]['im_list'].append([True]*config['n_items'])
        s['QA_image'][image_id]['key_list'].append('json_file')
            
        for key, value in config['json'].items():
            if value != None:
                #params that are a list of vals for each image
                if key in ["ImageType", "ShimSetting", "ImageOrientationPatientDICOM"]:
                    value = np.asarray(value).T
                    s['QA_image'][image_id]['im_list'].append(value)
                    #parse each value in the list separately
                    for i in range(len(value)):
                        s['QA_image'][image_id]['key_list'].append(f"{key}_{i}")
                        j_list = []
                        for j in jsons:
                            try:
                                j_list.append(j[key][i])
                            except:
                                j_list.append("Missing!") 
                            
                        s['QA_image'][image_id]['scan_list'].append(j_list)
                else:
                    s['QA_image'][image_id]['key_list'].append(key)
                    s['QA_image'][image_id]['im_list'].append(value)
                    j_list = []
                    for j in jsons:

                        try:
                            if key == 'normalized':
                                j_list.append("NORM" in j['ImageType'])
                            else:
                                j_list.append(j[key])
                        except:
                            j_list.append("Missing!") 
                        
                    s['QA_image'][image_id]['scan_list'].append(j_list)

        return 
    
    def get_dicoms(self, s, scans):
        """
        Loads dicom logs and gets the number of DICOM files. Similar to data_shape but may be more
        accessible for some users.

        --s (dict)
            slist dict

        --scans (list)
            session ids to load dicom logs for
        """
        if s['QA_dicomfolder'] == None:
            raise ge.CommandError(
                "run_qa",
                f"dicoms QA specified, but data_import is not dicom!",
                "Add config:\n\tdata_import: dicom in config",
            )
        dicoms = []
        for scan in scans:
            try:
                with open(os.path.join(s['QA_dicomfolder'],f"dcm2niix_{str(scan[0])[:-1]}0.log"), 'r') as file:
                    log = file.read()
                dicoms.append(re.search('Found (.*) DICOM file', log).group(1))
                
            except:
                dicoms.append(False)
        return dicoms
    
    def update_report(self, s):
        """
        Updates report with diagnostic and QA info in a human-readable table for a failed session.

        --s (dict)
            slist dict that has failed QA
        """
        
        for image_id, fail in s['QA_image_fail'].items():
            self.report+= f"\n   - {image_id}"

            if fail == 'missing':
                self.report+= "\n      No image(s) found in session.txt matching this description, check session.txt or set Required: False in config"
                continue
            elif fail == 'image_count':
                image_count = self.config['raw_data']['scan'][image_id]['session']['image_count']
                found_count = s['QA_image'][image_id]['n_scans']
                self.report+= f"\n      Incorrect number of scans specified! image_count: {image_count} specified in config, but {found_count} found. If as expected, change or remove image_count in config"
            elif fail == 'mismatch':
                self.report+= "\n      Config Key mismatch with scan! Suspected incorrect parameters are emphasized with *"
            self.report+=f"\n      Attempted to match {s['QA_image'][image_id]['n_configs']} config(s) to {s['QA_image'][image_id]['n_scans']} scan(s)"

            #Set up columns
            k_list = ['Config Key']
            k_len = len(k_list[0])
            v_list = ['Valid Configs']
            v_len = len(v_list[0])
            f_list = ['Failed Configs']
            f_len = len(f_list[0])
            r_list = ['Remaining Scans']
            r_len = len(r_list[0])
            sig_list = [" "*s['QA_image'][image_id]['n_configs']]

            internal_keys = ['available']

            #whitespace padding
            f_padding = []
            for f in s['QA_image'][image_id]['fail']:
                f_padding.append(np.max(np.vectorize(len)(f), axis=0))

            for i in range(len(s['QA_image'][image_id]['keys'])):
                key = s['QA_image'][image_id]['keys'][i][0]
                if key in internal_keys:
                    continue
                k_list.append(key)
                k_len = max(k_len, len(k_list[-1]))
                v_str = ""
                for c in s['QA_image'][image_id]['pass']:
                    v_str += np.array2string(c[i]).strip("[]").replace("'"," ") + " "
                v_list.append(v_str)
                v_len = max(v_len, len(v_list[-1]))
                f_str = ""
                sig_str = " " * (s['QA_image'][image_id]['n_configs'] - len(s['QA_image'][image_id]['fail']))
                for c, ck, cp in zip(s['QA_image'][image_id]['fail'],s['QA_image'][image_id]['fail_keys'],f_padding):
                    if not ck[i]:
                        f = np.array2string(c[i]).strip("[]").replace("'","*")
                        sig_str+="*"
                    else:
                        f = np.array2string(c[i]).strip("[]").replace("'"," ")
                        sig_str+=" "
                    f_str += f + (cp[0]+3 - len(f))*' '
                f_list.append(f_str)
                sig_list.append(sig_str)
                f_len = max(f_len, len(f_list[-1]))
                r_list.append(np.array2string(s['QA_image'][image_id]['remaining'][i], separator="\t").strip("[]").replace("'"," "))
                r_len = max(r_len, len(r_list[-1]))

            for i in range(len(k_list)):
                self.report+=f"\n       {sig_list[i]} {k_list[i] + (k_len - len(k_list[i]))*' '}"
                self.report+=f" | {v_list[i] + (v_len - len(v_list[i]))*' '}"
                self.report+=f" | {f_list[i] + (f_len - len(f_list[i]))*' '}"
                self.report+=f" | {r_list[i] + (r_len - len(r_list[i]))*' '}"
        self.report+="\n"
        return
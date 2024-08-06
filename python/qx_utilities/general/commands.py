#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``commands.py``

Definition of commands used in gmri along with their parameters.
"""

# qx_utilities imports
from general import dicom, bids, fourdfp, dicomdeid, fidl, qximg, img, nifti, palm, scheduler, utilities, meltmovfidl, commands_support, bruker, extensions

# pipeline imports
from hcp import import_hcp, setup_hcp, export_hcp
from nhp import import_nhp

# QA imports
from qa import run_qa

# all command mappings
commands = {'list_dicom': {'com': dicom.list_dicom, 'args': ('folder', )}, 
            'split_dicom': {'com': dicom.split_dicom, 'args': ('folder', )}, 
            'sort_dicom': {'com': dicom.sort_dicom, 'args': ('folder', 'out_dir', 'files', 'copy')}, 
            'dicom2nii': {'com': dicom.dicom2nii, 'args': ('folder', 'clean', 'unzip', 'gzip', 'verbose', 'parelements', 'debug')}, 
            'dicom2niix': {'com': dicom.dicom2niix, 'args': ('folder', 'clean', 'unzip', 'gzip', 'sessionid', 'verbose', 'parelements', 'debug', 'tool', 'add_image_type', 'add_json_info')}, 
            'import_dicom': {'com': dicom.import_dicom, 'args': ('sessionsfolder', 'sessions', 'masterinbox', 'check', 'pattern', 'nameformat', 'tool', 'parelements', 'logfile', 'archive', 'add_image_type', 'add_json_info', 'unzip', 'gzip', 'verbose', 'overwrite', 'test')}, 
            'get_dicom_info': {'com': dicom.get_dicom_info, 'args': ('dicomfile', 'scanner')}, 
            'import_bids': {'com': bids.import_bids, 'args': ('sessionsfolder', 'inbox', 'sessions', 'action', 'overwrite', 'archive', 'bidsname', 'fileinfo')}, 
            'map_bids2nii': {'com': bids.map_bids2nii, 'args': ('sourcefolder', 'overwrite', 'fileinfo')}, 
            'import_hcp': {'com': import_hcp.import_hcp, 'args': ('sessionsfolder', 'inbox', 'sessions', 'action', 'overwrite', 'archive', 'hcplsname', 'nameformat', 'filesort', 'processed_data')}, 
            'map_hcpls2nii': {'com': import_hcp.map_hcpls2nii, 'args': ('sourcefolder', 'overwrite', 'filesort')}, 
            'run_nil_folder': {'com': fourdfp.run_nil_folder, 'args': ('folder', 'pattern', 'overwite', 'sourcefile')}, 
            'run_nil': {'com': fourdfp.run_nil, 'args': ('folder', 'overwite', 'sourcefile')}, 
            'fz2zf': {'com': nifti.fz2zf, 'args': ('inf', 'outf')}, 
            'reorder': {'com': nifti.reorder, 'args': ('inf', 'outf')}, 
            'reslice': {'com': nifti.reslice, 'args': ('inf', 'slices', 'outf')}, 
            'slice_image': {'com': img.slice_image, 'args': ('sourcefile', 'targetfile', 'frames')}, 
            'nifti24dfp': {'com': nifti.nifti24dfp, 'args': ('inf', 'outf')}, 
            'setup_hcp': {'com': setup_hcp.setup_hcp, 'args': ('sourcefolder', 'targetfolder', 'sourcefile', 'check', 'existing', 'hcp_filename', 'hcp_folderstructure', 'hcp_suffix', 'use_sequence_info', 'slice_timing_info')}, 
            'prepare_slice_timing': {'com': setup_hcp.prepare_slice_timing, 'args': ('jsonfile', 'slicetimingfile')}, 
            'create_session_info': {'com': utilities.create_session_info, 'args': ('sessions', 'pipelines', 'sessionsfolder', 'sourcefile', 'targetfile', 'mapping', 'filter', 'overwrite')}, 
            'printniftihdr': {'com': img.printniftihdr, 'args': ('filename', )}, 
            'modniftihdr': {'com': qximg.modniftihdr, 'args': ('filename', 's')}, 
            'create_batch': {'com': utilities.create_batch, 'args': ('sessionsfolder', 'sourcefiles', 'targetfile', 'sessions', 'filter', 'overwrite', 'paramfile')}, 
            'manage_study': {'com': utilities.manage_study, 'args': ('studyfolder', 'action', 'folders', 'verbose')}, 
            'create_study': {'com': utilities.create_study, 'args': ('studyfolder', 'folders', )}, 
            'copy_study': {'com': utilities.copy_study, 'args': ('studyfolder', 'sourcefolder', 'sessions', 'filter', 'batchfile',)}, 
            'create_list': {'com': utilities.create_list, 'args': ('sessionsfolder', 'sessions', 'sessionids', 'filter', 'listfile', 'bolds', 'conc', 'fidl', 'glm', 'roi', 'boldname', 'bold_tail', 'img_suffix', 'bold_variant', 'overwrite', 'check')}, 
            'create_conc': {'com': utilities.create_conc, 'args': ('sessionsfolder', 'sessions', 'sessionids', 'filter', 'concfolder', 'concname', 'bolds', 'boldname', 'bold_tail', 'img_suffix', 'bold_variant', 'overwrite', 'check')}, 
            'gather_behavior': {'com': utilities.gather_behavior, 'args': ('sessionsfolder', 'sessions', 'filter', 'sourcefiles', 'targetfile', 'overwrite', 'check', 'report')}, 
            'pull_sequence_names': {'com': utilities.pull_sequence_names, 'args': ('sessionsfolder', 'sessions', 'filter', 'sourcefiles', 'targetfile', 'overwrite', 'check', 'report')}, 
            'batch_tag2namekey': {'com': utilities.batch_tag2namekey, 'args': ('filename', 'sessionid', 'bolds', 'output', 'prefix')}, 
            'meltmovfidl': {'com': meltmovfidl.meltmovfidl, 'args': ('cfile', 'ifile', 'iffile', 'offile')}, 
            'check_deprecated_commands': {'com': commands_support.check_deprecated_commands, 'args': ('command')}, 
            'export_hcp': {'com': export_hcp.export_hcp, 'args': ('sessionsfolder', 'sessions', 'filter', 'sessionids', 'mapaction', 'mapto', 'overwrite', 'mapexclude', 'hcp_suffix', 'verbose')}, 
            'join_fidl': {'com': fidl.join_fidl, 'args': ('concfile', 'fidlroot', 'outfolder', 'fidlname')}, 
            'join_fidl_folder': {'com': fidl.join_fidl_folder, 'args': ('concfolder', 'fidlfolder', 'outfolder', 'fidlname')}, 
            'split_fidl': {'com': fidl.split_fidl, 'args': ('concfile', 'fidlfile', 'outfolder')}, 
            'check_fidl': {'com': fidl.check_fidl, 'args': ('fidlfile', 'fidlfolder', 'plotfile', 'allcodes')}, 
            'map2pals': {'com': fourdfp.map2pals, 'args': ('volume', 'metric', 'atlas', 'method', 'mapping')}, 
            'map2hcp': {'com': fourdfp.map2hcp, 'args': ('volume', 'method')}, 
            'mask_map': {'com': palm.mask_map, 'args': ('image', 'masks', 'output', 'minv', 'maxv', 'join')}, 
            'join_maps': {'com': palm.join_maps, 'args': ('images', 'output', 'names', 'originals')}, 
            'run_palm': {'com': palm.run_palm, 'args': ('image', 'design', 'palm_args', 'root', 'surface', 'mask', 'parelements', 'overwrite', 'cleanup')}, 
            'create_ws_palm_design': {'com': palm.create_ws_palm_design, 'args': ('factors', 'nsubjects', 'root')}, 
            'schedule': {'com': scheduler.schedule, 'args': ('command', 'script', 'settings', 'replace', 'workdir', 'environment', 'output')}, 
            'get_dicom_fields': {'com': dicomdeid.get_dicom_fields, 'args': ('folder', 'targetfile', 'limit')}, 
            'change_dicom_files': {'com': dicomdeid.change_dicom_files, 'args': ('folder', 'paramfile', 'archivefile', 'outputfolder', 'extension', 'replacementdate')}, 
            'run_recipe': {'com': utilities.run_recipe,             'args': ('recipe_file', 'recipe', 'steps', 'logfolder', 'verbose', 'eargs')},
            'import_nhp': {'com': import_nhp.import_nhp,          'args': ('sessionsfolder', 'inbox', 'sessions', 'action', 'overwrite', 'archive')},
            'bruker_to_dicom': {'com': bruker.bruker_to_dicom,         'args': ('sessionsfolder', 'inbox', 'sessions', 'archive', 'parelements')},
            'get_sessions_for_slurm_array': {'com': utilities.get_sessions_for_slurm_array, 'args': ('sessions', 'sessionids')},
            'run_qa': {'com': run_qa.run_qa, 'args': ('datatype', 'sessionsfolder', 'sessions', 'configfile', 'overwrite', 'tag')}
            }

# -- update commands list with information from extensions
commands.update(extensions.compile_dict('commands'))
commands.update(extensions.commands)

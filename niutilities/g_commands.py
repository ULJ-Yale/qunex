#!/usr/bin/env python2.7
# encoding: utf-8
"""
g_commands.py

Definition of commands used in gmri along with their parameters.
"""

import g_dicom
import g_bids
import g_hcpls
import g_4dfp
import g_NIfTI
import g_img
import g_gimg
import g_HCP
import g_utilities
import g_fidl
import g_palm
import g_scheduler
import g_dicomdeid

commands = {'listDicom'            : {'com': g_dicom.listDicom,              'args': ('folder', )},
            'splitDicom'           : {'com': g_dicom.splitDicom,             'args': ('folder', )},
            'sortDicom'            : {'com': g_dicom.sortDicom,              'args': ('folder', 'out_dir', 'files', 'copy')},
            'dicom2nii'            : {'com': g_dicom.dicom2nii,              'args': ('folder', 'clean', 'unzip', 'gzip', 'verbose', 'cores', 'debug')},
            'dicom2niix'           : {'com': g_dicom.dicom2niix,             'args': ('folder', 'clean', 'unzip', 'gzip', 'sessionid', 'verbose', 'cores', 'debug', 'tool', 'options')},
            'processInbox'         : {'com': g_dicom.processInbox,           'args': ('subjectsfolder', 'sessions', 'masterinbox', 'check', 'pattern', 'tool', 'cores', 'logfile', 'archive', 'options', 'unzip', 'gzip', 'verbose')},
            'getDICOMInfo'         : {'com': g_dicom.getDICOMInfo,           'args': ('dicomfile', 'scanner')},
            'BIDSImport'           : {'com': g_bids.BIDSImport,              'args': ('subjectsfolder', 'inbox', 'sessions', 'action', 'overwrite', 'archive', 'bidsName')},
            'mapBIDS2nii'          : {'com': g_bids.mapBIDS2nii,             'args': ('sfolder', 'overwrite')},
            'HCPLSImport'          : {'com': g_hcpls.HCPLSImport,            'args': ('subjectsfolder', 'inbox', 'action', 'overwrite', 'archive', 'hcplsName')},
            'mapHCPLS2nii'         : {'com': g_hcpls.mapHCPLS2nii,           'args': ('sfolder', 'overwrite')},
            'runNILFolder'         : {'com': g_4dfp.runNILFolder,            'args': ('folder', 'pattern', 'overwite', 'sfile')},
            'runNIL'               : {'com': g_4dfp.runNIL,                  'args': ('folder', 'overwite', 'sfile')},
            'fz2zf'                : {'com': g_NIfTI.fz2zf,                  'args': ('inf', 'outf')},
            'reorder'              : {'com': g_NIfTI.reorder,                'args': ('inf', 'outf')},
            'reslice'              : {'com': g_NIfTI.reslice,                'args': ('inf', 'slices', 'outf')},
            'sliceImage'           : {'com': g_img.sliceImage,               'args': ('sfile', 'tfile', 'frames')},
            'nifti24dfp'           : {'com': g_NIfTI.nifti24dfp,             'args': ('inf', 'outf')},
            'setupHCP'             : {'com': g_HCP.setupHCP,                 'args': ('sfolder', 'tfolder', 'sfile', 'check', 'existing')},
            'setupHCPFolder'       : {'com': g_HCP.setupHCPFolder,           'args': ('subjectsfolder', 'tfolder', 'sfile', 'check')},
            'getHCPReady'          : {'com': g_HCP.getHCPReady,              'args': ('sessions', 'subjectsfolder', 'sfile', 'tfile', 'mapping', 'sfilter', 'overwrite')},
            'printniftihdr'        : {'com': g_img.printniftihdr,            'args': ('filename', )},
            'modniftihdr'          : {'com': g_gimg.modniftihdr,             'args': ('filename', 's')},
            'createBatch'          : {'com': g_utilities.createBatch,        'args': ('subjectsfolder', 'sfile', 'tfile', 'sessions', 'sfilter', 'overwrite', 'paramfile')},
            'createStudy'          : {'com': g_utilities.createStudy,        'args': ('studyfolder', )},
            'createList'           : {'com': g_utilities.createList,         'args': ('subjectsfolder', 'sessions', 'sfilter', 'listfile', 'bolds', 'conc', 'fidl', 'glm', 'roi', 'boldname', 'boldtail', 'overwrite', 'check')},
            'createConc'           : {'com': g_utilities.createConc,         'args': ('subjectsfolder', 'sessions', 'sfilter', 'concfolder', 'concname', 'bolds', 'boldname', 'boldtail', 'overwrite', 'check')},
            'gatherBehavior'       : {'com': g_utilities.gatherBehavior,     'args': ('subjectsfolder', 'sessions', 'sfilter', 'sfile', 'tfile', 'overwrite', 'check', 'report')},
            'pullSequenceNames'    : {'com': g_utilities.pullSequenceNames,  'args': ('subjectsfolder', 'sessions', 'sfilter', 'sfile', 'tfile', 'overwrite', 'check', 'report')},
            'batchTag2Num'         : {'com': g_utilities.batchTag2Num,       'args': ('filename', 'subjid', 'bolds')},
            'joinFidl'             : {'com': g_fidl.joinFidl,                'args': ('concfile', 'fidlroot', 'outfolder', 'fidlname')},
            'joinFidlFolder'       : {'com': g_fidl.joinFidlFolder,          'args': ('concfolder', 'fidlfolder', 'outfolder', 'fidlname')},
            'splitFidl'            : {'com': g_fidl.splitFidl,               'args': ('concfile', 'fidlfile', 'outfolder')},
            'checkFidl'            : {'com': g_fidl.checkFidl,               'args': ('fidlfile', 'fidlfolder', 'plotfile', 'allcodes')},
            'map2PALS'             : {'com': g_4dfp.map2PALS,                'args': ('volume', 'metric', 'atlas', 'method', 'mapping')},
            'map2HCP'              : {'com': g_4dfp.map2HCP,                 'args': ('volume', 'method')},
            'maskMap'              : {'com': g_palm.maskMap,                 'args': ('image', 'masks', 'output', 'minv', 'maxv', 'join')},
            'joinMaps'             : {'com': g_palm.joinMaps,                'args': ('images', 'output', 'names', 'originals')},
            'runPALM'              : {'com': g_palm.runPALM,                 'args': ('image', 'design', 'args', 'root', 'options', 'cores', 'overwrite', 'cleanup')},
            'createWSPALMDesign'   : {'com': g_palm.createWSPALMDesign,      'args': ('factors', 'nsubjects', 'root')},
            'schedule'             : {'com': g_scheduler.schedule,           'args': ('command', 'script', 'settings', 'replace', 'workdir', 'environment', 'output')},
            'getDICOMFields'       : {'com': g_dicomdeid.getDICOMFields,     'args': ('folder', 'tfile', 'limit')},
            'changeDICOMFiles'     : {'com': g_dicomdeid.changeDICOMFiles,   'args': ('folder', 'paramfile', 'archivefile', 'outputfolder', 'extension', 'replacementdate')},
            'runList'              : {'com': g_utilities.runList,            'args': ('listfile', 'runlists', 'logfolder', 'verbose', 'eargs')}
            }

extraParameters = ['sessions', 'filter', 'subjid', 'scheduler', 'cores', 'scheduler_environment', 'scheduler_workdir', 'scheduler_sleep', 'nprocess', 'logfolder', 'basefolder', 'subjectsfolder', 'sperlist', 'runinpar', 'ignore']

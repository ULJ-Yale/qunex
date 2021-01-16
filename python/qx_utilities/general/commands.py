#!/usr/bin/env python2.7
# encoding: utf-8
"""
``commands.py``

Definition of commands used in gmri along with their parameters.
"""

# qx_utilities imports
import dicom, bids, fourdfp, dicomdeid, fidl, qximg, img, nifti, palm, scheduler, utilities

# pipeline imports
from hcp import import_hcp, setup_hcp, process_hcp, export_hcp
from nhp import import_nhp

# all command mappings
commands = {'listDicom'            : {'com': dicom.listDicom,               'args': ('folder', )},
            'splitDicom'           : {'com': dicom.splitDicom,              'args': ('folder', )},
            'sortDicom'            : {'com': dicom.sortDicom,               'args': ('folder', 'out_dir', 'files', 'copy')},
            'dicom2nii'            : {'com': dicom.dicom2nii,               'args': ('folder', 'clean', 'unzip', 'gzip', 'verbose', 'parelements', 'debug')},
            'dicom2niix'           : {'com': dicom.dicom2niix,              'args': ('folder', 'clean', 'unzip', 'gzip', 'sessionid', 'verbose', 'parelements', 'debug', 'tool', 'options')},
            'importDICOM'          : {'com': dicom.importDICOM,             'args': ('sessionsfolder', 'sessions', 'masterinbox', 'check', 'pattern', 'nameformat', 'tool', 'parelements', 'logfile', 'archive', 'options', 'unzip', 'gzip', 'verbose', 'overwrite')},
            'getDICOMInfo'         : {'com': dicom.getDICOMInfo,            'args': ('dicomfile', 'scanner')},
            'importBIDS'           : {'com': bids.importBIDS,               'args': ('sessionsfolder', 'inbox', 'sessions', 'action', 'overwrite', 'archive', 'bidsname', 'fileinfo')},
            'mapBIDS2nii'          : {'com': bids.mapBIDS2nii,              'args': ('sourcefolder', 'overwrite', 'fileinfo')},
            'importHCP'            : {'com': import_hcp.importHCP,          'args': ('sessionsfolder', 'inbox', 'sessions', 'action', 'overwrite', 'archive', 'hcplsname', 'nameformat', 'filesort')},
            'mapHCPLS2nii'         : {'com': import_hcp.mapHCPLS2nii,       'args': ('sourcefolder', 'overwrite', 'filesort')},
            'runNILFolder'         : {'com': fourdfp.runNILFolder,          'args': ('folder', 'pattern', 'overwite', 'sourcefile')},
            'runNIL'               : {'com': fourdfp.runNIL,                'args': ('folder', 'overwite', 'sourcefile')},
            'fz2zf'                : {'com': nifti.fz2zf,                   'args': ('inf', 'outf')},
            'reorder'              : {'com': nifti.reorder,                 'args': ('inf', 'outf')},
            'reslice'              : {'com': nifti.reslice,                 'args': ('inf', 'slices', 'outf')},
            'sliceImage'           : {'com': img.sliceImage,                'args': ('sourcefile', 'targetfile', 'frames')},
            'nifti24dfp'           : {'com': nifti.nifti24dfp,              'args': ('inf', 'outf')},
            'setupHCP'             : {'com': setup_hcp.setupHCP,            'args': ('sourcefolder', 'targetfolder', 'sourcefile', 'check', 'existing', 'hcp_filename', 'folderstructure', 'hcp_suffix')},
            'createSessionInfo'    : {'com': utilities.createSessionInfo,   'args': ('sessions', 'pipelines', 'sessionsfolder', 'sourcefile', 'targetfile', 'mapping', 'filter', 'overwrite')},
            'printniftihdr'        : {'com': img.printniftihdr,             'args': ('filename', )},
            'modniftihdr'          : {'com': qximg.modniftihdr,             'args': ('filename', 's')},
            'createBatch'          : {'com': utilities.createBatch,         'args': ('sessionsfolder', 'sourcefiles', 'targetfile', 'sessions', 'filter', 'overwrite', 'paramfile')},
            'manageStudy'          : {'com': utilities.manageStudy,         'args': ('studyfolder', 'action', 'folders', 'verbose')},
            'createStudy'          : {'com': utilities.createStudy,         'args': ('studyfolder', 'folders', )},
            'createList'           : {'com': utilities.createList,          'args': ('sessionsfolder', 'sessions', 'filter', 'listfile', 'bolds', 'conc', 'fidl', 'glm', 'roi', 'boldname', 'bold_tail', 'img_suffix', 'bold_variant', 'overwrite', 'check')},
            'createConc'           : {'com': utilities.createConc,          'args': ('sessionsfolder', 'sessions', 'filter', 'concfolder', 'concname', 'bolds', 'boldname', 'bold_tail', 'img_suffix', 'bold_variant', 'overwrite', 'check')},
            'gatherBehavior'       : {'com': utilities.gatherBehavior,      'args': ('sessionsfolder', 'sessions', 'filter', 'sourcefiles', 'targetfile', 'overwrite', 'check', 'report')},
            'pullSequenceNames'    : {'com': utilities.pullSequenceNames,   'args': ('sessionsfolder', 'sessions', 'filter', 'sourcefiles', 'targetfile', 'overwrite', 'check', 'report')},
            'batchTag2NameKey'     : {'com': utilities.batchTag2NameKey,    'args': ('filename', 'sessionid', 'bolds', 'output', 'prefix')},
            'exportHCP'            : {'com': export_hcp.exportHCP,          'args': ('sessionsfolder', 'sessions', 'filter', 'sessionids', 'mapaction', 'mapto', 'overwrite', 'mapexclude', 'hcp_suffix', 'verbose')},
            'mapIO'                : {'com': export_hcp.exportHCP,          'args': ('sessionsfolder', 'sessions', 'filter', 'sessionids', 'mapaction', 'mapto', 'overwrite', 'mapexclude', 'hcp_suffix', 'verbose')},
            'joinFidl'             : {'com': fidl.joinFidl,                 'args': ('concfile', 'fidlroot', 'outfolder', 'fidlname')},
            'joinFidlFolder'       : {'com': fidl.joinFidlFolder,           'args': ('concfolder', 'fidlfolder', 'outfolder', 'fidlname')},
            'splitFidl'            : {'com': fidl.splitFidl,                'args': ('concfile', 'fidlfile', 'outfolder')},
            'checkFidl'            : {'com': fidl.checkFidl,                'args': ('fidlfile', 'fidlfolder', 'plotfile', 'allcodes')},
            'map2PALS'             : {'com': fourdfp.map2PALS,              'args': ('volume', 'metric', 'atlas', 'method', 'mapping')},
            'map2HCP'              : {'com': fourdfp.map2HCP,               'args': ('volume', 'method')},
            'maskMap'              : {'com': palm.maskMap,                  'args': ('image', 'masks', 'output', 'minv', 'maxv', 'join')},
            'joinMaps'             : {'com': palm.joinMaps,                 'args': ('images', 'output', 'names', 'originals')},
            'runPALM'              : {'com': palm.runPALM,                  'args': ('image', 'design', 'args', 'root', 'options', 'parelements', 'overwrite', 'cleanup')},
            'createWSPALMDesign'   : {'com': palm.createWSPALMDesign,       'args': ('factors', 'nsubjects', 'root')},
            'schedule'             : {'com': scheduler.schedule,            'args': ('command', 'script', 'settings', 'replace', 'workdir', 'environment', 'output')},
            'getDICOMFields'       : {'com': dicomdeid.getDICOMFields,      'args': ('folder', 'targetfile', 'limit')},
            'changeDICOMFiles'     : {'com': dicomdeid.changeDICOMFiles,    'args': ('folder', 'paramfile', 'archivefile', 'outputfolder', 'extension', 'replacementdate')},
            'runList'              : {'com': utilities.runList,             'args': ('listfile', 'runlists', 'logfolder', 'verbose', 'eargs')},
            'import_nhp'           : {'com': import_nhp.import_nhp,         'args': ('sessionsfolder', 'inbox', 'sessions', 'action', 'overwrite', 'archive', 'nameformat')},
            }

extraParameters = ['sessions', 'filter', 'sessionid', 'sessionids', 'scheduler', 'parelements', 'scheduler_environment', 'scheduler_workdir', 'scheduler_sleep', 'nprocess', 'logfolder', 'basefolder', 'sessionsfolder', 'sperlist', 'runinpar', 'ignore', 'bash']

# a dictonary of deprecated commands ("oldCommand": "newCommand")
deprecated_commands = {"HCPLSImport": "importHCP",
                       "BIDSImport": "importBIDS",
                       "processInbox": "importDICOM",
                       "mapIO": "exportHCP",
                       "listSubjectInfo": "listSessionInfo",
                       "getHCPReady": "createSesssionInfo"}

def checkDeprecatedCommands(command):
    """
    checkDeprecatedCommands(options, deprecatedCommands)
    Checks for deprecated commands, remaps deprecated ones
    and notifies the user.
    """

    # store the command
    newCommand = command
    # is it depreacted?
    for deprecatedName, newName in deprecated_commands.items():
        # if deprecated warn the user and call the new one
        if command == deprecatedName:
            newCommand = newName
            print "\nWARNING: Use of deprecated command!"
            print "Command %s is now known as %s.\n" % (command, newCommand)

    return newCommand

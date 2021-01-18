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
            'check_deprecated_commands' : {'com': utilities.check_deprecated_commands,   'args': ('command')},
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

# a dictonary of deprecated commands ("new_command": ["oldcommand1", "oldcommand2", ...])
deprecated_commands = {
                        "importHCP": ["HCPLSImport"],
                        "importBIDS": ["BIDSImport"],
                        "importDICOM": ["processInbox"],
                        "exportHCP": ["mapIO"],
                        "listSessionInfo": ["listSubjectInfo"],
                        "createSesssionInfo": ["getHCPReady"],
                        "create_study": ["createStudy"],
                        "run_qc": ["runQC","RunQC","QCPreproc"],
                        "fc_ComputeABCorr": "fc_compute_ab_corr",
                        "fc_ComputeABCorrKCA": "fc_compute_ab_corr_kca",
                        "fc_ComputeGBC3": "fc_compute_gbc3",
                        "fc_ComputeGBCd": "fc_compute_gbcd",
                        "fc_ComputeROIFC": "fc_compute_roifc",
                        "fc_ComputeROIFCGroup": "fc_compute_roifc_group",
                        "fc_ComputeSeedMaps": "fc_compute_seedmaps",
                        "fc_ComputeSeedMapsGroup": "fc_compute_seedmaps_group",
                        "fc_ComputeSeedMapsMultiple": "fc_compute_seedmaps_multiple",
                        "fc_ExtractROITimeseriesMasked": "fc_extract_roi_timeseries_masked",
                        "fc_ExtractTrialTimeseriesMasked": "fc_extract_trial_timeseries_masked",
                        "fc_fcMRISegment": "fc_mri_segment",
                        "fc_Preprocess": "fc_preprocess",
                        "fc_PreprocessConc": "fc_preprocess_conc",
                        "qa_imgOverlap": "general_image_overlap",
                        "g_ComputeBOLDListStats": "general_compute_bold_list_stats",
                        "g_ComputeBOLDStats": "general_compute_bold_stats",
                        "g_ComputeGroupBOLDStats": "general_compute_group_bold_stats",
                        "g_ExtractROIGLMValues": "general_extract_roi_glm_values",
                        "g_FindPeaks": "general_find_peaks",
                        "g_Parcellated2Dense": "general_parcellated2dense",
                        "g_PlotBoldTS": "general_plot_bold_timeseries",
                        "g_PlotBoldTSList": "general_plot_bold_timeseries_list",
                        "g_QAConcFile": "general_qa_concfile"
                      }

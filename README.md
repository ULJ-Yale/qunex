# README File for Quantitative Neuroimaging Environment & ToolboX (Qu|Nex)

The Quantitative Neuroimaging Environment & ToolboX (Qu|Nex) integrates a number of 
modules that support a flexible and extensible framework for data organization, preprocessing, 
quality assurance, and various analytics across neuroimaging modalities. The Qu|Nex suite is 
designed to be flexible and can be developed by adding functions developed around its component tools.

The Qu|Nex code is is co-developed and co-maintained by the 
[Mind and Brain Lab led by Grega Repovs](http://psy.ff.uni-lj.si/mblab/en) 
and the [Anticevic Lab](http://anticeviclab.yale.edu/).


Quick links
-----------

* [Website](http://qunex.yale.edu/)
* [Qu|Nex Wiki](https://bitbucket.org/oriadev/qunex/wiki/Home)
* [SDK Wiki](https://bitbucket.org/oriadev/qunexsdk/wiki/Home)
* [Qu|Nex quick start](https://bitbucket.org/oriadev/qunex/wiki/Overview/QuickStart.md)
* [Qu|Nex container deployment](https://bitbucket.org/oriadev/qunex/wiki/Overview/Installation.md)
* [Installing from source and dependencies](https://bitbucket.org/oriadev/qunex/wiki/Overview/Installation.md)


Versioning
----------

Qu|Nex suite version: 0.51.2

Submodules:

* connector: 0.50.1
* library: 0.50.2
* nitools: 0.50.0
* niutilities: 0.51.2


Release notes
-------------

* 0.51.2 Removed an MSMAll bug when hcp_icafix_bolds parameter was not provided.
* 0.51.1 Upgraded MSMAll and DeDriftAndResample in order to make it more user-friendly.
* 0.51.0 MSMAll and DeDriftAndResample HCP pipelines, qunex_envstatus upgrade and hcp_suffix harmonization.
* 0.50.4 Fixed a bug that crashed the Qu|Nex suite instead of reporting an error in hcp_PreFS.
* 0.50.2 Support for the HCP ICAFix pipelines, removed some bugs and implemented some minor optimizations.


References
----------

Yang GJ, Murray JD, Repovs G, Cole MW, Savic A, Glasser MF, Pittenger C,
Krystal JH, Wang XJ, Pearlson GD, Glahn DC, Anticevic A. Altered global brain
signal in schizophrenia. Proc Natl Acad Sci U S A. 2014 May 20;111(20):7438-43.
doi: 10.1073/pnas.1405289111. PubMed PMID: 24799682; PubMed Central PMCID:
PMC4034208.


Detailed change log
-------------------

* 0.51.2  [niutilities] Removed an MSMAll bug when hcp_icafix_bolds parameter was not provided.
* 0.51.1  [niutilities] Upgraded MSMAll and DeDriftAndResample in order to make it more user-friendly.
* 0.51.0  [niutilities] Integration of MSMAll and DeDriftAndResample HCP pipelines.
* 0.50.7  [library] qunex_envstatus now reports OS info.
* 0.50.6  [niutilities] Consistent parameter injection notation.
* 0.50.5  [niutilities] Harmonized the use of hcp_suffix.
* 0.50.4  [niutilities] Fixed a bug that crashed the Qu|Nex suite instead of reporting an error in hcp_PreFS.
* 0.50.3  [niutilities] Debug of hcpFS/hcp2 command when --hcp_fs_existing_subject is set to TRUE.
* 0.50.2  [niutilities library] ICAFix ordering of bolds now matches the hcp_icafix_bolds parameter. Removed double slash in logs for MATLABDIR. HCP glob search debug, nicer lookings exceptions in ICAFix. Revised the documentation for the hcp_icafix_bolds parameter.
* 0.50.1  [niutilities] ICAFix regname debug and optimized bold comparison.
* 0.50.0  [nitools library connector] Renamed gmrimage class to nimage and methods names from mri_ to img_.
* 0.49.11 [library niutilities] HCP ICAFix implementation.
* 0.49.10 [niutilities] Made SE selection for BOLD more robust and informative, added option to select by sequence number
* 0.49.9  [qunex] HCPpipelines v4.1.3
* 0.49.8  [connector] Corrected parameter name
* 0.49.7  [library niutilities] Fixed and expanded functionality for PBS scheduler
* 0.49.6  [library] Added reporting of HCPpipelines version
* 0.49.5  [niutilities library] Updated parameters
* 0.49.4  [Qu|Nex] Removal of hcp and qunexaccept subrepositories
* 0.49.3  [niutilities] Separate parameters for use of TOPUP in fMRIVolume, more robust handling of SE files in fMRIVolume
* 0.49.2  [niutilities] A fix to linkOrCopy function, expanded documentation
* 0.49.1  [niutilities] Additional changes to niutilities to match parameter names with HCPpipelines
* 0.49.0  [connector library niutilities] Initial changes to switch from Qu|Nex HCP clone to use of updated HCPpipelines
* 0.48.46 [connector] Fixed ls search for parcellated timeseries in ComputeFunctionalConnecivity
* 0.48.45 [niutilities] Fixed handling of files that go missing during BIDSImport
* 0.48.44 [connector] Fixed XNAT acceptance test bug for processInbox
* 0.48.43 [connector] Fixed mapRawData and processInbox for ingestion of BIDS data
* 0.48.42 [connector] Improvements to acceptance testing and mapRawData
* 0.48.41 [connector, niutilities] More robust acceptance testing and error reporting
* 0.48.40 [connector] Fixed RunTurnkey.sh syntax error
* 0.48.39 [connector] Corrected handling of logging in RunTurnkey.sh
* 0.48.38 [connector,niutilities] Corrected handling of bids_info_status and logging
* 0.48.37 [niutilities] Corrected handling of bids_info_status
* 0.48.36 [niutilities] Improved file locking and parallel execution of BIDSImport, createStudy and createBatch
* 0.48.35 [connector] Edited GBC command flag to --gbc-command not conflict with main input syntax
* 0.48.34 [connector,library] Edited qunex.sh to optimize reading cs-wrapper inputs and upgraded cs-wrapper
* 0.48.33 [connector] Edited RunTurnkey.sh to optimize syncing from XNAT
* 0.48.32 [connector library] Edited RunTurnkey.sh to speed up createBatch sync and deprecated QUNEX_LOGS for XNAT, adjusted cs-wrapper.sh to directly run qunex.sh 
* 0.48.31 [niutilities hcp] Minor fixes and updates
* 0.48.30 [niutilities nitools] Added additional option to g_ExtractGLMVolumes to save effects in text file by parcel for ptseries files
* 0.48.29 [library] Change to qunexContainer to utf8 encode input to stdin
* 0.48.28 [niutilities] Added fileinfo option to BIDSImport
* 0.48.27 [nitools] Corrected corrupt general/CIFTI_BrainModel.mat
* 0.48.26 [nitools] Moved CIFTI_BrainModel.mat from gmri/@gmrimage to general, which fixed the Issue #38
* 0.48.25 [connector] Added bold selection to HCP4 and HCP5 in RunTurnkey
* 0.48.24 [nitools] Fixed Issue #38 Error running g_FindPeaks: unable to find file CIFTI_BrainModel.mat, by changing the path to CIFI_BrainModel.mat
* 0.48.23 [niutilities] Fixed bids_study bug in BIDSImport
* 0.48.22 [library] Fixed a bug in processing 'csessions' parameter in qunexContiner
* 0.48.21 [niutilities nitools, library] Updated BIDSImport documentation, added ability to specify missing values for parcellated2dense, fixed csession parameter
* 0.48.20 [library, niutilities] Added csessions parameter to qunexContainer, resolved bugs in BIDSImport and sortDicom
* 0.48.19 [connector] Enabled working with individual cases from joint inbox in RunTurnkey for DICOM data
* 0.48.18 [connector] Fixed reading of --subjid parameter
* 0.48.17 [niutilities, library, connector] Fixed handling of file lock, dataformat, and qunexContainer PBS scheduling
* 0.48.16 [niutilities] Added more informative handling of errors during full file check
* 0.48.15 [library niutilities] Added support for MSMSulc and running HCP Pipelines in a 'strict' mode requested by HCP
* 0.48.14 [niutilities connector] Added a sessions parameter and functionality to HCPLSImport, added datatype parameter and functionality to RunTurnkey
* 0.48.13 [niutilities] Updated HCPLSImport to work with HCPYA, switched to os.walk for dicomSort
* 0.48.12 [niutilities connector] Added file locking, turned off gmri debugging splash
* 0.48.11 [qunexaccept] Target folders for example data specified more robustly
* 0.48.10 [library] Fixed variable errors in environment for gitqunexstatus function and added scene template for flat maps
* 0.48.9  [connector] Enabled RunTurnkey to work with bids datasets directly, changed createBatch overwrite settiing to append
* 0.48.8  [nitools] fc_ExtractROITimeseriesMasked now saves use information about frames
* 0.48.7  [library] Adjusted qunexContainer to take sessions instead of subjects parameter
* 0.48.6  [niutilities] Made BIDSImport more robust
* 0.48.5  [niutilities qunexaccept] Changed BIDSImport to import behavior with multiple sessions per subject, added dowload links to qunexaccept
* 0.48.4  [niutilities] Added parsing of behavioral data to BIDSImport
* 0.48.3  [library connector] Update to qunexContainer.sh and minor report correction
* 0.48.2  [library] Adjusted function name for container build alias
* 0.48.1  [connector library] Robust handling of BOLDs in RunTurnkey, removed ICAFIX variables from environment
* 0.48.0  [library] Removed ICAFIXDependencies from library for future integration with HCP code
* 0.47.0  [library] Added functions and aliases for Docker and source code build, push, pull and commits
* 0.46.3  [connector niutilities] Edits to allow overwrite of processInbox
* 0.46.2  [qunexaccept] Edits to qunexaccept
* 0.46.1  [library qunexaccept] Edits to qunexaccept
* 0.46.0  [connector library qunexaccept] Added qunexaccept and improved acceptance testing framework, cleaned up library
* 0.45.7  [connector] Fixed the naming error for runQC checks in RunTurnkey and improved mapping and batch file checks
* 0.45.6  [connector] Changed the rsync commands in RunTurnkey to conform with updated HCP pipeline mapping
* 0.45.5  [library connector] Changed the default HCP pipelines to qunex/hcp, improved error catching in RunTurnkey
* 0.45.4  [library] Updated library HCP course batch and mapping files
* 0.45.3  [library] Updated batch templates and XNAT JSONs
* 0.45.2  [library connector] Minor updates to code and XNAT JSONs
* 0.45.1  [connector nitools niutilities] Added createBatch to RunTurnkey, fixed fail check, added g_Parcellated2Dense 
* 0.45.0  [connector library niutilities] Updates to connector qunex.sh, RunTurnkey, addition of BIDS_DICOM_Validate_XNATUpload.sh code and tweaks to environment
* 0.44.7  [niutilites] Updates to in-line documentation
* 0.44.6  [nitools] Changed use of princom to pca
* 0.44.5  [niutilities] Fixed sorting by bold number in createConc
* 0.44.4  [niutilities] Fixed a sessions parameter name bug
* 0.44.3  [niutilities] Updated documentation, added logfolder information to all runExternalForFile calls
* 0.44.2  [niutilities] Extended bold selection options, extended logging functionality, more robust processing of deprecated parameters, bugfixes
* 0.44.1  [niutilities, HCP, library] HCP Pipelines updated to work with legacy datasets, bugfixes, documentation updates, README updates 
* 0.44.0  [connector, niutilities] Updated runTurnkey command and revised documentation.
* 0.43.4  [niutilities] Updated mapIO documentation, toHCPLS is also more flexible.
* 0.43.3  [niutilities] Fixed a None checkup bug
* 0.43.2  [niutilities] Updated mapIO documentation with examples
* 0.43.1  [niutilities] Added initial version of mapIO
* 0.43.0  [qunex] Major update to entire suite to reflect new public beta name change from MNAP to Qu|Nex
* 0.42.0  [niutilities librarry] Major update to niutilities functionality and compliance with latest HCP Pipelines
* 0.41.10 [niutilities] Updated processInbox with nameformat parameter
* 0.41.9  [niutilities] Updated processInbox to work with existing session folders
* 0.41.8  [niutilities, library] Fixed procesInbox parameter issue, moved unset to container section
* 0.41.7  [niutilities] Fixed bold_prefix bold_tail sequence
* 0.41.6  [niutilities] Added pullSequenceNames command
* 0.41.5  [niutilities] Now always reports an error when no file was found to process
* 0.41.4  [niutilities] Changed gmri to qunex in documentation
* 0.41.3  [niutilities] Changed file type for gaterBehavior to .txt and updated documentation
* 0.41.2  [niutilities] Added gatherBehavior command
* 0.41.1  [niutilities] Corrected default for addImageType
* 0.41.0  [niutilities] Changed subjects parameter to sessions, added CommandNull exception
* 0.40.0  [nitools] Renamed matlab subrepository to nitools
* 0.39.9  [nitools] Added extraction of all voxels within a ROI to ExtractROITimeseriesMasked
* 0.39.8  [niutilities] Updated checkFidl PDF printing
* 0.39.7  [niutilities] Updated handling of multiple dcm2niix outputs and sequence naming
* 0.39.6  [niutilities] Extended `processInbox` functionality
* 0.39.5  [niutilities] Made Philips extraneous dicom checking more specific
* 0.39.4  [library] Fixed a value conversion bug in qunexContainer
* 0.39.3  [library] Changed qunexContainer `image` parameter to `container`, fixed a bug in job submission
* 0.39.2  [library] Updated qunexContainer documentation and Docker use
* 0.39.1  [niutilities] fixed minor bugs
* 0.38.23 [niutilities] A number of improvements to robustness and reporting when converting DICOMs and creating subject_hcp.txt files
* 0.38.22 [connector] Made runTurnkey more robust, added copying of bids packages from raw input folder
* 0.38.21 [library] Fixed subjid selection in qunexContainer
* 0.38.20 [library] Fixed envars processing in qunexContainer
* 0.38.19 [library] Updated qunexContainer and qunex_environment.sh
* 0.38.18 [niutilities] Fixed missing colons
* 0.38.17 [niutilities] Now reporting also mapping of bvec and bval files
* 0.38.16 [niutilities] Made creation of BIDS sidecar an explicit request to dcm2niix
* 0.38.15 [connector] Fixed an issue with no session info in BIDS for RunTurnkey XNAT processing
* 0.38.14 [niutilities] Fixed an incomplete BIDSImport fix
* 0.38.13 [connector] Added the option to run multiple parcellations in RunTurnkey
* 0.38.12 [library] Resolved an issue calling commands against Docker container
* 0.38.11 [library, niutilities] Changed qunexSingularity to qunexContainer and extended functionality, fixed a bug in bidsImport
* 0.38.10 [connector] Fixed QCPreprocT1w, QCPreprocT2w names
* 0.38.9  [connector] Added option to remove files older than run
* 0.38.8  [connector hcpmodified] Added removal of stray catalog.xml files and fixed a hardcoded path
* 0.38.7  [connector] Fixed uset BOLDRUNS in RunTurnkey
* 0.38.6  [library connector] Turned off irrelevant octave wornings, added BOLDImages to acceptance testing
* 0.38.5  [library] Added ColeAnticevicNetPartition
* 0.38.4  [connector] Further RunTurnkey.sh bug fix
* 0.38.3  [connector] Further QuNexTurnkeyCleanFunction bug fix
* 0.38.2  [connector] Fixed a bug in QuNexTurnkeyCleanFunction
* 0.38.1  [connector] Tweaked flag name to --turnkeycleanstep in RunTurnkey.sh
* 0.38.0  [connector] Added ability to clean intermediate steps to RunTurnkey.sh with support for hcp4
* 0.37.4  [library] Added R packages environment test
* 0.37.3  [connector] Updated QuNexAcceptanceTest connector command to allow downloading QC results and fixed curl calls in RunTurnkey.sh
* 0.37.2  [niutilities] Fixed and error in hcp4 where no bolds are present
* 0.37.1  [connector library] Updated RunTurnkey to allow smoke test for requested steps and added missing library files
* 0.37.0  [connector] Updated QuNexAcceptanceTest connector command to allow running a loop on sessions
* 0.36.10 [connector niutilities] Added volume and dtseries specification for mapHCPData and changed BOLDPrefix default to "" in RunTurnkey
* 0.36.9  [connector] Corrected reporting of which step is being run in RunTurnkey
* 0.36.8  [connector] Fixed incomplete rsync command for hcp4 & hcp5
* 0.36.7  [connector] Reverted changes to curl calls in QuNexAcceptanceTest
* 0.36.6  [connector] Changed curl calls
* 0.36.5  [hcpmodified] Fixed a typo in c_ras.mat correction in PostFS step
* 0.36.4  [hcpmodified] Added c_ras.mat correction to PostFS step
* 0.36.3  [library] Made conda use and PYTHONPATH conditional on version of Pipelines
* 0.36.2  [library] Reintroduce PYTHONPATH for the correct Docker environment
* 0.36.1  [library] Small cosmetic fixes to the qunex_environment.sh code
* 0.36.0  [connector,qunexcontainer] Small tweaks to Turnkey functionality, removed qunexcontainer submodule
* 0.35.0  [connector] Upgraded acceptance testing and Turnkey functionality
* 0.34.4  [niutilities] Improved processing of existing bids/hcpls sessions
* 0.34.3  [niutilities] Improved frequency encoding and unwarp direction processing
* 0.34.2  [niutilities] Fixed a bug in accessing the relevant spin echo image
* 0.34.1  [library] Improvements to conda management
* 0.34.0  [niutilities, library] Switched to conda python environment management
* 0.33.3  [niutilities] Added cleanup to runPALM and made BIDS/HCPLSImport more robust to bad packages
* 0.33.2  [hcpmodified] Removed forced module loading
* 0.33.1  [niutilities] Added ability to run scripts through qunexSingularity
* 0.33.0  [connector library] Upgraded RunTurnkey for better XNAT API variable compliance
* 0.32.1  [hcpmodified niutilities] Fixed QuNexDev paths and added subjectsfolder as valid extra variable
* 0.32.0  [niutilities library] Added support for HCPPipelines and hcpls datasets
* 0.31.4  [hcpmodified] Bugfix with subjectfolder in fMRIVolume
* 0.31.3  [library connector] Futher improvements in the environment management
* 0.31.2  [library connector] Cleaning up environment settings
* 0.31.1  [niutilities] Added on the fly gzipping of bids files
* 0.31.0  [connector] Initial integration of BIDS mapping in runTunkey through XNAT
* 0.30.3  [library, connector] Corrected handling of HCPPIPEDIR and version command
* 0.30.2  [library] Added pylib to PYTHONPATH
* 0.30.1  [qunex] Added HCPpipelines install to Dockerfile_qunex_suite
* 0.30.0  [niutilities, hcpmodified] Added support for FSLongitudinal
* 0.29.1  [niutilities, library] Added qunexSingularity standalone command, fixed parallelization bug.
* 0.29.0  [connector, library] Major update to environment variables, environment checking and addition of qunex environment function
* 0.28.4  [connector, library] Updated environment settings and reporting, isolated container environment from user environment
* 0.28.3  [niutilities] Added conc_use parameter and functionality to specify absolute vs. relative use of file paths and file names in conc files
* 0.28.2  [qunex] Added FSL 6.. install to Docker container
* 0.28.1  [connector] Fixed bug in QCPreprocessing and added --cnr_maps flag to DWIPreprocPipelineLegacy.sh
* 0.28.0  [niutilities] Added within command BOLD processing parallelization and alternative handling of .conc file for preprocessConc
* 0.27.2  [library] Changed module loads to load defaults R and ggplot2
* 0.27.1  [niutilities] Added runchecks to folder structure
* 0.27.0  [library] Add bin directory for general purpose code. Added example code for running QuNex Singularity via SLURM.
* 0.26.1  [qunex, library] Add PALM112 install to container image and add PALM path to Octave 
* 0.26.0  [connector, hcpmodified, library] Introduced ICA FIX function, fixed bug in probtrackxGPUDense and updated environment script
* 0.25.3  [niutilities] Added the ability for processInbox to process tar archives
* 0.25.2  [nitools] Added an error message to g_PlotBoldTS when running with Octave
* 0.25.1  [niutilities] Added study folder structure test to gmri commands
* 0.25.0  [niutilities] Added dicom deidentification commands
* 0.24.0  [connector, library] Fixed error in QCPreprocessing, renamed and updated XNATUpload.sh, updated environment code.
* 0.23.13 [nitools] Fixed double quotes in preprocessConc
* 0.23.12 [niutilities] Fixed a typo in dicom2niix
* 0.23.11 [niutilities] Added error reporting to readConc and generic command for forming error strings
* 0.23.10 [nitools niutilities] Added additional error checking, made nifti reading more robust, and resolved options string processing bug
* 0.23.9  [connector] Added QuNex folder check in the connectorExec function
* 0.23.8  [connector] Added granularity to rsync commands for pulling data from XNAT within RunTurnkey
* 0.23.7  [connector] Updated QCPreproc to support --hcp_suffix flag for flexible specification of ~/hcp/ subfolders
* 0.23.6  [library] Updated NUMPY module loading version for HPC environment
* 0.23.5  [nitools] Added an option for handling ROI codes between .names file and group/subject masks in mri_ReadROI.
* 0.23.4  [niutilities] Added options parameter to dicom2niix and an option to add ImageType to sequence name
* 0.23.3  [nitools] Added an option for handling event names mismatch between fidl file and model events to g_CreateTaskRegressors.
* 0.23.2  [niutilities] Additional scaffolding for FSLongitudinal
* 0.23.1  [connector] Improved QCnifti documentation
* 0.23.0  [connector, dependencies] Improved QCPreproc to handle scalar and pconn BOLD FC processed data. Dependency: Workbench 1.3 or later.
* 0.22.0  [connector] Added QCnifti command to allow visual inspection of raw NIFTI files in <subjects_folder>/<case>/nii
* 0.21.16 [niutilities] Added raw_data info to subject.txt at BIDSImport
* 0.21.15 [niutilities] Made BIDSImport more robust to BIDS folder structure violations
* 0.21.14 [niutilities] BIDS inbox and archive folders are created if they do not yet exist
* 0.21.13 [niutilities] Updated FS code to delete previous symlinks or folders.
* 0.21.12 [niutilities] Added additional error reporting when running external programms and cleaning FS folder
* 0.21.11 [niutilities] Added tool parameter to specify the tool for nifti conversion
* 0.21.10 [niutilities] Excluded log validity checking for 'return'
* 0.21.9  [niutilities] Added checking for validity of log file directories in scheduler
* 0.21.8  [connector] Improved runTurnkey connector variable handling
* 0.21.7  [niutilities] Added checking for existence od dicom folder in dicom2nii(x) commands
* 0.21.6  [connector] Improved QCPreproc and curl checks for XNAT file downloads
* 0.21.5  [nitools] Fixed an issue with conversion of char to string due to changes in Matlab
* 0.21.4  [niutilities matlab] Minor bug fixes
* 0.21.3  [niutilities] Fixed reporting bug in HCP fMRIVolume and fMRISurface
* 0.21.2  [niutilities] BIDS: updated documentation, changed overwrite options, optimized reporting
* 0.21.1  [connector, niutilities] Updated handling of DTIFIT and BedpostX with new Turnkey support.
* 0.21.0  [niutilities] Initial version of BIDSImport.
* 0.20.28 [niutilities] Added scaffolding for cross session commands, dicm2nii processing of PAR/REC files, saving of real image from fieldmap sequences
* 0.20.27 [niutilities] bold_preprocess now accepts bold numbers, improved bold selection and reporting in HCP commands
* 0.20.26 [niutilties matlab] Deprecated -c help option and added commas to bold_actions parameter.
* 0.20.25 [niutilities] Enabled use of .dscalar and surface only cifti in runPALM
* 0.20.24 [connector] Improved handling of runTurnkey via qunex.sh, fixed recursive turnkey permissions and added curl to push logs
* 0.20.23 [connector] Improved handling of runTurnkey via qunex.sh and removed softlinks for hcp2 via RunTurnkey
* 0.20.22 [niutilities hcpmodified] Enabled use of custom brain masks and cerebellum edits in FS
* 0.20.21 [niutilities matlab] Fixed a reporting bug in preprocessConc and updated BOLD stats and scrub reporting
* 0.20.20 [connector] Misc minor improvements
* 0.20.19 [library] Updated --environment printout to reflect latest changes
* 0.20.18 [connector] Fixed bugs in RunTurnkey and QCProcessing
* 0.20.17 [connector] Minor improvements to BOLDParcellation
* 0.20.16 [connector] Rsync fix in RunTurnkey
* 0.20.15 [connector] Bug fix in RunTurnkey
* 0.20.14 [connector] Bug fix in RunTurnkey
* 0.20.13 [connector] Updates to BOLDParcellate and RunTurnkey
* 0.20.12 [qunex] Edit Dockerfile to compile Octave with 64-bit enabled
* 0.20.11 [connector] Refinements to RunTurnkey
* 0.20.10 [library] Added latest XNAT JSON definitions
* 0.20.9  [connector] Updated output parameters for rsync
* 0.20.8  [connector] Updated input parameters for rsync
* 0.20.7  [connector] RunTurnkey adopted to rsync from whole study folder
* 0.20.6  [hcpmodified] Brought back changes to DWI processing.
* 0.20.5  [connector] Adjusted rsync to only map needed XNAT data.
* 0.20.4  [connector] Added dicom cleanup for xnat
* 0.20.3  [connector] Added mapping of previous XNAT session data
* 0.20.2  [hcpmodified] Rolled back recent edits and moved them to a separate branch
* 0.20.1  [qunex connector] Improved RunTurnkey input handling
* 0.20.0  [qunex connector] Major stable RunTurnkey upgrade to suite
* 0.19.30 [qunex connector library] Updates to RunTurnkey. Added example XNAT json file to library/etc
* 0.19.29 [qunex connector] Updates to RunTurnkey
* 0.19.28 [nitools library] Fixed an ReadROI bug and changed .names files in the library to use relative image paths to ensure transferrability to other systems
* 0.19.27 [niutilities matlab] Removed -nojvm from QuNexMCOMMAND and added parameter checking for PlotBoldTS
* 0.19.26 [nitools] Fixed cleanup bug
* 0.19.25 [qunex connector] Updates to RunTurnkey QCPreproc and log handling
* 0.19.24 [qunex connector] Updates to RunTurnkey
* 0.19.23 [qunex connector] Updates to RunTurnkey
* 0.19.22 [niutilities] More robust handling of parameters
* 0.19.21 [qunex library] Edit Dockerfile_qunex_dep to install CUDA and add paths to environment 
* 0.19.20 [library] Environment to iron out CUDA compatibility
* 0.19.19 [qunex, connector, library, hcpmodified] Further RunTurnkey edits and misc updates across functions to iron out CUDA compatibility
* 0.19.18 [niutilities] Extended final summary reporting, documentation updates
* 0.19.17 [connector] Further RunTurnkey edits
* 0.19.16 [qunex library] Installed libraries for Octave and updated environment script to add path to libraries for container
* 0.19.15 [niutilities] Changed mapHCPData resampling to FSL, fixed bugs
* 0.19.14 [connector] Further RunTurnkey edits
* 0.19.13 [nitools niutilities] Added gmrimages to read an array of images and adopted g_PlotBoldTS to work with octave, getHCPReady checks for mapping file validity
* 0.19.12 [niutilities] Updated log file naming
* 0.19.11 [library] Added XNAT wrapper script to library/etc
* 0.19.10 [qunex] Changed source of environment script in Dockerfile_qunex_suite to system-wide 
* 0.19.9  [connector] Improved createStudy logging within RunTurnkey script
* 0.19.8  [niutilities] Updated createStudy to include comlogs and runlogs folders
* 0.19.7  [connector] Updated BOLDParcellation to allow both fisher-z and r calculations and fixed --useweights bug
* 0.19.6  [nitools] Futher updates to g_PlotBoldTS
* 0.19.5  [nitools] Updated g_PlotBoldTS to allow specification of a colormap
* 0.19.4  [connector] Improved log handling for hcp functions in RunTurnkey code
* 0.19.3  [library] Tweak to gitqunex command to allow more robust adding of files during commit/push
* 0.19.2  [connector] Further improvements to RunTurnkey code and testing on Docker
                      Improved RunTurnkey code and tested on Docker
                      Improved documentation for g_PlotBoldTS.m and variable handling
                      Ingested DWIPreprocPipelineLegacy.sh code into /connector/functions for unification w/other connector code
                      Integrated module checking ino qunex_environment.sh
                      Cleaned up qunex.sh code to read help directly from connector functions to avoid in-line help duplication
* 0.19.1  [connector, matlab, hcpmodified] Cleaned up FS module loading on FreeSurfer.sh to remove local assumotions
* 0.19.0  [niutilities] Improved error catching and status reporting
* 0.18.8  [library] Improved handling of gitqunex functions
* 0.18.7  [qunex] Added .gitignore to master and all subrepositories
* 0.18.6  [niutilities] Unified logging of comlogs and runlogs naming
* 0.18.5  [qunex] Change Docker container image base CentOS 7
* 0.18.4  [qunex] Made improvements to Dockerfiles
* 0.18.3  [niutilities] Made interpretation of subjects parameter more robust
* 0.18.2  [nitools] Updated error exits from matlab code
* 0.18.1  [library] Updated the dependencies handling and .octaverc
* 0.18.0  [qunex connector library] Upgraded Dockerfile specifications, cleaned up connector and added environment specs to library repo
* 0.17.6  [niutilities matlab] Updated matlab functions to be octave friendly, enabled support for hcp_bold_variant, added support for PAR/REC files
* 0.17.5  [library] Had to add MNI152_T1_2mm_brain_mask_dil.nii again
* 0.17.4  [library] Added ungzipped version of brain mask needed for PALM
* 0.17.3  [connector] Updates to turnkey code
* 0.17.2  [connector] Aligned redirects for logging to comply with bash versions 3 and 4.
* 0.17.1  [niutilities] Extended createStudy to include QC scenes
* 0.17.0  [connector] Upgraded QC functionality
* 0.16.6  [library] CARET7DIR points to WORKBENCHDIR to ensure across-system robust functionality
* 0.16.5  [library] Updates to environment code
* 0.16.4  [niutilities connector] Small updates to completion logging
* 0.16.3  [niutilities connector] Fixed a bug in sortDicom and createBatch, resolved realtime logging for python commands
* 0.16.2  [niutilities] Added more robust checking for and reporting of presence of image files in sortDicom
* 0.16.1  [library] Changes to to environment script
* 0.16.0  [qunex] Added Dockerfile for building Docker container
* 0.15.0  [connector] Integrated QuNex turnkey functionality for local servers and XNAT environment
* 0.14.1  [library] Updated environment script and added new atlases and parcelations
* 0.14.0  [connector] Integrated unified execution and logging functionality into connector
* 0.13.17 [niutilities] Added support for par/rec files and improved dicom processing
* 0.13.16 [library] Simplified octave setup and .octaverc
* 0.13.15 [library] Octave and branching environment settings, added a label file
* 0.13.14 [niutilities hcpmodified] Added option for custom brain mask in PreFreeSurfer pipeline
* 0.13.13 [niutilities] Added createConc command
* 0.13.12 [niutilities matlab] Added createList command and enabled comments in lists
* 0.13.11 [nitools niutilities] Optimized logging and updated processing of bad frames in computing seedmaps
* 0.13.10 [nitools] Moved to use specific rather than general cdf and icdf functions to support Octave
* 0.13.9  [nitools] Updated fc_Preprocess to store GLM data
* 0.13.8  [nitools, niutilities] Improved reporting of errors and parameters
* 0.13.7  [nitools, niutilities] Further updates for Octave compatibility, conc and fidl file searc
* 0.13.6  [nitools, library] Updates for Octave compatibility
* 0.13.5  [niutilities] Updated preprocessing log reporting and optimized bold selection
* 0.13.4  [niutilities] Updated inline documentation and defaults related to logging
* 0.13.3  [nitools] Fixed a bug and implemented printing in long format for g_ExtractROIValues
* 0.13.2  [library] Updated qunex environment script for better git handling and checks
* 0.13.1  [nitools] Updated reading of dscalar and pconn files
* 0.13.0  [library] Upgraded environment script
* 0.12.2  [connector, library] Fixed environment issue with FSL, fixed XNATCloudUpload working paths, and made small QCPreproc tweaks
* 0.12.1  [qunex] Updated README files across the suite
* 0.12.0  [library] Upgraded qunex environment script
* 0.11.12 [niutilities] Updated g_dicom.py to use both pydicom v1.x and < v1.
* 0.11.11 [connector] Improved XNATCloudUpload script to more robustly handle input flags
* 0.11.10 [connector] Improved handling of bash redirects
* 0.11.9  [niutilities, connector] Improved handling of batch paramaters options request
* 0.11.8  [niutilities, library] Improved handling of deprecated parameters
* 0.11.7  [connector] Improved handling of paramaters in organizeDicom function
* 0.11.6  [connector] Made QC functionality more robust to BOLD naming variation
* 0.11.5  [niutilities] Updated createStudy to use the new example batch and mapping file names
* 0.11.4  [connector] Edited names of example batch and mapping files to avoid conflicts
* 0.11.3  [connector] QC command exit call fix if BOLD missing
* 0.11.2  [library] Resolved GZIP issue with library atlas files
* 0.11.1  [connector] Resolved QC functionality bug
* 0.11.0  [connector] Upgraded QC functionality to include scene zipping and to allow time stamping and subject info integration into PNGs
* 0.10.24 [niutilities] Fixed subjects definition bug
* 0.10.23 [qunex] Changed licenses to new QuNex name
* 0.10.22 [niutilities] Fixed a bug in variable expansion
* 0.10.21 [niutilities] Added variable expansion to processing of processing parameters
* 0.10.20 [qunex] Improved README.md
* 0.10.19 [connector] Edited XNATCloudUpload.sh script to improve functionality 
* 0.10.18 [niutilities] Fixed a bug and cleaned up runFS code
* 0.10.17 [library] Added the Octave configuration file .octaverc that sets all the paths and packages. (Grace-specific for now)
* 0.10.16 [niutilities] Added support for Philips in getDICOMInfo
* 0.10.15 [connector] Improved probtrackxGPUDense help call to clarify usage
* 0.10.14 [connector] Improved QCPreproc help call to clarify --outpath and --templatefolder flags
* 0.10.13 [niutilities hcpextended] Added version checking and support for new PostFreeSurfer pipeline
* 0.10.12 [nitools] Added computation of RMSD and intensity normalized RMDS across time to mri_Stats
* 0.10.11 [hcpextended] Merged HCPe-QuNex with master
* 0.10.10 [connector] Improved handling of BOLD counts in the QCPreproc function
* 0.10.9  [library] Improved handling of environment checks in qunex_environment.sh code
* 0.10.8  [niutilities] Updated argument list in gmri
* 0.10.7  [niutilities, hcpextended] Added support for HCPe PreFreeSurferPipeline
* 0.10.6  [hcpmodified] Added fslreorient2std step to GenericfMRIVolumeProcessingPipeline to exhibit more robust handling of legacy EPI data
* 0.10.5  [nitools] Fixed a bug in g_FindPeaks that did not print headers in the peaks report
* 0.10.4  [hcpmodified] Edited DistortionCorrectionAndEPIToT1wReg_FLIRTBBRAndFreeSurferBBRbased to allow 12 DOF transform for Scout
* 0.10.3  [nitools] Fixed a bug in reporting frames in glm description
* 0.10.2  [niutilities] Fixed a datetime bug in runThroughScheduler and createStudy
* 0.10.1  [niutilities] Made deduceFolders more robust
* 0.10.0  [niutilities] Enabled automatic paralellization and scheduling of commands
* 0.9.14  [niutilities] Fixed a bug in getHCPReady
* 0.9.13  [connector] Fixed a bug in QCPreproc for DWI frame cleanup
* 0.9.12  [niutilities] Fixed a bug in importInbox
* 0.9.11  [niutilities] Minor chages to documentation and information on matlab callable functions
* 0.9.10  [nitools] Added median as a roi extraction method. 
* 0.9.9   [nitools] gmrimage now supports creation of dtseries and dscalar standard CIFTI images from numeric data
* 0.9.8   [nitools] Added verbose argument to fc_ComputeSeedMaps to fix a bug
* 0.9.7   [niutilities] Minor correction to runPALM command documentation
* 0.9.6   [connector] Fixed hcpdLegacy issue with legacy naming conventions
* 0.9.5   [hcpmodified] Updated `hcpdLegacy` DWI to T1w registration to work w/out fieldmaps
* 0.9.4   [connector, hcpmodified] Fixed `hcpdLegacy` arguments (changed path to subjectsfolder)
* 0.9.3   [nitools] Added documentation to PlotBold functions.
* 0.9.2   [connector] Unified how functions are read such that 1st argument passed is read as a command if no flags are provided
* 0.9.1   [niutilities] Added warning when no subject is identified to be processed and added Matlab as default when QuNexMCOMMAND is not set
* 0.9.0   [niutilities] Added option to run Matlab code through arbitrary Matlab or Octave command through system QuNexMCOMMAND setting
* 0.8.4   [connector] Fixed hcpdLegacy usage function
* 0.8.3   [connector] Updated hcpdLegacy to use correct options when running without fieldmap (needs PEdir, unwarpdir, and echospacing)
* 0.8.2   [connector] Aligned general input flags to conform across the QuNex suite
* 0.8.1   [connector] Improved command parsing to report if command not supported
* 0.8.0   [connector] Added `RsyncBackup` generic command to connector command for server-to-server backups of studies
* 0.7.12  [connector] Updated hcpdLegacy command loop to check if FieldMap is being used, and check subsequent params accordingly
* 0.7.11  [connector, niutilities] Updated inline documentation for `computeBOLDfc` and `hcpd`
* 0.7.10  [niutilities] Deprecated old ambiguous parameter names and added a warning when still used
* 0.7.9   [library] Added template Workbench scene and associated files for CIFTI visualization
* 0.7.8   [niutilities, hcpmodified] Added option to run FreeSurfer with manual control points
* 0.7.7   [connector] Expanded functionality for `QCPreproc` for BOLD to run only SNR via --snronly flag and added -eddyqcstats for motion reporting to `QCPreproc`
* 0.7.6   [connector] Expanded default functionality for `QCPreproc` for BOLD modality to check for presence of subject_hcp.txt file if no BOLDs are specified
* 0.7.5   [niutilities, matlab] Added warning to `getHCPReady` when no matching files found, and fixed bug when no stat file found when reading image
* 0.7.4   [nitools] Fixed a bug in `g_FindPeaks` when presmoothing images with multiple frames and changed the default value if frames is not passed
* 0.7.3   [niutilities] Made processing of subjects parameter more robust to different file names
* 0.7.2   [niutilities] Harmonized parameter names and extended `compileBatch` to take explicit subjects to add
* 0.7.1   [niutilities] Added earlier identification and more detailed reporting of packages already processed
* 0.7.0   [niutilities] Extended `processInbox` to work with directory packets and acquisition logs
* 0.6.9   [niutilities] Added append option to `compileBatch` and changed parameter names, made batch.txt reading more robust
* 0.6.8   [connector, library] Moved the batch parameter templates to library
* 0.6.7   [connector, niutilities, library] Updated front-end data organization functionality
* 0.6.6   [connector, library] Deprecated original connector hcp functions, improved parameter file documentation
* 0.6.5   [niutilities, library] Added parameters.txt and hcpmap.txt templates, which are now added automatically to subjects/specs in `createStudy`
* 0.6.4   [niutilities] Changed subjects.txt to batch.txt throughout and `compileSubjectsTxt` to `compileBatch`
* 0.6.3   [niutilities] Added support for arbitrary inbox folder for processInbox
* 0.6.2   [niutilities] Added timeSeries smoothing functionality to `g_FindPeaks` and corrected a few report generation mistakes
* 0.6.1   [niutilities] Added paramFile option to `compileSubjectsTxt` command
* 0.6.0   [connector] Added `eddyqc` command to the qunex wrapper for diffusion MRI quality control
* 0.5.6   [connector] Edited naming grammar of connector pipeline to 'qunex' 
* 0.5.5   [niutilities,connector] Upgraded high-performance cluster scheduler functionality
* 0.5.4   [connector] Added XNATCloudUpload.sh script to enable automated XNAT ingestion and integration with multi data format support
* 0.5.3   [connector] Updated `dicomorganize` usage
* 0.5.2   [niutilities, connector] Improved scheduler usage to include SLURM
* 0.5.0   [connector] Deprecated functions and added updated scheduler functionality 
* 0.4.1   [connector] Improved usage for `computeboldfc`
* 0.4.0   [connector] Added functionality for `computeboldfc`
* 0.3.0   [connector] Added functionality for thalamic seeding
* 0.2.1   [connector] Expanded usage for `dwiseedtractography`
* 0.2.0   [connector] Added functionality for `dwiseedtractography`
* 0.1.3   [qunex] Expanded usage and bug fixes
* 0.1.2   [qunex] Expanded usage and bug fixes
* 0.1.1   [qunex] Added high performance computing scheduler functionality
* 0.1.0   Initial pre-alpha release.

# README File for MNAP Tools


Background
==========
---

The Multimodal Neuroimaging Analysis Platform (MNAP) Suite of tools integrates several 
packages that support a flexible and extensible framework for data organization, preprocessing, 
quality assurance, and various analyses across neuroimaging modalities. The MNAP suite is 
flexible and can be updated by adding functions developed around its component tools.

The MNAP code is developed and maintained by Alan Anticevic, [Anticevic Lab], Yale 
University of Ljubljana in collaboration with Grega Repovs [Mind and Brain Lab], 
University of Ljubljana.

Installation
===============================
---

### Step 1. Clone all MNAP repos and initiate submodules.

* Clone a branch: `git clone -b <BRANCH> git@bitbucket.org:hidradev/mnaptools.git`
* Initiate submodules from inside cloned repo folder: `git submodule init`
* Pull and update all submodules: `git pull --recurse-submodules && git submodule update --recursive`
* Checkout desired branch for each submodule: `git submodule foreach git checkout <BRANCH>`
* Update submodules to latest commit on the branch: `git submodule foreach git pull origin <BRANCH>`

### Step 2. Configure `niutilities` repository. 

* Make `~/mnaptools/niutilities/gmri` executable
* Install latest version of numpy, pydicom, scipy & nibabel
* (e.g. `pip install numpy pydicom scipy nibabel`)

### Step 3. Configure the environment script by adding the following lines to your .bash_profile.

```
TOOLS=<path_to_folder_with_mnap_suite_and_dependencies>
export TOOLS
source $TOOLS/library/environment/mnap_environment.sh
```

### Step 4. Install all necessary dependencies for full functionality (see below). 

* All relevant dependencies should be inside `$TOOLS` folder.

* The `mnap_environment.sh` script automatically sets assumptions for dependency paths. 
These can be changed by the user. 
* For more info on how to define specific MNAP dependencies paths run:

`mnap --envsetup`

Updating the MNAP Suite
===============================

* To update the main MNAP Suite repository and all the submodules run:

`gitmnap --command="pull" --branch="<branch_name>" --branchpath="<absolute_path_to_mnap_repo_folder>" --submodules="all"`

* For this to work you need to have an active git account and read access across the MNAP Suite.


Usage and command documentation
===============================
---

List of functions can be obtained by running the following command from the terminal: 

* `mnap --help` prints the general help call

The utilities are used through the `mnap` command. The general use form is:

* `mnap --function="<command>" --option="<value>" --option="<value>" ...`

Or the simplified form with command name first omitting the flag:

* `mnap <command> --option="<value>" --option="<value>" ...`

The list of commands and their specific documentation is provided through `mnap`
command itself using the folowing options:

* `mnap ?<command>` prints specific help for the specified command.

Perusing documentation, please note the following conventions used:

* Square brackets `[]` denote an option or argument that is optional. The
  value listed in the brackets is the default value used, if the argument
  is not explicitly specified
* Angle brackets `<>` describe the value that should be provided
* Dashes or "flags", `-` in the documentation define input variables.
* Commands, arguments, and option names are either in small or "camel" case.
* Use descriptions are in regular "sentence" case.
* Option values are usually specified in capital case (e.g. `YES`, `NONE`).


External dependencies
=====================
---
For complete MNAP Suite functionality the following dependencies are needed for the latest stable release:

* All MNAP Suite repositories (https://bitbucket.org/hidradev/mnaptools)
* Connectome Workbench (v1.0 or above; https://www.humanconnectome.org/software/connectome-workbench)
* FSL (v5.0.9 or above with GPU-enabled DWI tools; https://fsl.fmrib.ox.ac.uk/fsl/fslwiki)
* FreeSurfer (v5.3-HCP version for HCP-compatible data; http://ftp.nmr.mgh.harvard.edu/pub/dist/freesurfer/5.3.0-HCP/)
* FreeSurfer (v6.0 or later stable for all other data; https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall)
* MATLAB (v2012b or above with Signal Processing, Statistics and Machine Learning and Image Processing Toolbox)
* FIX ICA (if wishing to run FIX de-noising only; https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FIX/UserGuide)
* PALM: Permutation Analysis of Linear Models (https://github.com/andersonwinkler/PALM) 
* Python (v2.7 or above with numpy, pydicom, scipy & nibabel)
* AFNI: Analysis of Functional NeuroImages (https://github.com/afni/afni) 
* Human Connectome Pipelines modified for MNAP (https://bitbucket.org/mnap/hcpmodified)
* Gradunwarp for HCP workflow (https://github.com/Washington-University/gradunwarp)
* R Statistical Environment with ggplot (https://www.r-project.org/)
* dcm2niix (23-June-2017 release; https://github.com/rordenlab/dcm2niix)

MNAP Versioning
============
---

The MNAP Suite follows the semantic versioning system (https://semver.org/). 
Given a version number MAJOR.MINOR.PATCH, increment the:

* MAJOR version when you make incompatible API changes,
* MINOR version when you add functionality in a backwards-compatible manner, and
* PATCH version when you make backwards-compatible bug fixes.

The version history and change log is listed below. The MNAP version in the current release 
is listed in the VERSION file or can be invoked via the command line by running:

* `mnap --version`

Change Log
============
---

* 0.1 Initial pre-alpha release.
* 0.1.1 [mnaptools] Added high performance computing scheduler functionality
* 0.1.2 [mnaptools] Expanded usage and bug fixes
* 0.1.3 [mnaptools] Expanded usage and bug fixes
* 0.2.0 [connector] Added functionality for `dwiseedtractography`
* 0.2.1 [connector] Expanded usage for `dwiseedtractography`
* 0.3.0 [connector] Added functionality for thalamic seeding
* 0.4.0 [connector] Added functionality for `computeboldfc`
* 0.4.1 [connector] Improved usage for `computeboldfc`
* 0.5.0 [connector] Deprecated functions and added updated scheduler functionality 
* 0.5.2 [niutilities, connector] Improved scheduler usage to include SLURM
* 0.5.3 [connector] Updated `dicomorganize` usage
* 0.5.4 [connector] Added XNATCloudUpload.sh script to enable automated XNAT ingestion and integration with multi data format support
* 0.5.5 [niutilities,connector] Upgraded high-performance cluster scheduler functionality
* 0.5.6 [connector] Edited naming grammar of connector pipeline to 'mnap' 
* 0.6.0 [connector] Added `eddyqc` function to the mnap wrapper for diffusion MRI quality control
* 0.6.1 [niutilities] Added paramFile option to `compileSubjectsTxt` command
* 0.6.2 [niutilities] Added timeSeries smoothing functionality to `g_FindPeaks` and corrected a few report generation mistakes
* 0.6.3 [niutilities] Added support for arbitrary inbox folder for processInbox
* 0.6.4 [niutilities] Changed subjects.txt to batch.txt throughout and `compileSubjectsTxt` to `compileBatch`
* 0.6.5 [niutilities, library] Added parameters.txt and hcpmap.txt templates, which are now added automatically to subjects/specs in `createStudy`
* 0.6.6 [connector, library] Deprecated original connector hcp functions, improved parameter file documentation
* 0.6.7 [connector, niutilities, library] Updated front-end data organization functionality
* 0.6.8 [connector, library] Moved the batch parameter templates to library
* 0.6.9 [niutilities] Added append option to `compileBatch` and changed parameter names, made batch.txt reading more robust
* 0.7.0 [niutilities] Extended `processInbox` to work with directory packets and acquisition logs
* 0.7.1 [niutilities] Added earlier identification and more detailed reporting of packages already processed
* 0.7.2 [niutilities] Harmonized parameter names and extended `compileBatch` to take explicit subjects to add
* 0.7.3 [niutilities] Made processing of subjects parameter more robust to different file names
* 0.7.4 [matlab] Fixed a bug in `g_FindPeaks` when presmoothing images with multiple frames and changed the default value if frames is not passed
* 0.7.5 [niutilities, matlab] Added warning to `getHCPReady` when no matching files found, and fixed bug when no stat file found when reading image
* 0.7.6 [connector] Expanded default functionality for `QCPreproc` for BOLD modality to check for presence of subject_hcp.txt file if no BOLDs are specified
* 0.7.7 [connector] Expanded functionality for `QCPreproc` for BOLD to run only SNR via --snronly flag and added -eddyqcstats for motion reporting to `QCPreproc`
* 0.7.8 [niutilities, hcpmodified] Added option to run FreeSurfer with manual control points
* 0.7.9 [library] Added template Workbench scene and associated files for CIFTI visualization
* 0.7.10 [niutilities] Deprecated old ambiguous parameter names and added a warning when still used
* 0.7.11 [connector, niutilities] Updated inline documentation for `computeBOLDfc` and `hcpd`
* 0.7.12 [connector] Updated hcpdLegacy function loop to check if FieldMap is being used, and check subsequent params accordingly
* 0.8.0 [connector] Added `RsyncBackup` generic function to connector function for server-to-server backups of studies
* 0.8.1 [connector] Improved function parsing to report if function not supported
* 0.8.2 [connector] Aligned general input flags to conform across the MNAP suite
* 0.8.3 [connector] Updated hcpdLegacy to use correct options when running without fieldmap (needs PEdir, unwarpdir, and echospacing)
* 0.8.4 [connector] Fixed hcpdLegacy usage function
* 0.9.0 [niutilities] Added option to run Matlab code through arbitrary Matlab or Octave command through system MNAPMCOMMAND setting
* 0.9.1 [niutilities] Added warning when no subject is identified to be processed and added Matlab as default when MNAPMCOMMAND is not set
* 0.9.2 [connector] Unified how functions are read such that 1st argument passed is read as a function if no flags are provided
* 0.9.3 [matlab] Added documentation to PlotBold functions.
* 0.9.4 [connector, hcpmodified] Fixed `hcpdLegacy` arguments (changed path to subjectsfolder)
* 0.9.5 [hcpmodified] Updated `hcpdLegacy` DWI to T1w registration to work w/out fieldmaps
* 0.9.6 [connector] Fixed hcpdLegacy issue with legacy naming conventions
* 0.9.7 [niutilities] Minor correction to runPALM function documentation
* 0.9.8 [matlab] Added verbose argument to fc_ComputeSeedMaps to fix a bug
* 0.9.9 [matlab] gmrimage now supports creation of dtseries and dscalar standard CIFTI images from numeric data
* 0.9.10 [matlab] Added median as a roi extraction method. 
* 0.9.11 [niutilities] Minor chages to documentation and information on matlab callable functions
* 0.9.12 [niutilities] Fixed a bug in importInbox
* 0.9.13 [connector] Fixed a bug in QCPreproc for DWI frame cleanup
* 0.9.14 [niutilities] Fixed a bug in getHCPReady
* 0.10.0 [niutilities] Enabled automatic paralellization and scheduling of commands
* 0.10.1 [niutilities] Made deduceFolders more robust
* 0.10.2 [niutilities] Fixed a datetime bug in runThroughScheduler and createStudy
* 0.10.3 [matlab] Fixed a bug in reporting frames in glm description
* 0.10.4 [hcpmodified] Edited DistortionCorrectionAndEPIToT1wReg_FLIRTBBRAndFreeSurferBBRbased to allow 12 DOF transform for Scout
* 0.10.5 [matlab] Fixed a bug in g_FindPeaks that did not print headers in the peaks report
* 0.10.6 [hcpmodified] Added fslreorient2std step to GenericfMRIVolumeProcessingPipeline to exhibit more robust handling of legacy EPI data
* 0.10.7 [niutilities, hcpextended] Added support for HCPe PreFreeSurferPipeline
* 0.10.8 [niutilities] Updated argument list in gmri
* 0.10.9 [library] Improved handling of environment checks in mnap_environment.sh code
* 0.10.10 [connector] Improved handling of BOLD counts in the QCPreproc function
* 0.10.11 [hcpextended] Merged HCPe-MNAP with master
* 0.10.12 [matlab] Added computation of RMSD and intensity normalized RMDS across time to mri_Stats
* 0.10.13 [niutilities hcpextended] Added version checking and support for new PostFreeSurfer pipeline
* 0.10.14 [connector] Improved QCPreproc help call to clarify --outpath and --templatefolder flags
* 0.10.15 [connector] Improved probtrackxGPUDense help call to clarify usage
* 0.10.16 [niutilities] Added support for Philips in getDICOMInfo
* 0.10.17 [library] Added the Octave configuration file .octaverc that sets all the paths and packages. (Grace-specific for now)
* 0.10.18 [niutilities] Fixed a bug and cleaned up runFS code
* 0.10.19 [connector] Edited XNATCloudUpload.sh script to improve functionality 
* 0.10.20 [mnaptools] Improved README.md
* 0.10.21 [niutilities] Added variable expansion to processing of processing parameters
* 0.10.22 [niutilities] Fixed a bug in variable expansion
* 0.10.23 [mnaptools] Changed licenses to new MNAP name
* 0.10.24 [niutilities] Fixed subjects definition bug
* 0.11.0 [connector] Upgraded QC functionality to include scene zipping and to allow time stamping and subject info integration into PNGs
* 0.11.1 [connector] Resolved QC functionality bug
* 0.11.2 [library] Resolved GZIP issue with library atlas files
* 0.11.3 [connector] QC function exit call fix if BOLD missing
* 0.11.4 [connector] Edited names of example batch and mapping files to avoid conflicts
* 0.11.5 [niutilities] Updated createStudy to use the new example batch and mapping file names
* 0.11.6 [connector] Made QC functionality more robust to BOLD naming variation
* 0.11.7 [connector] Improved handling of paramaters in organizeDicom function
* 0.11.8 [niutilities, library] Improved handling of deprecated parameters
* 0.11.9 [niutilities, connector] Improved handling of batch paramaters options request
* 0.11.10 [connector] Improved handling of bash redirects
* 0.11.11 [connector] Improved XNATCloudUpload script to more robustly handle input flags
* 0.11.12 [niutilities] Updated g_dicom.py to use both pydicom v1.x and < v1.0
* 0.12.0 [library] Upgraded mnap environment script
* 0.12.1 [mnaptools] Updated README files across the suite
* 0.12.2 [connector, library] Fixed environment issue with FSL, fixed XNATCloudUpload working paths, and made small QCPreproc tweaks
* 0.13.0 [library] Upgraded environment script
* 0.13.1 [matlab] Updated reading of dscalar and pconn files
* 0.13.2 [library] Updated mnap environment script for better git handling and checks
* 0.13.3 [matlab] Fixed a bug and implemented printing in long format for g_ExtractROIValues
* 0.13.4 [niutilities] Updated inline documentation and defaults related to logging
* 0.13.5 [niutilities] Updated preprocessing log reporting and optimized bold selection
* 0.13.6 [matlab, library] Updates for Octave compatibility
* 0.13.7 [matlab, niutilities] Further updates for Octave compatibility, conc and fidl file searc
* 0.13.8 [matlab, niutilities] Improved reporting of errors and parameters
* 0.13.9 [matlab] Updated fc_Preprocess to store GLM data
* 0.13.10 [matlab] Moved to use specific rather than general cdf and icdf functions to support Octave
* 0.13.11 [matlab niutilities] Optimized logging and updated processing of bad frames in computing seedmaps
* 0.13.12 [niutilities matlab] Added createList command and enabled comments in lists
* 0.13.13 [niutilities] Added createConc command
* 0.13.14 [niutilities hcpmodified] Added option for custom brain mask in PreFreeSurfer pipeline
* 0.13.15 [library] Octave and branching environment settings, added a label file
* 0.13.16 [library] Simplified octave setup and .octaverc
* 0.13.17 [niutilities] Added support for par/rec files and improved dicom processing
* 0.14.00 [connector] Integrated unified execution and logging functionality into connector
* 0.14.01 [library] Updated environment script and added new atlases and parcelations
* 0.15.00 [connector] Integrated MNAP turnkey functionality for local servers and XNAT environment
* 0.16.00 [mnaptools] Added Dockerfile for building Docker container
* 0.16.01 [library] Changes to to environment script
* 0.16.02 [niutilities] Added more robust checking for and reporting of presence of image files in sortDicom
* 0.16.03 [niutilities connector] Fixed a bug in sortDicom and createBatch, resolved realtime logging for python commands
* 0.16.04 [niutilities connector] Small updates to completion logging
* 0.16.05 [library] Updates to environment code
* 0.16.06 [library] CARET7DIR points to WORKBENCHDIR to ensure across-system robust functionality
* 0.17.00 [connector] Upgraded QC functionality
* 0.17.01 [niutilities] Extended createStudy to include QC scenes
* 0.17.02 [connector] Aligned redirects for logging to comply with bash versions 3 and 4.
* 0.17.03 [connector] Updates to turnkey code
* 0.17.04 [library] Added ungzipped version of brain mask needed for PALM
* 0.17.05 [library] Had to add MNI152_T1_2mm_brain_mask_dil.nii again
* 0.17.06 [niutilities matlab] Updated matlab functions to be octave friendly, enabled support for hcp_bold_variant, added support for PAR/REC files
* 0.18.00 [mnaptools connector library] Upgraded Dockerfile specifications, cleaned up connector and added environment specs to library repo
* 0.18.01 [library] Updated the dependencies handling and .octaverc
* 0.18.02 [matlab] Updated error exits from matlab code
* 0.18.03 [niutilities] Made interpretation of subjects parameter more robust
* 0.18.04 [mnaptools] Made improvements to Dockerfiles
* 0.18.05 [mnaptools] Change Docker container image base CentOS 7
* 0.18.06 [niutilities] Unified logging of comlogs and runlogs naming
* 0.18.07 [mnaptools] Added .gitignore to master and all subrepositories
* 0.18.08 [library] Improved handling of gitmnap functions
* 0.19.00 [niutilities] Improved error catching and status reporting
* 0.19.01 [connector, matlab, hcpmodified] Cleaned up FS module loading on FreeSurfer.sh to remove local assumotions
                                           Cleaned up mnap.sh code to read help directly from connector functions to avoid in-line help duplication
                                           Integrated module checking ino mnap_environment.sh
                                           Ingested DWIPreprocPipelineLegacy.sh code into /connector/functions for unification w/other connector code
                                           Improved documentation for g_PlotBoldTS.m and variable handling
                                           Improved RunTurnkey code and tested on Docker
* 0.19.02 [connector] Further improvements to RunTurnkey code and testing on Docker
* 0.19.03 [library] Tweak to gitmnap function to allow more robust adding of files during commit/push
* 0.19.04 [connector] Improved log handling for hcp functions in RunTurnkey code
* 0.19.05 [matlab] Updated g_PlotBoldTS to allow specification of a colormap
* 0.19.06 [matlab] Futher updates to g_PlotBoldTS
* 0.19.07 [connector] Updated BOLDParcellation to allow both fisher-z and r calculations and fixed --useweights bug
* 0.19.08 [niutilities] Updated createStudy to include comlogs and runlogs folders
* 0.19.09 [connector] Improved createStudy logging within RunTurnkey script
* 0.19.10 [mnaptools] Changed source of environment script in Dockerfile_mnap_suite to system-wide 
* 0.19.11 [library] Added XNAT wrapper script to library/etc
* 0.19.12 [niutilities] Updated log file naming
* 0.19.13 [matlab niutilities] Added gmrimages to read an array of images and adopted g_PlotBoldTS to work with octave, getHCPReady checks for mapping file validity
* 0.19.14 [connector] Further RunTurnkey edits
* 0.19.15 [niutilities] Changed mapHCPData resampling to FSL, fixed bugs
* 0.19.16 [mnaptools library] Installed libraries for Octave and updated environment script to add path to libraries for container
* 0.19.17 [connector] Further RunTurnkey edits
* 0.19.18 [niutilities] Extended final summary reporting, documentation updates
* 0.19.19 [mnaptools, connector, library, hcpmodified] Further RunTurnkey edits and misc updates across functions to iron out CUDA compatibility
* 0.19.20 [library] Environment to iron out CUDA compatibility
* 0.19.21 [mnaptools library] Edit Dockerfile_mnap_dep to install CUDA and add paths to environment 
* 0.19.22 [niutilities] More robust handling of parameters
* 0.19.23 [mnaptools connector] Updates to RunTurnkey
* 0.19.24 [mnaptools connector] Updates to RunTurnkey
* 0.19.25 [mnaptools connector] Updates to RunTurnkey QCPreproc and log handling
* 0.19.26 [matlab] Fixed cleanup bug
* 0.19.27 [niutilities matlab] Removed -nojvm from MNAPMCOMMAND and added parameter checking for PlotBoldTS
* 0.19.28 [matlab library] Fixed an ReadROI bug and changed .names files in the library to use relative image paths to ensure transferrability to other systems
* 0.19.29 [mnaptools connector] Updates to RunTurnkey
* 0.19.30 [mnaptools connector library] Updates to RunTurnkey. Added example XNAT json file to library/etc
* 0.20.00 [mnaptools connector] Major stable RunTurnkey upgrade to suite
* 0.20.01 [mnaptools connector] Improved RunTurnkey input handling
* 0.20.02 [hcpmodified] Rolled back recent edits and moved them to a separate branch
* 0.20.03 [connector] Added mapping of previous XNAT session data
* 0.20.04 [connector] Added dicom cleanup for xnat
* 0.20.05 [connector] Adjusted rsync to only map needed XNAT data.
* 0.20.06 [hcpmodified] Brought back changes to DWI processing.
* 0.20.07 [connector] RunTurnkey adopted to rsync from whole study folder
* 0.20.08 [connector] Updated input parameters for rsync
* 0.20.09 [connector] Updated output parameters for rsync
* 0.20.10 [library] Added latest XNAT JSON definitions
* 0.20.11 [connector] Refinements to RunTurnkey
* 0.20.12 [mnaptools] Edit Dockerfile to compile Octave with 64-bit enabled
* 0.20.13 [connector] Updates to BOLDParcellate and RunTurnkey
* 0.20.14 [connector] Bug fix in RunTurnkey
* 0.20.15 [connector] Bug fix in RunTurnkey
* 0.20.16 [connector] Rsync fix in RunTurnkey
* 0.20.17 [connector] Minor improvements to BOLDParcellation
* 0.20.18 [connector] Fixed bugs in RunTurnkey and QCProcessing
* 0.20.19 [library] Updated --environment printout to reflect latest changes
* 0.20.20 [connector] Misc minor improvements
* 0.20.21 [niutilities matlab] Fixed a reporting bug in preprocessConc and updated BOLD stats and scrub reporting
* 0.20.22 [niutilities hcpmodified] Enabled use of custom brain masks and cerebellum edits in FS
* 0.20.23 [connector] Improved handling of runTurnkey via mnap.sh and removed softlinks for hcp2 via RunTurnkey
* 0.20.24 [connector] Improved handling of runTurnkey via mnap.sh, fixed recursive turnkey permissions and added curl to push logs
* 0.20.25 [niutilities] Enabled use of .dscalar and surface only cifti in runPALM
* 0.20.26 [niutilties matlab] Deprecated -c help option and added commas to bold_actions parameter.
* 0.20.27 [niutilities] bold_preprocess now accepts bold numbers, improved bold selection and reporting in HCP commands
* 0.20.28 [niutilities] Added scaffolding for cross session commands, dicm2nii processing of PAR/REC files, saving of real image from fieldmap sequences
* 0.21.00 [niutilities] Initial version of BIDSImport.
* 0.21.01 [connector, niutilities] Updated handling of DTIFIT and BedpostX with new Turnkey support.
* 0.21.02 [niutilities] BIDS: updated documentation, changed overwrite options, optimized reporting
* 0.21.03 [niutilities] Fixed reporting bug in HCP fMRIVolume and fMRISurface
* 0.21.04 [niutilities matlab] Minor bug fixes
* 0.21.05 [matlab] Fixed an issue with conversion of char to string due to changes in Matlab
* 0.21.06 [connector] Improved QCPreproc and curl checks for XNAT file downloads
* 0.21.07 [niutilities] Added checking for existence od dicom folder in dicom2nii(x) commands
* 0.21.08 [connector] Improved runTurnkey connector variable handling
* 0.21.09 [niutilities] Added checking for validity of log file directories in scheduler
* 0.21.10 [niutilities] Excluded log validity checking for 'return'
* 0.21.11 [niutilities] Added tool parameter to specify the tool for nifti conversion
* 0.21.12 [niutilities] Added additional error reporting when running external programms and cleaning FS folder
* 0.21.13 [niutilities] Updated FS code to delete previous symlinks or folders.
* 0.21.14 [niutilities] BIDS inbox and archive folders are created if they do not yet exist
* 0.21.15 [niutilities] Made BIDSImport more robust to BIDS folder structure violations
* 0.21.16 [niutilities] Added raw_data info to subject.txt at BIDSImport
* 0.22.00 [connector] Added QCnifti function to allow visual inspection of raw NIFTI files in <subjects_folder>/<case>/nii
* 0.23.00 [connector, dependencies] Improved QCPreproc to handle scalar and pconn BOLD FC processed data. Dependency: Workbench 1.3 or later.
* 0.23.01 [connector] Improved QCnifti documentation
* 0.23.02 [niutilities] Additional scaffolding for FSLongitudinal
* 0.23.03 [matlab] Added an option for handling event names mismatch between fidl file and model events to g_CreateTaskRegressors.
* 0.23.04 [niutilities] Added options parameter to dicom2niix and an option to add ImageType to sequence name
* 0.23.05 [matlab] Added an option for handling ROI codes between .names file and group/subject masks in mri_ReadROI.
* 0.23.06 [library] Updated NUMPY module loading version for HPC environment
* 0.23.07 [connector] Updated QCPreproc to support --hcp_suffix flag for flexible specification of ~/hcp/ subfolders
* 0.23.08 [connector] Added granularity to rsync commands for pulling data from XNAT within RunTurnkey
* 0.23.09 [connector] Added MNAP folder check in the connectorExec function
* 0.23.10 [matlab niutilities] Added additional error checking, made nifti reading more robust, and resolved options string processing bug
* 0.23.11 [niutilities] Added error reporting to readConc and generic function for forming error strings
* 0.23.12 [niutilities] Fixed a typo in dicom2niix
* 0.23.13 [matlab] Fixed double quotes in preprocessConc
* 0.24.00 [connector, library] Fixed error in QCPreprocessing, renamed and updated XNATUpload.sh, updated environment code.
* 0.25.00 [niutilities] Added dicom deidentification commands
* 0.25.01 [niutilities] Added study folder structure test to gmri commands
* 0.25.02 [matlab] Added an error message to g_PlotBoldTS when running with Octave
* 0.25.03 [niutilities] Added the ability for processInbox to process tar archives
* 0.26.00 [connector, hcpmodified, library] Introduced ICA FIX function, fixed bug in probtrackxGPUDense and updated environment script
* 0.26.01 [mnaptools, library] Add PALM112 install to container image and add PALM path to Octave 
* 0.27.00 [library] Add bin directory for general purpose code. Added example code for running MNAP Singularity via SLURM.
* 0.27.01 [niutilities] Added runchecks to folder structure
* 0.27.02 [library] Changed module loads to load defaults R and ggplot2
* 0.28.00 [niutilities] Added within command BOLD processing parallelization and alternative handling of .conc file for preprocessConc
* 0.28.01 [connector] Fixed bug in QCPreprocessing and added --cnr_maps flag to DWIPreprocPipelineLegacy.sh


[Mind and Brain Lab]: http://mblab.si
[Anticevic Lab]: http://anticeviclab.yale.edu

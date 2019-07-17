# README File for Quantitative Neuroimaging Environment & ToolboX (Qu|Nex)

Background
==========
---

The Quantitative Neuroimaging Environment & ToolboX (Qu|Nex) integrates a number of 
modules that support a flexible and extensible framework for data organization, preprocessing, 
quality assurance, and various analytics across neuroimaging modalities. The Qu|Nex suite is 
designed to be flexible and can be developed by adding functions developed around its component tools.

The Qu|Nex code is is co-developed and co-maintained by the 
[Mind and Brain Lab led by Grega Repovs](http://psy.ff.uni-lj.si/mblab/en) 
and the [Anticevic Lab](http://anticeviclab.yale.edu/).


[Website](http://qunex.yale.edu/)
=========

[Wiki](https://bitbucket.org/oriadev/qunex/wiki/Home)
============

[Quick Start](https://bitbucket.org/oriadev/qunex/wiki/Overview/QuickStart.md)
============

Installation from Source
=========================
---

### Step 1. Clone all Qu|Nex repositories and initiate submodules.

* Clone a branch: `git clone -b <BRANCH> git@bitbucket.org:oriadev/qunex.git`
* Initiate submodules from inside cloned repo folder: `git submodule init`
* Pull and update all submodules: `git pull --recurse-submodules && git submodule update --recursive`
* Checkout desired branch for each submodule: `git submodule foreach git checkout <BRANCH>`
* Update submodules to latest commit on the branch: `git submodule foreach git pull origin <BRANCH>`

### Step 2. Configure `niutilities` repository. 

* Make `~/qunex/niutilities/gmri` executable
* Install latest version of numpy, pydicom, scipy & nibabel
* (e.g. `pip install numpy pydicom scipy nibabel`)

### Step 3. Configure the Qu|Nex environment script by adding the following lines to your .bash_profile.

```
TOOLS=<path_to_folder_with_qunex_suite_and_dependencies>
export TOOLS
source $TOOLS/library/environment/qunex_environment.sh
```

### Step 4. Install all necessary dependencies for full Qu|Nex functionality (see below). 

* All relevant dependencies should be inside the `$TOOLS` folder.

* The `qunex_environment.sh` script automatically sets assumptions for dependency paths. These can be changed by the user. 

* For more info on how to define specific Qu|Nex dependencies paths run:

`qunex --envsetup`


Updating the Qu|Nex Suite from Source
======================================
---

* To update the main Qu|Nex repository and all the submodules run:

`gitqunex --command="pull" --branch="<branch_name>" --branchpath="<absolute_path_to_qunex_repo_folder>" --submodules="all"`

* For this to work you need to have an active git account and read access to the main Qu|Nex repository and all submodules.


In-line Usage and documentation
===============================
---

List of functions can be obtained by running the following call from the terminal: 

* `qunex -help` prints the general help call

The general `qunex` call use form is:

`qunex --command="<command_name>" --option="<value>" --option="<value>" ...`

Or the simplified form with command name first omitting the flag:

* `qunex <command_name> --option="<value>" --option="<value>" ...`

The list of commands and their specific documentation is provided by running `qunex`.

To get help for a specific command use the folowing call:

* `qunex ?<command_name>` prints specific help for the specified command.

Perusing documentation, please note the following conventions used:

* Square brackets `[]` denote an option or argument that is optional. The
  value listed in the brackets is the default value used, if the argument
  is not explicitly specified
* Angle brackets `<>` describe the value that should be provided
* Dashes or "flags", `-` in the documentation define input variables.
* Command names, arguments, and option names are either in small or "camel" case.
* Use descriptions are in regular "sentence" case.
* Option values are usually specified in capital case (e.g. `YES`, `NONE`).


External dependencies
=====================
---
For complete Qu|Nex Suite functionality the following dependencies are needed for the latest stable release:

* All Qu|Nex Suite repositories (https://bitbucket.org/oriadev/qunex)
* Connectome Workbench (v1.0 or above; https://www.humanconnectome.org/software/connectome-workbench)
* FSL (v5.0.9 or above with GPU-enabled DWI tools; https://fsl.fmrib.ox.ac.uk/fsl/fslwiki)
* FreeSurfer (v5.3-HCP version for HCP-compatible data; http://ftp.nmr.mgh.harvard.edu/pub/dist/freesurfer/5.3.0-HCP/)
* FreeSurfer (v6.0 or later stable for all other data; https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall)
* MATLAB (v2012b or above with Signal Processing, Statistics and Machine Learning and Image Processing Toolbox)
* FIX ICA (if wishing to run FIX de-noising only; https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FIX/UserGuide)
* PALM: Permutation Analysis of Linear Models (https://github.com/andersonwinkler/PALM) 
* Python (v2.7 or above with numpy, pydicom, scipy & nibabel)
* AFNI: Analysis of Functional NeuroImages (https://github.com/afni/afni) 
* Human Connectome Pipelines modified for Qu|Nex (https://bitbucket.org/oriadev/hcp)
* Gradunwarp for HCP workflow (https://github.com/Washington-University/gradunwarp)
* R Statistical Environment with ggplot (https://www.r-project.org/)
* dcm2niix (23-June-2017 release; https://github.com/rordenlab/dcm2niix)

Qu|Nex Versioning
=================
---

The Qu|Nex Suite follows the semantic versioning system (https://semver.org/). 
Given a version number MAJOR.MINOR.PATCH, increment the:

* MAJOR version when you make incompatible API changes,
* MINOR version when you add functionality in a backwards-compatible manner, and
* PATCH version when you make backwards-compatible bug fixes.

The version history and change log is listed below. The Qu|Nex version in the current release 
is listed in the VERSION file or can be invoked via the command line by running:

* `qunex --version`

Change Log
============
---

* 0.1 Initial pre-alpha release.
* 0.1.1 [qunex] Added high performance computing scheduler functionality
* 0.1.2 [qunex] Expanded usage and bug fixes
* 0.1.3 [qunex] Expanded usage and bug fixes
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
* 0.5.6 [connector] Edited naming grammar of connector pipeline to 'qunex' 
* 0.6.0 [connector] Added `eddyqc` command to the qunex wrapper for diffusion MRI quality control
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
* 0.7.4 [nitools] Fixed a bug in `g_FindPeaks` when presmoothing images with multiple frames and changed the default value if frames is not passed
* 0.7.5 [niutilities, matlab] Added warning to `getHCPReady` when no matching files found, and fixed bug when no stat file found when reading image
* 0.7.6 [connector] Expanded default functionality for `QCPreproc` for BOLD modality to check for presence of subject_hcp.txt file if no BOLDs are specified
* 0.7.7 [connector] Expanded functionality for `QCPreproc` for BOLD to run only SNR via --snronly flag and added -eddyqcstats for motion reporting to `QCPreproc`
* 0.7.8 [niutilities, hcpmodified] Added option to run FreeSurfer with manual control points
* 0.7.9 [library] Added template Workbench scene and associated files for CIFTI visualization
* 0.7.10 [niutilities] Deprecated old ambiguous parameter names and added a warning when still used
* 0.7.11 [connector, niutilities] Updated inline documentation for `computeBOLDfc` and `hcpd`
* 0.7.12 [connector] Updated hcpdLegacy command loop to check if FieldMap is being used, and check subsequent params accordingly
* 0.8.0 [connector] Added `RsyncBackup` generic command to connector command for server-to-server backups of studies
* 0.8.1 [connector] Improved command parsing to report if command not supported
* 0.8.2 [connector] Aligned general input flags to conform across the QuNex suite
* 0.8.3 [connector] Updated hcpdLegacy to use correct options when running without fieldmap (needs PEdir, unwarpdir, and echospacing)
* 0.8.4 [connector] Fixed hcpdLegacy usage function
* 0.9.0 [niutilities] Added option to run Matlab code through arbitrary Matlab or Octave command through system QuNexMCOMMAND setting
* 0.9.1 [niutilities] Added warning when no subject is identified to be processed and added Matlab as default when QuNexMCOMMAND is not set
* 0.9.2 [connector] Unified how functions are read such that 1st argument passed is read as a command if no flags are provided
* 0.9.3 [nitools] Added documentation to PlotBold functions.
* 0.9.4 [connector, hcpmodified] Fixed `hcpdLegacy` arguments (changed path to subjectsfolder)
* 0.9.5 [hcpmodified] Updated `hcpdLegacy` DWI to T1w registration to work w/out fieldmaps
* 0.9.6 [connector] Fixed hcpdLegacy issue with legacy naming conventions
* 0.9.7 [niutilities] Minor correction to runPALM command documentation
* 0.9.8 [nitools] Added verbose argument to fc_ComputeSeedMaps to fix a bug
* 0.9.9 [nitools] gmrimage now supports creation of dtseries and dscalar standard CIFTI images from numeric data
* 0.9.10 [nitools] Added median as a roi extraction method. 
* 0.9.11 [niutilities] Minor chages to documentation and information on matlab callable functions
* 0.9.12 [niutilities] Fixed a bug in importInbox
* 0.9.13 [connector] Fixed a bug in QCPreproc for DWI frame cleanup
* 0.9.14 [niutilities] Fixed a bug in getHCPReady
* 0.10.0 [niutilities] Enabled automatic paralellization and scheduling of commands
* 0.10.1 [niutilities] Made deduceFolders more robust
* 0.10.2 [niutilities] Fixed a datetime bug in runThroughScheduler and createStudy
* 0.10.3 [nitools] Fixed a bug in reporting frames in glm description
* 0.10.4 [hcpmodified] Edited DistortionCorrectionAndEPIToT1wReg_FLIRTBBRAndFreeSurferBBRbased to allow 12 DOF transform for Scout
* 0.10.5 [nitools] Fixed a bug in g_FindPeaks that did not print headers in the peaks report
* 0.10.6 [hcpmodified] Added fslreorient2std step to GenericfMRIVolumeProcessingPipeline to exhibit more robust handling of legacy EPI data
* 0.10.7 [niutilities, hcpextended] Added support for HCPe PreFreeSurferPipeline
* 0.10.8 [niutilities] Updated argument list in gmri
* 0.10.9 [library] Improved handling of environment checks in qunex_environment.sh code
* 0.10.10 [connector] Improved handling of BOLD counts in the QCPreproc function
* 0.10.11 [hcpextended] Merged HCPe-QuNex with master
* 0.10.12 [nitools] Added computation of RMSD and intensity normalized RMDS across time to mri_Stats
* 0.10.13 [niutilities hcpextended] Added version checking and support for new PostFreeSurfer pipeline
* 0.10.14 [connector] Improved QCPreproc help call to clarify --outpath and --templatefolder flags
* 0.10.15 [connector] Improved probtrackxGPUDense help call to clarify usage
* 0.10.16 [niutilities] Added support for Philips in getDICOMInfo
* 0.10.17 [library] Added the Octave configuration file .octaverc that sets all the paths and packages. (Grace-specific for now)
* 0.10.18 [niutilities] Fixed a bug and cleaned up runFS code
* 0.10.19 [connector] Edited XNATCloudUpload.sh script to improve functionality 
* 0.10.20 [qunex] Improved README.md
* 0.10.21 [niutilities] Added variable expansion to processing of processing parameters
* 0.10.22 [niutilities] Fixed a bug in variable expansion
* 0.10.23 [qunex] Changed licenses to new QuNex name
* 0.10.24 [niutilities] Fixed subjects definition bug
* 0.11.0 [connector] Upgraded QC functionality to include scene zipping and to allow time stamping and subject info integration into PNGs
* 0.11.1 [connector] Resolved QC functionality bug
* 0.11.2 [library] Resolved GZIP issue with library atlas files
* 0.11.3 [connector] QC command exit call fix if BOLD missing
* 0.11.4 [connector] Edited names of example batch and mapping files to avoid conflicts
* 0.11.5 [niutilities] Updated createStudy to use the new example batch and mapping file names
* 0.11.6 [connector] Made QC functionality more robust to BOLD naming variation
* 0.11.7 [connector] Improved handling of paramaters in organizeDicom function
* 0.11.8 [niutilities, library] Improved handling of deprecated parameters
* 0.11.9 [niutilities, connector] Improved handling of batch paramaters options request
* 0.11.10 [connector] Improved handling of bash redirects
* 0.11.11 [connector] Improved XNATCloudUpload script to more robustly handle input flags
* 0.11.12 [niutilities] Updated g_dicom.py to use both pydicom v1.x and < v1.0
* 0.12.0 [library] Upgraded qunex environment script
* 0.12.1 [qunex] Updated README files across the suite
* 0.12.2 [connector, library] Fixed environment issue with FSL, fixed XNATCloudUpload working paths, and made small QCPreproc tweaks
* 0.13.0 [library] Upgraded environment script
* 0.13.1 [nitools] Updated reading of dscalar and pconn files
* 0.13.2 [library] Updated qunex environment script for better git handling and checks
* 0.13.3 [nitools] Fixed a bug and implemented printing in long format for g_ExtractROIValues
* 0.13.4 [niutilities] Updated inline documentation and defaults related to logging
* 0.13.5 [niutilities] Updated preprocessing log reporting and optimized bold selection
* 0.13.6 [nitools, library] Updates for Octave compatibility
* 0.13.7 [nitools, niutilities] Further updates for Octave compatibility, conc and fidl file searc
* 0.13.8 [nitools, niutilities] Improved reporting of errors and parameters
* 0.13.9 [nitools] Updated fc_Preprocess to store GLM data
* 0.13.10 [nitools] Moved to use specific rather than general cdf and icdf functions to support Octave
* 0.13.11 [nitools niutilities] Optimized logging and updated processing of bad frames in computing seedmaps
* 0.13.12 [niutilities matlab] Added createList command and enabled comments in lists
* 0.13.13 [niutilities] Added createConc command
* 0.13.14 [niutilities hcpmodified] Added option for custom brain mask in PreFreeSurfer pipeline
* 0.13.15 [library] Octave and branching environment settings, added a label file
* 0.13.16 [library] Simplified octave setup and .octaverc
* 0.13.17 [niutilities] Added support for par/rec files and improved dicom processing
* 0.14.00 [connector] Integrated unified execution and logging functionality into connector
* 0.14.01 [library] Updated environment script and added new atlases and parcelations
* 0.15.00 [connector] Integrated QuNex turnkey functionality for local servers and XNAT environment
* 0.16.00 [qunex] Added Dockerfile for building Docker container
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
* 0.18.00 [qunex connector library] Upgraded Dockerfile specifications, cleaned up connector and added environment specs to library repo
* 0.18.01 [library] Updated the dependencies handling and .octaverc
* 0.18.02 [nitools] Updated error exits from matlab code
* 0.18.03 [niutilities] Made interpretation of subjects parameter more robust
* 0.18.04 [qunex] Made improvements to Dockerfiles
* 0.18.05 [qunex] Change Docker container image base CentOS 7
* 0.18.06 [niutilities] Unified logging of comlogs and runlogs naming
* 0.18.07 [qunex] Added .gitignore to master and all subrepositories
* 0.18.08 [library] Improved handling of gitqunex functions
* 0.19.00 [niutilities] Improved error catching and status reporting
* 0.19.01 [connector, matlab, hcpmodified] Cleaned up FS module loading on FreeSurfer.sh to remove local assumotions
                                           Cleaned up qunex.sh code to read help directly from connector functions to avoid in-line help duplication
                                           Integrated module checking ino qunex_environment.sh
                                           Ingested DWIPreprocPipelineLegacy.sh code into /connector/functions for unification w/other connector code
                                           Improved documentation for g_PlotBoldTS.m and variable handling
                                           Improved RunTurnkey code and tested on Docker
* 0.19.02 [connector] Further improvements to RunTurnkey code and testing on Docker
* 0.19.03 [library] Tweak to gitqunex command to allow more robust adding of files during commit/push
* 0.19.04 [connector] Improved log handling for hcp functions in RunTurnkey code
* 0.19.05 [nitools] Updated g_PlotBoldTS to allow specification of a colormap
* 0.19.06 [nitools] Futher updates to g_PlotBoldTS
* 0.19.07 [connector] Updated BOLDParcellation to allow both fisher-z and r calculations and fixed --useweights bug
* 0.19.08 [niutilities] Updated createStudy to include comlogs and runlogs folders
* 0.19.09 [connector] Improved createStudy logging within RunTurnkey script
* 0.19.10 [qunex] Changed source of environment script in Dockerfile_qunex_suite to system-wide 
* 0.19.11 [library] Added XNAT wrapper script to library/etc
* 0.19.12 [niutilities] Updated log file naming
* 0.19.13 [nitools niutilities] Added gmrimages to read an array of images and adopted g_PlotBoldTS to work with octave, getHCPReady checks for mapping file validity
* 0.19.14 [connector] Further RunTurnkey edits
* 0.19.15 [niutilities] Changed mapHCPData resampling to FSL, fixed bugs
* 0.19.16 [qunex library] Installed libraries for Octave and updated environment script to add path to libraries for container
* 0.19.17 [connector] Further RunTurnkey edits
* 0.19.18 [niutilities] Extended final summary reporting, documentation updates
* 0.19.19 [qunex, connector, library, hcpmodified] Further RunTurnkey edits and misc updates across functions to iron out CUDA compatibility
* 0.19.20 [library] Environment to iron out CUDA compatibility
* 0.19.21 [qunex library] Edit Dockerfile_qunex_dep to install CUDA and add paths to environment 
* 0.19.22 [niutilities] More robust handling of parameters
* 0.19.23 [qunex connector] Updates to RunTurnkey
* 0.19.24 [qunex connector] Updates to RunTurnkey
* 0.19.25 [qunex connector] Updates to RunTurnkey QCPreproc and log handling
* 0.19.26 [nitools] Fixed cleanup bug
* 0.19.27 [niutilities matlab] Removed -nojvm from QuNexMCOMMAND and added parameter checking for PlotBoldTS
* 0.19.28 [nitools library] Fixed an ReadROI bug and changed .names files in the library to use relative image paths to ensure transferrability to other systems
* 0.19.29 [qunex connector] Updates to RunTurnkey
* 0.19.30 [qunex connector library] Updates to RunTurnkey. Added example XNAT json file to library/etc
* 0.20.00 [qunex connector] Major stable RunTurnkey upgrade to suite
* 0.20.01 [qunex connector] Improved RunTurnkey input handling
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
* 0.20.12 [qunex] Edit Dockerfile to compile Octave with 64-bit enabled
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
* 0.20.23 [connector] Improved handling of runTurnkey via qunex.sh and removed softlinks for hcp2 via RunTurnkey
* 0.20.24 [connector] Improved handling of runTurnkey via qunex.sh, fixed recursive turnkey permissions and added curl to push logs
* 0.20.25 [niutilities] Enabled use of .dscalar and surface only cifti in runPALM
* 0.20.26 [niutilties matlab] Deprecated -c help option and added commas to bold_actions parameter.
* 0.20.27 [niutilities] bold_preprocess now accepts bold numbers, improved bold selection and reporting in HCP commands
* 0.20.28 [niutilities] Added scaffolding for cross session commands, dicm2nii processing of PAR/REC files, saving of real image from fieldmap sequences
* 0.21.00 [niutilities] Initial version of BIDSImport.
* 0.21.01 [connector, niutilities] Updated handling of DTIFIT and BedpostX with new Turnkey support.
* 0.21.02 [niutilities] BIDS: updated documentation, changed overwrite options, optimized reporting
* 0.21.03 [niutilities] Fixed reporting bug in HCP fMRIVolume and fMRISurface
* 0.21.04 [niutilities matlab] Minor bug fixes
* 0.21.05 [nitools] Fixed an issue with conversion of char to string due to changes in Matlab
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
* 0.22.00 [connector] Added QCnifti command to allow visual inspection of raw NIFTI files in <subjects_folder>/<case>/nii
* 0.23.00 [connector, dependencies] Improved QCPreproc to handle scalar and pconn BOLD FC processed data. Dependency: Workbench 1.3 or later.
* 0.23.01 [connector] Improved QCnifti documentation
* 0.23.02 [niutilities] Additional scaffolding for FSLongitudinal
* 0.23.03 [nitools] Added an option for handling event names mismatch between fidl file and model events to g_CreateTaskRegressors.
* 0.23.04 [niutilities] Added options parameter to dicom2niix and an option to add ImageType to sequence name
* 0.23.05 [nitools] Added an option for handling ROI codes between .names file and group/subject masks in mri_ReadROI.
* 0.23.06 [library] Updated NUMPY module loading version for HPC environment
* 0.23.07 [connector] Updated QCPreproc to support --hcp_suffix flag for flexible specification of ~/hcp/ subfolders
* 0.23.08 [connector] Added granularity to rsync commands for pulling data from XNAT within RunTurnkey
* 0.23.09 [connector] Added QuNex folder check in the connectorExec function
* 0.23.10 [nitools niutilities] Added additional error checking, made nifti reading more robust, and resolved options string processing bug
* 0.23.11 [niutilities] Added error reporting to readConc and generic command for forming error strings
* 0.23.12 [niutilities] Fixed a typo in dicom2niix
* 0.23.13 [nitools] Fixed double quotes in preprocessConc
* 0.24.00 [connector, library] Fixed error in QCPreprocessing, renamed and updated XNATUpload.sh, updated environment code.
* 0.25.00 [niutilities] Added dicom deidentification commands
* 0.25.01 [niutilities] Added study folder structure test to gmri commands
* 0.25.02 [nitools] Added an error message to g_PlotBoldTS when running with Octave
* 0.25.03 [niutilities] Added the ability for processInbox to process tar archives
* 0.26.00 [connector, hcpmodified, library] Introduced ICA FIX function, fixed bug in probtrackxGPUDense and updated environment script
* 0.26.01 [qunex, library] Add PALM112 install to container image and add PALM path to Octave 
* 0.27.00 [library] Add bin directory for general purpose code. Added example code for running QuNex Singularity via SLURM.
* 0.27.01 [niutilities] Added runchecks to folder structure
* 0.27.02 [library] Changed module loads to load defaults R and ggplot2
* 0.28.00 [niutilities] Added within command BOLD processing parallelization and alternative handling of .conc file for preprocessConc
* 0.28.01 [connector] Fixed bug in QCPreprocessing and added --cnr_maps flag to DWIPreprocPipelineLegacy.sh
* 0.28.02 [qunex] Added FSL 6.0.0 install to Docker container
* 0.28.03 [niutilities] Added conc_use parameter and functionality to specify absolute vs. relative use of file paths and file names in conc files
* 0.28.04 [connector, library] Updated environment settings and reporting, isolated container environment from user environment
* 0.29.00 [connector, library] Major update to environment variables, environment checking and addition of qunex environment function
* 0.29.01 [niutilities, library] Added qunexSingularity standalone command, fixed parallelization bug.
* 0.30.00 [niutilities, hcpmodified] Added support for FSLongitudinal
* 0.30.01 [qunex] Added HCPpipelines install to Dockerfile_qunex_suite
* 0.30.02 [library] Added pylib to PYTHONPATH
* 0.30.03 [library, connector] Corrected handling of HCPPIPEDIR and version command
* 0.31.00 [connector] Initial integration of BIDS mapping in runTunkey through XNAT
* 0.31.01 [niutilities] Added on the fly gzipping of bids files
* 0.31.02 [library connector] Cleaning up environment settings
* 0.31.03 [library connector] Futher improvements in the environment management
* 0.31.04 [hcpmodified] Bugfix with subjectfolder in fMRIVolume
* 0.32.00 [niutilities library] Added support for HCPPipelines and hcpls datasets
* 0.32.01 [hcpmodified niutilities] Fixed QuNexDev paths and added subjectsfolder as valid extra variable
* 0.33.00 [connector library] Upgraded RunTurnkey for better XNAT API variable compliance
* 0.33.01 [niutilities] Added ability to run scripts through qunexSingularity
* 0.33.02 [hcpmodified] Removed forced module loading
* 0.33.03 [niutilities] Added cleanup to runPALM and made BIDS/HCPLSImport more robust to bad packages
* 0.34.00 [niutilities, library] Switched to conda python environment management
* 0.34.01 [library] Improvements to conda management
* 0.34.02 [niutilities] Fixed a bug in accessing the relevant spin echo image
* 0.34.03 [niutilities] Improved frequency encoding and unwarp direction processing
* 0.34.04 [niutilities] Improved processing of existing bids/hcpls sessions
* 0.35.00 [connector] Upgraded acceptance testing and Turnkey functionality
* 0.36.00 [connector,qunexcontainer] Small tweaks to Turnkey functionality, removed qunexcontainer submodule
* 0.36.01 [library] Small cosmetic fixes to the qunex_environment.sh code
* 0.36.02 [library] Reintroduce PYTHONPATH for the correct Docker environment
* 0.36.03 [library] Made conda use and PYTHONPATH conditional on version of Pipelines
* 0.36.04 [hcpmodified] Added c_ras.mat correction to PostFS step
* 0.36.05 [hcpmodified] Fixed a typo in c_ras.mat correction in PostFS step
* 0.36.06 [connector] Changed curl calls
* 0.36.07 [connector] Reverted changes to curl calls in QuNexAcceptanceTest
* 0.36.08 [connector] Fixed incomplete rsync command for hcp4 & hcp5
* 0.36.09 [connector] Corrected reporting of which step is being run in RunTurnkey
* 0.36.10 [connector niutilities] Added volume and dtseries specification for mapHCPData and changed BOLDPrefix default to "" in RunTurnkey
* 0.37.00 [connector] Updated QuNexAcceptanceTest connector command to allow running a loop on sessions
* 0.37.01 [connector library] Updated RunTurnkey to allow smoke test for requested steps and added missing library files
* 0.37.02 [niutilities] Fixed and error in hcp4 where no bolds are present
* 0.37.03 [connector] Updated QuNexAcceptanceTest connector command to allow downloading QC results and fixed curl calls in RunTurnkey.sh
* 0.37.04 [library] Added R packages environment test
* 0.38.00 [connector] Added ability to clean intermediate steps to RunTurnkey.sh with support for hcp4
* 0.38.01 [connector] Tweaked flag name to --turnkeycleanstep in RunTurnkey.sh
* 0.38.02 [connector] Fixed a bug in QuNexTurnkeyCleanFunction
* 0.38.03 [connector] Further QuNexTurnkeyCleanFunction bug fix
* 0.38.04 [connector] Further RunTurnkey.sh bug fix
* 0.38.05 [library] Added ColeAnticevicNetPartition
* 0.38.06 [library connector] Turned off irrelevant octave wornings, added BOLDImages to acceptance testing
* 0.38.07 [connector] Fixed uset BOLDRUNS in RunTurnkey
* 0.38.08 [connector hcpmodified] Added removal of stray catalog.xml files and fixed a hardcoded path
* 0.38.09 [connector] Added option to remove files older than run
* 0.38.10 [connector] Fixed QCPreprocT1w, QCPreprocT2w names
* 0.38.11 [library, niutilities] Changed qunexSingularity to qunexContainer and extended functionality, fixed a bug in bidsImport
* 0.38.12 [library] Resolved an issue calling commands against Docker container
* 0.38.13 [connector] Added the option to run multiple parcellations in RunTurnkey
* 0.38.14 [niutilities] Fixed an incomplete BIDSImport fix
* 0.38.15 [connector] Fixed an issue with no session info in BIDS for RunTurnkey XNAT processing
* 0.38.16 [niutilities] Made creation of BIDS sidecar an explicit request to dcm2niix
* 0.38.17 [niutilities] Now reporting also mapping of bvec and bval files
* 0.38.18 [niutilities] Fixed missing colons
* 0.38.19 [library] Updated qunexContainer and qunex_environment.sh
* 0.38.20 [library] Fixed envars processing in qunexContainer
* 0.38.21 [library] Fixed subjid selection in qunexContainer
* 0.38.22 [connector] Made runTurnkey more robust, added copying of bids packages from raw input folder
* 0.38.23 [niutilities] A number of improvements to robustness and reporting when converting DICOMs and creating subject_hcp.txt files
* 0.39.00 [connector niutilities library] Extended qunexContainer command, added runList command, added qunex symlink to qunex.sh, enabled conda management, changed bold_preprocess to bold, addedbatchTag2Num command
* 0.39.01 [niutilities] fixed minor bugs
* 0.39.02 [library] Updated qunexContainer documentation and Docker use
* 0.39.03 [library] Changed qunexContainer `image` parameter to `container`, fixed a bug in job submission
* 0.39.04 [library] Fixed a value conversion bug in qunexContainer
* 0.39.05 [niutilities] Made Philips extraneous dicom checking more specific
* 0.39.06 [niutilities] Extended `processInbox` functionality
* 0.39.07 [niutilities] Updated handling of multiple dcm2niix outputs and sequence naming
* 0.39.08 [niutilities] Updated checkFidl PDF printing
* 0.39.09 [nitools] Added extraction of all voxels within a ROI to ExtractROITimeseriesMasked
* 0.40.00 [nitools] Renamed matlab subrepository to nitools
* 0.41.00 [niutilities] Changed subjects parameter to sessions, added CommandNull exception
* 0.41.01 [niutilities] Corrected default for addImageType
* 0.41.02 [niutilities] Added gatherBehavior command
* 0.41.03 [niutilities] Changed file type for gaterBehavior to .txt and updated documentation
* 0.41.04 [niutilities] Changed gmri to qunex in documentation
* 0.41.05 [niutilities] Now always reports an error when no file was found to process
* 0.41.06 [niutilities] Added pullSequenceNames command
* 0.41.07 [niutilities] Fixed bold_prefix bold_tail sequence
* 0.41.08 [niutilities, library] Fixed procesInbox parameter issue, moved unset to container section
* 0.41.09 [niutilities] Updated processInbox to work with existing session folders
* 0.41.10 [niutilities] Updated processInbox with nameformat parameter
* 0.42.00 [niutilities librarry] Major update to niutilities functionality and compliance with latest HCP Pipelines
* 0.43.00 [qunex] Major update to entire suite to reflect new public beta name change from MNAP to Qu|Nex
* 0.43.01 [niutilities] Added initial version of mapIO
* 0.43.02 [niutilities] Updated mapIO documentation with examples
* 0.43.03 [niutilities] Fixed a None checkup bug
* 0.43.04 [niutilities] Updated mapIO documentation, toHCPLS is also more flexible.
* 0.44.00 [connector, niutilities] Updated runTurnkey command and revised documentation.
* 0.44.01 [niutilities, HCP, library] HCP Pipelines updated to work with legacy datasets, bugfixes, documentation updates, README updates 
* 0.44.02 [niutilities] Extended bold selection options, extended logging functionality, more robust processing of deprecated parameters, bugfixes
* 0.44.03 [niutilities] Updated documentation, added logfolder information to all runExternalForFile calls
* 0.44.04 [niutilities] Fixed a sessions parameter name bug
* 0.44.05 [niutilities] Fixed sorting by bold number in createConc
* 0.44.06 [nitools] Changed use of princom to pca
* 0.44.07 [niutilites] Updates to in-line documentation
* 0.45.00 [connector library niutilities] Updates to connector qunex.sh, RunTurnkey, addition of BIDS_DICOM_Validate_XNATUpload.sh code and tweaks to environment
* 0.45.01 [connector nitools niutilities] Added createBatch to RunTurnkey, fixed fail check, added g_Parcellated2Dense 
* 0.45.02 [library connector] Minor updates to code and XNAT JSONs
* 0.45.03 [library] Updated batch templates and XNAT JSONs
* 0.45.04 [library] Updated library HCP course batch and mapping files
* 0.45.05 [library connector] Changed the default HCP pipelines to qunex/hcp, improved error catching in RunTurnkey
* 0.45.06 [connector] Changed the rsync commands in RunTurnkey to conform with updated HCP pipeline mapping
* 0.45.07 [connector] Fixed the naming error for runQC checks in RunTurnkey and improved mapping and batch file checks
* 0.46.00 [connector library qunexaccept] Added qunexaccept and improved acceptance testing framework, cleaned up library
* 0.46.01 [library qunexaccept] Edits to qunexaccept
* 0.46.02 [qunexaccept] Edits to qunexaccept
* 0.46.03 [connector niutilities] Edits to allow overwrite of processInbox
* 0.47.00 [library] Added functions and aliases for Docker and source code build, push, pull and commits
* 0.48.00 [library] Removed ICAFIXDependencies from library for future integration with HCP code
* 0.48.01 [connector library] Robust handling of BOLDs in RunTurnkey, removed ICAFIX variables from environment
* 0.48.02 [library] Adjusted function name for container build alias

ICAFIXDependencies

Stable Container Tag Log
========================
---

* docker.io/qunex/qunex_suite:qunex_dev 0.45.05

[Mind and Brain Lab]: http://mblab.si
[Anticevic Lab]: http://anticeviclab.yale.edu

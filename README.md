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

`mnapupdateall --branch="<name_of_branch_you_wish_to_update>"`

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

=======
[Mind and Brain Lab]: http://mblab.si
[Anticevic Lab]: http://anticeviclab.yale.edu

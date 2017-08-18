# README File for MNAP General Analysis Pipeline


Background
==========
---

This is a general purpose Analysis Pipeline (AP) as part of the MNAP package that handles 
flexible directory inputs and subject lists. The pipeline supports data organization, QC, 
preprocessing, various analyses etc. The pipeline is flexible and can be updated by adding 
functions developed around other tools. 

The AP code is developed and maintained by Alan Anticevic, [Anticevic Lab], Yale 
University of Ljubljana in collaboration with Grega Repovs [Mind and Brain Lab], 
University of Ljubljana.

Installation
===============================
---

### Step 1. Clone all MNAP repos (git clone git@bitbucket.org:mnap/mnaptools.git).

### Step 2. Install all necessary dependencies (see below). 

### Step 3. Configure `niutilities` repository. 

* Add `MNAP/niutilities` folder to `$PATH`
* Add `MNAP/niutilities` folder to `$PYTHONPATH`
* Make `MNAP/niutilities/gmri` executable
* Install latest version of numpy, pydicom, scipy & nibabel  
* 			(e.g. `pip install numpy pydicom scipy nibabel `)

### Step 3. Configure the environment script by adding the following lines to your .bash_profile.

	TOOLS=/PATH_TO_MNAP_FOLDER/
	export TOOLS
	source $TOOLS/library/environment/mnap_environment.sh

Usage and command documentation
===============================
---

List of functions can be obtained by running the following command from the terminal: 

* `ap -help` prints the general help call

The utilities are used through the `ap` command. The general use form is:

`ap --function="<command>" --option="<value>" --option="<value>" ...`

The list of commands and their specific documentation is provided through `ap`
command itself using the folowing options:

* `ap ?<command>` prints specific help for the specified command.

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

* All MNAP repositories (git clone git@bitbucket.org:mnap/mnaptools.git)
* Connectome Workbench (v1.0 or above)
* FSL (version 5.0.9 or above with GPU-enabled DWI tools)
* FreeSurfer (5.3 HCP version for HCP-compatible data)
* FreeSurfer (6.0 version for all other data)
* MATLAB (version 2012b or above with Signal Processing, Statistics and Machine Learning and Image Processing Toolbox)
* FIX ICA
* PALM
* Python (version 2.7 or above with numpy, pydicom, scipy & nibabel)
* AFNI
* Gradunwarp (https://github.com/ksubramz/gradunwarp)
* Human Connectome Pipelines for modified MNAP (https://bitbucket.org/mnap/hcpmodified)
* R Statistical Environment with ggplot
* dcm2nii (23-June-2017 release) 


References
==========
---

Yang GJ, Murray JD, Repovs G, Cole MW, Savic A, Glasser MF, Pittenger C,
Krystal JH, Wang XJ, Pearlson GD, Glahn DC, Anticevic A. Altered global brain
signal in schizophrenia. Proc Natl Acad Sci U S A. 2014 May 20;111(20):7438-43.
doi: 10.1073/pnas.1405289111. PubMed PMID: 24799682; PubMed Central PMCID:
PMC4034208.


Change Log
============
---

* 0.1: Initial pre-alpha release with major functionality
* 0.1.1: Initial pre-alpha release with added functionality
* 0.1.2: Initial pre-alpha release with expanded usage
* 0.1.3: Initial pre-alpha release with expanded usage 
* 0.2.0: Initial pre-alpha release with added functionality (dwiseedtractography)
* 0.2.1: Initial pre-alpha release with expanded usage for dwiseedtractography
* 0.3.0: Initial pre-alpha release with added functionality for thalamic seeding
* 0.4.0: Initial pre-alpha release with added functionality (computeboldfc)
* 0.4.1: Initial pre-alpha release with improved usage for computeboldfc
* 0.5.1: Initial pre-alpha release. Deprecated functions: isolatesubcortexrois,probtracksubcortex,pretractography,probtrackxgpucortex,makedensecortex,boldmergenifti,boldmergecifti,nii4dfpconvert,cifti4dfpconvert,dicom2nii; Added updated scheduler functionality 
* 0.5.2: Initial pre-alpha release. Improved scheduler usage to include SLURM
* 0.5.3: Initial pre-alpha release. Updated dcm2nii usage
* 0.5.4: Initial pre-alpha release. Added XNATCloudUpload.sh script to enable automated XNAT ingestion and integration with multi data format support
* 0.5.5: Initial pre-alpha release. Upgraded high-performance cluster scheduler functionality

[Mind and Brain Lab]: http://mblab.si
[Anticevic Lab]: http://anticeviclab.yale.edu

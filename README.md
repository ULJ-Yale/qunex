# README File for MNAP connector tools


Background
==========
---

The `connector` pipeline as part of the MNAP package serves as the overall wrapper for the suite. 
It handles flexible directory inputs and subject lists. The `connector` supports all functionality 
across the MNAP suite, including data organization, QC, preprocessing, various analyses etc. 
The wrapper code is flexible and can be updated by adding functions developed around 
other MNAP suite tools (e.g. `gmri` or `matlab` MNAP packages). 

The MNAP code is developed and maintained by Alan Anticevic, [Anticevic Lab], Yale 
University of Ljubljana in collaboration with Grega Repovs [Mind and Brain Lab], 
University of Ljubljana.

Installation
===============================
---

### Step 1. Clone all MNAP repos and initiate submodules.

* Clone: `git clone git@bitbucket.org/hidradev/mnaptools.git` 
* Initiate submodules from inside cloned repo folder: `git submodule init`
* Pull and update all submodules: `git pull --recurse-submodules && git submodule update --recursive`
* Update submodules to latest commit on origin: `git submodule foreach git pull origin master`

### Step 2. Install all necessary dependencies for full functionality (see below). 

### Step 3. Configure `niutilities` repository. 

* Add `~/mnaptools/niutilities` folder to `$PATH`
* Add `~/mnaptools/niutilities` folder to `$PYTHONPATH`
* Make `~/mnaptools/niutilities/gmri` executable
* Install latest version of numpy, pydicom, scipy & nibabel
* (e.g. `pip install numpy pydicom scipy nibabel `)

### Step 4. Configure the environment script by adding the following lines to your .bash_profile.

	TOOLS=~/mnaptools
	export TOOLS
	source $TOOLS/library/environment/mnap_environment.sh

Usage and command documentation
===============================
---

List of functions can be obtained by running the following command from the terminal: 

* `mnap -help` prints the general help call

The utilities are used through the `mnap` command. The general use form is:

`mnap --function="<command>" --option="<value>" --option="<value>" ...`

The list of commands and their specific documentation is provided through `ap`
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


Specific Example Usage
===============================
---

* Here is a specific example usage based on an MNAP call for sorting incoming DICOMs:


	`mnap --path='<study_folder>' --function='dicomorganize' --subjects='<comma_separarated_list_of_cases>' --scheduler='<name_of_scheduler_and_options>'`
	

External dependencies
=====================
---

* All MNAP repositories for optimal functionality (git clone git@bitbucket.org:mnap/mnaptools.git)
* Connectome Workbench (v1.0 or above)
* FSL (version 5.0.9 or above with GPU-enabled DWI tools)
* FreeSurfer (5.3 HCP version for HCP-compatible data)
* FreeSurfer (6.0 version for all other data)
* MATLAB (version 2012b or above with Signal Processing, Statistics and Machine Learning and Image Processing Toolbox)
* FIX ICA
* PALM
* Python (version 2.7 or above with numpy, pydicom, scipy & nibabel)
* AFNI
* Human Connectome Pipelines modified for MNAP (https://bitbucket.org/mnap/hcpmodified)
* Gradunwarp for HCP workflow (https://github.com/ksubramz/gradunwarp)
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

[Mind and Brain Lab]: http://mblab.si
[Anticevic Lab]: http://anticeviclab.yale.edu

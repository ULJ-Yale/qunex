# README File for MNAP General Neuroimaging Utilities Pipeline

Background
==========
---

MNAP General Neuroimaging Utilities (gMRI) are neuroimaging
preprocessing and analysis utilities that support multiple tasks through a
common user interface, designed to simplify multiple steps of neuroimaging
data preprocessing and analysis from sorting of dicom files to second level
statistical analysis. They often provide a wrapper for efficiently running
other tools and software either on a single computer or computer cluster
by using PBS, SLURM or LSF scheduling.

The utilities make use of and assume that relevant information and data
is provided in a number of file formats, further described below. The utilities
assume and help maintain a specific folder structure, further described below.
A number of utilities depend on external dependencies and make use of data and
data templates provided in a separate library.

The utilities can be used as a self standing toolset, they were, however,
developed to efficiently integrate with a set of Matlab functions, methods and
utilities, and a modified version of HCP (Human Connectome Project)
preprocessing tools. They are best utilized as a part of MNAP (Multimodal
Neuroimaging Analysis Pipeline).

The utilites are developed and maintained by Grega Repovš, [Mind and Brain
Lab], University of Ljubljana in collaboration with the [Anticevic Lab], Yale
University.

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

The utilities are by-defult called through the `mnap` command:

`mnap <command> [option=value] [option=value]`


The utilities can also be called specifically through the `gmri` command. 

This bypasses the `mnap` wrapper and directly calles the python engine. 

The general use form is:

`gmri <command> [option=value] [option=value] ...`


The list of commands and their specific documentation is provided through `gmri`
command itself using the folowing options:

* `gmri -h` prints general help information,
* `gmri -l` lists all the available commands,
* `gmri -o` lists all the available options,
* `gmri -<command>` prints specific help for the specified command.

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


File formats
============
---

* PENDING

Change Log
============
---

* 0.1: Initial pre-alpha release with major functionality
* 0.2: Pre-alpha release with added scheduler functionality

[Mind and Brain Lab]: http://mblab.si
[Anticevic Lab]: http://anticeviclab.yale.edu

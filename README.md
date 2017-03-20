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


External dependencies
=====================
---

* Connectome Workbench (v1.0 or above)
* FSL (version 5.0.6 or above with CUDA libraries)
* FreeSurfer (5.3 HCP version or later)
* MATLAB (version 2012b or above with Signal Processing, Statistics and Machine Learning and Image Processing Toolbox)
* FIX ICA
* PALM
* Python (version 2.7 or above)
* AFNI
* Gradunwarp
* Human Connectome Pipelines (Modified versions for single-band preprocessing)
* R Statistical Environment
* MNAP niutilities Repo
* MNAP matlab Repo


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


[Mind and Brain Lab]: http://mblab.si
[Anticevic Lab]: http://anticeviclab.yale.edu
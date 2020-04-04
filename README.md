# README File for Quantitative Neuroimaging Environment & ToolboX (Qu|Nex)
# Connector Code

Background
==========
---

The `connector` repository as part of the Qu|Nex package serves as the overall wrapper 
for the Qu|Nex suite. It handles flexible directory inputs and subject lists. 
The `connector` code supports various functionality across the Qu|Nex suite, 
including data organization, QC, preprocessing, various analyses etc. 
The wrapper code is flexible and can be updated by adding functions developed around 
other Qu|Nex suite tools (e.g. `niutilities` or `nitools` Qu|Nex submodules).

The Qu|Nex code is is co-developed and co-maintained by the [Mind and Brain Lab led by Grega Repovs](http://psy.ff.uni-lj.si/mblab/en) 
and the [Anticevic Lab](http://anticeviclab.yale.edu/).


Installation
============
---

### See https://bitbucket.org/oriadev/qunex/src/master/README.md


Usage and documentation
=======================
---

List of functions can be obtained by running the following call from the terminal: 

* `qunex -help` prints the general help call

The general `qunex` call use form is:

`qunex --command="<command_name>" --option="<value>" --option="<value>" ...`

Or the simplified form with command name first omitting the flag:

* `qunex <command_name> --option="<value>" --option="<value>" ...`

The list of functions and their specific documentation is provided by running `qunex`.

To get help for a specific command use the following call:

* `qunex ?<command_name>` prints specific help for the specified function.

Perusing documentation, please note the following conventions used:

* Square brackets `[]` denote an option or argument that is optional. The
  value listed in the brackets is the default value used, if the argument
  is not explicitly specified
* Angle brackets `<>` describe the value that should be provided
* Dashes or "flags", `-` in the documentation define input variables.
* command names, arguments, and parameter names are either in small or "camel" case.
* Use descriptions are in regular "sentence" case.
* Option values are usually specified in capital case (e.g. `YES`, `NONE`).


Specific Example Usage
======================
---

* Here is a specific example usage based on an Qu|Nex call for sorting incoming DICOMs:


  `qunex --path='<study_folder>' --function='dicomorganize' --subjects='<comma_separarated_list_of_cases>' --scheduler='<name_of_scheduler_and_options>'`


External dependencies
=====================
---

### See https://bitbucket.org/oriadev/qunex/src/master/README.md


Change log
==========
---

* 0.50.0 Renamed gmrimage class to nimage and methods names from mri_ to img_.
* 0.49.10 Initial submodule versioning.


References
==========
---

Yang GJ, Murray JD, Repovs G, Cole MW, Savic A, Glasser MF, Pittenger C,
Krystal JH, Wang XJ, Pearlson GD, Glahn DC, Anticevic A. Altered global brain
signal in schizophrenia. Proc Natl Acad Sci U S A. 2014 May 20;111(20):7438-43.
doi: 10.1073/pnas.1405289111. PubMed PMID: 24799682; PubMed Central PMCID:
PMC4034208.

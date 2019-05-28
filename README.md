# README File for Quantitative Neuroimaging Environment & ToolboX (Qu|Nex)


Background
==========
---

The `connector` repository as part of the Qu|Nex package serves as the overall wrapper for the suite. 
It handles flexible directory inputs and subject lists. The `connector` supports all functionality 
across the Qu|Nex suite, including data organization, QC, preprocessing, various analyses etc. 
The wrapper code is flexible and can be updated by adding functions developed around 
other Qu|Nex suite tools (e.g. `gmri` or `matlab` Qu|Nex packages). 

The Qu|Nex code is is co-developed and co-maintained by the [Mind and Brain Lab led by Grega Repovs](http://psy.ff.uni-lj.si/mblab/en) 
and the [Anticevic Lab](http://anticeviclab.yale.edu/).

Installation
===============================
---

### See https://bitbucket.org/oriadev/qunex/src/master/README.md


Usage and command documentation
===============================
---

List of functions can be obtained by running the following command from the terminal: 

* `qunex -help` prints the general help call

The utilities are used through the `qunex` command. The general use form is:

`qunex --function="<command>" --option="<value>" --option="<value>" ...`

The list of commands and their specific documentation is provided through `ap`
command itself using the folowing options:

* `qunex ?<command>` prints specific help for the specified command.

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
======================
---

* Here is a specific example usage based on an Qu|Nex call for sorting incoming DICOMs:


	`qunex --path='<study_folder>' --function='dicomorganize' --subjects='<comma_separarated_list_of_cases>' --scheduler='<name_of_scheduler_and_options>'`
	

External dependencies
=====================
---

### See https://bitbucket.org/oriadev/qunex/src/master/README.md


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

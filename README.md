# README File for Quantitative Neuroimaging Environment & ToolboX (Qu|Nex) 
# NeuroImaging Utilities (NIutilities) Code

Background
==========
---

Qu|Nex Neuroimaging Utilities (NIutilities) are neuroimaging preprocessing and 
analysis framework that supports a variety of functions through a common 
user interface, designed to automate multiple steps of neuroimaging
data preprocessing and analysis. Beyond stand-alone functions, NIutilities 
also support the broader Qu|Nex processing and analytic pipeline functionality, 
from from sorting of dicom files to second level statistical analysis. 
NIutilities provide an 'engine' for efficiently running other functions either 
on a single computer or computer cluster by using PBS, SLURM or LSF scheduling.

NIutilities make use of and assume that relevant information and data
is provided in a number of file formats, further described below. The utilities
assume and help maintain a specific folder structure, further described below.
A number of utilities depend on external dependencies and make use of data and
data templates provided in a separate library.

The utilities can be used as a stand-alone toolset. However, the `gmri` utilities
were developed to efficiently integrate with the Qu|Nex suite, as well as with a 
set of native Matlab functions, methods and utilities, and a modified version 
of HCP (Human Connectome Project) preprocessing tools. They are best utilized as 
a part of Qu|Nex (Multimodal Neuroimaging Analysis Platform).

The Qu|Nex code is is co-developed and co-maintained by the 
[Mind and Brain Lab led by Grega Repovs](http://psy.ff.uni-lj.si/mblab/en) 
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

To get help for a specific command use the folowing call:

* `qunex ?<command_name>` prints specific help for the specified function.

The utilities can also be called specifically through the `gmri` call. 

This bypasses the `qunex` wrapper and directly calles the python engine. 

The general use form is:

`gmri <command_name> [option=value] [option=value] ...`

The list of functions and their specific documentation is provided through `gmri`
functions itself using the folowing options:

* `gmri -h` prints general help information,
* `gmri -l` lists all the available functions,
* `gmri -o` lists all the available options,
* `gmri -<command_name>` prints specific help for the specified function.

Perusing documentation, please note the following conventions used:

* Square brackets `[]` denote an option or argument that is optional. The
  value listed in the brackets is the default value used, if the argument
  is not explicitly specified
* Angle brackets `<>` describe the value that should be provided
* Dashes or "flags", `-` in the documentation define input variables.
* command names, arguments, and option names are either in small or "camel" case.
* Use descriptions are in regular "sentence" case.
* Option values are usually specified in capital case (e.g. `YES`, `NONE`).


External dependencies
=====================
---

### See https://bitbucket.org/oriadev/qunex/src/master/README.md


Change log
==========
---

* 0.50.8  hcp_PreFS glob debug.
* 0.50.7  Debug of hcpFS/hcp2 command when --hcp_fs_existing_subject is set to TRUE.
* 0.50.6  Revised the documentation for the hcp_icafix_bolds parameter.
* 0.50.5  HCP glob debug, ICAFix exceptions now look nicer.
* 0.50.4  ICAFix ordering of bolds now matches the hcp_icafix_bolds parameter.
* 0.50.3  ICAFix regname debug.
* 0.50.2  Added filesort option for HCPLSImport.
* 0.50.1  Optimized bold comparison.
* 0.50.0  HCP ICAFix implementation.
* 0.49.10 Initial submodule versioning.

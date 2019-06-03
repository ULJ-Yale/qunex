# README File for Qu|Nex Suite Matlab NeuroImaging Tools (nitools)

Background
==========
---

Qu|Nex Matlab NeuroImaging Tools, (i.e. `nitools`) are preprocessing and 
analysis tools developed in matlab that support multiple 
tasks through a common code base, designed to simplify multiple steps of 
neuroimaging data preprocessing and analysis.

The `nitools` make use of and assume that relevant information and data
is provided in a number of file formats, further described below. The `nitools` 
assume and help maintain a specific folder structure, further described below.
A number of `nitools` depend on external dependencies and make use of data and
data templates provided in a separate library.

The `nitools` can be used as a self standing toolset, they were, however,
developed to efficiently integrate with a set of native Matlab functions, methods and
utilities, and a modified version of HCP (Human Connectome Project)
preprocessing tools. They are best utilized as a part of Qu|Nex (Multimodal
Neuroimaging Analysis Platform).

The `nitools` code is is co-developed and co-maintained by the 
[Mind and Brain Lab led by Grega Repovs](http://psy.ff.uni-lj.si/mblab/en) 
and the [Anticevic Lab](http://anticeviclab.yale.edu/).

Installation
============
---

### See https://bitbucket.org/oriadev/qunex/src/master/README.md

Usage and documentation
===============================
---
The Qu|Nex `nitools` are generally used as core functions across 
various Qu|Nex tools but can be run independently in two ways:

1. 
A number of `nitools` functions provided as part of QuNex/nitools package can be 
run directly through the `qunex` connector wrapper. 
For more information on each command run `qunex ?<command_name>`. 
Arguments can be specified in any order. Arguments that are not provided will 
be passed as empty strings / vectors to be processed with default values. 
Take care to embed vectors in square brackets (e.g. "[1 8 6 12]") and cell arrays 
in curly braces (e.g. "{'DLPFC', 'ACC','FEF'}"). 
In addition, 'saveOutput' argument can be specified to redirect Matlab
output to a file (e.g. "both:command.log" or "stdout:ok.log|stderr:error.log").
2. 
Directly from inside Matlab by calling each function directly.  

To obtain a list of all supported `qunex nitools` commands run:

`qunex nitoolshelp`

The function-specific help and usage is imbedded in the help call for each function.
You can acces this by running `help <function_name>` inside the Matlab terminal. 

External dependencies
=====================
---

### See https://bitbucket.org/oriadev/qunex/src/master/README.md


[Mind and Brain Lab]: http://mblab.si
[Anticevic Lab]: http://anticeviclab.yale.edu

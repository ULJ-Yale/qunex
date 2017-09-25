# README File for MNAP Matlab Analysis Utilities

Background
==========
---

MNAP Matlab Analysis Utilities, (i.e. `matlab`) are neuroimaging
preprocessing and analysis tools developed in matlab that support multiple 
tasks through a common code base, designed to simplify multiple steps of 
neuroimaging data preprocessing and analysis.

The matlab tools make use of and assume that relevant information and data
is provided in a number of file formats, further described below. The matlab tools
assume and help maintain a specific folder structure, further described below.
A number of matlab tools depend on external dependencies and make use of data and
data templates provided in a separate library.

The matlab tools can be used as a self standing toolset, they were, however,
developed to efficiently integrate with a set of Matlab functions, methods and
utilities, and a modified version of HCP (Human Connectome Project)
preprocessing tools. They are best utilized as a part of MNAP (Multimodal
Neuroimaging Analysis Pipeline).

The matlab tools are developed and maintained by Grega Repovš, [Mind and Brain
Lab], University of Ljubljana in collaboration with the [Anticevic Lab], Yale
University.


Usage and command documentation
===============================
---
The MNAP Matlab Analysis Utilities are generally used as core functions across 
various MNAP tools but can be run independently in two ways:

1. 
A number of Matlab functions provided as part of MNAP/matlab package can be 
run directly through the `mnap` connector wrapper. 
For more information on each function run `mnap ?<function name>`. 
Arguments can be specified in any order. Arguments that are not provided will 
be passed as empty strings / vectors to be processed with default values. 
Take care to embed vectors in square brackets (e.g. "[1 8 6 12]") and cell arrays 
in curly braces (e.g. "{'DLPFC', 'ACC','FEF'}"). 
In addition, 'saveOutput' argument can be specified to redirect Matlab
output to a file (e.g. "both:command.log" or "stdout:ok.log|stderr:error.log").
2. 
Also the MNAP Matlab  Analysis Utilities usage can be found imbedded in each 
function by running `help <command>` via the matlab terminal. 

External dependencies
=====================
---

* Connectome Workbench (v1.0 or above)
* MATLAB (version 2012b or above with Signal Processing, Statistics and Machine Learning and Image Processing Toolbox)
* MNAP suite (recommended for seamless functionality) 

Change Log
============
---

* 0.1: Initial pre-alpha release with major functionality

[Mind and Brain Lab]: http://mblab.si
[Anticevic Lab]: http://anticeviclab.yale.edu

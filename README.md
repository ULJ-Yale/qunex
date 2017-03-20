# README File for MNAP Matlab Analysis Code

Background
==========
---

Mind & Brain Lab Matlab Utilities, i.e. matlab are neuroimaging
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

The matlab tools usage can be found imbedded in each function by running:
 
`help <command>` via the matlab terminal. 

External dependencies
=====================
---

* Connectome Workbench (v1.0 or above)
* MATLAB (version 2012b or above with Signal Processing, Statistics and Machine Learning and Image Processing Toolbox)

Change Log
============
---

* 0.1: Initial pre-alpha release with major functionality

[Mind and Brain Lab]: http://mblab.si
[Anticevic Lab]: http://anticeviclab.yale.edu

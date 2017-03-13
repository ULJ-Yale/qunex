# README File for MNAP General Analysis Pipeline


Background
==========

This is a general purpose Analysis Pipeline (AP) as part of the MNAP package that handles 
flexible directory inputs and subject lists. The pipeline supports data organization, QC, 
preprocessing, various analyses etc. The pipeline is flexible and can be updated by adding 
functions developed around other tools. 

The AP code is developed and maintained by Alan Anticevic, [Anticevic Lab], Yale 
University of Ljubljana in collaboration with Grega Repovs [Mind and Brain Lab], 
University of Ljubljana.


External dependencies
=====================

# * Connectome Workbench (v1.0 or above)
# * FSL (version 5.0.6 or above with CUDA libraries)
# * FreeSurfer (5.3 HCP version or later)
# * MATLAB (version 2012b or above with signal processing and imaging toolbox)
# * FIX ICA
# * PALM
# * Python (version 2.7 or above)
# * AFNI
# * Gradunwarp
# * Human Connectome Pipelines (Modified versions for single-band preprocessing)
# * R Statistical Environment


Usage & Descriptions of functions
==================================
List of functions can be obtained by running the following command from the terminal: 

* `ap -help` prints the general help call


References
==========

Yang GJ, Murray JD, Repovs G, Cole MW, Savic A, Glasser MF, Pittenger C,
Krystal JH, Wang XJ, Pearlson GD, Glahn DC, Anticevic A. Altered global brain
signal in schizophrenia. Proc Natl Acad Sci U S A. 2014 May 20;111(20):7438-43.
doi: 10.1073/pnas.1405289111. PubMed PMID: 24799682; PubMed Central PMCID:
PMC4034208.

[Mind and Brain Lab]: http://mblab.si
[Anticevic Lab]: http://anticeviclab.yale.edu
# README File for Qu|Nex NeuroImaging Utilities (niutilities)

Qu|Nex Neuroimaging Utilities (`niutilities`) are neuroimaging preprocessing and 
analysis framework that supports a variety of functions through a common 
user interface, designed to automate multiple steps of neuroimaging
data preprocessing and analysis. Beyond stand-alone functions, `niutilities` 
also support the broader Qu|Nex processing and analytic pipeline functionality, 
from from sorting of dicom files to second level statistical analysis. 
`niutilities` provide an 'engine' for efficiently running other functions either 
on a single computer or computer cluster by using PBS, SLURM or LSF scheduling.

`niutilities` make use of and assume that relevant information and data
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


Quick links
-----------

* [Website](http://qunex.yale.edu/)
* [Qu|Nex Wiki](https://bitbucket.org/oriadev/qunex/wiki/Home)
* [SDK Wiki](https://bitbucket.org/oriadev/qunexsdk/wiki/Home)
* [Qu|Nex quick start](https://bitbucket.org/oriadev/qunex/wiki/Overview/QuickStart.md)
* [Qu|Nex container deployment](https://bitbucket.org/oriadev/qunex/wiki/Overview/Installation.md)
* [Installing from source and dependencies](https://bitbucket.org/oriadev/qunex/wiki/Overview/Installation.md)


Change log
----------

* 0.50.10 Consistent parameter injection notation.
* 0.50.9  Harmonized use of hcp_suffix.
* 0.50.8  hcp_PreFS glob debug.
* 0.50.7  Debug of hcpFS/hcp2 command when --hcp_fs_existing_subject is set to TRUE.
* 0.50.6  Revised the documentation for the hcp_icafix_bolds parameter.
* 0.50.5  HCP glob debug, ICAFix exceptions now look nicer.
* 0.50.4  ICAFix ordering of bolds now matches the hcp_icafix_bolds parameter.
* 0.50.3  ICAFix regname debug.
* 0.50.2  Added filesort option for HCPLSImport.
* 0.50.1  Optimized bold comparison.
* 0.50.0  HCP ICAFix implementation.
* 0.49.10 Initial submodule versioning.


References
----------

Yang GJ, Murray JD, Repovs G, Cole MW, Savic A, Glasser MF, Pittenger C,
Krystal JH, Wang XJ, Pearlson GD, Glahn DC, Anticevic A. Altered global brain
signal in schizophrenia. Proc Natl Acad Sci U S A. 2014 May 20;111(20):7438-43.
doi: 10.1073/pnas.1405289111. PubMed PMID: 24799682; PubMed Central PMCID:
PMC4034208.

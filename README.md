# README File for Qu|Nex Matlab NeuroImaging Tools (nitools)

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

The `nitools` code is is co-developed and co-maintained by:

* [Anticevic Lab, Yale University](http://anticeviclab.yale.edu/),
* [Mind and Brain Lab, University of Ljubljana](http://psy.ff.uni-lj.si/mblab/en),
* [Murray Lab, Yale University](https://medicine.yale.edu/lab/murray/).


Quick links
-----------

* [Website](http://qunex.yale.edu/)
* [Qu|Nex Wiki](https://bitbucket.org/oriadev/qunex/wiki/Home)
* [SDK Wiki](https://bitbucket.org/oriadev/qunexsdk/wiki/Home)
* [Qu|Nex quick start](https://bitbucket.org/oriadev/qunex/wiki/Overview/QuickStart.md)
* [Qu|Nex container deployment](https://bitbucket.org/oriadev/qunex/wiki/Overview/Installation.md)
* [Installing from source and dependencies](https://bitbucket.org/oriadev/qunex/wiki/Overview/Installation.md)


Change Log
----------

* 0.60.1  Full support for hcp_suffix in runQC.
* 0.60.0  Renamed all subject related parameters to session. Pipeline architecture restructure.
* 0.50.1  License and README updates.
* 0.50.0  Renamed gmrimage class to nimage and methods names from mri_ to img_.
* 0.49.10 Initial submodule versioning.


References
----------

Yang GJ, Murray JD, Repovs G, Cole MW, Savic A, Glasser MF, Pittenger C,
Krystal JH, Wang XJ, Pearlson GD, Glahn DC, Anticevic A. Altered global brain
signal in schizophrenia. Proc Natl Acad Sci U S A. 2014 May 20;111(20):7438-43.
doi: 10.1073/pnas.1405289111. PubMed PMID: 24799682; PubMed Central PMCID:
PMC4034208.

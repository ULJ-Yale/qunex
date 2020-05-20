# README File for Qu|Nex Connector Component

The `connector` repository as part of the Qu|Nex package serves as the overall wrapper 
for the Qu|Nex suite. It handles flexible directory inputs and subject lists. 
The `connector` code supports various functionality across the Qu|Nex suite, 
including data organization, QC, preprocessing, various analyses etc. 
The wrapper code is flexible and can be updated by adding functions developed around 
other Qu|Nex suite tools (e.g. `niutilities` or `nitools` Qu|Nex submodules).

The Qu|Nex `connector` code is is co-developed and co-maintained by the:

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

* 0.50.4  License and README updates.
* 0.50.3  Fixed incorrect calling of hcpd.
* 0.50.2  Renamed cores and threads parameters.
* 0.50.1  Harmonized the use of hcp_suffix.
* 0.50.0  Renamed gmrimage class to nimage and methods names from mri_ to img_.
* 0.49.10 Initial submodule versioning.


References
----------

Yang GJ, Murray JD, Repovs G, Cole MW, Savic A, Glasser MF, Pittenger C,
Krystal JH, Wang XJ, Pearlson GD, Glahn DC, Anticevic A. Altered global brain
signal in schizophrenia. Proc Natl Acad Sci U S A. 2014 May 20;111(20):7438-43.
doi: 10.1073/pnas.1405289111. PubMed PMID: 24799682; PubMed Central PMCID:
PMC4034208.

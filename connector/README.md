# README File for Qu|Nex Connector Component

The `connector` repository as part of the Qu|Nex package serves as the overall wrapper 
for the Qu|Nex suite. It handles flexible directory inputs and session lists. 
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

* 0.63.1  Fixed the issue where some QuNex functions did not create a runlog or a comlog.
* 0.63.0  Added support for processing post mortem macaque images.
* 0.62.10 BOLDcomputeFC now reports errors in a QuNex compliant fashion.
* 0.62.9  qunex.sh patched to include pushd and popd functionality to preserve initial user working directory.
* 0.62.8  runTurnkey patch to include T2 to rsync command for hcp2 step.
* 0.62.7  Bolds parameter is now properly passed to all commands.
* 0.62.6  Robust parsing of the hcp_filename parameter.
* 0.62.5  Consistent naming of all DWI related commands, documentation polish to for consistencty purposes across the whole suite.
* 0.62.4  Renamed filename to hcp_filename in SetupHCP.
* 0.62.3  RunQC now works both on bold numbers and names, RunQC no longer crashes if there are more than 10 bolds.
* 0.62.2  Added DWI prefix to all DWI related Qu|Nex commands.
* 0.62.1  Qunex commands ran through the scheduler can now execute bash commands prior to 
* 0.62.0  Documentation rework.
* 0.61.6  Added CUDA 9.1 bedpostx support.
* 0.61.5  Fixed a bug where Qu|nex would create unnecessary folders.
* 0.61.4  When running single Qu|Nex commands warnings would erroneously state that we are running throgh RunTurnkey.
* 0.61.3  Added bedpostx and probtrackx CUDA 9.1 binaries.
* 0.61.2  Added some additional printouts to runQC for user friendliness.
* 0.61.1  runQC now works properly when overwrite is set to no.
* 0.61.0  Implementation of bug fixes across connector and pipeline restructure back-compatibility
* 0.60.1  Full support for hcp_suffix in runQC.
* 0.60.0  Renamed all subject related parameters to session. Pipeline architecture restructure.
* 0.50.5  Splash screen update, uploaded gpu_binaries.
* 0.50.4  License and README updates.
* 0.50.3  Fixed incorrect calling of hcpd.
* 0.50.2  Renamed cores and threads parameters.
* 0.50.1  Harmonized the use of hcp_suffix.
* 0.50.0  Renamed gmrimage class to nimage and methods names from mri_ to img_.
* 0.49.10 Initial submodule versioning.


References
----------

* Yang GJ, Murray JD, Repovs G, Cole MW, Savic A, Glasser MF, Pittenger C,
Krystal JH, Wang XJ, Pearlson GD, Glahn DC, Anticevic A. Altered global brain
signal in schizophrenia. Proc Natl Acad Sci U S A. 2014 May 20;111(20):7438-43.
doi: 10.1073/pnas.1405289111. PubMed PMID: 24799682; PubMed Central PMCID:
PMC4034208.

* bedpostx and probtrackx CUDA binaries included in this repository were
developed by: Hernandez-Fernandez M, Reguly I, Jbabdi S, Giles M, Smith S,
Sotiropoulos SN. Using GPUs to accelerate computational diffusion MRI: From 
icrostructure estimation to tractography and connectomes. NeuroImage
2019;188:598-615. doi: 10.1016/j.neuroimage.2018.12.015.


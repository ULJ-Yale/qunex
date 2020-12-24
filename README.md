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

The `niutilities` code is is co-developed and co-maintained by:

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


Change log
----------

* 0.62.9  Updated importHCP.txt for HCPYA support, hcpDiffusion now warns users when using legacy parameter names.
* 0.62.8  MSMAll now properly executes DeDriftAndResample in case of a multi-run HCP ICAFix.
* 0.62.7  Bolds parameter is now properly passed to all commands.
* 0.62.6  The order of images in the hcpDiffusion command is now correct.
* 0.62.5  gmri documentation polish for consistency across the whole suite.
* 0.62.4  Renamed filename to hcp_filename in SetupHCP.
* 0.62.3  batchTag2NameKey optimizations and documentation update.
* 0.62.2  Fixed a bug with the bash parameter for specifying bash commands when scheduling.
* 0.62.1  SLURM scheduling now supports flags (parameters without values).
* 0.62.0  Documentation rework.
* 0.61.23 hcp_bold_unwarpdir support for HCPYA.
* 0.61.22 Outgoing command call is not printed if there is an error earlier in execution.
* 0.61.21 Added correction of invalid movement regressor files upon mapHCPData.
* 0.61.20 Fixed a bug in MSMAll error reporting.
* 0.61.19 Improved HCPYA dataset support by ensuring the import of SE-FM and FM images.
* 0.61.18 Added a missing import to ge_HCP, hcp_dwi_selectbestb0 is now a flag.
* 0.61.17 Robust parsing of integer parameters in HCP processing commands.
* 0.61.16 HCP Diffusion now uses pipe (|) as the extra eddy args separator.
* 0.61.15 On some systems HCP Pipelines had trouble injecting numbers into outgoing command calls.
* 0.61.14 Beautified and debugged extra-eddy-arg printout in HCP Diffusion pipeline.
* 0.61.13 Added new parameters (hcp_dwi_phasepos, hcp_dwi_cudaversion, hcp_dwi_nogpu) to HCP Diffusion pipeline.
* 0.61.12 Removed a bug with standard filename in ICAFix.
* 0.61.11 Removed race conditions in createBOLDBrainMasks and mapHCPData.
* 0.61.10 Added support for running bash commands before the qunex command inside the compute node when scheduling.
* 0.61.9  HCP Diffusion pipeline upgrades.
* 0.61.8  All DeDriftAndResample parameters are now properly passed to HCP pipelines.
* 0.61.7  Added additional parameters to DeDriftAndResample.
* 0.61.6  Removed a bug where the topupconfig parameter was not properly set when running hcp4.
* 0.61.5  Fixed checking of dc correction parameters in fMRIVolume.
* 0.61.4  Added support for multiple nested folders within BIDS study level directories.
* 0.61.3  Added import of ast library to g_bids.py.
* 0.61.2  Inclusion of sequence information from JSON files when running importDICOM and dicom2niix is now optional.
* 0.61.1  Replaced the old variable name sfile with sourcefile in createSessionInfo.
* 0.61.0  Implementation of bug fixes across connector and pipeline restructure back-compatibility.
* 0.60.1  Full support for hcp_suffix in runQC.
* 0.60.0  Renamed all subject related parameters to session. Pipeline architecture restructure.
* 0.51.10 External command calls are now printed in stdout and at the beginning of comlogs.
* 0.51.9  Consistent jobname in scheduling between qunex and qunexContainer.
* 0.51.8  License and README updates.
* 0.51.7  Fixed reporting when hcp_fs_existing_session is true.
* 0.51.6  Changed hcpsuffix to hcp_suffix throughout.
* 0.51.5  Updated in-line documentation.
* 0.51.4  Renamed cores and threads parameters.
* 0.51.3  Changed dcm2niix ERROR to WARNING, removed full file checking documentation.
* 0.51.2  Removed an MSMAll bug when hcp_icafix_bolds parameter was not provided.
* 0.51.1  Upgraded MSMAll and DeDriftAndResample in order to make it more user-friendly.
* 0.51.0  Integration of MSMAll and DeDriftAndResample HCP pipelines.
* 0.50.11 Updated extraction of PAR file id.
* 0.50.10 Consistent parameter injection notation.
* 0.50.9  Harmonized use of hcp_suffix.
* 0.50.8  hcp_PreFS glob debug.
* 0.50.7  Debug of hcpFS/hcp2 command when --hcp_fs_existing_session is set to TRUE.
* 0.50.6  Revised the documentation for the hcp_icafix_bolds parameter.
* 0.50.5  HCP glob debug, ICAFix exceptions now look nicer.
* 0.50.4  ICAFix ordering of bolds now matches the hcp_icafix_bolds parameter.
* 0.50.3  ICAFix regname debug.
* 0.50.2  Added filesort option for importHCP.
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

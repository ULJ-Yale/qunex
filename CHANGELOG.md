<!--
SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>

SPDX-License-Identifier: GPL-3.0-or-later
-->

# Change Log

## 0.97.3

* Fixed the parametrization of `hcp_icafix` and `hcp_msmall` to reflect the latest changes in HCP Pipelines.

## 0.97.2

* Fixed the default CUDA version for `hcp_diffusion`, required by the latest FSL version.

## 0.97.1

* In `fc_preprocess`, when motion was not included as a regressor, `.mov` files were not read, but the data was still referenced later in the code. This interaction is now resolved.
* Fixed a bug where `fc_process` could sometime create an invalid GLM table.
* Fixed a bug where FSL's `imrm` did not remove some images which caused `hcp_diffusion` to crash.

## 0.97.0

* Improved the documentation at several locations.
* Added the ability to create slice timing files when preparing data for HCP pipelines using the setup_hcp command.
* Upgraded FSL to 6.0.6.2.
* Optimization of parameter parsing for hcp_icafix.
* Fixed the use of TR parameter in some cases.
* Consistent scheduler parameter specification in documentation.
* import_hcp can now import DWI beyond dir98 and dir99.

## 0.96.2

* Fixed a bug where the phase enconding direction was not set correctly in `hcp_diffusion`.

## 0.96.1

* Default value for the model parameter of `dwi_bepostx_gpu` is is reversed to 2, which is the correct FSL default.

## 0.96.0

* Added the ability to generate predicted timeseries and residual timeseries for arbitrary set of regressors used in the GLM analyses.
* Updated HCP Pipelines to v4.7.0.
* Default value for the model parameter of `dwi_bepostx_gpu` is now 3. This is also the FSL's default and by far the most commonly used value in practice.
* Fixed a bug where some analysis commands that do not need hcp data would not work if hcp folder is not present.

## 0.95.3

* Fixed a bug with setting the default value of `hcp_bold_topupconfig`.
* Added support for `hcp_icafix_fallbackthreshold` in `hcp_icafix`.

## 0.95.2

* Fixed a path in pconn template `run_qc` BOLD.
* Added a new parameter to MSMAll (`hcp_msmall_myelin_target`).

## 0.95.1

* Fixed a bug with positional parameters in gmri.
* `dwi_eddy_qc` input parameters are now parsed properly.

## 0.95.0

* Parameter `pedir` is now named consistently across the whole suite.
* Fixed a bug where `_AP/PA` tags in `setup_hcp` were sometimes missing.
* You can now check which data will be imported with `import_dicom` by using the `--test` flag.
* `qunex_container` now has the `cuda_path` parameter for binding external cuda libraries.
* Fixed sorting of imported data in `import_bids`.
* Updated HCP Pipelines to the latest version.

## 0.94.14

* dwi_pre_tractography now works when continuing from dwi_legacy_gpu.
* Removed the scanner parameter from dwi_legacy_gpu as it was redundant.
* HCP PreFreeSurfer's fnirtconfig can be now customized through the hcp_prefs_fnirtconfig parameter.

## 0.94.13

* hcp_asl now properly reads SE pairs. 

## 0.94.12

* run_qc will now work if you changed the name of session_hcp.txt during the file preparation.
* Fixed permission for compiled FSL CUDA binaries.
* hcp_asl default parameters are now setup more robustly.

## 0.94.11

* Fixed setting of the default training files in ICAFix.
* Added the ability to set custom templates in HCP PreFreeSurfer.
* Improved stability of qunex_container.
* Fixed a bug in BOLD run_qc when overwrite option was used.

## 0.94.10

* Removed some warnings from the MATLAB code.

## 0.94.9

* Updated the version of HCP Pipelines.

## 0.94.8

* BedpostX support for `dwi_legacy_gpu`.
* Improved parsing of BOLDs in the `hcp_msmall` command.

## 0.94.7

* Fixed a bug where `overwrite` was not used with `qunex_container`.

## 0.94.6

* Fixed a backwards compatibility bug in `qunex_container`.

## 0.94.5

* Missing `EDDYCUDADIR` was reported erroneously inside the container.
* `qunex_container` with PBS now supports the `select` flag.
* Fixed a backwards compatibility and a stability issue with `qunex_continer`.
* Update FSL verision in the container.
* DICOM deidentification pipeline is now working again.
* `import_bids` should now import ASL data.

## 0.94.4

* Fixed a bug in qunex_container that caused it to crash if sessions or batchfile were not provided.
* Fixed a bug in bruker_to_dicom that caused the command to crash.

## 0.94.3

* Removed a bug that caused run_turnkey to crash.

## 0.94.2

* Fixed a container bug where the sessions and sessionids parameters were not parsed correctly.

## 0.94.1

* Added the ability to define custom numbering in mapping files.

## 0.94.0

* Fixed a bug in `extract_roi` that caused the command to crash in some cases.
* Improved and optimised the mapping file logic.
* Logic for filtering sessions is now consistent across the whole suite.
* Added mice preprocessing pipelines. 

## 0.93.8

* Fixed writing and reading whitespaces to/from sequence specific infomration.
* Help for commands can be now accessed by using the `--help` flag.

## 0.93.6

* Fixed a bug in the `qunex_container` script that prevented it from running without using a scheduler.

## 0.93.5

* Improved flexibility of GLM analyses.
* Processing of Philips PAR files is now more robust.
* Fixed a bug with the `hcp_task_confound` parameter.
* You can now process DWIs that do not have a matching pos/neg pair with `hcp_diffusion`.
* Improved stability, scheduling and documentation of the suite.

## 0.93.4

* The default normalization for assumed HRF modelling has changed from 'run', which normalizes assumed regressors to amplitude 1 within each run separately, to 'uni', which normalizes regressors universally to HRF area-under-the-curve = 1.

## 0.93.3

* Improved several aspects of parallelism inside QuNex.
* Added SLURM job array support.
* Added additional information to several command's documentation.
* You can now generate predicted timeseries and residual timeseries for arbitrary set of regressors used in the GLM analyses.

## 0.93.2

* Fixed a bug in backwards compatibility of import functions.

## 0.93.1

* `The preprocess_bold` and `preprocess_conc` commands now allow user to normalize the assumed regressors within each run or to normalize the area under the curve of the hrf function and this way ensure universal normalization.
* Increased the consistency of parameter passing across commands.

## 0.93.0

* Fixed a backwards compatibility issue with `hcp_fmri_volume`.
* Optimized the `qunex_container` script.
* Implemented support for HCP temporal ICA fix.

## 0.92.2

* Fixed a bug in the `fsl_xtract` command that prevented users from running it.
* Corrected some typos in inline documentation.

## 0.92.1

* Fixed a bug with time stamps in qunex_container.

## 0.92.0

* Improved scheduling.
* HCP ASL support.
* XNAT support update.
* RawNII QC should now again work.
* `setup_hcp` now also copies over the JSON files associated with the mapped scan.
* Improved the documentation at several location.
* Squashed a number of minor bugs that should improve the overall stability of QuNex.

## 0.91.11 (2021-04-10)

* File link creation inside QuNex is now more robust and should not crash on certain file systems.

## 0.91.10 (2021-29-09)

* Removed a bug that caused the hcp_icafix command to crash.
* All QuNex functions imeplemented in MATLAB now again print their inline help when requested.
* When QuNex is running an external command the exact command call in the log is now printed out in a nicer fashion.

## 0.91.9 (2021-15-09)

* Renamed the `hcp_folderstructure` parameter value from `initial` to `hcpya` to increase clarity.
* Optimized the entry point script for faster execution of commands.

## 0.91.8 (2021-01-09)

* Fixed a bug when running the `create_study` command through `qunex_container`.
* Optimized the environment setup.
* Fixed `run_turnkey` behavior when reran on the same study multiple times.
* Improved CUDA libraries linkup with `bedpostx` and `probtrackx`.
* Removed a bug in probtrackx when using a certain parameter configuration.
* The `dwi_parcellate` command is now able to parcellate length matrices as well.

## 0.91.7 (2021-11-08)

* Fixed a bug in `hcp_fmri_task_analysis` and made the command more robust.

## 0.91.6 (2021-06-08)

*  Optimized `dwi_probtrackx_dense_gpu` so it is now more robust and zips additional files at the end.
* Squashed some minor bugs that arose when transitioning from Python 2 to 3.
* Fixed a bug when echospacing was not printed correctly in batch files.

## 0.91.4 (2021-06-08)

* Improved completion checking in several commands and removed a bug when reslicing nifti images.

## 0.91.3 (2021-06-08)

* Default summaryname value setting in HCP TaskfMRIAnalysis pipeline.
* Fixed BIDS import.

## 0.91.2 (2021-02-08)

* Environment status script now works properly, upgraded the automatic setting of parallelism parameters.

## 0.91.1 (2021-29-07)

* Fixed a bug where input flags were not properly parsed.

## 0.91.0 (2021-29-07)

* QuNex Python codebase upgraded to Python 3.
* Integration of the HCP ASL and the HCP task analysis pipelines.
* Fixed a bug in `import_dicom` and `qunex_container` that caused the command to crash under a certain conditions.
* Added support for distance correction parameters in `dwi_probtrackx_dense_gpu`.

## 0.90.10 (2021-23-07)

* Consistent naming of dwi functions, upgraded `dwi_dtifit` so it now supports all of the FSL's dtifit parameters.
* Fixed a bug with `dwi_bedpostx_gpu` when running through the container. Fixed a bug in DWI `run_qc`.

## 0.90.8 (2021-06-28)

* The output of the `general_find_peaks` function now includes grayordinates of the identified regions of interest (ROI).
* The qunex_container scripts now properly passes the sessions parameter to all commands.

## 0.90.7 (2021-06-21)

* Minor bug fixes (ordering of entries in create_stats_report output, python exceptions are now always properly printed), fixed the reference in the README file.
* The `qunex_container` script now allows direct prinout of the environment status through the `--env_status` flag.

## 0.90.6 (2021-04-02)

* Beautified some QuNex documentation, outputs and logs.
* The `run_palm` command now has an option that allows it to use custom masks.
* Moved all third party files into the QuNex library repository.
* Changed some command names for the sake of consistency.
* Licensing compliant with with version 3.0 of the REUSE Specification.

## 0.90.1 (2021-02-21)

* Fixed some minor issues regarding parameter parsing.
* Updated `qunex_container` so it now fully works with Docker containers.

## 0.90.0 (2021-02-21)

* Quantitative Neuroimaging Environment & ToolboX (QuNex) public release candidate.

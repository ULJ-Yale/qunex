<!--
SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>

SPDX-License-Identifier: GPL-3.0-or-later
-->

# Change Log

## 1.1.0 [QIO]

* Fixed a bug where some optional parameters were not properly passed to the HCP ReapplyFix pipeline.
* Fixed a bug where hcp_msmall crashed as it did not parse bolds correctly.
* Set the default `hcp_matlab_mode` for single-run HCP ICAFix to `octave` as that is the option that works in the container.

## 1.0.4 [QIO]

* Added additional tests for MATLAB functions to reduce the probability of bugs on release.
* Fixed a bug where QuNex metadata (glm and lists information) were not written when saving images.
* Fixed a bug where `hcp_bold_dcmethod` set to `SiemensFieldMap` did not work.
* `import_hcp` is now more flexible when it comes to Diffusion data.
* Fixed a bug in `qunex_container` when using the SLURM job array.

## 1.0.3 [QIO]

* Fixed a bug in `general_extract_glm_volumes` that did not detect the CIFTI version properly.
* Fixed a bug in `hcp_fmri_volume` that sometimes loaded too many fieldmaps and then errored out.

## 1.0.2 [QIO]

* Fixed a bug in `import_bids` when importing SE pairs.
* Fixed a bug where bold tag (e.g., rest) was not properly converted into a list of bolds when specified as a parameter value.
* Added some additional error messages for user friendliness.
* Fixed a `qunex_container` bug that did not properly pass some parameters to the called QuNex command.
* By default, QuNex will now leave the raw imaging data archives on import alone (`--archive="leave"`). Previously, the default behavior was to move the archive into the QuNex study's archive subolder (`--archive="move"`).
* Fixed a bug where `hcp_echo_te` was not correctly prepared for HCP Pipelines.
* Fixed some MATLAB code so it is now Octave compliant.

## 1.0.1 [QIO]

* Fixed a bug when image loading was not working as it should in some commands of the analytics pipeline.
* QuNex now supports scenarios where FM-Magnitude is composed of two acquisitions.
* `run_recipe` will now error out if unknown commands are provided in the list.
* Fixed some minor `run_recipe` bugs.
* Fixed a bug in `create_session_info` where the results were sometimes not what was expected.
* Made a polish pass over the documentation.
* Added a `run_recipe` tutorial to the QuNex quickstart (<https://qunex.readthedocs.io/en/latest/wiki/Overview/QuickStart.html>).
* Auto setting of the template resolution for HCP Pipelines is now more robust.
* QuNex will now printout an error if you want to rerun `hcp_freesurfer` after `hcp_post_freesurfer` was already completed on the same session. This scenario is not supported and can cause invalid data. You need to cleanup the data and rerun from `hcp_pre_freesurfer` if you want to do this.

## 1.0.0 [QIO]

* Replacement of `run_turnkey` with `run_recipe`, a much more flexible and powerful engine for transparent and reproducible chaining of QuNex commands (<https://qunex.readthedocs.io/en/latest/wiki/UsageDocs/RunningQuNexRecipes.html>).
* `run_qa`, quality assurance (QA) functionality, which you can use to quickly validate raw neuroimaging data and metadata to check if there are discrepancies between acquired sessions or images. The commands generates input-friendly session lists that can be used in commands that follow and user-readable reports of the QA (<https://qunex.readthedocs.io/en/latest/api/gmri/run_qa.html>).
* Updated core functions for functional connectivity analyses, enabling flexible extraction of timeseries and computation of seed-based, ROI-based, and global brain connectivity (GBC). Some of Specific improvements are: a) the ability to work with resting state and different types of task-based data, b) the ability to use different functional connectivity measures (r, rho, covariance, cross correlation, inverse covariance, coherence, mutual information and multivariate autoregressive model coefficients), c) a flexible specification of target ROI using different types of input data and masks, and d) the ability to process mulitple session in a single call, compute and store both session specific and group level results (<https://qunex.readthedocs.io/en/latest/wiki/UsageDocs/BOLDFunctionalConnectivity.html>).
* The container now includes the recently released version of HCP Pipelines (`v5.0.0`), which includes a number of new functionalities and improvements (<https://github.com/Washington-University/HCPpipelines>).
* Added support for the HCP longitudinal FreeSurfer pipeline (`hcp_long_freesurfer` and `hcp_long_post_freesurfer` commands).
* Support for the HCP TransmitBias pipeline (`hcp_transmit_bias_individual`). Also added onboading functionalities for imaging data required by this pipeline (B1).
* `hcp_icafix` now uses `pyfix` by default, to use legacy MATLAB fix, add the `--hcp_legacy_fix` flag to your command call
* Simplification of the registration and access process.
* You can now map HCP derivatives (e.g., denoised concatenated REST BOLDs) from HCP folder structure to QuNex with `map_hcp_data`.
* Default value for the `hcp_prefs_template_res` parameter of `hcp_pre_freesurfer` is now read and set from the imaging data.
* Made several optimizations that should make QuNex more user friendly (e.g., automatic setting of parameter values from JSON sidecars, more robust logic for automatic setting of parameter values when they are inferred from imaging data ...).
* Fixed some bugs in our data onboarding functions (`import_dicom`, `import_bids`, `import_hcp`).
* Fixed a bug in the use of IntendedFor BIDS field.
* You can now specify ROIs using a .roi file that defines ROIs by the center and radius of a sphere.
* Easier to understand error reports at several locations.
* Connectome Workbench updated to the latest version.
* The commercial rights for the container of QuNex 1.0 (QIO) are transferd to a Yale startup called Manifest Technologies, Inc. For any QuNex container v1.0 commercial licensing inquiries please contact <qunex@manifesttech.io>.

## 0.100.0 [QX IO]

* Completely new FC pipeline (`fc_compute_roifc`, `fc_compute_seedmap`).
* Complete container rework with updates to almost all of the tools in it.
* Added the ability to export unprocessed data into BIDS format.
* Improved `import_bids` image sorting.
* Added the ability to manually assign boldrefs to bolds.
* Added two additional `hcp_temporal_ica` parameters.
* Added support to two new `hcp_icafix` parameters.
* Fixed the wrong default value for `MSMSulc`.
* Fixed a wrong name for the `hcp_highresmesh` parameter.
* Fixed a minor bug in regards to help and extensions.
* Fixed img.TR writing from CIFTI metadata in `img_read_nifti`.
* Fixed some typos and minor bugs in documentation.
* Fixed a bug where `run_qc` did not work if `scenezip` was set to no.
* Several additional bug fixes and improvements that will make QuNex more stable and robust.
* Improved acceptance testing and extensions.

## 0.99.3

* Fixed a bug in parameter parsing from batch files.

## 0.99.2

* Made HCP commands more robust to parameter types.

## 0.99.1

* Fixed a bug in completion check when importing BIDS data through `run_turnkey`.

## 0.99.0

* `fc_compute_wrapper` now checks if input files exist.
* Removed some race conditions in parallel runs.
* Added better reporting in case FM numbers are missing in the batch file.
* Allowed custom setup of POS/NEG pairs in `hcp_diffusion`.
* Now you can onboard processed HCP data along with unprocessed.
* QuNex DWI pipelines now supports microstrucutre modelling (NODDI).
* Improved the file locking mechanism.
* Fixed a bug with a non-existing parameter in DeDriftAndResample.
* Added support for the HCP ApplyAutoReclean Pipeline (`hcp_apply_auto_reclean`).
* Improved support for SEBASED `hcp_bold_biascorrection` in `hcp_fmri_volume`.

## 0.98.6

* Improved several aspects of `run_turnkey` when running on XNAT.
* Fixed the use of `hcp_asl`_stages parameter and updated HCP ASL version.
* Improved the robustness of `dwi_dtifit`.

## 0.98.5

* Fixed the output checks of HCP ASL.

## 0.98.4

* Fixed an incompatibility betweeb MATLAB and Octave.

## 0.98.3

* Fixed a bug that crashed `preprocess_conc` and `preprocess_bold` with some parameter configurations.
* `import_dicom` is now capable of onboarding data folders that contain multiple compressed sessions or compressed files that contain multiple session within them.
* `import_bids` now acknowledges data from supporting JSON files.
* `map_hcp_data` now acknowledges the `hcp_bold_res` parameter.
* Added meaningful error messages at several locations where QuNex previously just crashed with a very technical message.
* Updated `hcp_asl` version and added version reporting to QX environment status.
* Added support to the `hcp_asl` parameter `stages` through `hcp_asl_stages`.

## 0.98.2

* Updated `hcp_asl` to the latest version.
* `hcp_diffusion` now prints an error if there are no pos/neg pairs insted of crashing.
* Optimized speed of `dwi_parcellate`.
* `create_batch` now replaces an existing session when using `append` mode.
* Fixed an issue where QuNex was using some unavailable Octave functions in analysis commands.
* `omp_threads` parameter is now used globally for setting parallelism for `wb_command`.

## 0.98.1

* Added statistics package back to Octave in the container, required for `preprocess_bold` and `preprocess_conc`.
* You can now merge of multiple DWI images before running `dwi_legacy_gpu`.
* You can now run manual bash scripts through `qunex_container`.
* You can change the data that gets used for `dwi_dtifit` (previously you could change only bvals and bvecs).

## 0.98.0

* Optimized DWI pipelines, all commands now support newer GPUs and `nogpu` processing for systems without an NVIDIA graphics card.
* Added the fucionality to GLM modelling that allows to generate the output image with standard errors of each coefficient along with GLM beta coefficients.
* Optimized Philips and GE scanner support in `hcp_pre_freesurfer`.
* All HCP Pipelines parameters are now accessible to QuNex, added documentation for all of them and made the documentation consistent across commands.
* `fc_preprocess` and `fc_preprocess_conc` can now be executed without regression, only with filtering.
* Location of HCP Pipelines is now always read from the system HCPPIPEDIR variable.
* Added the ability to assign manual spin echo and fieldmap numbers to images in mapping files.
* QuNex will now print a warning if `hcp_diffusion` echo spacing parameter has a value that is larger or smaller than expected.
* Fixed a bug where some commands did not work properly if both `batchfile` and `sessions` parameters are used.
* All `dwi_dtifit` parameters are now properly acknowledged.
* `create_list` and `create_conc` now use the same log folder structure as other commands.
* Fixed a bug in `hcp_reapply_fix` where the `overwrite` parameter was not acknowledged.
* Improved several command examples in documentation.

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

## 0.96.3

* Fixed a bug where `hcp_reapply_fix` did not properly overwrite previous results.

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

* Missing `EDDYCUDA` was reported erroneously inside the container.
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

* Optimized `dwi_probtrackx_dense_gpu` so it is now more robust and zips additional files at the end.
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

# QuNex change log

* 0.90.0  TODO COPY FROM RELEASE CARD AT RELEASE.
* 0.62.11 qunex.sh patched to include pushd and popd functionality to preserve initial user working directory.
* 0.62.10 runTurnkey patch to include T2 to rsync command for hcp2 step.
* 0.62.9  Improved parameter checking in the createList command.
* 0.62.8  Added the use_sequence_info parameter that specifies which information is extracted from JSON sidecars during dcm2niix conversion.
* 0.62.7  Importing HCP data now works properly for dwi and HCPYA, diffusion processing now warns users when using legacy parameter names.
* 0.62.6  MSMAll now properly executes DeDriftAndResample in case of a multi-run HCP ICAFix.
* 0.62.5  Bolds parameter is now properly passed to all commands.
* 0.62.4  The order of images in the hcpDiffusion command is now correct.
* 0.62.3  Robust parsing of the hcp_filename parameter in RunTurnkey.
* 0.62.2  Consistent naming of all DWI related commands, documentation polish to for consistencty purposes across the whole suite.
* 0.62.1  Fixed run_qc_bold issues with filenames and a large number of bolds.Increase the robustness of QuNex when processing multiple sessions in parallel.
* 0.62.0  Documentation rework.
* 0.61.19 The mapHCPData command now copies only valid movement correctionparameter data.
* 0.61.18 QuNex no longer generates unnecessary folders, added CUDA 9.1bedpostx support, improved HCPYA dataset support.
* 0.61.17 hcp_dwi_selectbestb0 in HCP Diffusion pipelines is now a flag.
* 0.61.16 HCP Diffusion now uses pipe (|) as the extra eddy args separator.
* 0.61.15 Beautified and debugged extra-eddy-arg printout in HCP Diffusion pipeline.
* 0.61.14 Added new parameters introduced by the latest HCP pipelines to HCP Diffusion command.
* 0.61.13 Added --nv flag to qunex_container for Singularity CUDA support.
* 0.61.12 Added CUDA support for Diffusion pipelines.
* 0.61.11 Replaced spaces with underscores in general_extract_glm_volumes saveoption.
* 0.61.10 Removed a bug in single-run HCP ICAFix
* 0.61.9  HCP Diffusion pipeline updated to match the latest version in HCP pipelines, removed race conditions in python qx_utilities, added CUDA.
* 0.61.8  All DeDriftAndResample parameters are now properly passed to HCP pipelines.
* 0.61.7  Added additional parameters to DeDriftAndResample.
* 0.61.6  run_qc now works properly when overwrite is set to no.
* 0.61.5  Removed a bug that prevented proper setup of hcp_fMRIVolume parameters.
* 0.61.4  Fixed several bugs when when importing BIDS data.
* 0.61.1  Hotfix of a breaking bug in createSessionInfo. Inclusion of sequence information from JSON files when running importDICOM and dicom 2niix is now optional.
* 0.61.0  Implementation of bug fixes across bash code and pipeline restructure back-compatibility.
* 0.60.0  Renamed all subject related parameters to session. Pipeline architecture restructure.
* 0.51.2  Removed an MSMAll bug when hcp_icafix_bolds parameter was not provided.
* 0.51.1  Upgraded MSMAll and DeDriftAndResample in order to make it more user-friendly.
* 0.51.0  MSMAll and DeDriftAndResample HCP pipelines, qunex_envstatus upgrade and hcp_suffix harmonization.
* 0.50.4  Fixed a bug that crashed the QuNex suite instead of reporting an error in hcp_PreFS.
* 0.50.2  Support for the HCP ICAFix pipelines, removed some bugs and implemented some minor optimizations.

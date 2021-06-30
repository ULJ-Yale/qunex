<!--
SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>

SPDX-License-Identifier: GPL-3.0-or-later
-->

# Change Log

## 0.90.8 (2021-06-28)

The output of the general_find_peaks function now includes grayordinates of the identified regions of interest (ROI). The qunex_container scripts now properly passes the sessions parameter to all commands.

## 0.90.7 (2021-06-21)

Minor bug fixes (ordering of entries in create_stats_report output, python exceptions are now always properly printed), fixed the reference in the README file. The qunex_container script now allows direct prinout of the environment status through the --env_status flag.

## 0.90.6 (2021-04-02)

Beautified some QuNex documentation, outputs and logs. The run_palm command now has an option that allows it to use custom masks. Moved all third party files into the QuNex library repository. Changed some command names for the sake of consistency. Licensing compliant with with version 3.0 of the REUSE Specification.

## 0.90.1 (2021-02-21)

Fixed some minor issues regarding parameter parsing, updated qunex_container so it now fully works with Docker containers.

## 0.90.0 (2021-02-21)

Quantitative Neuroimaging Environment & ToolboX (QuNex) public release candidate.

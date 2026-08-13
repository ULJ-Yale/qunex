#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``workflow/``

This package holds the code for running functional connectivity
preprocessing and GLM computation workflow. It consists of one module per
command, each named after the command it holds:

--get_bold_data             Maps NIL preprocessed data to images folder.
--create_bold_brain_masks   Extracts the first frame of each BOLD file.
--compute_bold_stats        Computes per volume image statistics for scrubbing.
--create_stats_report       Creates a report of movement and image statistics.
--extract_nuisance_signal   Extracts the nuisance signal for regressions.
--preprocess_bold           Processes a single BOLD file.
--preprocess_conc           Processes concatenated BOLD files.

The side-effect guards the commands share, and the MATLAB command they are
run with, are in ``dryrun.py``.

All the functions are part of the processing suite. They should be called
from the command line using `qunex` command. Help is available through:

- `qunex ?<command>` for command specific help

Import a command from here rather than from its module: the registry
records it under its own module path, but everything else in the tree
reaches it through the package.
"""

# Created by Grega Repovs on 2016-12-17.
# Code split from dofcMRIp_core gCodeP/preprocess codebase.
# Copyright (c) Grega Repovs. All rights reserved.

from qx_utilities.processing.workflow.get_bold_data import get_bold_data
from qx_utilities.processing.workflow.create_bold_brain_masks import create_bold_brain_masks
from qx_utilities.processing.workflow.compute_bold_stats import compute_bold_stats
from qx_utilities.processing.workflow.create_stats_report import create_stats_report
from qx_utilities.processing.workflow.extract_nuisance_signal import extract_nuisance_signal
from qx_utilities.processing.workflow.preprocess_bold import preprocess_bold
from qx_utilities.processing.workflow.preprocess_conc import preprocess_conc

__all__ = [
    "get_bold_data",
    "create_bold_brain_masks",
    "compute_bold_stats",
    "create_stats_report",
    "extract_nuisance_signal",
    "preprocess_bold",
    "preprocess_conc",
]

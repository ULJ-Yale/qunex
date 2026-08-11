#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``general.log``

QuNex command logging: what a command reports, where it is written, and
whether it is written at all.

The package is the public surface; the implementation is split by concern:

- :mod:`~qx_utilities.general.log.report` -- :class:`ReportLog` and
  :class:`SessionLog`, the runlog *text* a command builds as it works.
- :mod:`~qx_utilities.general.log.settings` -- where logging settings come
  from (user file, study file, the registry ``logging:`` field, ``--logging``)
  and how they are resolved into a :class:`LogSettings`.
- :mod:`~qx_utilities.general.log.context` -- :class:`RunContext` and
  :class:`ComContext`, which own the runlog and comlog *files*: where they
  live, when they are written, and what their names say about how the call
  ended.

Import the names from here, not from the submodules::

    from qx_utilities.general.log import SessionLog, resolve_logging

so the internal split can move without touching the ~42 modules that log.

Note for the layer below: nothing in this package may import
``general.core`` or ``processing.core`` at module level -- those import
paths run the other way. Where a helper from them is needed, import it
lazily inside the function.
"""

from qx_utilities.general.log.context import (
    ComContext,
    RunContext,
    call_echo,
    comlog_folder,
    comlog_name,
    digest,
    log_folder,
    read_status,
    run_and_log,
)
from qx_utilities.general.log.report import (
    INDENT,
    PREFIXES,
    RAW,
    REPORT_RULE,
    REPORT_TIME,
    ReportLog,
    SessionLog,
    action,
    log_or_console,
)
from qx_utilities.general.log.settings import (
    LOGGING_MODES,
    USER_SETTINGS_PATHS,
    LogSettings,
    active,
    apply_study_settings,
    load_settings,
    resolve_logging,
    set_active,
)

__all__ = [
    "INDENT",
    "LOGGING_MODES",
    "ComContext",
    "LogSettings",
    "PREFIXES",
    "RAW",
    "REPORT_RULE",
    "REPORT_TIME",
    "ReportLog",
    "RunContext",
    "SessionLog",
    "USER_SETTINGS_PATHS",
    "action",
    "active",
    "apply_study_settings",
    "call_echo",
    "comlog_folder",
    "comlog_name",
    "digest",
    "load_settings",
    "log_folder",
    "log_or_console",
    "read_status",
    "resolve_logging",
    "run_and_log",
    "set_active",
]

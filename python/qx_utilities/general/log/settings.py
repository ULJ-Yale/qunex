#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``general.log.settings``

Whether a command logs, and where.

QuNex reads a general settings file -- ``qunex_settings.yaml`` -- from the
user's home and from the study folder. Its ``logging:`` section answers the
questions the log machinery asks before it writes anything::

    logging:
        enabled: true            # master switch
        runlog: true             # write the per-run summary log
        comlog: true             # write the per-call raw output logs
        outside_study: home      # home | cwd | <path>, for every run outside
                                 # a study, whatever the layout; a relative
                                 # path is taken from the current folder
        layout: default          # default | legacy (<study>/processing/logs)
                                 #   | nested (a numbered folder per recipe
                                 #   step, external steps included)
        keep_comlogs: false      # never delete a comlog, whatever a caller asks
        comlog_folders: [study]  # study | session | hcp | <path>, one or more
        runlog_content: manifest # manifest | full -- whether the runlog also
                                 # carries each utility command's report
        skip_commands: []        # never log these commands
        log_commands: []         # always log these, whatever else says
        skip_types: []           # skip by registry command type, e.g. [utility]

:func:`resolve_logging` folds that together with the command's own
declaration and the command line into one :class:`LogSettings`, applied in
this order, each layer overriding the one before it:

1. the built-in defaults (the field defaults of :class:`LogSettings`),
2. the user settings file,
3. the study settings file,
4. the command's ``logging:`` field in its ``.. qx_command:`` block,
5. ``skip_types`` then ``skip_commands``, then ``log_commands``, which wins
   over both -- and, for commands not yet carrying a ``logging:`` field, the
   legacy ``commands_support.logskip_commands`` list,
6. ``--logging=<none|comlog|runlog|full>``, ``--keep_comlogs`` and
   ``--runlog_content=<manifest|full>`` on the command line.

``layout`` and ``outside_study`` are the two settings that say where a run's
logs go, and ``general.folders`` applies them: ``run_folders`` decides a run's
log folder once, where the run starts, and the container launcher, which can
not import this package, decides it on the host with a copy of the same code.
So the settings files are the ones ``general.folders`` names, and the values
the two settings take are the ones it knows. ``legacy`` is a layout of a
study's logs: a run outside a study logs where ``outside_study`` says,
whatever the layout.

``comlog_folders`` is the destination half of what ``--log`` used to answer;
``--log`` kept the retention half. A command's own ``--comlog_folders``
overrides the settings value, and ``do_options_check`` is where the two meet.

Two tiers named in the design are not implemented here: batch file and recipe
settings sit between the study file and the command line, and there is no
carrier for them until the merged-options model exists. They belong in
:func:`resolve_logging`, between steps 3 and 6, and nowhere else.

The result is handed down through the drivers, but the helpers at the bottom
of ``processing.core`` are reached by 110 call sites that pass a folder and no
context at all. :func:`set_active` and :func:`active` are how the answer
reaches them without those call sites moving.
"""

import os
import os.path
from dataclasses import dataclass, replace

import yaml

import qx_utilities.general.exceptions as ge
import qx_utilities.general.folders as gf
import qx_utilities.general.parsing as gp

# the user settings file is accepted in exactly these locations; finding it in
# more than one is an error rather than a silent pick, since the loser would
# look like it was being honoured. `general.folders` names them, because the
# container launcher reads the same files to place a run's logs; this module
# keeps a list of its own, which tests point at a file of their own
USER_SETTINGS_PATHS = list(gf.USER_SETTINGS_PATHS)

# the study settings file, relative to the study folder
STUDY_SETTINGS_FILE = gf.STUDY_SETTINGS_FILE

# what a logging mode means, as (enabled, runlog, comlog). `both` is the
# spelling the registry `logging:` field uses for `full`; both are accepted
# everywhere so a user writing either gets what they meant
LOGGING_MODES = {
    "none": (False, False, False),
    "comlog": (True, False, True),
    "runlog": (True, True, False),
    "full": (True, True, True),
    "both": (True, True, True),
}

# where a run outside a study may put its logs, besides a path of its own
OUTSIDE_STUDY = list(gf.OUTSIDE_STUDY)

# recognised log folder layouts
LAYOUTS = list(gf.LAYOUTS)

# what a runlog may hold beyond the call echoes, the status lines and the
# closing manifest
RUNLOG_CONTENTS = ["manifest", "full"]


@dataclass(frozen=True)
class LogSettings:
    """
    The resolved logging configuration for one command invocation.

    Fields:
        enabled: master switch; when False nothing is written at all.
        runlog: write the per-run summary log.
        comlog: write the per-call raw output logs.
        outside_study: where a run outside any study logs, whatever the
            layout -- ``home`` (``~/qunex_logs``), ``cwd`` (the current
            folder), or a path, a relative one taken from the current folder.
            The run gets a ``<stamp>_<name>`` folder of its own in it.
        layout: how a study's logs are laid out -- ``default``
            (``<study>/logs/<stamp>_<name>``, a folder per run), ``legacy``
            (``<study>/processing/logs``, which every run of the study
            shares), or ``nested``, which is ``default`` plus a numbered
            folder per ``run_recipe`` step, external steps included, so each
            step keeps its own runlog and comlogs; the recipe's ``status``
            records stay at the root of its folder.
        keep_comlogs: the run-level override -- when True no comlog is ever
            deleted, whatever a call site's ``remove=`` or ``--log=remove``
            asks for.
        comlog_folders: where each comlog goes -- ``study``, ``session``,
            ``hcp`` or a path. The first is where it is written, the rest are
            where it is mapped. A tuple, because the dataclass is frozen.
        runlog_content: what the runlog holds for a **utility** command --
            ``manifest`` (the default: the call echo, a status line naming the
            comlog, and the closing manifest) or ``full``, which adds each
            call's report. A utility command's report and its comlog hold the
            same text, so ``full`` writes every line twice; it is what to ask
            for when one self-contained file is wanted. Read only by
            ``general.core.run_with_log``, and clamped there: a call with no
            comlog puts its report in the runlog whatever this says, since
            ``manifest`` is asking to avoid duplication and not to discard the
            only copy. Processing commands do not read it -- they have no
            comlog of their own, so ``ReportLog.write_to`` is the only thing
            that puts their report in a file.
    """

    enabled: bool = True
    runlog: bool = True
    comlog: bool = True
    outside_study: str = "home"
    layout: str = "default"
    keep_comlogs: bool = False
    comlog_folders: tuple = ("study",)
    runlog_content: str = "manifest"


def user_settings_file():
    """
    Locate the user settings file among the accepted locations.

    Returns:
        the path, or None when the user has no settings file.

    Raises:
        ge.CommandError: when more than one location holds a settings file.
    """
    found = [
        path
        for path in (os.path.expanduser(c) for c in USER_SETTINGS_PATHS)
        if os.path.isfile(path)
    ]
    if len(found) > 1:
        raise ge.CommandError(
            "qunex settings",
            "More than one user settings file found",
            "QuNex reads user settings from one file only, but found %d:"
            % len(found),
            *["    %s" % path for path in found],
            "Please keep the one you want and remove or rename the others.",
        )
    return found[0] if found else None


def read_settings_file(path):
    """
    Read one settings file into a dict; a missing file reads as empty.

    Its ``logging:`` section, the one QuNex reads, is checked here, where the
    file can still be named: it must be a mapping of settings, or empty. One
    that is anything else is an error whatever the other file states, as it
    is for the container launcher, which reads the files with
    ``general.folders``.
    """
    if not path or not os.path.isfile(path):
        return {}

    with open(path, "r") as settings_file:
        try:
            content = yaml.safe_load(settings_file)
        except yaml.YAMLError as e:
            raise ge.CommandError(
                "qunex settings", "Could not parse settings file", path, str(e)
            )

    if content is None:
        return {}
    if not isinstance(content, dict):
        raise ge.CommandError(
            "qunex settings",
            "Invalid settings file",
            "%s does not hold a mapping of settings sections." % path,
        )

    section = content.get("logging")
    if section and not isinstance(section, dict):
        raise ge.CommandError(
            "qunex settings",
            "Invalid logging setting",
            "logging must be a mapping of settings, got: %r" % (section,),
            "Please write the logging section of %s as indented `key: value` "
            "lines under `logging:`." % path,
        )
    return content


def load_settings(studyfolder=None):
    """
    Read the user and study settings files and merge them.

    Study settings override user settings section by section: a study that
    sets ``logging: {comlog: false}`` leaves the user's other logging keys in
    place rather than replacing the whole section, and a section the study
    file leaves empty -- ``logging:`` with nothing under it -- states nothing,
    so the user's section stands. The container launcher reads the two files
    the same way, with ``general.folders.placement_settings``, and so decides
    a run's log folder as QuNex does.

    Parameters:
        studyfolder: the study folder, when the run has one.

    Returns:
        the merged settings dictionary.

    Raises:
        ge.CommandError: on more than one user settings file, or an
            unparsable or malformed settings file.
    """
    settings = read_settings_file(user_settings_file())

    if studyfolder:
        study = read_settings_file(os.path.join(studyfolder, STUDY_SETTINGS_FILE))
        for section, values in study.items():
            if not values:
                continue
            if isinstance(values, dict) and isinstance(settings.get(section), dict):
                settings[section] = {**settings[section], **values}
            else:
                settings[section] = values

    return settings


def _as_list(value):
    """Read a settings value that is a list, tolerating a bare string."""
    if not value:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return list(value)


def _flag(section, key, default):
    """Read a boolean settings value, rejecting anything that is not one."""
    value = section.get(key, default)
    if not isinstance(value, bool):
        raise ge.CommandError(
            "qunex settings",
            "Invalid logging setting",
            "logging.%s must be true or false, got: %r" % (key, value),
        )
    return value


def _choice(section, key, default, valid, free_form=False):
    """Read a settings value restricted to `valid` (unless `free_form`)."""
    value = section.get(key, default)
    if not isinstance(value, str) or (not free_form and value not in valid):
        raise ge.CommandError(
            "qunex settings",
            "Invalid logging setting",
            "logging.%s must be one of [%s]%s, got: %r"
            % (
                key,
                ", ".join(valid),
                " or a path" if free_form else "",
                value,
            ),
        )
    return value


def settings_to_log_settings(section):
    """Build the base :class:`LogSettings` from a ``logging:`` section."""
    section = section or {}
    return LogSettings(
        enabled=_flag(section, "enabled", True),
        runlog=_flag(section, "runlog", True),
        comlog=_flag(section, "comlog", True),
        outside_study=_choice(
            section, "outside_study", "home", OUTSIDE_STUDY, free_form=True
        ),
        layout=_choice(section, "layout", "default", LAYOUTS),
        keep_comlogs=_flag(section, "keep_comlogs", False),
        comlog_folders=tuple(_as_list(section.get("comlog_folders")) or ["study"]),
        runlog_content=_choice(
            section, "runlog_content", "manifest", RUNLOG_CONTENTS
        ),
    )


def apply_mode(settings, mode, source):
    """
    Apply a ``none|comlog|runlog|full`` mode to `settings`.

    Parameters:
        settings: the settings to override.
        mode: the mode; None or empty leaves `settings` untouched.
        source: where the mode came from, for the error message.

    Returns:
        the resulting :class:`LogSettings`.
    """
    if not mode:
        return settings

    key = str(mode).strip().lower()
    if key not in LOGGING_MODES:
        raise ge.CommandError(
            "qunex settings",
            "Invalid logging mode",
            "%s must be one of [%s], got: %r"
            % (source, ", ".join(sorted(set(LOGGING_MODES))), mode),
        )

    enabled, runlog, comlog = LOGGING_MODES[key]
    return replace(settings, enabled=enabled, runlog=runlog, comlog=comlog)


def apply_keep_comlogs(settings, value):
    """
    Apply ``--keep_comlogs`` to `settings`.

    Parameters:
        settings: the settings to override.
        value: the bare flag (``True``), ``yes|no|true|false|on|off|1|0``, or
            None, which leaves `settings` untouched.

    Returns:
        the resulting :class:`LogSettings`.

    Raises:
        ge.CommandError: on a value that is neither.
    """
    if value is None:
        return settings

    keep = gp.as_bool(value)
    if keep is None:
        raise ge.CommandError(
            "qunex settings",
            "Invalid keep_comlogs value",
            "--keep_comlogs must be given bare or as one of [%s], got: %r"
            % (", ".join(gp.TRUE_VALUES + gp.FALSE_VALUES), value),
        )

    return replace(settings, keep_comlogs=keep)


def apply_runlog_content(settings, value):
    """
    Apply ``--runlog_content`` to `settings`.

    Parameters:
        settings: the settings to override.
        value: ``manifest``, ``full``, or None, which leaves `settings`
            untouched.

    Returns:
        the resulting :class:`LogSettings`.

    Raises:
        ge.CommandError: on any other value.
    """
    if value is None:
        return settings

    content = str(value).strip().lower()
    if content not in RUNLOG_CONTENTS:
        raise ge.CommandError(
            "qunex settings",
            "Invalid runlog_content value",
            "--runlog_content must be one of [%s], got: %r"
            % (", ".join(RUNLOG_CONTENTS), value),
        )

    return replace(settings, runlog_content=content)


# The settings this process resolved. A module-level value models exactly what
# this is: one QuNex invocation per process, resolved once before any dispatch
# and never changed afterwards. It exists for the deep helpers in
# `processing.core`, which hold no context and cannot be handed one without
# moving 110 call sites.
_active = None


def set_active(settings):
    """
    Record the settings this process resolved.

    Called once per invocation, immediately after the settings are known:
    ``gmri`` once it has placed the run and resolved them for its study,
    ``process.run`` after it has built its context from them, and
    ``run_recipe`` with the settings its run is placed by -- the ones it was
    handed, or else those :func:`resolve_logging` gives for the study it is
    placed in.

    Parameters:
        settings: the resolved :class:`LogSettings`.
    """
    global _active
    _active = settings


def active():
    """
    The settings this process resolved, for helpers that hold no context.

    Returns:
        the :class:`LogSettings` :func:`set_active` was given, or the defaults
        -- everything on -- when nothing set them. So a path that never sets
        them (a unit test, a direct import) behaves as the tree did before,
        and the failure mode is "logs too much", never "logs nothing".

    Processing workers come from a ``ProcessPoolExecutor``, which forks on
    Linux, so they inherit the value; scheduler jobs re-enter ``gmri`` and
    re-resolve. A spawn-start platform would fall back to the defaults.
    """
    return _active if _active is not None else LogSettings()


def resolve_logging(command, args, qx_command=None, studyfolder=None, legacy_skip=None):
    """
    Resolve the logging configuration for one command invocation.

    Applies, in order, the built-in defaults, the user and study settings
    files, the command's registry ``logging:`` field, the skip and log lists
    (including the legacy ``logskip_commands`` fallback for commands with no
    ``logging:`` field), and finally ``--logging`` from the command line.
    See the module docstring for the full precedence.

    Parameters:
        command: the command name as invoked.
        args: the parsed command line arguments; ``logging`` is read from it.
        qx_command: the registry entry for the command, when it has one; its
            ``logging`` and ``type`` fields participate.
        studyfolder: the study folder, when the run has one.
        legacy_skip: the pre-registry skip list, when the caller has one. It
            applies only to commands that state no ``logging:`` field, and is
            passed in rather than read from ``general.commands_support``,
            which extensions extend and which consumes this package.

    Returns:
        the resolved :class:`LogSettings`.

    Raises:
        ge.CommandError: on an invalid settings file or an invalid mode.
    """
    section = load_settings(studyfolder).get("logging") or {}
    settings = settings_to_log_settings(section)

    declared = getattr(qx_command, "logging", None) if qx_command else None
    settings = apply_mode(settings, declared, "the command's `logging:` field")

    command_type = (getattr(qx_command, "type", None) if qx_command else None) or ""
    if command_type in _as_list(section.get("skip_types")):
        settings = replace(settings, enabled=False)
    if command in _as_list(section.get("skip_commands")):
        settings = replace(settings, enabled=False)

    if command in _as_list(section.get("log_commands")):
        settings = replace(settings, enabled=True)
    elif not declared and command in (legacy_skip or ()):
        settings = replace(settings, enabled=False)

    settings = apply_mode(settings, args.get("logging"), "--logging")
    settings = apply_keep_comlogs(settings, args.get("keep_comlogs"))
    return apply_runlog_content(settings, args.get("runlog_content"))

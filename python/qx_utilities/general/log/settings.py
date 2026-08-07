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
        outside_study: home      # home | cwd | <path>, for runs with no study
        layout: default          # default | legacy (<study>/processing/logs)
                                 #          | nested (a folder per recipe step)
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
6. ``--logging=<none|comlog|runlog|full>`` on the command line.

Two tiers named in the design are not implemented here: batch file and recipe
settings sit between the study file and the command line, and there is no
carrier for them until the merged-options model exists. They belong in
:func:`resolve_logging`, between steps 3 and 6, and nowhere else.
"""

import os
import os.path
from dataclasses import dataclass, replace

import yaml

import qx_utilities.general.exceptions as ge

# the user settings file is accepted in exactly these locations; finding it in
# more than one is an error rather than a silent pick, since the loser would
# look like it was being honoured
USER_SETTINGS_PATHS = [
    "~/.qunex_settings.yaml",
    "~/qunex_settings.yaml",
    "~/qunex/qunex_settings.yaml",
    "~/.qunex/qunex_settings.yaml",
]

# the study settings file, relative to the study folder
STUDY_SETTINGS_FILE = "qunex_settings.yaml"

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

# where a run outside a study may put its logs
OUTSIDE_STUDY = ["home", "cwd"]

# recognised log folder layouts
LAYOUTS = ["default", "legacy", "nested"]


@dataclass(frozen=True)
class LogSettings:
    """
    The resolved logging configuration for one command invocation.

    Fields:
        enabled: master switch; when False nothing is written at all.
        runlog: write the per-run summary log.
        comlog: write the per-call raw output logs.
        outside_study: where to log when the run has no study folder --
            ``home`` (``~/qunex_logs``), ``cwd``, or an explicit path.
        layout: ``default`` (``<study>/logs/<stamp>_<command>``),
            ``legacy`` (``<study>/processing/logs``), or ``nested``, which is
            ``default`` plus a subfolder per ``run_recipe`` step so each step
            keeps its own runlog and comlogs.
    """

    enabled: bool = True
    runlog: bool = True
    comlog: bool = True
    outside_study: str = "home"
    layout: str = "default"


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
    """Read one settings file into a dict; a missing file reads as empty."""
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
    return content


def load_settings(studyfolder=None):
    """
    Read the user and study settings files and merge them.

    Study settings override user settings section by section: a study that
    sets ``logging: {comlog: false}`` leaves the user's other logging keys in
    place rather than replacing the whole section.

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


def apply_study_settings(settings, studyfolder, args):
    """
    Layer a study's ``logging:`` section over already resolved settings.

    For the caller that learns which study it is in only *after* its settings
    were resolved: ``run_recipe``, whose recipe file can name a study the
    command line never mentioned. Only the keys that study actually states are
    taken -- the rest of the resolution stands -- and ``--logging`` is applied
    again on top, so the command line still wins over the file.

    Parameters:
        settings: the settings resolved without knowing the study.
        studyfolder: the study folder, or None.
        args: the parsed arguments; ``logging`` is read from them.

    Returns:
        the resulting :class:`LogSettings`.
    """
    section = (load_settings(studyfolder).get("logging") or {}) if studyfolder else {}
    if not section:
        return settings

    stated = settings_to_log_settings(section)
    overrides = {
        field: getattr(stated, field)
        for field in ("enabled", "runlog", "comlog", "outside_study", "layout")
        if field in section
    }

    return apply_mode(replace(settings, **overrides), args.get("logging"), "--logging")


def _legacy_skip(command, declared):
    """Whether the pre-registry skip list still applies to this command."""
    if declared:
        return False

    import qx_utilities.general.commands_support as gcs

    return command in gcs.logskip_commands


def resolve_logging(command, args, qx_command=None, studyfolder=None):
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
    elif _legacy_skip(command, declared):
        settings = replace(settings, enabled=False)

    return apply_mode(settings, args.get("logging"), "--logging")

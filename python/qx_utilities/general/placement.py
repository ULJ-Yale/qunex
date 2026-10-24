#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``placement.py``

How ``gmri`` sets a run up in its study, in the order it does it:

- :func:`anchor` makes absolute what the command line names that is read
  before the run knows every study it may name -- the batch file, a ``.list``
  of sessions, the recipe file -- and reads ``run_recipe``'s recipe file, once
  for the run;
- :func:`hand_on_folders` hands the study and the sessions folder on as
  ``process.merge_options`` settled them, absolute;
- :func:`place_run` decides, in the folder the run was started in, the run's
  study, the folder it takes its relative paths from and its log folder, by
  the one rule ``general.folders.run_folders`` holds;
- :func:`work_in_study` says what that means for the values the run was given,
  and enters the folder. ``gmri.runCommand`` returns to the folder it was
  started in however the run ends;
- :func:`for_jobs` hands a scheduled job the study the run settled.

A run that knows its study -- one it names, or the one a sessions folder it
names is in -- works in it, once the study exists and unless the command
creates it, so that the command, and every script, MATLAB session and tool it
starts, takes the relative paths it is given from there. :func:`enter` is the
one place in QuNex that changes the current folder
(``tests/test_relative_paths_runs.py``). A run that names neither folder works
in the current folder, as it always has.

Not spliced into ``bin/qunex_container``: the launcher never changes folder,
and this module imports the tree.
"""

import os
import sys
from datetime import datetime

import qx_utilities.general.batch_io as bio
import qx_utilities.general.commands_support as gcs
import qx_utilities.general.core as gc
import qx_utilities.general.exceptions as ge
import qx_utilities.general.folders as gf
import qx_utilities.general.log as gl
import qx_utilities.general.recipe as gr

# the two folders a run names its study with
FOLDERS = ("studyfolder", "sessionsfolder")


def anchor(command: str, args: dict) -> tuple[dict, dict, dict, str | None]:
    """
    ``anchor(command, args)``

    The command line with what it names that is read before the study is
    known made absolute (``batch_io.anchor_command_line``): the study from the
    current folder, and the batch file, a ``.list`` of sessions and the recipe
    file from the study the command line names.

    For ``run_recipe`` the recipe file is read here, once for the run: its
    tier of the parameters that place a run (``recipe.recipe_folders``), its
    labels resolved where the run works (:func:`run_environment`), and,
    when the command line names no study, the study the recipe names, which is
    then the one the batch file, a list of sessions and the sessions of the
    call are found in, as each step finds them; a sessions folder the command
    line names without a study is taken from the study the recipe names.

    Returns:
        ``(anchored, recipe, recipe_named, study)``: the anchored arguments;
        the recipe file's tier, empty for every other command; the study and
        sessions folder the recipe names, when they stand in for a command
        line that names neither, else empty; and the study the files read
        early were taken from, None for the current folder.
    """
    anchored, study = bio.anchor_command_line(args, command)

    recipe = {}
    if command == "run_recipe" and anchored.get("recipe_file"):
        recipe = gr.recipe_folders(
            anchored["recipe_file"], anchored.get("recipe"), run_environment(args)
        )

    recipe_named = {key: recipe[key] for key in FOLDERS if _named(recipe.get(key))}
    if study is not None or not recipe_named:
        return _sessions_in_recipe_study(anchored, recipe), recipe, {}, study

    study = gf.study_folder(
        recipe_named.get("studyfolder"), recipe_named.get("sessionsfolder")
    )
    args = {**args, "recipe_file": anchored["recipe_file"]}
    anchored, _ = bio.anchor_command_line(args, command, study=study)
    return anchored, recipe, recipe_named, study


def run_environment(args: dict) -> dict | None:
    """
    ``run_environment(args)``

    The environment a recipe's ``{{$NAME}}`` labels are resolved in: this
    one, and for a run handed to a scheduler also what its ``--bash`` exports
    (``batch_io.bash_post_exports``), as the job runs it on the node before
    the command -- what ``qunex_container`` does with ``--bash_post``. None,
    the environment as it is, for a run that is not scheduled.
    """
    if not args.get("scheduler") or not _named(args.get("bash")):
        return None
    return {**os.environ, **bio.bash_post_exports(args["bash"])}


def _sessions_in_recipe_study(anchored: dict, recipe: dict) -> dict:
    """
    A sessions folder the command line names without a study, taken from the
    study the recipe names, as one named together with a study in a batch file
    header is taken from that study (``process.merge_options``): the command
    line's sessions folder wins over the recipe's, the recipe's study over the
    folder that sessions folder is in. Settled here rather than at the merge,
    so that the call's sessions are matched in it as well. The files read
    early stay where ``bio.anchor_command_line`` found them.
    """
    sessions = anchored.get("sessionsfolder")
    if not _named(sessions) or _named(anchored.get("studyfolder")):
        return anchored
    if not _named(recipe.get("studyfolder")):
        return anchored
    return {**anchored, "sessionsfolder": bio.run_path(sessions, recipe["studyfolder"])}


def _named(value) -> bool:
    """Whether `value` names a folder: a string that is not blank."""
    return isinstance(value, str) and bool(value.strip())


def warn_read_early(
    typed: dict, study: str | None, start: str | None, notes: list | None = None
) -> None:
    """
    ``warn_read_early(typed, study, start, notes=None)``

    Says, before any of them is read, which of the batch file, a ``.list`` of
    sessions and the recipe file the command line names -- as `typed` --
    names something in `start`, the folder the run was started from, and
    nothing in `study`, the folder it is taken from. A recipe file the command
    line names without a study is read to learn the study, from the current
    folder, and is not one of them. A warning is also added to `notes`, when
    given, for the runlog the run has not opened yet.
    """
    if not study or not start or same_folder(study, start):
        return

    early = {
        key: typed[key]
        for key in bio.READ_EARLY + ("sessions",)
        if key in typed and (key != "sessions" or bio.LIST_FILE.match(str(typed[key])))
    }
    if not any(_named(typed.get(key)) for key in FOLDERS):
        early.pop("recipe_file", None)

    warn_misplaced(misplaced(early, study, start), study, start, notes)


def without_unset(header: dict, args: dict, command: str) -> tuple[dict, list]:
    """
    ``without_unset(header, args, command)``

    The batch file header less what the run said not to take from it
    (``--unset_batch_header_parameters``), taken out before anything reads
    the header: the folders and the log folder it names place the run.

    Twice, around the remap of the deprecated spellings, because the names a
    header states and the names it contributes are not the same set -- a
    header saying ``log:`` contributes ``log`` and ``comlog_folders``, one of
    them under a name nobody wrote. Filtering on both sides is what makes
    either spelling work; ``merge_options`` remaps again and finds nothing
    left to do, the remap being idempotent.

    Returns:
        ``(header, unset)``: the header, and the names taken out of it.
    """
    return gcs.header_without_unset(header, args, command)


def hand_on_folders(options: dict, given: tuple) -> None:
    """
    ``hand_on_folders(options, given)``

    Hands the study and the sessions folder on as ``process.merge_options``
    settled them -- absolute, a relative sessions folder taken from a study
    any tier names -- to each dictionary in `given` that names them: the
    command line, and what the command is called with. An empty value, a
    folder nobody named, is left as it is.
    """
    for parameters in given:
        for key in FOLDERS:
            if parameters.get(key):
                parameters[key] = options[key]


def for_jobs(
    command: str, args: dict, options: dict, placement: gf.Placement
) -> dict:
    """
    ``for_jobs(command, args, options, placement)``

    The command line each scheduled job of the run is handed: `args`, with
    the study and the sessions folder the run settled, absolute, when the run
    knows its study and its command line does not name them. A job reads the
    batch file header again where it starts, which ``--scheduler_workdir``
    can make another folder than the one a relative study in it was read
    from. A study found only by its marker or as the current folder's parent
    is not handed on: such a run works in the current folder, as each of its
    jobs does. Not for ``run_recipe``, whose command line overrides what each
    of its steps states, nor for a command that creates its study.
    """
    if not placement.known or command == "run_recipe" or command in bio.CREATES_STUDY:
        return args

    folders = {
        "studyfolder": placement.studyfolder,
        "sessionsfolder": options.get("sessionsfolder"),
    }
    return {
        **args,
        **{
            key: value
            for key, value in folders.items()
            if _named(value) and not _named(args.get(key))
        },
    }


def place_run(
    command: str,
    args: dict,
    batch_header: dict | None,
    timestamp: str,
    qx_command=None,
    recipe: dict | None = None,
) -> gf.Placement:
    """
    ``place_run(command, args, batch_header, timestamp, qx_command=None, recipe=None)``

    Where a run is, where it takes its relative paths from, and where it
    logs: the one decision every entry point makes the same way,
    ``general.folders.run_folders``, from the tiers ``gmri`` knows -- the
    command line, the recipe file of a ``run_recipe`` run, and the batch file
    header, in that order. The logging settings are resolved for the study
    that answer names, so a study named only in a recipe file or a batch file
    header has its ``qunex_settings.yaml`` read as well.

    Called in the folder the run was started in. `recipe` is the recipe
    file's tier :func:`anchor` read; it is read here only when it is not
    given.

    Returns:
        the ``general.folders.Placement``; its ``settings`` are the resolved
        ``LogSettings``.
    """
    if recipe is None:
        recipe = {}
        if command == "run_recipe":
            recipe = gr.recipe_folders(args.get("recipe_file"), args.get("recipe"))

    return gf.run_folders(
        gf.run_name(command, args),
        [args, recipe, batch_header],
        timestamp,
        settings=lambda study: gl.resolve_logging(
            command,
            args,
            qx_command=qx_command,
            studyfolder=study,
            legacy_skip=gcs.logskip_commands,
        ),
        creating=command in bio.CREATES_STUDY,
    )


def work_in_study(
    command: str,
    placement: gf.Placement,
    typed: dict,
    start: str | None,
    scheduled: bool = False,
    notes: list | None = None,
) -> tuple[bool, str | None]:
    """
    ``work_in_study(command, placement, typed, start, scheduled=False, notes=None)``

    Enters the folder the run takes its relative paths from,
    ``placement.base``. Before it does, it warns about the values the run was
    given -- as `typed` -- that name something in `start`, the folder it was
    started from, and nothing in the study. A study the run names that does
    not exist yet leaves it where it is, and is said; under a scheduler each
    job decides again. ``run_recipe`` stays where it is: each of its steps is
    a run of its own and enters its own study. Each warning is also added to
    `notes`, when given, for the runlog the run has not opened yet.

    Returns:
        ``(moved, workfolder)``: whether the current folder changed, and the
        folder the run works in, None for the current folder.
    """
    recipe = command == "run_recipe"
    workfolder = None if recipe else placement.base

    missing = None
    if placement.known and placement.base is None and not recipe:
        if command not in bio.CREATES_STUDY:
            missing = placement.studyfolder

    if workfolder and start and not same_folder(workfolder, start):
        # `session` is the id of the session a script runs, as `sessions` is
        skip = set(gcs.extra_parameters) | {"session"}
        warn_misplaced(
            misplaced(typed, workfolder, start, skip=skip),
            workfolder,
            start,
            notes,
        )
    elif missing:
        warn(
            "WARNING: The study folder [%s] does not exist yet (or holds nothing "
            "but logs), relative paths are taken from the current folder [%s]."
            % (missing, start),
            notes,
        )
        if scheduled:
            warn(
                "WARNING: Each job decides again when it starts: a job that "
                "starts after an earlier one has created the study takes them "
                "from the study. Give them as absolute paths, or create the "
                "study first.",
                notes,
            )

    return enter(workfolder, notes), workfolder


def warn(text: str, notes: list | None = None) -> None:
    """Prints a warning to stderr, and adds it to `notes` when given."""
    print(text, file=sys.stderr)
    if notes is not None:
        notes.append(text)


def same_folder(a, b):
    """Whether `a` and `b` are one folder, however each is spelled."""
    try:
        return os.path.samefile(a, b)
    except OSError:
        return os.path.normpath(a) == os.path.normpath(b)


def enter(folder, notes=None):
    """
    ``enter(folder, notes=None)``

    Changes into `folder`, the study a run works in, so that the command, and
    every script and tool it starts -- which inherit the folder -- take their
    relative paths from there. Returns True when the current folder changed;
    False when `folder` is not given, is the current folder already, or can not
    be entered, which is said with a warning (added to `notes` as well, when
    given).
    """
    try:
        start = os.getcwd()
    except OSError:
        start = None
    if not folder or (start and same_folder(folder, start)):
        return False

    try:
        os.chdir(folder)
    except OSError as e:
        warn(
            "WARNING: The study folder [%s] can not be entered (%s), relative "
            "paths are taken from the current folder [%s]."
            % (folder, e.strerror or e, start),
            notes,
        )
        return False
    return True


def misplaced(given, base, start, skip=()):
    """
    ``misplaced(given, base, start, skip=())``

    The values among `given` -- as they were typed -- that are relative paths
    naming something in `start`, the folder the run was started from, and
    nothing in `base`, the study they are taken from. The one mistake taking
    relative paths from the study makes likely, as `--<key>=<value>` strings.
    Keys in `skip` are not looked at.
    """
    found = []
    for key, value in given.items():
        if key in skip or not isinstance(value, str):
            continue
        value = value.strip()
        if not value or os.path.isabs(os.path.expanduser(value)):
            continue
        if os.path.exists(os.path.join(start, value)) and not os.path.exists(
            os.path.join(base, value)
        ):
            found.append("--%s=%s" % (key, value))
    return found


def warn_misplaced(values, base, start, notes=None):
    """Says which values `misplaced` found, and what to do about them."""
    if values:
        warn(
            "WARNING: Relative paths are taken from the study folder [%s], not "
            "from the current folder [%s]. These name something in the current "
            "folder and nothing in the study folder: %s. Give them as absolute "
            "paths, or relative to the study folder."
            % (base, start, ", ".join(values)),
            notes,
        )


def print_log_folder(args: dict) -> None:
    """
    ``gmri log_folder --command=<command> [--timestamp=<stamp>] [<parameters>]``

    Prints the folder a run of `<command>` with `<parameters>` logs in, as
    ``gmri`` would place a run started here: its command line anchored as
    :func:`anchor` anchors it, and the header of a batch file it names taken
    as ``gmri`` takes it. For ``bin/qunex.sh``, which runs one command itself
    and has to log it where every other command logs. Not a registered
    command: nothing about it is logged, and anything it warns about is
    printed before the folder, which is the last line.

    Raises:
        ge.CommandError: when `--command` is not given.
    """
    args = dict(args)
    command = args.pop("command", None)
    if not _named(command):
        raise ge.CommandError(
            "log_folder", "Missing parameter", "--command is required"
        )

    timestamp = args.pop("timestamp", None)
    if not _named(timestamp):
        timestamp = datetime.now().strftime(gf.TIMESTAMP)

    args = gcs.check_deprecated_parameters(args, command)
    args, recipe, _, _ = anchor(command, args)

    header = {}
    if _named(args.get("batchfile")):
        _, header = gc.resolve_sessions(
            batchfile=args["batchfile"],
            command=command,
            verbose=False,
            resolve_folders=False,
        )
        header, _ = without_unset(header, args, command)

    print(place_run(command, args, header, timestamp, recipe=recipe).logfolder)

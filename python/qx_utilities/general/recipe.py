#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``recipe.py``

Run recipe framework.
"""

# Copyright (c) Grega Repovs and Jure Demsar. All rights reserved.

import os
import os.path
import re
import shlex
import subprocess
import sys
from datetime import datetime

import qx_utilities.general.batch_io as bio
import qx_utilities.general.commands_support as gcs
import qx_utilities.general.exceptions as ge
import qx_utilities.general.folders as gf
import qx_utilities.general.log as gl
import qx_utilities.general.xnat as gx
import yaml
from qx_registry import qx_commands

# the parameters that place the recipe's own run. Decided once, for the run, they
# are not inherited by its steps: every step logs in the run's folder, and
# reports to the status record the recipe names for it
RUN_PLACEMENT = ("logfolder", "logstatus")


def run_recipe(recipe_file=None, recipe=None, steps=None, startwith=None, logfolder=None, eargs=None, log_settings=None):
    """
    ``run_recipe [recipe_file=None] [recipe=None] [steps=None] [startwith=None] [logfolder=None] [<extra arguments>]``

    A command for chaining multiple commands through recipe files and recipes.

    ..  qx_command:
        type: utility

    Parameters:
        --recipe_file (str):
            Path to a YAML file that contains recipe definitions.

        --recipe (str):
            Name of the recipe in the recipe_file to run.

        --startwith (str, default ''):
            Name of the step (QuNex command) in the recipe to start with. If
            provided, the execution of the recipe will start with the specified
            step, skipping any preceding steps.

        --steps (str, default ''):
            A comma separated list of steps (QuNex commands) to run. This can
            be used to run only a subset of commands from the list or as an
            alternative to specifying the recipe file and a recipe name.

        --logfolder (str, default '<studyfolder>/logs/<date>_<time>_run_recipe_<recipe>'):
            The folder this run logs in: the run_recipe runlog, the runlog and
            comlogs of every step and of every recipe run for a set of
            sessions, and the steps' status records in its `status` folder. A
            relative path is taken from the study when the run knows its study
            and that study exists -- holds more than logs -- else from the
            current folder; `legacy` is `<studyfolder>/processing/logs`. A
            `logfolder` the recipe file states is used when the command line
            gives none (see Notes).

        --eargs:
            Other arguments that can be passed to the command (see Notes).

    Notes:

        Running external scripts:
            If a command in the recipe is specified as `external`, it will be
            ran as an external command. The path to the command needs to be
            provided in the `path` parameter. The command can be a binary or a
            script. If it is a script, the type of the script needs to be
            specified through the extension (e.g. .sh, .py, .R). The parameters
            for the external command can be provided in the same way as for
            QuNex commands, but they will be passed to the command as command
            line arguments, by default in the form of `--<parameter>=<value>`.
            User can tweak this by setting the external_parameter_prefix and
            external_parameter_delimiter parameters for the script. The first
            one defines the prefix for the parameters (default is "--"), while
            the second one defines the delimiter between the parameter name and
            value (default is "="). For example, if the prefix is set to "-" and
            the delimiter is set to " ", the parameters will be passed in the form
            of `-<parameter> <value>`. A relative `path` is found, and the
            command is run, in the study (see Recipe file and recipes).

        Parallelism:
            These parameters allow spreading processing of multiple sessions
            across multiple run_recipe invocations:

            --batchfile     A path to a batch.txt file.

            --sessions      Either a string with comma separated list of
                            sessions (sessions ids) to be processed (use of grep
                            patterns is possible), e.g.  `"OP128,OP139,ER*"` or
                            `*list` file with a list of session ids.

            --scheduler     An optional scheduler settings description string.
                            If provided, each run_recipe invocation will be
                            scheduled to run on a separate cluster node.

            With `--scheduler` the run is submitted as jobs -- one per chunk of
            `parsessions` sessions, or one for the whole recipe without
            sessions -- and every job logs in the run's log folder.

            A `scheduler` stated in the recipe file for a step submits that
            step to the scheduler: `run_recipe` does not wait for its jobs,
            goes on to the next step while they run, and says so. To run the
            steps of a recipe in order on a cluster, schedule the `run_recipe`
            call itself.

            To setup run_recipe parallelism, you can use the traditional
            parsessions and parelements parameters.

            --parsessions   An optional parameter specifying how many sessions
                            to run in parallel.

            --parelements   An optional parameter specifying how many elements
                            to run in parallel within each of the jobs (e.g. how
                            many bolds).

            The parsessions parameter defines the number of sessions that will
            be ran in parallel within a single run_recipe invocation. The
            default is 1, which means that each session will be ran in parallel
            within a separate job. If parsessions is set to the number of
            sessions, then all the sessions will  be executed in sequence within
            a single run_recipe invocation.

        Recipe file and recipes:
            run_recipe takes a `recipe_file` and a `recipe` name and executes
            the commands defined in the recipe. The `recipe_file` contains
            commands that should be run and parameters that it should use.
            Alternatively, you can provide a comma separated list of commands
            with the `steps` parameter.

            All the logs of a `run_recipe` call are kept in one folder: its
            own runlog, the runlog and comlogs of every step and of every
            recipe it runs for a set of sessions -- scheduled or not -- and
            the steps' status records in its `status` folder. By default it is
            `<studyfolder>/logs/<date>_<time>_run_recipe_<recipe>`
            (`run_recipe_steps` for `--steps` without a recipe file). The
            study is the one named on the command line, else in the recipe
            file, else in the header of the batch file the command line
            names, else the one marked by `.qunexstudy` at or above the
            current folder; with none, the logs go where a run outside a
            study logs (`~/qunex_logs`, unless the `outside_study` setting
            says otherwise). The folder is created before the first step
            runs, so a recipe can name a study its own `create_study` step
            creates; a relative `logfolder` is then taken from the current
            folder, the study not existing yet. If the folder can not be
            created the `run_recipe` command will exit with a failure.

            `run_recipe` is checking for a successful completion of commands
            that it runs. If any of the commands fail to complete successfully,
            the execution of the commands will stop and the failure will be
            reported both in stdout as well as the log.

            Individual commands that are run can generate their own logs, the
            presence and location of those logs depend on the specific command
            and settings specified in the recipe file.

            Recipe files use YAML markup language. At the top of the recipe file
            is the global_parameters section, where the global settings are
            defined in the form of `<parameter>: <value>` pairs. These are the
            settings that will be used as defaults throughout all recipes and
            individual commands defined in the rest of the recipe file.

            The study is best named there once, with `studyfolder`: every QuNex
            command in the recipe is given it, the commands that work on
            sessions take them from its `sessions` folder, and the logs go to
            its `logs` folder, however the recipe is run. Set `sessionsfolder`
            as well only when the sessions are in another folder.

            Every relative path in the recipe is taken from the study the step
            it is given to works in -- the one named on the command line, else
            the step's own, else the recipe's -- once that study exists; a
            relative `studyfolder` itself is taken from the folder `run_recipe`
            is started in. `--recipe_file` is taken from the study the command
            line names (or the folder a `--sessionsfolder` it names is in),
            else from the current folder, and a relative `--batchfile` or
            `.list` file given to `--sessions` from that study, else from the
            recipe's, else from the current folder. An external step is found
            and run in the study, or -- while the study does not exist yet, as
            before the recipe's `create_study` step -- in the folder
            `run_recipe` was started in; a study folder that holds nothing but
            the recipe's logs counts as one that does not exist yet.

            Recipes are defined in the recipes portion of the file where each
            recipe is defined by its unique name. Each recipe has two sections,
            the parameters and the commands. The parameters section defines the
            parameters and the values that are specific to that recipe. The
            commands section defines the commands that are specific to that
            recipe along with command specific parameters. All parameters are
            provided in the form of <parameter>:<value> pairs. Recipe level
            parameters have a higher priority than global parameters, while
            command level parameters have a higher priority than recipe level
            parameters. Parameters provided through the command line interface
            call have the highest priority, meaning that their values will
            override any values in recipe files.

        Parameters a step is not to inherit:
            A parameter stated for the whole run is passed to every command
            that accepts it. When a step must not have one, say so, in either
            of two ways. Write `unset_parameters`, which takes a parameter
            name, a comma separated list of them, or an array::

                - create_session_info:
                    mapping          : /data/specs/hcp_mapping.txt
                    unset_parameters : batchfile

            or write the name itself with a leading `-` and no value::

                - create_session_info:
                    mapping    : /data/specs/hcp_mapping.txt
                    -batchfile :

            Both are accepted against a step and in a recipe's parameters
            section, where they hold for every step of that recipe. Neither is
            allowed in global_parameters: a parameter unset for every command
            of the run is one that need not be written at all.

            Note that an empty value does *not* unset a parameter. `''` and
            `None` are values commands accept, so `img_suffix : ""` states the
            empty string rather than removing the parameter.

            `unset_parameters` is about what the recipe hands a step. What a
            *batch file* hands a command is a separate question, answered by
            `unset_batch_header_parameters` and
            `unset_batch_session_parameters`, which may also be written against
            a command, for a recipe or in global_parameters -- and, unlike this
            one, are allowed at the global level, the batch file not being
            something the recipe supplies.

        A batch file the recipe itself creates:
            A recipe usually states the study's `batchfile` globally and then
            builds that file with `create_batch` partway through. The steps
            before it cannot be given a file that does not exist yet, and
            `create_batch` cannot be told to take its sessions from the file
            it is about to write, so `run_recipe` withholds the run wide
            `batchfile` from every step up to and including the one that
            writes it, and reports that it did.

            If the file already exists, it is still withheld -- so that
            running a recipe a second time does what running it the first time
            did -- and a warning says so. If one of those steps is meant to
            read the file that is there, state `batchfile` against that step.

            If nothing creates the file and it does not exist, the recipe does
            not start: no step would ever have been able to read it. A recipe
            whose steps all resolve their sessions from the sessions folder is
            unaffected, since none of them takes a batch file.

        Example recipe file:
            ::

                global_parameters:
                    studyfolder       : /data/qx_study
                    sessions          : OP101,OP102
                    overwrite         : yes
                    batchfile         : /data/qx_study/processing/batch.txt

                recipes:
                    onboard_dicom:
                        commands:
                            - external:
                                path: /scripts/data_download.sh
                                url: www.dummy.com/mri/data
                                out_dir: /data/qx_data
                                external_parameter_prefix: "-"
                                external_parameter_delimiter: " "
                            - create_study
                            - import_dicom:
                                inbox: /data/qx_data
                                archive: leave
                            - create_session_info:
                                mapping: /data/qx_specs/hcp_mapping.txt
                            - create_batch:
                                targetfile: /data/qx_study/processing/batch.txt
                                paramfile : /data/qx_specs/hcp_parameters.txt
                            - setup_hcp

                    hcp_preprocess:
                        parameters:
                            parsessions: 2

                        commands:
                            - hcp_pre_freesurfer
                            - hcp_freesurfer
                            - hcp_post_freesurfer
                            - hcp_fmri_volume
                            - hcp_fmri_surface

                    hcp_denoise:
                        commands:
                            - hcp_icafix:
                                hcp_matlab_mode: "{{$MATLAB_MODE}}"
                            - hcp_msmall:
                                hcp_matlab_mode: "{{$MATLAB_MODE}}"

    Examples:
        ::

            qunex run_recipe \\
            --recipe_file="/data/settings/recipe.yaml" \\
            --recipe="onboard_dicom"

        ::

            qunex run_recipe \\
            --recipe_file="/data/settings/recipe.yaml" \\
            --recipe="hcp_preprocess" \\
            --batchfile="/data/testStudy/processing/batch_baseline.txt" \\
            --scheduler="SLURM,jobname=doHCP,time=04-00:00:00,cpus-per-task=2,mem-per-cpu=40000,partition=week"

        ::

            export MATLAB_MODE="interpreted"
            qunex run_recipe \\
            --recipe_file="/data/settings/recipe.yaml" \\
            --recipe="hcp_denoise"

        ::

            export MATLAB_MODE="interpreted"
            qunex run_recipe \\
            --recipe_file="/data/settings/recipe.yaml" \\
            --recipe="hcp_denoise" \\
            --steps="hcp_icafix"

        ::

            qunex run_recipe \\
            --studyfolder="/data/qx_study" \\
            --batchfile="/data/qx_study/processing/batch.txt" \\
            --steps="hcp_pre_freesurfer,hcp_freesurfer,hcp_post_freesurfer"

        The first call will execute all the commands in recipe `onboard_dicom`.

        The second call will execute all the steps of the HCP preprocessing
        pipeline via a scheduler. It will execute two sessions in parallel
        within the run, and the steps in sequence.

        The third call will execute the hcp_denoise list where the
        hcp_matlab_mode parameter will be set to "interpreted" this value will
        be read from the system environment variable $MATLAB_MODE. This is an
        example of how you can inject custom values into specially marked slots
        (marked with "{{<label>}}") in the recipe file. Note that the labels
        need to be provided in the form of a string, so they need to be
        encapsulated with double quotes.

        The fourth call is the same as the third call, except that only
        hcp_icafix will be executed from the hcp_denoise list.

        The fifth example shows how to use the steps parameter to run a set of
        commands sequentially.
    """

    flags = ["test"]

    # a parameter given on the command line without a value arrives as True,
    # as does one whose value was split off by a space instead of `=`. As a
    # recipe file, True is opened as the file descriptor 1: the recipe read
    # its own standard output and closed it
    for name, value in (
        ("recipe_file", recipe_file),
        ("recipe", recipe),
        ("steps", steps),
        ("startwith", startwith),
        ("logfolder", logfolder),
    ):
        if isinstance(value, bool):
            raise ge.CommandError(
                "run_recipe",
                "Invalid parameter value!",
                f"--{name} was given without a value.",
                f"Please give it as --{name}=<value>!",
            )

    if recipe_file is None and steps is None:
        raise ge.CommandError(
            "run_recipe",
            "both recipe_file and steps are not specified",
            "No recipe file or steps specified",
            "Please provide path to the recipe file or a comma separated list of steps to run!",
        )

    if recipe_file is not None and recipe is None:
        raise ge.CommandError(
            "run_recipe",
            "recipe not specified",
            "No recipe specified",
            "Please provide the recipe name!",
        )

    if recipe_file is not None and not os.path.isfile(recipe_file):
        raise ge.CommandFailed(
            "run_recipe",
            "recipe file does not exist",
            f"Recipe file not found [{recipe_file}]",
            "Please check your paths!",
        )

    if startwith and recipe is None:
        raise ge.CommandError(
            "run_recipe",
            "startwith specified without a recipe",
            "No recipe specified",
            "Please provide --recipe together with --recipe_file when using --startwith!",
        )

    # parse the recipe file
    parameters = {}
    recipe_unset = []
    commands = []

    timestamp = datetime.now().strftime(gf.TIMESTAMP)

    # open the recipe file
    if recipe_file:
        with open(recipe_file, "r", encoding="UTF-8") as file:
            try:
                recipe_data = yaml.load(file, Loader=yaml.FullLoader)
            except Exception:
                raise ge.CommandFailed("run_recipe", "Cannot parse the recipe file")

        # get the recipe
        recipes = recipe_data.get("recipes") if isinstance(recipe_data, dict) else None
        if not isinstance(recipes, dict):
            raise ge.CommandFailed("run_recipe", "Recipes not found in the recipe file")

        if recipe not in recipes:
            raise ge.CommandFailed(
                "run_recipe", f"Recipe {recipe} not found in the recipe file"
            )

        # a recipe with nothing written under it states nothing, and is
        # reported below as one without commands
        recipe_dict = recipes[recipe]
        if not isinstance(recipe_dict, dict):
            recipe_dict = {}

        # global parameters
        global_parameters = _section(
            recipe_data, "global_parameters", "the recipe file"
        )
        if _states_an_unset(global_parameters):
            raise ge.CommandError(
                "run_recipe",
                "Parameters cannot be unset globally",
                "global_parameters unsets a parameter, which can only be a mistake:",
                "a parameter stated for no command at all is one not written.",
                "Move the unset to the recipe, or to the step that is not to inherit it.",
            )
        parameters.update(global_parameters)

        # recipe parameters
        recipe_parameters = _section(recipe_dict, "parameters", f"recipe {recipe}")
        recipe_unset = _unset_names(recipe_parameters, f"recipe {recipe}")
        parameters.update(recipe_parameters)

        # what the recipe unsets, no step of it inherits
        for name in recipe_unset:
            parameters.pop(name, None)
    else:
        # define recipe name
        recipe = "steps"

        # create the commands dict
        recipe_dict = {}
        recipe_dict["commands"] = steps.split(",")

    # log location
    #
    # The run's folder, by the rule every entry point follows
    # (`general.folders.run_folders`). Called through `gmri` it is handed the
    # folder `gmri` decided -- the recipe file is a tier `gmri` reads before
    # anything is logged -- as `logfolder`, and uses it as it is. Called on its
    # own it decides it here the same way: the call (`eargs`, `logfolder`) over
    # the recipe's run wide parameters, over the header of the batch file the
    # call names.
    #
    # Labels are injected first, and not only into `logfolder`: these are the
    # values this run resolves its own study, log folder and status paths
    # from, and a `{{$VAR}}` left in any of them is a folder of that name.
    # Every path the recipe derives and every path it hands a step then come
    # from the same resolved text.
    called = dict(eargs or {})
    if logfolder:
        called["logfolder"] = logfolder
    called = {key: _inject_labels(value) for key, value in called.items()}
    stated = {key: _inject_labels(value) for key, value in parameters.items()}

    # what the run states, the call winning over the recipe file, with the
    # folders it names settled as a run settles them: the study from the
    # current folder, a sessions folder from that study
    hints = _settle_folders({**stated, **called})

    placement = gf.run_folders(
        gf.run_name("run_recipe", {"recipe_file": recipe_file, "recipe": recipe}),
        [called, stated, _call_header(called, stated) if not logfolder else {}],
        timestamp,
        settings=lambda study: (
            log_settings or gl.resolve_logging("run_recipe", hints, studyfolder=study)
        ),
    )

    # the study the run is in, which the batch file a step writes by default
    # is predicted in when no study is named for it
    folders = {"basefolder": placement.studyfolder}

    run = gl.RunContext(
        "run_recipe",
        hints,
        placement.settings,
        timestamp=timestamp,
        name=placement.name,
        logfolder=placement.logfolder,
    )

    # the settings this run is logged by, for the deep helpers
    gl.set_active(placement.settings)

    if run.settings.enabled:
        print(f"\n---> Logs: {run.logfolder}")

    # a recipe that cannot log is a recipe that fails, as documented above --
    # unless it was told not to log at all
    try:
        if run.settings.enabled:
            os.makedirs(run.logfolder, exist_ok=True)
    except OSError:
        raise ge.CommandFailed(
            "run_recipe",
            "Cannot open log",
            f"Unable to create the log folder [{run.logfolder}]",
            "Please check the paths!",
        )

    # the study the steps work in, and so the one an external step is found
    # and run in: the one the command line names, as it wins for every step,
    # else the recipe's own. The study this run is placed in, when it knows it
    base = _recipe_study(parameters, eargs)

    # run
    summary = "\n----==== RECIPE EXECUTION SUMMARY ====----"

    run.header()
    run.write(
        "\n\n============================== RUN_RECIPE LOG ==============================\n\n"
    )

    summary += f"\n\nRecipe: {recipe}"

    print(f"---> Running commands from recipe: {recipe}")
    run.write(f"---> Running commands from recipe: {recipe}\n\n")

    # commands: a list of steps, which `commands:` with nothing under it is not
    if not isinstance(recipe_dict.get("commands"), list):
        raise ge.CommandFailed(
            "run_recipe", f"Recipe {recipe} missing commands specification"
        )

    commands = recipe_dict["commands"]
    # subset commands when using both the recipe and steps
    if steps and recipe_file:
        commands_subset = []
        steps = [s.strip() for s in steps.split(",")]
        for com in commands:
            if isinstance(com, dict):
                key = list(com.keys())[0]
                if key in steps:
                    commands_subset.append(com)
                elif key == "external":
                    for step in steps:
                        if com["external"]["path"].endswith(step):
                            commands_subset.append(com)
                # backwards compatibility
                elif key == "script":
                    for step in steps:
                        if com["script"]["path"].endswith(step):
                            commands_subset.append(com)
            elif com in steps:
                commands_subset.append(com)

        commands = commands_subset

    commands_skipped = []
    if startwith and startwith.strip() != "":
        start_indices = [
            idx for idx, command_spec in enumerate(commands)
            if _get_command_name(command_spec) == startwith
        ]

        if not start_indices:
            print(f"WARNING: startwith step [{startwith}] is not a part of recipe [{recipe}].")
            run.write(f"WARNING: startwith step [{startwith}] is not a part of recipe [{recipe}].\n")
            raise ge.CommandError(
                "run_recipe",
                "startwith step not found in recipe",
                "Startwith step not found",
                "Please check the recipe steps and provide a valid --startwith step name!",
            )

        if len(start_indices) > 1:
            print(f"WARNING: startwith step [{startwith}] is present more than once in recipe [{recipe}]. Starting with the first occurrence.")
            run.write(f"WARNING: startwith step [{startwith}] is present more than once in recipe [{recipe}]. Starting with the first occurrence.\n")

        start_index = start_indices[0]
        commands_skipped = commands[:start_index]
        commands = commands[start_index:]

    # print commands
    def _print_commands(title, command_list):
        print(title)
        run.write(title + "\n")
        commands_set = []
        for com in command_list:
            if isinstance(com, dict):
                command_name = list(com.keys())[0]
            else:
                command_name = com
            if command_name not in commands_set:
                commands_set.append(command_name)
                print(f"    - {command_name}")
                run.write(f"    - {command_name}\n")

    if startwith:
        _print_commands("\n---> Commands skipped:", commands_skipped)
        _print_commands("\n---> Commands to run:", commands)
    else:
        _print_commands("\n---> Commands:", commands)

    # what a run wide parameter names that this recipe writes itself
    withheld = _withheld_by_production(
        commands, parameters, recipe_unset, hints, folders, run, eargs
    )

    # XNAT initial setup
    # If running on XNAT, try and load checkpoint if supplied
    if os.environ.get("XNAT", "") == "yes":
        checkpoint_str = os.environ.get("XNAT_CHECKPOINT", "")
        run.write("Checkpoint Supplied: " + checkpoint_str + "\n")
        print("Checkpoint Supplied: " + checkpoint_str)

        if checkpoint_str == "":
            run.write("XNAT Checkpoint empty, skipping...\n")
            print("XNAT Checkpoint empty, skipping...")
        else:
            file_path, find_summary = gx.xnat_find_checkpoint(checkpoint_str)
            run.write(find_summary + "\n")
            load_summary = gx.xnat_load_checkpoint(file_path)
            run.write(load_summary + "\n")

    # a dry run: --test on the call, or stated for the whole recipe. A step
    # that does not read it -- an external one, a utility -- is named rather
    # than run; the steps that do are handed it
    dry = "test" in (eargs or {}) or "test" in parameters

    for step, com in enumerate(commands, start=1):
        if isinstance(com, dict):
            command_name = list(com.keys())[0]
            command_parameters = list(com.values())[0]
        else:
            command_name = com
            command_parameters = {}

        # executing a custom script
        if command_name == "script" or command_name == "external":
            if "path" in command_parameters:
                external_path = _inject_labels(command_parameters["path"])

                del command_parameters["path"]
            else:
                summary += f"\n - external {command_parameters} ... FAILED"
                _print_end_summary(
                    summary, run, f"{command_parameters} path not provided!"
                )

                raise ge.CommandFailed(
                    "run_recipe",
                    "Path to the external script or programme not provided",
                    f"Path not provided [{command_parameters}]",
                    "Please provide the path!",
                )
            print(
                f"\n--------------------------------------------\n---> Running external: {external_path}"
            )
            run.write(
                f"\n--------------------------------------------\n---> Running external: {external_path}\n"
            )

            # found in, and run in, the study the steps work in, so that a
            # relative path it is given means what it means to every QuNex
            # step. Asked when the step is reached: a step before the one that
            # creates the study is found and run where the recipe was started.
            # A folder holding nothing but logs is a study that does not exist
            # yet -- this run's own log folder may be the one thing in it
            workdir = base if base and gf.study_exists(base) else os.getcwd()
            if base and workdir != base:
                note = (
                    f"WARNING: the study folder [{base}] does not exist yet (or "
                    f"holds nothing but logs), {external_path} is found and run "
                    f"in the current folder [{workdir}]"
                )
                print(note)
                run.write(note + "\n")
            external_file = bio.run_path(external_path, workdir)

            if not os.path.exists(external_file):
                summary += f"\n - external {external_path} ... FAILED"
                _print_end_summary(summary, run, f"{external_file} does not exist!")

                raise ge.CommandFailed(
                    "run_recipe",
                    "External command not found",
                    f"External command not found [{external_file}]",
                    "Please check the external command path!",
                )

            external_name = os.path.basename(external_path)

            # prep command: the type is the file's own extension -- a dot in a
            # folder name says nothing about it
            if external_name.endswith(".sh") or "." not in external_name:
                command = ["bash", external_file]
            elif external_name.endswith(".py"):
                command = ["python", external_file]
            elif external_name.endswith(".R"):
                command = ["Rscript", external_file]
            else:
                # ended as every other failing step ends, so the runlog says so
                summary += f"\n - external {external_path} ... FAILED"
                _print_end_summary(
                    summary, run, f"{external_path} is not of a type run_recipe runs!"
                )

                raise ge.CommandFailed(
                    "run_recipe",
                    "External command type not supported",
                    f"External command type not supported [{external_path}]",
                    "Please use binaries, .sh, .py or .R scripts!",
                )

            # prefix and delimiter
            external_parameter_prefix = command_parameters.pop(
                "external_parameter_prefix", "--"
            )
            external_parameter_delimiter = command_parameters.pop(
                "external_parameter_delimiter", "="
            )

            # add parameters to the command, with the labels the recipe author
            # wrote against this step injected, as for a QuNex step
            for param, value in command_parameters.items():
                try:
                    value = _inject_labels(value)
                except ge.CommandFailed:
                    summary += f"\n - external {external_path} ... FAILED"
                    _print_end_summary(
                        summary,
                        run,
                        f"Failed running external {external_path}! Cannot inject values marked with double curly braces in the recipe.",
                    )
                    raise

                command.append(
                    f"{external_parameter_prefix}{param}{external_parameter_delimiter}{value}"
                )

            if dry:
                note = f"    ... test, not run: {shlex.join(command)} (in {workdir})"
                print(note)
                run.write(note + "\n")
                summary += f"\n - external {external_path} ... test, not run"
                continue

            # the external command's output is this step's comlog: opened as
            # `tmp_`, renamed by the exit status when it closes -- in the
            # step's own folder under `layout: nested`, as a command's is
            comlog = gl.ComContext(
                _step_folder(run, step, external_name, "comlogs"),
                external_name,
                command_name,
                enabled=run.settings.enabled and run.settings.comlog,
            ).open()

            process = subprocess.Popen(
                command, stdout=comlog.file, stderr=subprocess.STDOUT, cwd=workdir
            )
            process.communicate()

            # Get the exit code
            exit_code = process.returncode
            comlog_path = comlog.close(status="error" if exit_code else "done")

            if exit_code != 0:
                report = f"    ... failed [{external_path}], see [{comlog_path}]"
                print(report)
                run.write(report + "\n")

                summary += f"\n - external {external_path} ... FAILED"
                _print_end_summary(summary, run, f"Failed external {external_path}!")

                raise ge.CommandFailed(
                    "run_recipe",
                    "External command failed",
                    f"External command failed [{external_path}]",
                    "Please check the log for details!",
                )
            else:
                summary += f"\n - external {external_path} ... OK"
                report = f"    ... done [{external_path}], see [{comlog_path}]"
                print(report)
                run.write(report + "\n")

        elif qx_commands.get(command_name) is not None:
            # what this step is not to inherit from the tiers above it
            unset = set(recipe_unset) | set(
                _unset_names(command_parameters, f"step {step} ({command_name})")
            )

            # where each of this step's parameters came from, so that what the
            # command cannot take can be reported to whoever wrote it: the
            # recipe states these against the command itself, the tiers below
            # state them for every command of the run
            sources = dict.fromkeys(command_parameters, "recipe")

            # override params with those from eargs (passed because of parallelization on a higher level)
            #
            # but for the ones that placed this run: the step is told below
            # where to log and where to report
            if eargs is not None:
                for k in eargs:
                    if k in unset or k in RUN_PLACEMENT:
                        continue
                    if k in ["parsessions", "parelements"]:
                        if k in command_parameters:
                            command_parameters[k] = str(
                                min([int(e) for e in [eargs[k], command_parameters[k]]])
                            )
                    else:
                        command_parameters[k] = eargs[k]
                    sources[k] = gcs.RECIPE_RUN

            # append global and recipe parameters
            #
            # A parameter naming something a later step of this recipe writes
            # is withheld until it has been written -- see `withheld` above. A
            # value written against the step itself is untouched: that one was
            # meant, and a file missing under it is still an error. Nor is what
            # placed the recipe's own run inherited: a `logfolder` stated for
            # the whole run is the run's folder, which the step is given below
            for parameter, value in parameters.items():
                if parameter in unset or parameter in RUN_PLACEMENT:
                    continue
                if step <= withheld.get(parameter, 0):
                    continue
                if parameter not in command_parameters:
                    command_parameters[parameter] = value
                    sources[parameter] = gcs.RECIPE_RUN

            # an unset is written away from the parameter it is about, so the
            # log says what it did rather than leaving a reader to notice an
            # absence in the call below
            kept_out = sorted(unset & (set(parameters) | set(eargs or {})))
            if kept_out:
                note = "\n---> %s: unset for this step, not passed to it\n" % (
                    ", ".join(kept_out)
                )
                print(note)
                run.write(note)

            # narrow to what the command accepts, and say what that leaves out:
            # a parameter written against a command that cannot take it is a
            # mistake in the recipe, and was dropped without a word
            qx_command = qx_commands.get(command_name)

            # a python command other than a processing one runs whatever --test
            # says unless it declares it: in a dry run it is named, not run
            not_run = (
                "test" in command_parameters
                and qx_command.language == "python"
                and not qx_command.type.startswith("processing")
                and "test" not in gcs.declared_parameters(qx_command)
            )

            # every python command but a processing one, as `gmri` rejects
            # what such a command does not take: `run_qa` (type `qa`) as well
            # as the utilities
            if qx_command.language == "python" and not qx_command.type.startswith(
                "processing"
            ):
                kept, dropped = gcs.select_parameters(
                    command_parameters, sources, qx_command
                )

                # the run level parameters steer `gmri` rather than the
                # command, so they go on when the command is one `gmri` can run
                # over sessions; a command that cannot has no use for them
                passthrough = set(gcs.extra_parameters)
                if not any(qx_command.has_arg(e) for e in ["sourcefolder", "folder"]):
                    # the study folder goes on as well: `gmri` derives the
                    # sessions folder from it, and files the logs under it
                    passthrough = {"logfolder", "studyfolder"}

                    # except that a command taking a batch file is handed its
                    # header whether or not it runs over sessions, so what the
                    # recipe said not to take from it has to travel with it.
                    # The nine utilities that take one, and `run_qa`, are
                    # narrowed here
                    if qx_command.has_arg("batchfile"):
                        passthrough |= {gcs.UNSET_BATCH_HEADER, gcs.UNSET_BATCH_SESSION}

                command_parameters = {
                    key: value
                    for key, value in command_parameters.items()
                    if key in kept or key in passthrough
                }

                for param in dropped:
                    warning = (
                        "\nWARNING: %s is not a parameter of %s and was not passed to "
                        "it. Please check the recipe!\n" % (param, command_name)
                    )
                    print(warning)
                    run.write(warning)

            # a bash script is handed what it declares and what the step states
            # for it. A recipe wide parameter it does not declare was meant for
            # another step, and the scripts stop on an option they do not know;
            # the run level ones go on, `gmri` runs a script over the sessions,
            # and so does --test, which `gmri` honours by not running it. So
            # does one the script reads under a name its usage text does not
            # document: run_qc takes `--bolds` for its `--bolddata`
            elif qx_command.language == "bash":
                declared = gcs.declared_parameters(qx_command)
                undeclared = {
                    key
                    for key in command_parameters
                    if key not in declared
                    and key != "test"
                    and key not in gcs.extra_parameters
                    and sources.get(key) in gcs.RUN_WIDE_SOURCES
                }
                undeclared -= _read_by_script(qx_command, undeclared)
                command_parameters = {
                    key: value
                    for key, value in command_parameters.items()
                    if key not in undeclared
                }

            # XNAT individual command prep, creates _in checkpoint
            if os.environ.get("XNAT", "") == "yes":
                run.write("Attemping XNAT specific setup...\n")
                possibles = globals().copy()
                possibles.update(locals())
                # XNAT helper functions for individual commands must be in format xnat_ + command_name
                xnat_command = possibles.get("xnat_" + command_name)
                if not xnat_command:
                    run.write(
                        "\n------------------------\n"
                        "\nNo XNAT setup method detected for: "
                        + command_name
                        + ", continuing...\n"
                        "\n------------------------\n"
                    )
                else:
                    run.write(str(xnat_command(prep=True)) + "\n")
                run.write("Making checkpoint IN...\n")
                print("Making checkpoint IN...")
                gx.xnat_make_checkpoint(
                    command_name + "_in",
                    tag=os.environ.get("XNAT_CHECKPOINT_TAG", "timestamp"),
                )

            # setup command
            #
            # A step re-enters at `gmri`, the dispatcher, rather than at
            # `qunex`, the shell front end: for a command `gmri` runs, `qunex`
            # asks it for the list of commands it runs (one python start of
            # its own), searches the matlab tree for the command's name,
            # creates a log folder `gmri` then does not use, re-quotes the
            # arguments and `eval`s the same call. The user facing spelling is
            # still what the recipe reports, because `qunex <command>` is what
            # a reader of the log would type.
            command = ["gmri"]
            command.append(command_name)
            commandr = (
                "\n--------------------------------------------\n---> Running command:\n\n     qunex "
                + command_name
            )

            # where the step logs, and where it reports back
            #
            # In the recipe's own folder: the run's logs are kept together.
            # Under `layout: nested` each step gets a folder of its own inside
            # it, numbered so the listing reads in execution order. Only a
            # `logfolder` stated against the step itself sends it elsewhere.
            # Either way the step is told where to write its status record --
            # the parent names the path, so there is nothing to glob for --
            # and the path carries this recipe's stamp, so that the recipes a
            # run starts for its sessions, which share the folder, do not
            # overwrite each other's records.
            if "logfolder" not in command_parameters:
                command_parameters["logfolder"] = _step_folder(run, step, command_name)

            status_path = os.path.join(
                run.logfolder,
                "status",
                f"{step:02d}_{command_name}-{run.timestamp}.yaml",
            )
            command_parameters["logstatus"] = status_path

            for param, value in command_parameters.items():
                # a label the recipe author wrote against this command; the
                # run level ones were injected before the folders were deduced
                try:
                    value = _inject_labels(value)
                except ge.CommandFailed:
                    summary += f"\n - command {command_name} ... FAILED"
                    _print_end_summary(
                        summary,
                        run,
                        f"Failed running command {command_name}! Cannot inject values marked with double curly braces in the recipe.",
                    )
                    raise

                if param in flags:
                    command.append(f"--{param}")
                    commandr += f" \\\n          --{param}"
                else:
                    command.append(f"--{param}={value}")
                    commandr += f" \\\n          --{param}='{value}'"

            if not_run:
                commandr = commandr.replace("---> Running command:", "---> test, not run:", 1)
                print(commandr)
                run.write(commandr + "\n")
                summary += f"\n - command {command_name} ... test, not run"
                continue

            # a scheduler stated in the recipe file submits the step: its
            # `gmri` schedules the jobs and returns, so the recipe goes on to
            # the next step without waiting for them
            if "scheduler" in command_parameters:
                warning = (
                    f"\nWARNING: the scheduler parameter stated for {command_name} in "
                    "the recipe file submits this step to the scheduler: run_recipe "
                    "does not wait for its jobs before it runs the next step. To run "
                    "the steps in order on a cluster, schedule the run_recipe call "
                    "itself.\n"
                )
                print(warning)
                run.write(warning)

            print(commandr)
            run.write(commandr + "\n")

            # run command
            #
            # the child's output is watched, not read for meaning: what the
            # step did comes back as its status record, and whether it worked
            # comes back as its exit code
            #
            # A command line says what a parameter is, never where it came
            # from, so the tier is named here: everything the recipe puts on a
            # step's command line reached the step through the recipe,
            # whatever wrote it -- the recipe file, its global parameters or
            # the call that started the recipe -- and the step's own banner
            # reports it as `recipe`. The batch file the step is given it
            # reads for itself, so that tier still names itself.
            with subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=0,
                env={**os.environ, gcs.RECIPE_PARAMETERS: ",".join(command_parameters)},
            ) as process:
                for line in iter(process.stdout.readline, b""):
                    # `readline` keeps the newline it read, so the line is
                    # relayed as it came; printing it would add a second one
                    # and double space everything every step says
                    print(line.decode("utf-8"), end="")

                exit_code = process.wait()

            run.write(_step_report(command_name, status_path, exit_code))

            if exit_code != 0:
                summary += f"\n - command {command_name} ... FAILED"
                _print_end_summary(
                    summary, run, f"Failed running command {command_name}!"
                )

                raise ge.CommandFailed(
                    "run_recipe",
                    "run_recipe command failed",
                    f"Command {command_name} inside recipe {recipe} failed",
                    "See error logs in the study folder for details",
                )
            else:
                summary += f"\n - command {command_name} ... OK"
                print(
                    f"---> Successful completion of the run_recipe command {command_name} at {datetime.now()}\n"
                )

            # XNAT individual command cleanup, creates _out checkpoint
            if os.environ.get("XNAT", "") == "yes":
                run.write("Attempting XNAT specific cleanup...\n")
                if not xnat_command:
                    print("\n------------------------")
                    run.write(
                        "\nNo XNAT cleanup method detected for: "
                        + command_name
                        + ", continuing...\n"
                    )
                    print("\n------------------------")
                else:
                    run.write(str(xnat_command(prep=False)) + "\n")
                run.write("Making checkpoint OUT...\n")
                print("Making checkpoint OUT...")
                gx.xnat_make_checkpoint(
                    command_name + "_out",
                    tag=os.environ.get("XNAT_CHECKPOINT_TAG", "timestamp"),
                )

        else:
            summary += f"\n - command {command_name} ... FAILED"
            _print_end_summary(summary, run, f"Unknown command [{command_name}]!")

            raise ge.CommandFailed(
                "run_recipe",
                "Unknown command",
                f"Unknown command [{command_name}]",
                "This is not a QuNex command or an external script!",
            )

    _print_end_summary(summary, run, None)


def _step_folder(run: gl.RunContext, step: int, name: str, *subfolders: str) -> str:
    """
    The folder step `step` of the recipe logs in: the recipe's own, or under
    `layout: nested` a numbered one of its own inside it -- for an external
    step as for a QuNex one -- and `subfolders` within that.
    """
    folder = run.logfolder
    if run.settings.layout == "nested":
        folder = os.path.join(folder, f"{step:02d}_{name}")
    return os.path.join(folder, *subfolders)


def _step_report(command_name, status_path, exit_code):
    """
    The step's own report, for the recipe log.

    Read from the status record the step was asked to write, so what the
    recipe reports is what the command reported -- the top level compiling
    its report from each command's, rather than grepping it out of a pipe.

    A step that wrote no record is reported from its **exit code**, which is
    the one thing a parent always has. A record can be missing for reasons no
    amount of care inside the child covers -- it was killed, it ran out of
    memory, the scheduler took the node -- so the recipe says what it knows
    rather than that it knows nothing. The old line said the latter, and said
    it about failures as well, so the report and the summary two screens down
    disagreed.
    """
    record = gl.read_status(status_path)

    if not record:
        outcome = (
            "completed" if exit_code == 0 else f"failed with exit code {exit_code}"
        )
        return f"\n---> {command_name}: {outcome}; no status record written\n"

    lines = [f"\n---> Report for {command_name}"]
    if record.get("runlog"):
        lines.append("     runlog: %s" % record["runlog"])
    for session in record.get("sessions") or []:
        lines.append("... %s ---> %s" % (session["id"], session["summary"]))

    return "\n".join(lines) + "\n"


def _print_end_summary(summary, run, error=None):
    summary += "\n\n----------==== END SUMMARY ====----------"

    run.write(summary + "\n")
    print(summary)

    if not error:
        run.write(
            f"\n------------------------\n"
            f"\n---> Successful completion of QuNex run_recipe at {datetime.now()}\n"
        )

        print("\n------------------------")
        print(f"---> Successful completion of QuNex run_recipe at {datetime.now()}")
    else:
        run.write(
            f"\n------------------------\n"
            f"\nERROR: {error}\n"
            f"\n---> run_recipe failed at {datetime.now()}\n"
        )

        print("\n------------------------")
        print(f"\nERROR: {error}")
        print(f"---> run_recipe failed at {datetime.now()}")


UNSET_PARAMETERS = "unset_parameters"

# What a command writes that a run wide parameter names for the steps that
# read it: `command -> (the parameter naming what it writes, the run wide
# parameter that names the same file)`. A recipe usually states the study's
# `batchfile` for the whole run and then builds it partway through, so the
# same value means "read this" after that step and nothing at all before it.
# One row today; the shape is what matters, since nothing else in the tree
# says which commands produce what another command consumes.
PRODUCERS = {"create_batch": ("targetfile", "batchfile")}


def _get_command_name(command_spec):
    """The command a step runs, whether or not it states parameters."""
    if isinstance(command_spec, dict):
        return list(command_spec.keys())[0]
    return command_spec


def _step_parameters(command_spec):
    """A step's own parameters, read without taking anything out of them."""
    stated = list(command_spec.values())[0] if isinstance(command_spec, dict) else None
    return stated or {}


def _read_by_script(qx_command, names):
    """
    The names among `names` a bash script reads although its usage text does
    not document them. The registry knows a script by its usage text alone,
    so the script is asked: a name it reads is one it matches as a case branch
    (`--name=*)`) or looks up quoted (`opts_GetOpt "--name"`). A script that
    can not be read is taken to read nothing more.
    """
    if not names:
        return set()

    # resolved as `run_bash` resolves it, so an extension's script is the one read
    root = getattr(qx_command, "root", None) or os.environ.get("QUNEXPATH", "")
    try:
        with open(os.path.join(root, "bash", qx_command.path), encoding="UTF-8") as f:
            script = f.read()
    except (OSError, UnicodeDecodeError):
        return set()

    return {
        name
        for name in names
        if re.search(r"--%s(?:=\*|\")" % re.escape(name), script)
    }


def _step_keeps_out(command_spec, name):
    """
    Whether a step would be left without the run wide value of `name` -- it
    states one of its own, or unsets it in either spelling. Read only, so it
    can be asked before the step is reached.
    """
    stated = _step_parameters(command_spec)

    if name in stated or f"-{name}" in stated:
        return True

    unset = stated.get(UNSET_PARAMETERS) or []
    if isinstance(unset, str):
        unset = unset.split(",")

    return name in [str(one).strip() for one in unset]


def recipe_folders(
    recipe_file: str | None, recipe: str | None, environ: dict | None = None
) -> dict:
    """
    ``recipe_folders(recipe_file, recipe, environ=None)``

    The recipe file's tier of the parameters that place a `run_recipe` run:
    what the recipe states for every step -- its global parameters,
    overridden by its own, less what it unsets -- that places a run
    (`general.folders.recipe_placement`), under the names the parameters have
    now and with its labels injected. The study and the sessions folder are
    settled as a run settles them (`_settle_folders`); the others -- the log
    folder and the folders a study is found from -- are left as written.

    `gmri` reads it once per `run_recipe` call, before anything else, so that
    the study the recipe names is the one its batch file, its list of
    sessions and its sessions are found in, and the one it logs in. Labels
    are injected from `environ`, the environment unless another is given --
    for a scheduled run, with what its `--bash` exports
    (`placement.run_environment`). A parameter with a label it does not hold
    is left out, with a warning: `run_recipe` stops on it when it runs,
    unless the variable is set there.

    Returns:
        the parameters, or an empty dict without a recipe file or a recipe,
        or when the file is missing or can not be parsed: `run_recipe`
        reports a recipe it can not use itself.
    """
    if (
        not isinstance(recipe_file, str)
        or not recipe
        or not os.path.isfile(recipe_file)
    ):
        return {}

    try:
        with open(recipe_file, "r", encoding="UTF-8") as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
    except Exception:
        return {}

    named, unresolved = gf.recipe_placement(data, recipe, environ)
    for key, message in unresolved:
        print(
            f"WARNING: {message} The recipe's {key} does not place this run; "
            "run_recipe stops on the label when it runs unless the variable is "
            "set there. Set the variable before the run starts, export it in "
            "--bash (export NAME=value) for a scheduled run, or name "
            "--studyfolder or --logfolder on the command line.",
            file=sys.stderr,
        )

    return _settle_folders(named)


def _call_header(called: dict, stated: dict) -> dict:
    """
    The header of the batch file the call names, less what the call unsets
    from it: the third tier a run is placed by, read as `gmri` reads it for its
    own command line -- the batch file taken from the study the call names,
    else from the one the recipe names, else from the current folder. Empty
    when the call names no batch file, or one that can not be read, which the
    steps that read it report.
    """
    batchfile = called.get("batchfile")
    if not isinstance(batchfile, str) or not batchfile.strip():
        return {}

    named = _settle_folders(
        {key: stated.get(key) for key in ("studyfolder", "sessionsfolder")}
    )
    study = gf.study_folder(named["studyfolder"], named["sessionsfolder"])
    anchored, _ = bio.anchor_command_line(
        {
            key: called[key]
            for key in ("studyfolder", "sessionsfolder", "batchfile")
            if key in called
        },
        "run_recipe",
        study=study,
    )
    try:
        _, header = bio.resolve(batchfile=anchored["batchfile"])
    except (bio.BatchError, OSError):
        return {}
    header, _ = gcs.header_without_unset(header, called, "run_recipe")
    return header


def _settle_folders(named: dict) -> dict:
    """
    Makes the study and the sessions folder `named` states absolute, in place:
    the study from the current folder, a sessions folder from that study, or
    from the current folder when there is none. Returns `named`.
    """
    study = named.get("studyfolder")
    if isinstance(study, str) and study.strip():
        study = named["studyfolder"] = bio.run_path(study)
    else:
        study = None

    sessions = named.get("sessionsfolder")
    if isinstance(sessions, str) and sessions.strip():
        named["sessionsfolder"] = bio.run_path(sessions, study)
    return named


def _step_study(
    command_spec: dict | str | None, parameters: dict | None, eargs: dict | None
) -> str | None:
    """
    The study a step works in, as its own `gmri` settles it from what the step
    loop of `run_recipe` hands it: of the study folder and the sessions
    folder, the command line's, else the step's own, else the recipe's --
    each under the name it has now, as `gmri` remaps a deprecated one. The
    study is the study folder, else the folder the sessions folder is in --
    absolute, taken from the current folder -- or None when neither is named:
    the rule `general.folders.run_folders` places a run by, so the study of
    the recipe as a whole (`command_spec` None) is the one its run is placed
    in. Not checked for existence: a recipe may create its study in an
    earlier step.
    """
    stated = _step_parameters(command_spec) if command_spec is not None else {}

    # labels injected into the two folders alone: a step's other values are
    # injected when it is reached
    tiers = [
        {
            key: _inject_labels(value)
            for key, value in (tier or {}).items()
            if gf.FOLDER_ALIASES.get(key, key) in ("studyfolder", "sessionsfolder")
        }
        for tier in (eargs, stated, parameters)
    ]

    study, known = gf.run_study(gf.placement_parameters(*tiers))
    return study if known else None


def _recipe_study(parameters: dict | None, eargs: dict | None) -> str | None:
    """The study the steps of a recipe work in, unless one names its own."""
    return _step_study(None, parameters, eargs)


def _produced_path(command_spec, produces, hints, folders, parameters=None, eargs=None):
    """
    The path a producing step writes, resolved the way the command resolves
    it: what the call that started the recipe states, else what the step
    states, else what the recipe states for every step, else `create_batch`'s
    own default of `<study>/processing/batch.txt`. A relative one is taken
    from the study the step works in (`_step_study`), else from the current
    folder; the default is in that study, else in the run's resolved one.
    """
    stated = _step_parameters(command_spec)
    study = _step_study(command_spec, parameters, eargs)

    # in the order the step loop of `run_recipe` gives it the value: the call
    # wins over the step, and `hints` holds the call over the recipe
    if produces in (eargs or {}):
        target = eargs[produces]
    else:
        target = stated.get(produces, hints.get(produces))

    if target is None:
        default = study or folders.get("basefolder")
        if default is None:
            return None
        target = os.path.join(gf.processing_folder(default), "batch.txt")

    return bio.run_path(_inject_labels(target), study)


def _withheld_by_production(
    commands, parameters, recipe_unset, hints, folders, run, eargs=None
):
    """
    ``_withheld_by_production(commands, parameters, recipe_unset, hints, folders, run, eargs=None)``

    Which run wide parameters this recipe writes itself, and up to which step
    they are therefore not to be handed to anybody.

    Two facts are knowable before the first step runs: whether the file exists
    now, and whether a step of this recipe writes that same path. They answer
    the question the steps cannot -- a step only ever sees a path, and a path
    that does not exist yet looks exactly like one that never will:

    - written by step N, absent now: withheld from steps 1..N, and said so.
    - written by nobody, absent now: no step will ever be able to read it, so
      the run does not start -- but only if some step could have received it.
    - written by nobody, present now: nothing to do, everybody gets it.
    - written by step N, present now: withheld from 1..N as if it were absent,
      so that a re-run does what a first run does, and warned about, because
      an earlier step may have been meant to read the file that is there.

    Deciding from the state at the start rather than at each step is what
    makes a recipe do the same thing twice: a `batch.txt` left by last week's
    run is otherwise indistinguishable from the one this run just wrote.

    Returns:
        `parameter -> the last step that writes it`, for the loop to skip on.

    Raises:
        ge.CommandError: on a run wide value that names a file nothing will
            write and some step of the recipe would be given.
    """
    withheld = {}

    for produces, consumed_as in PRODUCERS.values():
        if consumed_as not in parameters or consumed_as in recipe_unset:
            continue

        # taken from the study the steps work in, as each step takes it
        value = bio.run_path(
            _inject_labels(parameters[consumed_as]), _recipe_study(parameters, eargs)
        )
        exists = os.path.exists(value)

        writers = [
            (step, _get_command_name(com))
            for step, com in enumerate(commands, start=1)
            if _get_command_name(com) in PRODUCERS
            and _produced_path(com, produces, hints, folders, parameters, eargs)
            == value
        ]

        if not writers:
            if exists:
                continue

            # only a step that would have been given it could have failed on it
            wanted = _steps_given(commands, consumed_as)
            if not wanted:
                continue

            raise ge.CommandError(
                "run_recipe",
                f"The recipe's {consumed_as} does not exist and no step creates it",
                f"{consumed_as} is stated for the whole run as [{value}], which does",
                "not exist, and no step of this recipe writes it. It would be given to:",
                ", ".join(wanted),
                "Create the file first, add the step that writes it, or unset",
                f"{consumed_as} for the steps that must not have it.",
            )

        step, name = writers[-1]
        withheld[consumed_as] = step

        note = (
            f"\n---> {consumed_as} [{value}] is written by step {step} ({name}),"
            f"\n     so steps 1-{step} are not given it and select their sessions"
            f"\n     from the sessions folder.\n"
        )
        if exists:
            note = (
                f"\nWARNING: {consumed_as} [{value}] already exists and is rewritten by"
                f"\n     step {step} ({name}). Steps 1-{step} are not given it, so that this"
                f"\n     run does what a first run does. If one of them is meant to read the"
                f"\n     file that is there, state {consumed_as} against that step; to say"
                f"\n     that none of them is, unset_parameters: {consumed_as}.\n"
            )

        print(note)
        run.write(note)

    return withheld


def _steps_given(commands: list, name: str) -> list:
    """
    The commands of `commands` that would be given the run wide value of
    `name`: those that declare the parameter, and neither state a value of
    their own nor unset it (`_step_keeps_out`).
    """
    return sorted(
        {
            _get_command_name(com)
            for com in commands
            if qx_commands.get(_get_command_name(com)) is not None
            and name in gcs.declared_parameters(qx_commands.get(_get_command_name(com)))
            and not _step_keeps_out(com, name)
        }
    )


def _section(data: dict, key: str, where: str) -> dict:
    """
    The parameters a section of the recipe file states, as a dict: empty when
    nothing is written under it.

    Raises:
        ge.CommandFailed: on a section that is not `<parameter>: <value>`
            pairs.
    """
    section = data.get(key)
    if section is None:
        return {}
    if not isinstance(section, dict):
        raise ge.CommandFailed(
            "run_recipe",
            f"Invalid {key} in the recipe file",
            f"The {key} of {where} must be `<parameter>: <value>` pairs, got: {section!r}",
            "Please check the recipe file!",
        )
    return dict(section)


def _states_an_unset(params):
    """Whether `params` holds either spelling of an unset."""
    return UNSET_PARAMETERS in params or any(
        isinstance(key, str) and key.startswith("-") for key in params
    )


def _unset_names(params, where):
    """
    The names `params` says are not to be inherited, taken out of `params`.

    Two spellings, because they are good at different things. A step or a
    recipe writes ``unset_parameters`` to name several at once -- as a name, a
    comma separated list of them, or an array -- or writes the name itself
    with a leading ``-`` and no value, which reads on the parameter's own
    line. No command parameter can begin with `-`, so the prefix is
    unambiguous, and the one plausible way to mistype it (`- name:`, with a
    space) is YAML list syntax in a mapping and does not parse at all.

    Neither spelling can be an *absent* value: the empty string is what
    `img_suffix` and its kind default to, and `None` is a value `export_hcp`
    documents, so a recipe has to be able to state both.

    Parameters:
        --params    The parameter dictionary to read and strip.
        --where     Where it was written, for the error messages.

    Returns:
        The list of names not to inherit.

    Raises:
        ge.CommandError: on `-name: value`, which unsets and states at once,
            on an `unset_parameters` that is neither a string nor a list, and
            on a name the same block also states.
    """
    stated = params.pop(UNSET_PARAMETERS, None)

    if stated is None:
        names = []
    elif isinstance(stated, str):
        names = stated.split(",")
    elif isinstance(stated, (list, tuple)):
        names = [str(name) for name in stated]
    else:
        raise ge.CommandError(
            "run_recipe",
            f"Invalid {UNSET_PARAMETERS} in {where}",
            f"{UNSET_PARAMETERS} takes a parameter name, a comma separated list",
            "of them, or an array.",
        )

    for key in [key for key in params if isinstance(key, str) and key.startswith("-")]:
        if params.pop(key) is not None:
            raise ge.CommandError(
                "run_recipe",
                f"Parameter {key} in {where} is both unset and given a value",
                f"A parameter written as `{key}` is not inherited, so it takes no value.",
                f"Write `{key}:` to unset it, or `{key[1:]}: <value>` to state it.",
            )
        names.append(key[1:])

    names = [name.strip() for name in names if name.strip()]

    for name in names:
        if name in params:
            raise ge.CommandError(
                "run_recipe",
                f"Parameter {name} in {where} is both unset and stated",
                "A parameter that is not to be inherited cannot also be given",
                "a value in the same place. Please remove one of the two.",
            )

    return names


def _inject_labels(value):
    """
    Replace every ``{{$VAR}}`` in `value` with what the environment says.

    The recipe's one substitution rule, `general.folders.inject_labels`, which
    the container launcher applies as well when it reads a recipe file to
    place a run's logs. It used to be spelled three times -- for the log
    folder, for an external step's path and for each command parameter --
    and the copies did not run at the same point: a value the recipe resolved
    its **own** folders from was still uninjected when it did so, while the
    copy of it handed to a step was injected on the way out. That is how a
    recipe could log to a folder literally named `{{$STUDY_FOLDER}}` while
    every step it ran logged to the study.

    Parameters:
        value: the value to inject into. Anything that is not a string
            holding a label is returned unchanged, so this can be mapped over
            a whole parameter dictionary.

    Returns:
        the value with every label replaced.

    Raises:
        ge.CommandFailed: when a label names something the environment does
            not hold. A recipe cannot be run half resolved.
    """
    try:
        return gf.inject_labels(value)
    except gf.PlacementError as e:
        raise ge.CommandFailed("run_recipe", str(e))


def _find_enclosed_substrings(input_string, start_delimiter="{{", end_delimiter="}}"):
    """
    Find all substrings enclosed by start and end delimiters in a string.

    How `run_recipe` found its labels before `general.folders.inject_labels`
    took them over; kept as the reference `tests/test_log_placement.py` holds
    that function's pattern to.
    """
    substrings = []
    start_index = 0

    while True:
        start_pos = input_string.find(start_delimiter, start_index)
        if start_pos == -1:
            break

        end_pos = input_string.find(end_delimiter, start_pos + len(start_delimiter))
        if end_pos == -1:
            break

        substrings.append(input_string[start_pos : (end_pos + len(end_delimiter))])
        start_index = end_pos + len(end_delimiter)

    return substrings

#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``recipe.py``

Run recipe framework.
"""

"""
Copyright (c) Grega Repovs and Jure Demsar. All rights reserved.
"""

import os
import os.path
import shutil
import subprocess
from datetime import datetime

import qx_utilities.general.commands_support as gcs
import qx_utilities.general.core as gc
import qx_utilities.general.exceptions as ge
import qx_utilities.general.xnat as gx
import yaml
from qx_registry import qx_commands


def run_recipe(recipe_file=None, recipe=None, steps=None, startwith=None, logfolder=None, eargs=None):
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

        --logfolder (str, default ''):
            The folder within which to save the log.

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
            of `-<parameter> <value>`.

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

            Please take note that if `run_recipe` command is ran using a
            scheduler, any scheduler specification within the `recipe_file` will
            be ignored to avoid the attempts to spawn new cluster jobs when
            `run_recipe` instance is already running on a cluster node.

            Importantly, if `scheduler` is specified in the `run_recipe` file,
            do bear in mind, that all the commands in the recipe will be
            scheduled at the same time, and not in a succession, as `run_recipe`
            can not track execution of jobs on individual cluster nodes.

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

            The log of the commands ran will be by default stored in
            `<study>/logs/` stamped with date and time that
            the log was started. If a study folder is not yet created, please
            provide a valid folder to save the logs to. If the log can not be
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

            Recpies are defined in the recipes portion of the file where each
            recipeis defined by its unique name. Each recipe has two sections,
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

        Example recipe file:
            ::

                global_parameters:
                    sessionsfolder    : /data/qx_study/sessions
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
                            - create_study:
                                studyfolder: /data/qx_study
                            - import_dicom:
                                masterinbox: /data/qx_data
                                archive: leave
                            - create_session_info
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
                            - hcp_msmall
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
            --sessionsfolder="/data/qx_study/sessions" \\
            --batchfile="/data/qx_study/processing/batch.txt" \\
            --steps="hcp_pre_freesurfer,hcp_freesurfer,hcp_post_freesurfer"

        The first call will execute all the commands in recipe `onboard_dicom`.

        The second call will execute all the steps of the HCP preprocessing
        pipeline via a scheduler. It will execute two sessions in parallel
        within the run. in sequence.

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

    if recipe_file is not None and not os.path.exists(recipe_file):
        raise ge.CommandFailed(
            "run_recipe",
            "recipe file file does not exist",
            f"Recipe file file not found [{recipe_file}]",
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
    commands = []

    timestamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")

    # open the recipe file
    if recipe_file:
        with open(recipe_file, "r", encoding="UTF-8") as file:
            try:
                recipe_data = yaml.load(file, Loader=yaml.FullLoader)
            except Exception:
                raise ge.CommandFailed("run_recipe", "Cannot parse the recipe file")

        # get the recipe
        if "recipes" not in recipe_data:
            raise ge.CommandFailed("run_recipe", "Recipes not found in the recipe file")

        recipes = recipe_data["recipes"]

        if recipe not in recipes:
            raise ge.CommandFailed(
                "run_recipe", f"Recipe {recipe} not found in the recipe file"
            )

        recipe_dict = recipes[recipe]

        # global parameters
        if "global_parameters" in recipe_data:
            for parameter, value in recipe_data["global_parameters"].items():
                parameters[parameter] = value

        # recipe parameters
        if "parameters" in recipe_dict:
            for parameter, value in recipe_dict["parameters"].items():
                parameters[parameter] = value
    else:
        # define recipe name
        recipe = "steps"

        # create the commands dict
        recipe_dict = {}
        recipe_dict["commands"] = steps.split(",")

    # log location
    if "logfolder" in parameters and parameters["logfolder"] != "legacy":
        logfolder = parameters["logfolder"]
    elif logfolder is None:
        if "studyfolder" in parameters:
            logfolder = os.path.join(
                parameters["studyfolder"], "logs", f"{timestamp}_run_recipe_{recipe}"
            )
        elif "studyfolder" in eargs:
            logfolder = os.path.join(
                eargs["studyfolder"], "logs", f"{timestamp}_run_recipe_{recipe}"
            )
        elif "sessionsfolder" in parameters:
            logfolder = gc.deduce_folders(
                parameters, f"run_recipe_{recipe}", timestamp
            )["logfolder"]
        elif "sessionsfolder" in eargs:
            logfolder = gc.deduce_folders(eargs, f"run_recipe_{recipe}", timestamp)[
                "logfolder"
            ]
    elif logfolder == "legacy":
        if "studyfolder" in parameters:
            logfolder = os.path.join(parameters["studyfolder"], "logs")
        elif "studyfolder" in eargs:
            logfolder = os.path.join(eargs["studyfolder"], "logs")
        elif "sessionsfolder" in parameters:
            logfolder = gc.deduce_folders(parameters)["logfolder"]
        elif "sessionsfolder" in eargs:
            logfolder = gc.deduce_folders(eargs)["logfolder"]

    # mustache injections to logfolder?
    if "{{" in logfolder and "}}" in logfolder:
        labels = _find_enclosed_substrings(logfolder)
        for label in labels:
            cleaned_label = label.replace("{", "").replace("}", "")
            os_label = cleaned_label[1:]
            if cleaned_label[0] == "$" and os_label in os.environ:
                logfolder = logfolder.replace(label, os.environ[os_label])
            else:
                raise ge.CommandFailed(
                    "run_recipe",
                    f"Cannot inject values marked with double curly braces in the recipe. Label [{label}] not found in system environment variables.",
                )

    comlogfolder = os.path.join(logfolder, "comlogs")

    print(f"\n---> Saving the run_recipe runlog to: {logfolder}")

    # create comlogfolder if it does not exist
    os.makedirs(comlogfolder, exist_ok=True)

    logstamp = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")
    logfilename = f"Log-run_recipe-{logstamp}.log"
    logname = os.path.join(logfolder, logfilename)

    # run
    summary = "\n----==== RECIPE EXECUTION SUMMARY ====----"

    try:
        log = open(logname, "w", encoding="utf-8")
    except:
        raise ge.CommandFailed(
            "run_recipe",
            "Cannot open log",
            f"Unable to open log [{logname}]",
            "Please check the paths!",
        )

    print(
        "\n\n============================== RUN_RECIPE LOG ==============================\n",
        file=log,
    )

    summary += f"\n\nRecipe: {recipe}"

    print(f"---> Running commands from recipe: {recipe}")
    print(f"---> Running commands from recipe: {recipe}\n", file=log)

    # commands
    if "commands" not in recipe_dict:
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
        def _get_command_name(command_spec):
            if isinstance(command_spec, dict):
                return list(command_spec.keys())[0]
            return command_spec

        start_indices = [
            idx for idx, command_spec in enumerate(commands)
            if _get_command_name(command_spec) == startwith
        ]

        if not start_indices:
            print(f"WARNING: startwith step [{startwith}] is not a part of recipe [{recipe}].")
            print(f"WARNING: startwith step [{startwith}] is not a part of recipe [{recipe}].", file=log,)
            log.close()
            raise ge.CommandError(
                "run_recipe",
                "startwith step not found in recipe",
                "Startwith step not found",
                "Please check the recipe steps and provide a valid --startwith step name!",
            )

        if len(start_indices) > 1:
            print(f"WARNING: startwith step [{startwith}] is present more than once in recipe [{recipe}]. Starting with the first occurrence.")
            print(f"WARNING: startwith step [{startwith}] is present more than once in recipe [{recipe}]. Starting with the first occurrence.", file=log)

        start_index = start_indices[0]
        commands_skipped = commands[:start_index]
        commands = commands[start_index:]

    # print commands
    def _print_commands(title, command_list):
        print(title)
        print(title, file=log)
        commands_set = []
        for com in command_list:
            if isinstance(com, dict):
                command_name = list(com.keys())[0]
            else:
                command_name = com
            if command_name not in commands_set:
                commands_set.append(command_name)
                print(f"    - {command_name}")
                print(f"    - {command_name}", file=log, flush=True)

    if startwith:
        _print_commands("\n---> Commands skipped:", commands_skipped)
        _print_commands("\n---> Commands to run:", commands)
    else:
        _print_commands("\n---> Commands:", commands)

    # XNAT initial setup
    # If running on XNAT, try and load checkpoint if supplied
    if os.environ.get("XNAT", "") == "yes":
        checkpoint_str = os.environ.get("XNAT_CHECKPOINT", "")
        print("Checkpoint Supplied: " + checkpoint_str, file=log)
        print("Checkpoint Supplied: " + checkpoint_str)

        if checkpoint_str == "":
            print("XNAT Checkpoint empty, skipping...", file=log)
            print("XNAT Checkpoint empty, skipping...")
        else:
            file_path, find_summary = gx.xnat_find_checkpoint(checkpoint_str)
            print(find_summary, file=log)
            load_summary = gx.xnat_load_checkpoint(file_path)
            print(load_summary, file=log)

    # track command failures across the loop (stays defined even if commands is empty)
    error = False

    for com in commands:
        if isinstance(com, dict):
            command_name = list(com.keys())[0]
            command_parameters = list(com.values())[0]
        else:
            command_name = com
            command_parameters = {}

        # executing a custom script
        error = False
        if command_name == "script" or command_name == "external":
            if "path" in command_parameters:
                external_path = command_parameters["path"]

                labels = _find_enclosed_substrings(external_path)
                for label in labels:
                    cleaned_label = label.replace("{", "").replace("}", "")
                    os_label = cleaned_label[1:]
                    if cleaned_label[0] == "$" and os_label in os.environ:
                        external_path = external_path.replace(
                            label, os.environ[os_label]
                        )
                    else:
                        raise ge.CommandFailed(
                            "run_recipe",
                            f"Cannot inject values marked with double curly braces in the recipe. Label [{label}] not found in system environment variables.",
                        )

                del command_parameters["path"]
            else:
                summary += f"\n - external {command_parameters} ... FAILED"
                _print_end_summary(
                    summary, log, f"{command_parameters} path not provided!"
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
            print(
                f"\n--------------------------------------------\n---> Running external: {external_path}",
                file=log,
            )
            if not os.path.exists(external_path):
                summary += f"\n - external {external_path} ... FAILED"
                _print_end_summary(summary, log, f"{external_path} does not exist!")

                raise ge.CommandFailed(
                    "run_recipe",
                    "External command not found",
                    f"External command not found [{external_path}]",
                    "Please check the external command path!",
                )

            # log
            external_name = os.path.basename(external_path)
            log_path = os.path.join(
                comlogfolder,
                f"tmp_{external_name}_{command_name}_{timestamp}.log",
            )

            # prep command
            if external_path.endswith(".sh") or "." not in external_path:
                command = ["bash", external_path]
            elif external_path.endswith(".py"):
                command = ["python", external_path]
            elif external_path.endswith(".R"):
                command = ["Rscript", external_path]
            else:
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

            # add parameters to the command
            for param, value in command_parameters.items():
                # inject mustache marked values
                if (
                    isinstance(value, str)
                    and len(value) > 0
                    and "{{" in value
                    and "}}" in value
                ):
                    labels = _find_enclosed_substrings(value)
                    for label in labels:
                        cleaned_label = label.replace("{", "").replace("}", "")
                        os_label = cleaned_label[1:]
                        if cleaned_label[0] == "$" and os_label in os.environ:
                            value = value.replace(label, os.environ[os_label])
                        else:
                            raise ge.CommandFailed(
                                "run_recipe",
                                f"Cannot inject values marked with double curly braces in the recipe. Label [{label}] not found in system environment variables.",
                            )

                command.append(
                    f"{external_parameter_prefix}{param}{external_parameter_delimiter}{value}"
                )

            # run the command with subprocess Popen
            with open(log_path, "w", encoding="UTF-8") as log_file:
                process = subprocess.Popen(
                    command, stdout=log_file, stderr=subprocess.STDOUT
                )
                process.communicate()

            # Get the exit code
            exit_code = process.returncode

            if exit_code != 0:
                error = True
                summary += f"\n - external {external_path} ... FAILED"
                error_log = log_path.replace("tmp_", "error_")
                print(f"    ... failed [{external_path}], see [{error_log}]")
                print(f"    ... failed [{external_path}], see [{error_log}]", file=log)
                os.rename(log_path, error_log)

                summary += f"\n - external {external_path} ... FAILED"
                _print_end_summary(summary, log, f"Failed external {external_path}!")

                raise ge.CommandFailed(
                    "run_recipe",
                    "External command failed",
                    f"External command failed [{external_path}]",
                    "Please check the log for details!",
                )
            else:
                summary += f"\n - external {external_path} ... OK"
                done_log = log_path.replace("tmp_", "done_")
                print(f"    ... done [{external_path}], see [{done_log}]")
                print(f"    ... done [{external_path}], see [{done_log}]", file=log)
                os.rename(log_path, done_log)

        elif qx_commands.get(command_name) is not None:
            # override params with those from eargs (passed because of parallelization on a higher level)
            if eargs is not None:
                # do not add parameter if it is flagged as removed
                for k in eargs:
                    if k in ["parsessions", "parelements"]:
                        if k in command_parameters:
                            command_parameters[k] = str(
                                min([int(e) for e in [eargs[k], command_parameters[k]]])
                            )
                    else:
                        command_parameters[k] = eargs[k]

            # append global and recipe parameters
            for parameter, value in parameters.items():
                if parameter not in command_parameters:
                    command_parameters[parameter] = value

            # remove parameters that are not allowed
            qx_command = qx_commands.get(command_name)

            if qx_command.type == "utility" and qx_command.language == "python":
                allowed_parameters = list([e.name for e in qx_command.args] + ["logfolder"])
                if any([e in allowed_parameters for e in ["sourcefolder", "folder"]]):
                    allowed_parameters += gcs.extra_parameters

                new_parameters = command_parameters.copy()
                for param in command_parameters.keys():
                    if param not in allowed_parameters:
                        del new_parameters[param]
                command_parameters = new_parameters

            # XNAT individual command prep, creates _in checkpoint
            if os.environ.get("XNAT", "") == "yes":
                print("Attemping XNAT specific setup...", file=log)
                possibles = globals().copy()
                possibles.update(locals())
                # XNAT helper functions for individual commands must be in format xnat_ + command_name
                xnat_command = possibles.get("xnat_" + command_name)
                if not xnat_command:
                    print("\n------------------------", file=log)
                    print(
                        "\nNo XNAT setup method detected for: "
                        + command_name
                        + ", continuing...",
                        file=log,
                    )
                    print("\n------------------------", file=log)
                else:
                    print(xnat_command(prep=True), file=log)
                print("Making checkpoint IN...", file=log)
                print("Making checkpoint IN...")
                gx.xnat_make_checkpoint(
                    command_name + "_in",
                    tag=os.environ.get("XNAT_CHECKPOINT_TAG", "timestamp"),
                )

            # setup command
            command = ["qunex"]
            command.append(command_name)
            commandr = (
                "\n--------------------------------------------\n---> Running command:\n\n     qunex "
                + command_name
            )

            # add logfolder to command_parameters if not already in there
            if "logfolder" not in command_parameters:
                command_parameters["logfolder"] = logfolder

            for param, value in command_parameters.items():
                # inject mustache marked values
                if (
                    isinstance(value, str)
                    and len(value) > 0
                    and "{{" in value
                    and "}}" in value
                ):
                    labels = _find_enclosed_substrings(value)
                    for label in labels:
                        cleaned_label = label.replace("{", "").replace("}", "")
                        os_label = cleaned_label[1:]
                        if cleaned_label[0] == "$" and os_label in os.environ:
                            value = value.replace(label, os.environ[os_label])
                        else:
                            summary += f"\n - command {command_name} ... FAILED"
                            _print_end_summary(
                                summary,
                                log,
                                f"Failed running command {command_name}! Cannot inject values marked with double curly braces in the recipe.",
                            )

                            raise ge.CommandFailed(
                                "run_recipe",
                                f"Cannot inject values marked with double curly braces in the recipe. Label [{label}] not found in system environment variables.",
                            )

                if param in flags:
                    command.append(f"--{param}")
                    commandr += f" \\\n          --{param}"
                else:
                    command.append(f"--{param}={value}")
                    commandr += f" \\\n          --{param}='{value}'"

            # warn if scheduler was used in the recipe file
            if "scheduler" in command_parameters:
                print(
                    "\nWARNING: the scheduler parameter defined in the recipe file will be ignored. Scheduling needs to be defined at the command call level."
                )

            print(commandr)
            print(commandr, file=log, flush=True)

            # run command
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0
            )

            # Poll process for new output until finished
            logging = False

            for line in iter(process.stdout.readline, b""):
                line = line.decode("utf-8")
                print(line)
                if any([tag in line for tag in ["ERROR", "failed with error", "/error_", "Not all tasks completed"]]):
                    print("", file=log)
                    error = True

                if "Final report" in line:
                    print("", file=log)
                    logging = True

                # print
                if logging or error:
                    print(line, end=" ", file=log)
                    log.flush()

            exit_code = process.wait()

            if error or exit_code != 0:
                summary += f"\n - command {command_name} ... FAILED"
                _print_end_summary(
                    summary, log, f"Failed running command {command_name}!"
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
                print("Attempting XNAT specific cleanup...", file=log)
                if not xnat_command:
                    print("\n------------------------")
                    print(
                        "\nNo XNAT cleanup method detected for: "
                        + command_name
                        + ", continuing...",
                        file=log,
                    )
                    print("\n------------------------")
                else:
                    print(xnat_command(prep=False), file=log)
                print("Making checkpoint OUT...", file=log)
                print("Making checkpoint OUT...")
                gx.xnat_make_checkpoint(
                    command_name + "_out",
                    tag=os.environ.get("XNAT_CHECKPOINT_TAG", "timestamp"),
                )

        else:
            summary += f"\n - command {command_name} ... FAILED"
            _print_end_summary(summary, log, f"Unknown command [{command_name}]!")

            raise ge.CommandFailed(
                "run_recipe",
                "Unknown command",
                f"Unknown command [{command_name}]",
                "This is not a QuNex command or an external script!",
            )

    _print_end_summary(summary, log, None)

    # hack copy the log from runlogs to comlogs as well
    comlog = os.path.join(comlogfolder, logfilename)
    if not error:
        comlog = comlog.replace("Log-", "done_")
    else:
        comlog = comlog.replace("Log-", "error_")

    # copy logname to comlog
    shutil.copyfile(logname, comlog)


def _print_end_summary(summary, log, error=None):
    summary += "\n\n----------==== END SUMMARY ====----------"

    print(summary, file=log)
    print(summary)

    if not error:
        print("\n------------------------", file=log)
        print(f"\n---> Successful completion of QuNex run_recipe at {datetime.now()}", file=log)

        print("\n------------------------")
        print(f"---> Successful completion of QuNex run_recipe at {datetime.now()}")
    else:
        print("\n------------------------", file=log)
        print(f"\nERROR: {error}", file=log)
        print(f"\n---> run_recipe failed at {datetime.now()}", file=log)

        print("\n------------------------")
        print(f"\nERROR: {error}")
        print(f"---> run_recipe failed at {datetime.now()}")

    log.close()


def _find_enclosed_substrings(input_string, start_delimiter="{{", end_delimiter="}}"):
    """
    Find all substrings enclosed by start and end delimiters in a string.
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

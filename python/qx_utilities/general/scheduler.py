#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``scheduler.py``

This file holds the functions for running jobs through job schedulers on a
computer cluster. It supports PBS, SLURM and GridEngine. The functions are
accessible and used both as terminal commands as well as internal use functions.
"""

import subprocess
import math
import os
import os.path
import time
import re
import shlex

import qx_utilities.general.exceptions as ge
from qx_registry import qx_commands

from datetime import datetime


def schedule(
    command=None,
    script=None,
    settings=None,
    replace=None,
    workdir=None,
    environment=None,
    output=None,
    bash=None,
    parsessions=1,
    parelements=1,
    logfolder=None,
):
    """
    ``schedule [command=<command string>] [script=<path to script>] settings=<settings string> [replace=<"key:value|key:value" string>] [workdir=<path to working directory>] [environment=<path to environment setup script>] [output=<string specifying how to process output>] [logfolder=<the run's log folder>]``

    Schedule the provided command.

    ..  qx_command:
        type: utility

    Parameters:
        --command (str):
            The command string to be executed by the scheduler.

        --script (str):
            The path to a script to be executed by the scheduler.

        --settings (str):
            A string specifying the scheduler to be used and the additional
            settings for it.

            Settings string should be a comma separated list of parameters. The first
            parameter has to be the scheduler name (PBS, SLURM or GridEngine), the rest
            of the parameters are key-value pairs that are to be passed as settings to
            the scheduler.

            Example settings strings::

                "SLURM,jobname=bet1,time=03-24:00:00,cpus-per-task=2,mem-per-cpu=2500,partition=week"

        --replace (str):
            A string of key-value pairs that specify the specific values
            to be imputed into the script or command.

        --workdir (str):
            The folder the job starts in. A relative path is taken from the
            folder the submission runs in, which is the study folder once
            the run has entered it. The job changes into it after the --bash
            commands and the --environment script, before the command or
            script; when it can not, it warns and runs in the folder the
            scheduler started it in.

        --environment (str):
            A path to a script to be executed before all other commands
            to set up the environment for execution.

        --output (str):
            A string specifying whether to return or redirect the
            standard output and error. See "REDIRECTING OUTPUT" for
            details

        --bash (str):
            Used if any additional commands have to be run in the
            compute node before the execution of the QuNex command
            itself. Use a semicolon separated list to chain multiple
            commands.

        --logfolder (str, default '<the run's log folder>'):
            The run's log folder. With no --output, the job's standard
            output and error go to its `batchlogs` folder, as
            `<scheduler>_schedule.<timestamp>.log`, beside the output of
            every other job QuNex submits. QuNex sets it to the folder the
            run logs in.

    Notes:

        Schedules the provided command the referenced script to be run by the
        specified scheduler (PBS, SLURM and GridEngine are currently supported).

        command, script and settings are required parameters. If the optional
        parameters are not specified, they will not be used.

        Value substitution in command or script

        If replace parameter is set, all instances of {{key}} in the command or
        script will be replaced with the provided value. The key/value pairs need
        to be separated by the pipe character, whereas key and value need to be
        separated by a colon. An example replacement string::

            "session:AP23791|folder:/studies/WM/sessions/AP23791"

        Redirecting output

        If no output is specified, the job's standard output and error (stdout,
        stderr) both go to `<scheduler>_schedule.<timestamp>.log` in the
        `batchlogs` folder of --logfolder; without a log folder they are left
        as is and processed by the scheduler. The result of submitting the job
        is printed to standard output. Output string can specify four
        different directives provided by "<key>:<value>" strings separated by
        pipe:

        - stdout  (specifies a path to a log file that should store standard output
          of the submitted job.)
        - stderr  (specifies a path to a log file that should store error output
          of the submitted job.)
        - both    (specifies a path to a log file that should store joint standard
          and error outputs of the submitted job.)
        - return  (specifies whether standard output ('stdout'), error output
          ('stderr'), both ('both') or none ('none') should be returned as
          a string from the job submission call.)

        A relative log file path is taken from the folder the submission runs
        in, and its folder has to exist. Specify "return" value only when
        schedule is used as a function called from another python script or
        function to process the result.

        Examples:

        ::

            "stdout:processing.log"

        ::

            "stdout:processing.output.log|stderr:processing.error.log"

        ::

            "both:processing.log|return:both"

        Do not specify error and standard outputs both using --output parameter and
        scheduler specific options within settings string.

        Scheduler specifics:

            Each of the supported scheduler systems has a somewhat different way of
            specifying job parameters. Please see documentation for each of the
            supported schedulers to provide the correct settings. Below are the
            information for each of the schedulers on how to specify --settings.

            PBS settings:

                PBS uses various flags to specify parameters. Be careful that the settings
                string includes only comma separated 'key=value' pairs. Scheduler will then
                do its best to use the right flags. Specifically:

                Keys: mem, walltime, software, file, procs, pmem, feature, host,
                naccesspolicy, epilogue, prologue will be submitted using::

                    "#PBS -l <key>=<value>"

                Keys: j, m, o, S, a, A, M, q, t, e, N, l will be submitted using::

                    "#PBS -<key> <value>"

                Key: depend will be submitted using::

                    "#PBS -W depend=<value>"

                Key: umask will be submitted using::

                    "#PBS -W umask=<value>"

                Key: nodes is a special case. It will be submitted as::

                    "#PBS -l <value>"

            SLURM settings:

                For SLURM any provided key/value pair will be passed in the form::

                    "#SBATCH --<key>=<value>"

                Some of the possible parameters to set are:

                - partition        (The partition (queue) to use.)
                - nodes            (Total number of nodes to run on.)
                - cpus-per-task    (Number of cores per task.)
                - time             (Maximum wall time DD-HH:MM:SS.)
                - constraint       (Specific node architecture.)
                - mem-per-cpu      (Memory requested per CPU in MB.)
                - mail-user        (Email address to send notifications to.)
                - mail-type        (On what events to send emails.)

            GridEngine settings:

                For GridEngine the comma separated list of settings will be unwrapped and
                each setting will be passed to the scheduler "as is". For example:

                    ---scheduler="GridEngine,N example_job,l h_rt=24:00:00,pe smp 1,l mem_free=32G"

                Will be converted to the following GridEngine header:

                    #$ -N example_job
                    #$ -l h_rt=24:00:00
                    #$ -pe smp 1
                    #$ -l mem_free=32G

    Examples:

        ::

            qunex schedule command="bet t1.nii.gz brain.nii.gz" \\
                           settings="SLURM,jobname=bet1,time=03-24:00:00,cpus-per-task=2,mem-per-cpu=2500,partition=week"

        ::

            qunex schedule command="bet {{in}} {{out}}" \\
                           replace="in:t1.nii.gz|out:brain.nii.gz" \\
                           settings="SLURM,jobname=bet1,time=03-24:00:00,cpus-per-task=2,mem-per-cpu=2500,partition=week" \\
                           workdir="/studies/WM/sessions/AP23791/images/structural"
    """

    # --- check inputs
    if command is None and script is None:
        raise ge.CommandError(
            "schedule",
            "Missing parameter",
            "Either command or script need to be specified to run scheduler!",
        )

    if command is not None and script is not None:
        raise ge.CommandError(
            "schedule",
            "Parameter conflict",
            "Only command or script need to be provided to run scheduler!",
        )

    if settings is None:
        raise ge.CommandError(
            "schedule",
            "Missing parameter",
            "Settings need to be provided to run scheduler!",
        )

    # --- parse settings
    try:
        settings_list = [e.strip() for e in settings.split(",")]
        scheduler = settings_list.pop(0)
        # pass parameters as is for GridEngine
        if scheduler != "GridEngine":
            settings_dict = dict([e.strip().split("=", 1) for e in settings_list])
            jobname = settings_dict.pop("jobname", "qx_schedule")
        else:
            settings_dict = {}

            for s in settings_list:
                if s.startswith("jobname"):
                    if "N" not in settings_dict:
                        str_split = s.split("=")
                        settings_dict["N"] = str_split[1].strip()
                # what QuNex adds itself names the job rather than sets a flag
                elif s.startswith(("jobnum=", "comname=")):
                    key, value = s.split("=", 1)
                    settings_dict[key.strip()] = value.strip()
                else:
                    str_split = s.split()
                    setting = str_split[0].strip()
                    value = " ".join(str_split[1:]).strip()
                    if setting in settings_dict:
                        settings_dict[setting] = [settings_dict[setting], value]
                    else:
                        settings_dict[str_split[0].strip()] = " ".join(
                            str_split[1:]
                        ).strip()

        comname = settings_dict.pop("comname", "")
        jobnum = settings_dict.pop("jobnum", "")

        # a GridEngine job of several is named after its number, as the others are
        if scheduler == "GridEngine" and jobnum != "":
            settings_dict["N"] = "%s_%s" % (settings_dict.get("N", "qx_schedule"), jobnum)
    except Exception:
        raise ge.CommandError(
            "schedule",
            "Misspecified parameter",
            "Could not parse the settings string:",
            settings,
        )

    # --- compile command to pass
    if command is None:
        if not os.path.exists(script):
            raise ge.CommandFailed(
                "schedule",
                "File not found",
                "The specified script does not exist! [%s]" % (script),
            )
        with open(script, "r") as f:
            command = f.read()

    if workdir is not None:
        # absolute, as a job does not start where it was submitted from on
        # every scheduler: PBS and GridEngine start it in the home folder
        workdir = os.path.abspath(workdir)
        if not os.path.exists(workdir):
            raise ge.CommandFailed(
                "schedule",
                "Folder does not exist",
                "The specified working directory does not exist! [%s]" % (workdir),
            )
        # quoted for the shell in the warning as well, where the double
        # quotes are closed around it: inside them a `"` in the folder's name
        # would end the string, and a `$` would be expanded
        folder = shlex.quote(workdir)
        command = (
            'cd %s || echo "WARNING: could not change into "%s", relative paths '
            'are taken from $(pwd)" >&2\n' % (folder, folder)
        ) + command

    if environment is not None:
        if not os.path.exists(environment):
            raise ge.CommandFailed(
                "schedule",
                "File not found",
                "The specified environment script does not exist! [%s]" % (environment),
            )
        with open(environment, "r") as f:
            command = f.read() + "\n" + command

    # --- do search replace
    if replace is not None:
        replace = [e.strip().split(":") for e in replace.split("|")]

        for key, value in replace:
            command = command.replace("{{%s}}" % (key), value)

    # --- parse output
    outputs = {"stdout": None, "stderr": None, "both": None, "return": None}

    # a run's job keeps its output beside the run's other logs unless it is
    # told where to put it: left to the scheduler, it lands in the folder the
    # job starts in
    if output is None and logfolder:
        batchlogs = os.path.join(logfolder, "batchlogs")
        os.makedirs(batchlogs, exist_ok=True)
        output = "both:%s" % os.path.join(
            batchlogs,
            "%s_schedule.%s.log"
            % (scheduler, datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")),
        )

    if output is not None:
        for directive in output.split("|"):
            # split at the first colon only: a path may hold one of its own
            k, _, v = [f.strip() for f in directive.partition(":")]
            if k not in outputs or not v:
                raise ge.CommandError(
                    "schedule",
                    "Misspecified parameter",
                    "Could not read the output directive '%s': it has to be "
                    "stdout, stderr or both with a log file, or return with "
                    "stdout, stderr, both or none." % (directive),
                )
            if k == "return":
                if v not in ("stdout", "stderr", "both", "none"):
                    raise ge.CommandError(
                        "schedule",
                        "Misspecified parameter",
                        "return has to be stdout, stderr, both or none, got: %s"
                        % (v),
                    )
                outputs[k] = None if v == "none" else v
                continue
            # absolute, as it is written into the job script: a file named
            # without a folder is in the current one, which exists
            v = os.path.abspath(v)
            if not os.path.exists(os.path.dirname(v)):
                raise ge.CommandFailed(
                    "schedule",
                    "Folder does not exist",
                    "The specified folder for the '%s' log file does not exist! [%s]"
                    % (k, os.path.dirname(v)),
                    "Please check your paths!",
                )
            outputs[k] = v

    if outputs["both"] is not None:
        outputs["stderr"] = outputs["both"]
        outputs["stdout"] = outputs["both"]

    # --- build scheduler commands
    s_command = ""

    if scheduler == "PBS":
        for k, v in settings_dict.items():
            if k in (
                "mem",
                "walltime",
                "software",
                "file",
                "procs",
                "pmem",
                "feature",
                "host",
                "naccesspolicy",
                "epilogue",
                "prologue",
            ):
                s_command += "#PBS -l %s=%s\n" % (k, v)
            elif k in ("j", "m", "o", "S", "a", "A", "M", "q", "t", "e", "l"):
                s_command += "#PBS -%s %s\n" % (k, v)
            elif k == "depend":
                s_command += "#PBS -W depend=%s\n" % (v)
            elif k == "umask":
                s_command += "#PBS -W umask=%s\n" % (v)
            elif k == "N" and jobname == "qx_schedule":
                jobname = v
            elif k == "nodes":
                s_command += "#PBS -l nodes=%s\n" % v

        # set default nodes
        if "nodes" not in settings_dict.keys():
            s_command += "#PBS -l nodes=1:ppn=%s\n" % (parsessions * parelements)

        # job name
        if comname != "":
            jobname = "%s-%s" % (jobname, comname)
        if jobnum != "":
            jobname = "%s_%s" % (jobname, jobnum)
        s_command += "#PBS -N %s\n" % jobname

        if outputs["stdout"] is not None:
            s_command += "#PBS -o %s\n" % (outputs["stdout"])
        if outputs["stderr"] is not None:
            s_command += "#PBS -e %s\n" % (outputs["stderr"])
        if outputs["both"]:
            s_command += "#PBS -j oe\n"
        com = "qsub"

    elif scheduler == "SLURM":
        s_command += "#!/bin/bash\n"
        for key, value in settings_dict.items():
            # the job name is written once, below
            if key in ("J", "job-name"):
                if jobname == "qx_schedule":
                    jobname = value
            elif not value:
                s_command += "#SBATCH --%s\n" % (key.replace("--", ""))
            else:
                s_command += "#SBATCH --%s=%s\n" % (key.replace("--", ""), value)

        # set default cpus-per-task
        if (
            "cpus-per-task" not in settings_dict.keys()
            and "c" not in settings_dict.keys()
        ):
            s_command += "#SBATCH --cpus-per-task=%s\n" % (parsessions * parelements)

        # jobname
        if comname != "":
            jobname = "%s-%s" % (jobname, comname)
        if jobnum != "":
            jobname = "%s_%s" % (jobname, jobnum)
        s_command += "#SBATCH --job-name=%s\n" % jobname

        if outputs["stdout"] is not None:
            s_command += "#SBATCH -o %s\n" % (outputs["stdout"])
        if outputs["stderr"] is not None:
            s_command += "#SBATCH -e %s\n" % (outputs["stderr"])
        com = "sbatch"

    elif scheduler == "GridEngine":
        s_command += "#!/bin/bash\n"

        for k, v in settings_dict.items():
            # if v is a list add an entry for each value
            if isinstance(v, list):
                for i in v:
                    s_command += f"#$ -{k} {i}\n"
            else:
                s_command += f"#$ -{k} {v}\n"

        if outputs["stdout"] is not None:
            s_command += f"#$ -o {outputs['stdout']}\n"
        if outputs["stderr"] is not None:
            s_command += f"#$ -e {outputs['stderr']}\n"

        com = "qsub"

    # --- run scheduler
    # add bash commands before the qunex command if specified
    if bash:
        s_command += "\n" + bash + "\n"

    # --- report
    print("\nSubmitting:\n------------------------------")
    print(s_command)
    print(command + "\n")

    if outputs["return"] is None:
        serr = None
        sout = None
    elif outputs["return"] == "both":
        serr = subprocess.STDOUT
        sout = subprocess.PIPE
    elif outputs["return"] == "stderr":
        serr = subprocess.PIPE
        sout = None
    elif outputs["return"] == "stdout":
        serr = None
        sout = subprocess.PIPE

    run = subprocess.Popen(
        com, shell=True, stdin=subprocess.PIPE, stdout=sout, stderr=serr, close_fds=True
    )

    run.stdin.write((s_command + command).encode("utf-8"))
    run.stdin.close()

    # --- getting results
    result = ""
    if outputs["return"] in ["both", "stdout"]:
        result = run.stdout.read().decode("utf-8")
    elif outputs["return"] in ["stderr"]:
        result = run.stderr.read().decode("utf-8")

    # --- extracting job id
    jobid = "NA"
    for search in [r"Submitted batch job ([0-9]+)"]:
        m = re.search(search, result)
        if m:
            jobid = m.group(1)

    # --- returning results
    return result, jobid


# -----------------------------------------------------------------------
#                                                  general scheduler code


def run_through_scheduler(command, sessions=None, args=[], parsessions=1, run=None):
    """
    Submits `command` to the scheduler, one job per chunk of sessions.

    The submission record -- what was submitted, with which arguments, and
    which job ids came back -- is printed and appended to the run's runlog.
    The runlog belongs to the run, not to the scheduler: it already holds the
    header and whatever the caller wrote before submitting, so it is never
    opened for writing here.

    Every job is handed the run's log folder with ``--logfolder``, so its
    runlog and comlogs sit beside the submission's, and its own output goes
    to ``<run.logfolder>/batchlogs``, filed under the run's name:
    ``<scheduler>_<name>[_job<NN>].<timestamp>.log``.

    A job starts in the folder the run was started from
    (``run.startfolder``), or in ``--scheduler_workdir``, and runs the
    command line again from there: it decides its study, and where its
    relative paths are taken from, again, as the run did. `gmri` hands it the
    study the run settled (``placement.for_jobs``), so a relative study in the
    batch file header is not read again from another folder.

    A dry run -- ``--test`` or ``--run`` other than ``run`` -- submits
    nothing and creates no ``batchlogs`` folder: it records each job it would
    have submitted, with its command.

    A status record the run was asked for (``--logstatus``, as ``run_recipe``
    asks each step for one) is written here, by the submission: which job each
    session went to, or that it was not submitted. The jobs are not handed
    the path -- each would write the same file, and the last to finish would
    overwrite the others -- so what they did is in their own runlogs.

    For internal use only.
    """
    jobs = []
    # the status record: `(session or command, what was done with it, failed)`;
    # whether a submitted job fails is not known here
    stati = []

    def record(*parts):
        """Print a line of the submission record and add it to the runlog."""
        text = " ".join(str(part) for part in parts)
        print(text)
        if run:
            run.write(text + "\n")

    # ---- setup options to pass to each job
    nopt = []
    for k, v in args.items():
        if k not in [
            "scheduler",
            "scheduler_environment",
            "scheduler_workdir",
            "scheduler_sleep",
            "nprocess",
            "bash",
            "parjobs",
            "logstatus",
        ]:
            nopt.append((k, v))

    # ---- every job logs in the run's folder: it is handed the folder rather
    #      than deciding one of its own, which spread one run over as many
    #      folders as it had jobs. The folder already answers for a
    #      `--logfolder` the run was given, `legacy` and relative ones included
    if run:
        nopt = [(k, v) for k, v in nopt if k != "logfolder"]
        nopt.append(("logfolder", run.logfolder))

    record("---> Running scheduler for command %s" % (command))

    # ---- setup scheduler options
    settings = args["scheduler"]
    settings_list = [e.strip() for e in settings.split(",")]
    scheduler = settings_list.pop(0)
    # the job starts where this run was started, on every scheduler -- PBS and
    # GridEngine would start it in the home folder -- so that its own run
    # settles its study, and takes its relative paths, as this one did
    workdir = (
        args.get("scheduler_workdir")
        or getattr(run, "startfolder", None)
        or os.getcwd()
    )
    environment = args.get("scheduler_environment", None)
    # seconds; a number given on the command line arrives as text
    sleeptime = float(args.get("scheduler_sleep") or 0)

    parjobs = args.get("parjobs", None)
    if parjobs is not None:
        parjobs = int(parjobs)

    parelements = args.get("parelements", 1)
    if parelements is not None:
        parelements = int(parelements)

    # a dry run submits nothing. `--test` arrives here as the flag it was
    # typed as -- `process.flaglist` turns it into `run=test` only in the
    # merged options -- so reading `run` alone submitted the jobs of every
    # `--test` run. A `run` other than `run` is a dry run, as the commands
    # themselves read it
    test = "run" if args.get("run", "run") == "run" and not args.get("test") else "test"

    # check scheduler
    if scheduler not in ["PBS", "SLURM", "GridEngine"]:
        raise ge.CommandError(
            "schedule",
            "Misspecified parameter",
            "First value in the settings string has to specify one of PBS, SLURM or GridEngine!",
            "The settings string submitted was:",
            settings,
        )

    # ---- setup bash (commands to run inside compute node before the QuNex command)
    bash = args.get("bash", None)

    # --- the jobs' own output goes beside the run's other logs, filed under the
    #     run's name as its folder is. Created only when something is
    #     submitted: a dry run submits nothing
    name = run.name if run else command
    logfolder = os.path.join(run.logfolder, "batchlogs") if run else os.path.abspath(".")
    if test == "run":
        os.makedirs(logfolder, exist_ok=True)

    # ---- construct gmri command
    c_base = "\ngmri " + command

    # `nopt` is already free of the scheduler's own parameters; `sessionids`
    # no longer reaches here, the front door having remapped it
    for k, v in nopt:
        c_base += ' --%s="%s"' % (k, v)

    # ---- if sessions is None
    if sessions is None:
        record(
            "\n---> %s %s"
            % ("submitting" if test == "run" else "test, not submitted:", command)
        )
        record(c_base)

        if test != "run":
            stati.append((command, "test, not submitted", 0))
        else:
            exectime = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")
            logfile = os.path.join(
                logfolder, "%s_%s.%s.log" % (scheduler, name, exectime)
            )
            result, jobid = schedule(
                command=c_base,
                settings=settings,
                workdir=workdir,
                environment=environment,
                output="both:%s|return:both" % (logfile),
                bash=bash,
                parsessions=parsessions,
                parelements=parelements,
            )
            jobs.append((jobid, command))
            stati.append((command, "submitted as job %s" % jobid, None))

    # ---- if session list is present
    else:
        settings = {}

        # slurm array
        slurm_array = False

        # split settings
        for s in settings_list:
            # parameters with values
            if "=" in s:
                s_split = s.split("=", 1)

                # SLURM job array?
                if scheduler == "SLURM" and s_split[0].strip() == "array":
                    slurm_array = True

                settings[s_split[0].strip()] = s_split[1].strip()
            # flags
            else:
                # SLURM job array?
                if scheduler == "SLURM" and s.strip() == "array":
                    slurm_array = True
                    if parjobs is None:
                        settings["array"] = "0-%s" % (len(sessions) - 1)
                    else:
                        settings["array"] = "0-%s%%%s" % (len(sessions) - 1, parjobs)
                else:
                    settings[s.strip()] = None

        # only allow HCP MPP commands with job array
        qx_command = command.split(" ")[0]
        if slurm_array:

            array_commands = [
                "hcp_pre_freesurfer",
                "hcp_freesurfer",
                "hcp_nhp_freesurfer",
                "hcp_post_freesurfer",
                "hcp_fmri_volume",
                "hcp_fmri_surface",
                "run_recipe",
            ]
            if qx_command not in array_commands:
                raise ge.CommandError(
                    qx_command,
                    "SLURM job arrays are supported only for HCP Minimal Preprocessing Pipelines: hcp_pre_freesurfer, hcp_freesurfer, hcp_nhp_freesurfer, hcp_post_freesurfer, hcp_fmri_volume and hcp_fmri_surface.",
                )

        settings["jobname"] = settings.get("jobname", command)

        # if job array we have a single job
        if slurm_array:
            parjobs = 1

        # split sessions
        # how big are chunks of sessions
        n_sessions = len(sessions)
        chunks = int(math.ceil(n_sessions / float(parsessions)))
        chunk_size = int(math.ceil(n_sessions / float(chunks)))

        # is parjobs none create a job for each session
        if parjobs is None:
            parjobs = n_sessions

        # if chunks is lower then parjobs tweak parjobs
        if chunks < parjobs:
            parjobs = chunks

        # do not create multiple jobs if running a multi-session command (registered commands only)
        sched_command = qx_commands.get(qx_command)
        if sched_command and "processing.study" in sched_command.type:
            parjobs = 1

        # init queues
        sessionids_array = [""] * parjobs

        # divide sessions among jobs
        job = 0
        start = 0
        for i in range(chunks):
            # get job index
            job = i % parjobs

            if start < n_sessions:
                # get chunk
                sessionids_chunk = []
                for j in range(start, start + chunk_size):
                    if j < n_sessions:
                        sessionids_chunk.append(sessions[j]["id"])

                # add comma if not empty
                if sessionids_array[job] != "":
                    sessionids_array[job] = sessionids_array[job] + ","
                # append chunk
                sessionids_array[job] = sessionids_array[job] + ",".join(
                    sessionids_chunk
                )

            # increase start index
            start = start + chunk_size

        # report how the sessions were divided among the jobs
        record(
            "\n---> QuNex will run the command over %s sessions. It will utilize:\n"
            % n_sessions
        )
        record("    Scheduled jobs: %s " % parjobs)
        record("    Maximum sessions run in parallel for a job: %s." % parsessions)
        record("    Maximum elements run in parallel for a session: %s." % parelements)
        record(
            "    Up to %s processes will be utilized for a job.\n"
            % (parelements * parsessions)
        )

        if slurm_array:
            record("    Using SLURM job array over sessions: %s" % sessionids_array[0])
        else:
            for i in range(0, parjobs):
                record(
                    "    Job #%s will run sessions: %s" % ((i + 1), sessionids_array[i])
                )

        for i in range(parjobs):
            # ---- set the sessions this job runs; the later value wins over
            #      the one c_base carries
            c_str = c_base + ' --sessions="%s"' % sessionids_array[i]
            jobname = "%s_#%02d" % (command, i)
            job_sessions = [sid for sid in sessionids_array[i].split(",") if sid]

            # ---- a dry run says what it would have submitted, and submits
            #      nothing
            if test != "run":
                record("\n---> test, not submitted: %s" % (jobname))
                record(c_str)
                stati += [
                    (sid, "test, not submitted (%s)" % jobname, 0)
                    for sid in job_sessions
                ]
                continue

            # ---- set scheduler settings
            if parjobs > 1:
                settings["jobnum"] = str(i)
            if scheduler != "GridEngine":
                s_string = (
                    scheduler
                    + ","
                    + ",".join(["%s=%s" % (k, v) for (k, v) in settings.items()])
                )
            else:
                s_string = scheduler
                for k, v in settings.items():
                    if v:
                        s_string = "%s,%s" % (s_string, k + "=" + v)
                    else:
                        s_string = "%s,%s" % (s_string, k)

            exectime = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")

            # set different output format for slurm_array
            if not slurm_array:
                logfile = os.path.join(
                    logfolder,
                    "%s_%s_job%02d.%s.log" % (scheduler, name, i, exectime),
                )
            else:
                logfile = os.path.join(
                    logfolder,
                    "%s_%s_job%%a.%s.log" % (scheduler, name, exectime),
                )

            record("\n---> submitting %s" % (jobname))
            record(c_str)

            result, jobid = schedule(
                command=c_str,
                settings=s_string,
                workdir=workdir,
                environment=environment,
                output="both:%s|return:both" % (logfile),
                bash=bash,
                parsessions=parsessions,
                parelements=parelements,
            )
            jobs.append((jobid, jobname))
            stati += [
                (sid, "submitted as job %s (%s)" % (jobid, jobname), None)
                for sid in job_sessions
            ]

            record("...\n", result)

            time.sleep(sleeptime)

    # --- print report
    if jobs:
        record("\n---> Submitted jobs")
        for jobid, jobname in jobs:
            record("     %s -> %s" % (jobid, jobname))

    # --- the status record a parent asked for, written once, by the submission
    if run and args.get("logstatus"):
        run.write_status(stati)

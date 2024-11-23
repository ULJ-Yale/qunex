#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``scheduler.py``

This file holds the functions for running jobs through job schedulers on a
computer cluster. It supports PBS  and SLURM. The functions are accessible and
used both as terminal commands as well as internal use functions.
"""

import subprocess
import math
import os
import os.path
import time
import re

import general.exceptions as ge
import general.core as gc
import general.process as gp

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
):
    """
    ::

        schedule [command=<command string>] [script=<path to script>] \\
                 settings=<settings string> \\
                 [replace=<"key:value|key:value" string>] \\
                 [workdir=<path to working directory>] \\
                 [environment=<path to environment setup script>] \\
                 [output=<string specifying how to process output>]

    Schedules the provided command.

    INPUTS
    ======

    Required parameters
    -------------------

    To run successfully, one of the following has to be provided:

    --command   The string to be executed. It can be a single command or a
                complex multiline script.
    --script    The path to a script to be executed.

    The settings need to be specified by:

    --settings  A string specifying the scheduler to be used and the additional
                settings for it.

    Settings string should be a comma separated list of parameters. The first
    parameter has to be the scheduler name (PBS, SLURM), the rest of the
    parameters are key-value pairs that are to be passed as settings to the
    scheduler. Additional parameters common to all the schedulers can be
    specified:

    - jobname (the name of the job to run)
    - comname (the name of the command the job runs)
    - jobnum  (the number of the job being run)

    Example settings strings::

        "SLURM,jobname=bet1,time=03-24:00:00,cpus-per-task=2,mem-per-cpu=2500,partition=week"

    Optional parameters
    -------------------

    --replace       A string of key-value pairs that specify the specific values
                    to be imputed into the script or command.
    --workdir       A path to the working directory in which the command or
                    script is to be executed.
    --environment   A path to a script to be executed before all other commands
                    to set up the environment for execution.
    --output        A string specifying whether to return or redirect the
                    standard output and error. See "REDIRECTING OUTPUT" for
                    details
    --bash          Used if any additional commands have to be run in the
                    compute node before the execution of the QuNex command
                    itself. Use a semicolon separated list to chain multiple
                    commands. ['']

    If the optional parameters are not specified, they will not be used.

    VALUE EMBEDDING
    ---------------

    If replace parameter is set, all instances of {{key}} in the command or
    script will be replaced with the provided value. The key/value pairs need
    to be separated by pipe characted, whereas key and value need to be
    separated by a colon. An example replacement string::

        "session:AP23791|folder:/studies/WM/sessions/AP23791"

    REDIRECTING OUTPUT
    ------------------

    If no output is specified, the job's standard output and error (stdout,
    stderr) are left as is and processed by the scheduler, and the result of
    submitting the job is printed to standard output. Output string can specify
    four different directives provided by "<key>:<value>" strings separated by
    pipe:

    - stdout  (specifies a path to a log file that should store standard output
      of the submitted job.)
    - stderr  (specified a path to a log file that should store error output
      of the submitted job.)
    - both    (specifies a path to a log file that should store joint standard
      and error outputs of the submitted job.)
    - return  (specifies whether standard output ('stdout'), error outpout
      ('stderr'), both ('both') or none ('none') should be returned as
      a string from the job submission call.)

    Specify "return" value only when schedule is used as a function called from
    another python script or function to process the result.

    Examples
    ~~~~~~~~

    ::

        "stdout:processing.log"

    ::

        "stdout:processing.output.log|stderr:processing.error.log"

    ::
    
        "both:processing.log|return:true"

    Do not specify error and standard outputs both using --output parameter and
    scheduler specific options within settings string.

    SCHEDULER SPECIFICS
    -------------------

    Each of the supported scheduler systems has a somewhat different way of
    specifying job parameters. Please see documentation for each of the
    supported schedulers to provide the correct settings. Below are the
    information for each of the schedulers on how to specify --settings.

    PBS settings
    ~~~~~~~~~~~~

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

    SLURM settings
    ~~~~~~~~~~~~~~

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

    USE
    ===

    Schedules the provided command the referenced script to be run by the
    specified scheduler (PBS and SLURM are currently supported).

    EXAMPLE USE
    ===========
    
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
        setList = [e.strip() for e in settings.split(",")]
        scheduler = setList.pop(0)
        setDict = dict([e.strip().split("=", 1) for e in setList])
        jobname = setDict.pop("jobname", "qx_schedule")
        comname = setDict.pop("comname", "")
        jobnum = setDict.pop("jobnum", "")
    except:
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
        file = open(script, "r")
        command = file.read()

    if workdir is not None:
        if not os.path.exists(workdir):
            raise ge.CommandFailed(
                "schedule",
                "Folder does not exist",
                "The specified working directory does not exist! [%s]" % (workdir),
            )
        command = "cd %s\n" % (workdir) + command

    if environment is not None:
        if not os.path.exists(environment):
            raise ge.CommandFailed(
                "schedule",
                "File not found",
                "The specified environment script does not exist! [%s]" % (environment),
            )
        command = file(environment).read() + "\n" + command

    # --- do search replace
    if replace is not None:
        replace = [e.strip().split(":") for e in replace.split("|")]

        for key, value in replace:
            command.replace("{{%s}}" % (key), value)

    # --- parse output
    outputs = {"stdout": None, "stderr": None, "both": None, "return": None}

    if output is not None:
        for k, v in [[f.strip() for f in e.split(":")] for e in output.split("|")]:
            if not os.path.exists(os.path.dirname(v)) and k != "return":
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
    sCommand = ""

    if scheduler == "PBS":
        for k, v in setDict.items():
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
                sCommand += "#PBS -l %s=%s\n" % (k, v)
            elif k in ("j", "m", "o", "S", "a", "A", "M", "q", "t", "e", "l"):
                sCommand += "#PBS -%s %s\n" % (k, v)
            elif k == "depend":
                sCommand += "#PBS -W depend=%s\n" % (v)
            elif k == "umask":
                sCommand += "#PBS -W umask=%s\n" % (v)
            elif k == "N" and jobname == "qx_schedule":
                jobname = v
            elif k == "nodes":
                sCommand += "#PBS -l nodes=%s\n" % v

        # set default nodes
        if "nodes" not in setDict.keys():
            sCommand += "#PBS -l nodes=1:ppn=%s\n" % (parsessions * parelements)

        # job name
        if comname != "":
            jobname = "%s-%s" % (jobname, comname)
        if jobnum != "":
            jobname = "%s_%s" % (jobname, jobnum)
        sCommand += "#PBS -N %s\n" % jobname

        if outputs["stdout"] is not None:
            sCommand += "#PBS -o %s\n" % (outputs["stdout"])
        if outputs["stderr"] is not None:
            sCommand += "#PBS -e %s\n" % (outputs["stderr"])
        if outputs["both"]:
            sCommand += "#PBS -j oe\n"
        com = "qsub"

    elif scheduler == "SLURM":
        sCommand += "#!/bin/bash\n"
        for key, value in setDict.items():
            if key in ("J", "job-name") and jobname == "qx_schedule":
                jobname = v
            elif value == "QX_FLAG":
                sCommand += "#SBATCH --%s\n" % (key.replace("--", ""))
            else:
                sCommand += "#SBATCH --%s=%s\n" % (key.replace("--", ""), value)

        # set default cpus-per-task
        if "cpus-per-task" not in setDict.keys() and "c" not in setDict.keys():
            sCommand += "#SBATCH --cpus-per-task=%s\n" % (parsessions * parelements)

        # jobname
        if comname != "":
            jobname = "%s-%s" % (jobname, comname)
        if jobnum != "":
            jobname = "%s_%s" % (jobname, jobnum)
        sCommand += "#SBATCH --job-name=%s\n" % jobname

        if outputs["stdout"] is not None:
            sCommand += "#SBATCH -o %s\n" % (outputs["stdout"])
        if outputs["stderr"] is not None:
            sCommand += "#SBATCH -e %s\n" % (outputs["stderr"])
        com = "sbatch"

    # --- run scheduler
    # add bash commands before the qunex command if specified
    if bash:
        sCommand += "\n" + bash + "\n"

    # --- report
    print("\nSubmitting:\n------------------------------")
    print(sCommand)
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

    run.stdin.write((sCommand + command).encode("utf-8"))
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


def runThroughScheduler(
    command, sessions=None, args=[], parsessions=1, logfolder=None, logname=None
):
    jobs = []

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
        ]:
            nopt.append((k, v))

    # ---- open log
    if logname:
        flog = open(logname, "w")
    else:
        flog = None

    gc.printAndLog("---> Running scheduler for command %s" % (command), file=flog)

    # ---- setup scheduler options
    settings = args["scheduler"]
    settings_list = [e.strip() for e in settings.split(",")]
    scheduler = settings_list.pop(0)
    workdir = args.get("scheduler_workdir", None)
    environment = args.get("scheduler_environment", None)
    sleeptime = args.get("scheduler_sleep", 0)

    parjobs = args.get("parjobs", None)
    if parjobs is not None:
        parjobs = int(parjobs)

    parelements = args.get("parelements", 1)
    if parelements is not None:
        parelements = int(parelements)

    test = args.get("run", "run")

    # check scheduler
    if scheduler not in ["PBS", "SLURM"]:
        raise ge.CommandError(
            "schedule",
            "Misspecified parameter",
            "First value in the settings string has to specify one of PBS, SLURM!",
            "The settings string submitted was:",
            settings,
        )

    # ---- setup bash (commands to run inside compute node before the QuNex command)
    bash = args.get("bash", None)

    # --- set logfolder
    if logfolder is None:
        logfolder = os.path.abspath(".")
    else:
        if not os.path.exists(logfolder):
            os.makedirs(logfolder)

    # ---- construct gmri command
    cBase = "\ngmri " + command

    for k, v in nopt:
        if k not in ["sessionids", "scheduler"]:
            cBase += ' --%s="%s"' % (k, v)

    # ---- if sessions is None
    if sessions is None:
        gc.printAndLog("\n---> submitting %s" % (command), file=flog)
        gc.printAndLog(cBase, file=flog)

        if test == "run":
            exectime = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")
            logfile = os.path.join(
                logfolder, "%s_%s.%s.log" % (scheduler, command, exectime)
            )
            result, jobid = schedule(
                command=cBase,
                settings=settings,
                workdir=workdir,
                environment=environment,
                output="both:%s|return:both" % (logfile),
                bash=bash,
                parsessions=parsessions,
                parelements=parelements,
            )
            jobs.append((jobid, command))

    # ---- if session list is present
    else:
        settings = {}

        # slurm array
        slurm_array = False

        # split settings
        for s in settings_list:
            # parameters with values
            if "=" in s:
                sSplit = s.split("=", 1)

                # SLURM job array?
                if scheduler == "SLURM" and sSplit[0].strip() == "array":
                    slurm_array = True

                settings[sSplit[0].strip()] = sSplit[1].strip()
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
                    settings[s.strip()] = "QX_FLAG"

        # only allow HCP MPP commands with job array
        if slurm_array:
            qx_command = command.split(" ")[0]

            array_commands = [
                "hcp_pre_freesurfer",
                "hcp_freesurfer",
                "hcp_post_freesurfer",
                "hcp_fmri_volume",
                "hcp_fmri_surface",
                "run_recipe",
            ]
            if qx_command not in array_commands:
                raise ge.CommandError(
                    qx_command,
                    "SLURM job arrays are supported only for HCP Minimal Preprocessing Pipelines: hcp_pre_freesurfer, hcp_freesurfer, hcp_post_freesurfer, hcp_fmri_volume and hcp_fmri_surface.",
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

        # do not create multiple jobs if running a multi-session command
        if command in gp.mactions or command in gp.lactions:
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

        # print out details
        print(
            "\n---> QuNex will run the command over %s sessions. It will utilize:\n"
            % n_sessions
        )
        print("    Scheduled jobs: %s " % parjobs)
        print("    Maximum sessions run in parallel for a job: %s." % parsessions)
        print("    Maximum elements run in parallel for a session: %s." % parelements)
        print(
            "    Up to %s processes will be utilized for a job.\n"
            % (parelements * parsessions)
        )

        if slurm_array:
            print("    Using SLURM job array over sessions: %s" % sessionids_array[0])
        else:
            for i in range(0, parjobs):
                print(
                    "    Job #%s will run sessions: %s" % ((i + 1), sessionids_array[i])
                )

        if test == "run":
            for i in range(parjobs):
                # ---- set sessionids
                cStr = cBase + ' --sessionids="%s"' % sessionids_array[i]

                # ---- set sheduler settings
                if parjobs > 1:
                    settings["jobnum"] = str(i)
                sString = (
                    scheduler
                    + ","
                    + ",".join(["%s=%s" % (k, v) for (k, v) in settings.items()])
                )
                exectime = datetime.now().strftime("%Y-%m-%d_%H.%M.%S.%f")

                # set different output format for slurm_array
                if not slurm_array:
                    logfile = os.path.join(
                        logfolder,
                        "%s_%s_job%02d.%s.log" % (scheduler, command, i, exectime),
                    )
                else:
                    logfile = os.path.join(
                        logfolder,
                        "%s_%s_job%%a.%s.log" % (scheduler, command, exectime),
                    )

                jobname = "%s_#%02d" % (command, i)

                gc.printAndLog("\n---> submitting %s" % (jobname), file=flog)
                gc.printAndLog(cStr, file=flog)

                result, jobid = schedule(
                    command=cStr,
                    settings=sString,
                    workdir=workdir,
                    environment=environment,
                    output="both:%s|return:both" % (logfile),
                    bash=bash,
                    parsessions=parsessions,
                    parelements=parelements,
                )
                jobs.append((jobid, jobname))

                gc.printAndLog("...\n", result, file=flog)

                time.sleep(sleeptime)

    # --- print report
    if jobs:
        gc.printAndLog("\n---> Submitted jobs", file=flog)
        for jobid, jobname in jobs:
            gc.printAndLog("     %s -> %s" % (jobid, jobname), file=flog)

    # --- close log if specified
    if flog:
        flog.close()

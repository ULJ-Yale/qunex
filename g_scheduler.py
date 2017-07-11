#!/usr/bin/env python
# encoding: utf-8
"""
This file holds the functions for running jobs through job schedulers on a
computer cluster. It supports PBS, LSF, and SLURM. The functions are accessible
and used both as terminal commands as well as internal use functions.

Created by Grega Repovs on 2017-06-17.
Copyright (c) Grega Repovs. All rights reserved.
"""

import sys
import subprocess
import os
import os.path


def schedule(command=None, script=None, settings=None, replace=None, workdir=None, environment=None, output=None):
    '''
    schedule [command=<command string>] [script=<path to script>] \\
             settings=<settings string> \\
             [replace=<"key:value|key:value" string>] \\
             [workdir=<path to working directory>] \\
             [environment=<path to environment setup script>] \\
             [output=<string specifying how to process output>]

    USE
    ===

    Schedules the provided command the referenced script to be run by the
    specified scheduler (PBS, LSF, SLURM are currently supported).

    PARAMETERS
    ==========

    Required parameters
    -------------------

    To run successfully, both one of the following has to be provided:

    --command   The string to be executed. It can be a single command or a
                complex multiline script.
    --script    The path to a script to be executed.

    as well the settings need to be specified by:

    --settings  A string specifying the scheduler to be used and the additional
                settings for it.

    Settings string should be a comma separated list of parameters. The first
    parameter has to be the scheduler name (PBS, LSF, SLURM), the rest of the
    parameters are key-value pairs that are to be passed as settings to the
    scheduler. Additional parameters common to all the schedulers can be
    specified:

    * jobname  - the name of the job to run
    * comname  - the name of the command the job runs
    * jobnum   - the number of the job being run

    Example settings strings:

    "SLURM,jobname=bet1,time=03-24:00:00,ntasks=10,cpus-per-task=2,mem-per-cpu=2500,partition=pi_anticevic"
    "LSF,jobname=DWIproc,jobnum=1,cores=20,mem=250000,walltime=650:00,queue=anticevic"

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

    If the optional parameters are not specified, they will not be used.

    VALUE EMBEDDING
    ===============

    If replace parameter is set, all instances of {{key}} in the command or
    script will be replaced with the provided value. The key/value pairs need
    to be separated by pipe characted, whereas key and value need to be
    separated by a colon. An example replacement string:

    "subject:AP23791|folder:/studies/WM/Subjects/AP23791"

    REDIRECTING OUTPUT
    ==================

    If no output is specified, the job's standard output and error (stdout,
    stderr) are left as is and processed by the scheduler. If --output is set
    to "return", then both the standard output and error are captured and
    returned as a string (to be used when the function is called from python).
    The ouput can be also redirected and appended to specifed file(s) by listing
    them as key/value pairs in a string specifying stdout, stderr or both:

    * "stdout:processing.log"
    * "stdout:processing.output.log|stderr:processing.error.log"
    * "both:processing.log"

    SCHEDULER SPECIFICS
    ===================

    Each of the supported scheduler systems has a somewhat different way of
    specifying job parameters. Please see documentation for each of the
    supported schedulers to provide the correct settings. Below are the
    information for each of the schedulers on how to specify --settings.

    PBS settings
    ------------

    PBS uses various flags to specify parameters. Be careful that the settings
    string includes only comma separated 'key=value' pairs. Scheduler will then
    do its best to use the right flags. Specifically:

    Keys: mem, walltime, software, file, procs, pmem, feature, host,
    naccesspolicy, epilogue, prologue will be submitted using:
    "#PBS -l <key>=<value>".

    Keys: j, m, i, S, a, A, M, q, t will be submitted using:
    "#PBS -<key> <value>"

    Key: depend will be submitted using:

    "#PBS -W depend=<value>"

    Key: nodes is a special case. It can have up to three values separated by
    colon (":"). If there is only one value e.g. "nodes=4" it will submit:

    "#PBS -l nodes=4"

    When there are two values e.g. "nodes=4:2" it will submit:

    "#PBS -l nodes=4:ppn=2"

    When there are three values what is submitted depends on the type of the
    last value. When it is numeric, e.g. "nodes:8:4:2", it will submit:

    "#PBS -l nodes=8:ppn=4:cpus=2"

    If the last of the three values is a string, e.g. "nodes:8:4:blue", it will
    submit the last value as a self-standing key:

    "#PBS -l nodes=8:ppn=4:blue"

    LSF settings
    ------------

    For LSF only the following key/value parameters are passed on:

    * queue    -> "#BSUB -q <queue>"
    * mem      -> "#BSUB -R 'span[hosts=1] rusage[mem=<mem>]"
    * walltime -> "#BSUB -W <walltime>"
    * cores    -> "#BSUB -n <cores>"

    SLURM settings
    --------------

    For SLURM any provided key/value pair will be passed in the form:

    "#SBATCH --<key>=<value>"

    Some of the possible parameters to set are:

    partition        ... The partition (queue) to use
    nodes            ... Total number of nodes to run on
    ntasks           ... Number of tasks
    cpus-per-task    ... Number of cores per task
    time             ... Maximum wall time DD-HH:MM:SS
    constraint       ... Specific node architecture
    mem-per-cpu      ... Memory requested per CPU in MB
    mail-user        ... Email address to send notifications to
    mail-type        ... On what events to send emails


    EXAMPLE USE
    ===========

    gmri schedule command="bet t1.nii.gz brain.nii.gz" \\
                  settings="SLURM,jobname=bet1,time=03-24:00:00,ntasks=10,cpus-per-task=2,mem-per-cpu=2500,partition=pi_anticevic"

    gmri schedule command="bet {{in}} {{out}}" \\
                  replace="in:t1.nii.gz|out:brain.nii.gz" \\
                  settings="SLURM,jobname=bet1,time=03-24:00:00,ntasks=10,cpus-per-task=2,mem-per-cpu=2500,partition=pi_anticevic" \\
                  workdir="/studies/WM/Subjects/AP23791/images/structural"

    ----------------
    Written by Grega Repovš, 2017-06-17

    '''

    # --- check inputs

    if command is None and script is None:
        raise ValueError("ERROR: Either command or script need to be provided to run scheduler!")

    if command is not None and script is not None:
        raise ValueError("ERROR: Only command or script need to be provided to run scheduler!")

    if settings is None:
        raise ValueError("ERROR: Settings need to be provided to run scheduler!")

    # --- parse settings

    setList   = [e.strip() for e in settings.split(",")]
    scheduler = setList.pop(0)
    setDict   = dict([e.strip().split("=") for e in setList])
    jobname   = setDict.pop('jobname', "schedule")
    comname   = setDict.pop('comname', "C")
    jobnum    = setDict.pop('jobnum', "1")

    if scheduler not in ['PBS', 'LSF', 'SLURM']:
        raise ValueError("ERROR: First value in the settings file has to specify one of PBS, LSF, SLURM!")


    # --- compile command to pass

    if command is None:
        if not os.path.exists(script):
            raise ValueError("ERROR: The referenced script does not exist!")
        command = file(script).read()

    if workdir is not None:
        if not os.path.exists(workdir):
            raise ValueError("ERROR: The referenced working directory does not exist!")
        command = "cd %s\n" % (workdir) + command

    if environment is not None:
        if not os.path.exists(environment):
            raise ValueError("ERROR: The referenced environment script does not exist!")
        command = file(environment).read() + "\n" + command

    # --- do search replace

    if replace is not None:
        replace = [e.strip().split(":") for e in replace.split("|")]

        for key, value in replace:
            command.replace("{{%s}}" % (key), value)


    # --- build scheduler commands

    sCommand = ""

    if scheduler == "PBS":
        for k, v in setDict.items():
            if k in ('mem', 'walltime', 'software', 'file', 'procs', 'pmem', 'feature', 'host', 'naccesspolicy', 'epilogue', 'prologue'):
                sCommand += "#PBS -l %s=%s" % (k, v)
            elif k in ('j', 'm', 'o', 'S', 'a', 'A', 'M', 'q', 't'):
                sCommand += "#PBS -%s %s" % (k, v)
            elif k == 'depend':
                sCommand += "#PBS -W depend=%s" % (v)
            elif k == 'nodes':
                v = v.split(':')
                res = 'nodes=%s' % (v.pop(0))
                if v:
                    res += ":ppn=%s" % (v.pop(0))
                if v:
                    if v[0].isnumeric():
                        res += ":gpus=%s" % (v.pop(0))
                    else:
                        res += ":" + v.pop(0)
        sCommand += "#PBS -N %s%s_#%s" % (jobname, comname, jobnum)
        com = 'qsub'

    elif scheduler == "LSF":
        sCommand += "#BSUB -o %s-%s_#%s_%%J\n" % (jobname, comname, jobnum)
        for k, v in [('queue', '#BSUB -q %s\n'), ('mem', "#BSUB -R 'span[hosts=1] rusage[mem=%s]'\n"), ('walltime', '#BSUB -W %s\n'), ('cores', '#BSUB -n %s\n')]:
            if k in setDict:
                sCommand += v % (setDict[k])
        sCommand += "#BSUB -P %s-%s\n" % (jobname, comname)
        sCommand += "#BSUB -J %s-%s_%d\n" % (jobname, comname, jobnum)
        com = 'bsub'

    elif scheduler == "SLURM":
        sCommand += "#!/bin/sh\n"
        sCommand += "#SBATCH --job-name=%s-%s_#%s\n" % (jobname, comname, jobnum)
        for key, value in setDict.items():
            sCommand += "#SBATCH --%s=%s\n" % (key.replace('--', ''), value)
        com = 'sbatch'


    # --- parse output

    sout = None
    serr = None

    if output is not None:
        if 'return' in output:
            serr = subprocess.STDOUT
            sout = subprocess.PIPE
        elif 'both' in output:
            serr = subprocess.STDOUT
            sout = open(output.split(':')[1].strip(), 'a')
        else:
            for k, v in [[f.strip() for f in e.split(":")] for e in output.split("|")]:
                if k == 'stdout':
                    sout = open(v, 'a')
                elif k == 'stderr':
                    serr = open(v, 'a')

    print "Running\n", sCommand + command

    run = subprocess.Popen(com, shell=True, stdin=subprocess.PIPE, stdout=sout, stderr=serr, close_fds=True)
    run.stdin.write(sCommand + command)
    run.stdin.close()

    # ---- storing results

    if output is not None:
        if 'return' in output:
            result = run.stdout.read()
            return result
        elif 'both' in output:
            sout.close()
        else:
            if sout is not None:
                sout.close()
            if serr is not None:
                serr.close()


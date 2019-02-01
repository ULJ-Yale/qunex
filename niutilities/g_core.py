#!/usr/bin/env python2.7
# encoding: utf-8
"""
This file holds code for core support functions used by other code for
preprocessing and analysis. The functions are for internal use
and can not be called externaly.
"""

import re
import os.path
import subprocess
import time
import multiprocessing
import datetime
import glob
import sys
import traceback
import niutilities.g_exceptions as ge


def readSubjectData(filename, verbose=False):
    '''
    readSubjectData(filename, verbose=False)

    An internal function for reading batch.txt files. It reads the file and
    returns a list of subjects with the information on images and the additional
    parameters specified in the header.

    ---
    Written by Grega Repovš.
    '''

    if not os.path.exists(filename):
        print "\n\n=====================================================\nERROR: Batch file does not exist [%s]" % (filename)
        raise ValueError("ERROR: Batch file not found: %s" % (filename))

    s = file(filename).read()
    s = s.replace("\r", "\n")
    s = s.replace("\n\n", "\n")
    s = re.sub("^#.*?\n", "", s)

    s = s.split("\n---")
    s = [e for e in s if len(e) > 10]

    nsearch = re.compile('(.*?)\((.*)\)')
    csearch = re.compile('c([0-9]+)$')

    slist = []
    gpref = {}

    c = 0
    try:
        for sub in s:
            sub = sub.split('\n')
            sub = [e.strip() for e in sub]
            sub = [e.split("#")[0].strip() for e in sub]
            sub = [e for e in sub if len(e) > 0]

            dic = {}
            for line in sub:
                c += 1
                line = line.split(':')
                line = [e.strip() for e in line]
                if len(line) < 2:
                    continue

                # --- read global preferences / settings

                if len(line[0]) > 0:
                    if line[0][0] == "_":
                        gpref[line[0][1:]] = line[1]

                # --- read ima data

                if line[0].isdigit():
                    image = {}
                    image['ima'] = line[0]
                    remove = []
                    for e in line:
                        m = nsearch.match(e)
                        if m:
                            image[m.group(1)] = m.group(2)
                            remove.append(e)
                    
                    for e in remove:
                        line.remove(e)

                    ni = len(line)
                    if ni > 1:
                        image['name'] = line[1]
                    if ni > 2:
                        image['task'] = line[2]
                    if ni > 3:
                        image['ext']  = line[3]

                    dic[line[0]] = image


                # --- read conc data

                elif csearch.match(line[0]):
                    conc = {}
                    conc['cnum'] = line[0]
                    for e in line:
                        m = nsearch.match(e)
                        if m:
                            conc[m.group(1)] = m.group(2)
                            line.remove(e)

                    ni = len(line)
                    if ni < 3:
                        print "Missing data for conc entry!"
                        raise AssertionError('Not enough values in conc definition line!')

                    conc['label'] = line[1]
                    conc['conc']  = line[2]
                    conc['fidl']  = line[3]
                    dic[line[0]]  = conc

                # --- read rest of the data

                else:
                    dic[line[0]] = line[1]

            if len(dic) > 0:
                if "id" not in dic:
                    if verbose:
                        print "WARNING: There is a record missing an id field and is being omitted from processing."
                # elif "data" not in dic:
                #    if verbose:
                #        print "WARNING: Subject %s is missing a data field and is being omitted from processing." % (dic['id'])
                else:
                    slist.append(dic)

            # check paths

            for field in ['dicom', 'raw_data', 'data', 'hpc']:
                if field in dic:
                    if not os.path.exists(dic[field]) and verbose:
                        print "WARNING: subject %s - folder %s: %s specified in %s does not exist! Check your paths!" % (dic['id'], field, dic[field], os.path.basename(filename))


    except:
        print "\n\n=====================================================\nERROR: There was an error with the batch.txt file in line %d:\n---> %s\n\n--------\nError raised:\n" % (c, line)
        raise

    return slist, gpref



def readList(filename, verbose=False):
    '''
    readList(filename, verbose=False)

    An internal function for reading list files. It reads the file and
    returns a list of subjects each with the provided list of files.

    ---
    Written by Grega Repovš.'''

    slist   = []
    subject = None

    with open(filename) as f:
        for line in f:
            if line.strip()[:1] == "#":
                continue

            line = [e.strip() for e in line.split(":")]

            if len(line) == 2:

                if line[0] == "subject id":
                    if subject is not None:
                        slist.append(subject)
                    subject = {'id': line[1]}

                else:
                    if line[0] in subject:
                        subject[line[0]].append(line[1])
                    else:
                        subject[line[0]] = [line[1]]

    return slist


def getSubjectList(listString, sfilter=None, subjid=None, subjectsfolder=None, verbose=False):
    '''
    getSubjectList(listString, sfilter=None, subjid=None, subjectsfolder=None, verbose=False)

    An internal function for getting a list of subjects as an array of dictionaries in
    the form: [{'id': <subject id>, [... other keys]}, {'id': <subject id>, [... other keys]}].

    The provided listString can be:

    * a comma, space or pipe separated list of subject id codes,
    * a path to a batch file (identified by .txt extension),
    * a path to a *.list file (identified by .list extension).

    In the first cases, the dictionary will include only subject ids, in the second all the
    other information present in the batch file, in the third lists of specified files, e.g.:
    [{'id': <subject id>, 'file': [<first file>, <second file>], 'roi': [<first file>], ...}, ...]

    If sfilter is provided (not None), only subjects that match the filter will be returned.
    If subjid is provided (not None), only subjects with matching id will be returned.
    If subjectsfolder is provided (not None), subjects from a listString will be treated as
    glob patterns and all folders that match the pattern in the subjectsfolder will be returned
    as subject ids.

    ---
    Written by Grega Repovš.
    '''

    gpref = {}

    listString = listString.strip()

    if re.match(".*\.list$", listString):
        slist = readList(listString, verbose=verbose)

    elif os.path.isfile(listString):
        slist, gpref = readSubjectData(listString, verbose=verbose)

    elif re.match(".*\.txt$", listString) or '/' in listString:
        raise ValueError("ERROR: The specified subject file is not found! [%s]!" % listString)

    else:
        slist = [e.strip() for e in re.split(' +|,|\|', listString)]

        if subjectsfolder is None:
            slist = [{'id': e} for e in slist]

        else:
            nlist = []
            for s in slist:
                nlist += glob.glob(os.path.join(subjectsfolder, s))
            slist = [{'id': os.path.basename(e)} for e in nlist]

    if subjid is not None and subjid.strip() is not "":
        subjid = re.split(' +|,|\|', subjid)
        slist = [e for e in slist if e['id'] in subjid]

    if sfilter is not None and sfilter.strip() is not "":
        try:
            filters = [[f.strip() for f in e.split(':')] for e in sfilter.split("|")]
        except:
            raise ValueError("ERROR: The provided filter parameter is invalid [%s]!" % sfilter)

        for key, value in filters:
            slist = [e for e in slist if key in e and e[key] == value]

    return slist, gpref


def deduceFolders(args):
    '''
    deduceFolders(args)

    Tries to deduce the location of study specific folders based on the provided
    arguments. For internal use only.

    ---
    Written by Grega Repovš, 2018-03-31
    '''

    logfolder  = args.get('logfolder')
    basefolder = args.get('basefolder')
    subjectsfolder = args.get('subjectsfolder')
    sfolder = args.get('sfolder')
    folder = args.get('folder')

    if basefolder is None:
        if subjectsfolder:
            basefolder = os.path.dirname(subjectsfolder)
        else:
            for f in [os.path.abspath(e) for e in [logfolder, sfolder, folder, "."] if e]:
                if f and not basefolder:
                    while os.path.dirname(f) and os.path.dirname(f) != '/':
                        f = os.path.dirname(f)
                        if os.path.exists(os.path.join(f, '.mnapstudy')):
                            basefolder = f
                            break

    if logfolder is None:
        logfolder = os.path.abspath(".")
        if basefolder:
            logfolder = os.path.join(basefolder, 'processing', 'logs')

    return {'basefolder': basefolder, 'subjectsfolder': subjectsfolder, 'logfolder': logfolder}


def runExternalParallel(calls, cores=None, prepend=''):
    '''
    runExternalParallel(calls, cores=None, prepend='')

    Runs external commands specified in 'calls' in parallel utilizing all the available or the number of cores specified in 'cores'.
    Parameters:

    calls   : A list of dictionaries that specifies the commands to run. It should consists of:
              - name : The name of the command to run.
              - args : The actual command provided as a list of arguments.
              - sout : The name of the log file to which to direct the standard output from the command ran.
    cores   : The number of cores to utilize. If specified as None or 'all', all available cores will be utilised.
    prepend : The string to prepend to each line of progress report.

    Example call:
    runExternalParallel({'name': 'List all zip files', 'args': ['ls' '-l' '*.zip'], 'sout': 'zips.log'}, cores=1, prepend=' ... ')

    ---
    Written by Grega Repovš.
    '''

    if cores is None or cores in ['all', 'All', 'ALL']:
        cores = multiprocessing.cpu_count()
    else:
        try:
            cores = int(cores)
        except:
            cores = 1

    running   = []
    completed = []

    while True:

        # --- check if we can add a process to run
        if len(running) < cores:
            if calls:
                call = calls.pop(0)
                if call['sout']:
                    sout = open(call['sout'], 'a', 1)
                else:
                    sout = open(os.devnull, 'w')
                print >> sout, "Starting log for %s at %s\nThe command being run: \n>> %s\n" % (call['name'], str(datetime.datetime.now()).split('.')[0], " ".join(call['args']))
                try:
                    running.append({'call': call, 'sout': sout, 'p': subprocess.Popen(call['args'], stdout=sout, stderr=sout, bufsize=0)})
                    if call['sout']:
                        print prepend + "started running %s at %s, track progress in %s" % (call['name'], str(datetime.datetime.now()).split('.')[0], call['sout'])
                    else:
                        print prepend + "started running %s at %s" % (call['name'], str(datetime.datetime.now()).split('.')[0])
                except:
                    print prepend + "failed to start running %s. Please check your environment!" % (call['name'])
                    completed.append({'exit': -9, 'name': call['name'], 'log': call['sout'], 'args': call['args']})
                continue

        # --- check if a process finished
        done = []
        for n in range(len(running)):
            running[n]['sout'].flush()

            if running[n]['p'].poll() is not None:
                running[n]['sout'].close()
                if running[n]['call']['sout']:
                    print prepend + "finished running %s (exit code: %d), log in %s" % (running[n]['call']['name'], running[n]['p'].poll(), running[n]['call']['sout'])
                else:
                    print prepend + "finished running %s (exit code: %d)" % (running[n]['call']['name'], running[n]['p'].poll())
                completed.append({'exit': running[n]['p'].poll(), 'name': running[n]['call']['name'], 'log': running[n]['call']['sout'], 'args': running[n]['call']['args']})
                done.append(n)
        if done:
            while done:
                running.pop(done.pop())
            continue

        # --- check if we are done:
        if not calls and not running:
            print prepend + "DONE"
            break

        # --- wait a bit
        time.sleep(1)

    return completed


results = []
lock    = multiprocessing.Lock()

def record(response):
    '''
    record(response)

    Appends response from a completed function.

    For internal use only.

    ---
    Written by Grega Repovš, 2018-03-31

    Change log:
    2019-01-17 - Grega Repovš
                 Fixed the correct response
    '''

    global results

    results.append(response)

    with lock:
        name, result, targetLog, prepend = response
        if targetLog:
            see = " [log: %s]." % (targetLog)
        else:
            see = "."

        if result:
            print "%s%s failed%s" % (prepend, name, see)
        else:
            print "%s%s finished successfully%s" % (prepend, name, see)



def runWithLog(function, args=None, logfile=None, name=None, prepend=None):
    '''
    runWithLog(function, args=None, logfile=None, name=None)
    Runs a function with the arguments by redirecting standard output and
    standard error to the specified log file.

    For internal use only.

    ---
    Written by Grega Repovš, 2018-03-31
    '''

    if name is None:
        name = function.__name__

    if logfile:
        logFolder, logName = os.path.split(logfile)
        logNameBase, logNameExt = os.path.splitext(logName)
        logName  = logNameBase + "_" + datetime.datetime.now().strftime("%Y-%m-%d.%H.%M.%S.%f") + logNameExt
        tlogfile = os.path.join(logFolder, 'running_' + logName)

        if not os.path.exists(logFolder):
            os.makedirs(logFolder)
        with lock:
            print prepend + "started running %s at %s, track progress in %s" % (name, str(datetime.datetime.now()).split('.')[0], tlogfile)

        sysstdout = sys.stdout
        sysstderr = sys.stderr
        sys.stdout = open(tlogfile, 'w', 1)
        sys.stderr = sys.stdout
    else:
        with lock:
            print prepend + "started running %s at %s" % (name, str(datetime.datetime.now()).split('.')[0])

    with lock:
        print "Started running %s at %s\ncall: gmri %s %s\n-----------------------------------------" % (name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), function.__name__, " ".join(['%s="%s"' % (k, v) for (k, v) in args.items()]))

    try:
        result = function(**args)
    except (ge.CommandError, ge.CommandFailed) as e:
        with lock:
            print "\n\nERROR"
            print e.message
        result = e.error
    except Exception as e:
        with lock:
            print "\n\nERROR"
            print traceback.format_exc()
        result = e.message

    with lock:
        print "\n-----------------------------------------\nFinished at %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    if logfile:
        sys.stdout.close()
        sys.stdout = sysstdout
        sys.stderr = sysstderr

        if result:
            targetLog = os.path.join(logFolder, 'error_' + logName)            
        else:
            targetLog = os.path.join(logFolder, 'done_' + logName)
        os.rename(os.path.join(logFolder, 'running_' + logName), targetLog)
    else:
        targetLog = None

    return name, result, targetLog, prepend



def runInParallel(calls, cores=None, prepend=""):
    '''
    runInParallel(calls, cores=None, prepend="")

    Runs functions specified in 'calls' in parallel utilizing all the available or the number of cores specified in 'cores'.
    Parameters:

    calls   : A list of dictionaries that specifies the commands to run. It should consists of:
              - name     : The name of the command to run.
              - function : The function to be run.
              - args     : The arguments to be passed to the function.
              - logfile  : The path to the log file to which to direct the standard output from the command ran.
    cores   : The number of cores to utilize. If specified as None or 'all', all available cores will be utilised.
    prepend : The string to prepend to each line of progress report.

    Example call:
    runInParallel({'name': 'Sort dicom files', 'function': niu.g_dicom.sortDicom, 'args': {'folder': '.'}, 'sout': 'sortDicom.log'}, cores=1, prepend=' ... ')

    ---
    Written by Grega Repovš, 2018-03-31
    '''

    global results

    if cores is None or cores in ['all', 'All', 'ALL']:
        cores = multiprocessing.cpu_count()
    else:
        try:
            cores = int(cores)
        except:
            cores = 1

    pool    = multiprocessing.Pool(processes=cores)
    results = []

    for call in calls:
        pool.apply_async(runWithLog, (call['function'], call['args'], call['logfile'], call['name'], prepend), callback=record)

    pool.close()
    pool.join()

    return results



def checkFiles(testFolder, specFile, fields=None, report=None, append=False):
    '''
    Check the testFolder for presence of files as specified in specFile, which 
    lists files one per line with space delimited paths. Additionally an array
    of key-value pairs can be provided. If present every instance of {<key>} 
    will be replaced by <value>. If report is specified, a report will be 
    written to that file.
    '''

    # --- initial tests

    if not os.path.exists(testFolder):
        raise ge.CommandFailed("checkFiles", "Folder to test does not exist", "The folder to be tested does not exist: %s" % (testFolder), "Please check your settings and paths!")

    if not os.path.exists(specFile):
        raise ge.CommandFailed("checkFiles", "Specification file does not exist", "The specification file to test folder against does not exist: %s" % (specFile), "Please check your settings and paths!")

    # --- open the report if needed:

    if report:
        try:
            if append:
                rout = open(report, 'a')
                print >> rout, "\n-----------------------------------------\nFull file check report\n"
            else:
                rout = open(report, 'w')
        except:
            raise ge.CommandFailed("checkFiles", "Report file could not be opened", "Failed to open a report file for writing: %s" % (report), "Please check your settings and paths!")

    # --- read the spec

    files = open(specFile, 'r').read()

    if fields:
        for key, value in fields:
            files = files.replace('{%s}' % (key), value)

    files = [e.split() for e in files.split('\n') if len(e)]

    # --- test the files

    present = []
    missing = []
    for file in files:
        test = [testFolder] + file
        tfile = os.path.join(*test)
        if os.path.exists(tfile):
            present.append(tfile)
            if report:
                print >> rout, ". " + tfile
        else:
            missing.append(tfile)
            if report:
                print >> rout, "X " + tfile

    if report:
        rout.close()

    status = len(missing) == 0

    return status, present, missing


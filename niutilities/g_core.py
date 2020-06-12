#!/usr/bin/env python2.7
# encoding: utf-8
"""
This file holds code for core support functions used by other code for
preprocessing and analysis. The functions are for internal use
and can not be called externaly.
"""

import re
import os.path
import os
import shutil
import subprocess
import time
import multiprocessing
import datetime
import glob
import sys
import types
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

    Change log

    2019-05-22 Grega Repovš
             - Now only reads '_' parameters as global variables in the initial section
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
    first = True
    try:
        for sub in s:
            sub = sub.split('\n')
            sub = [e.strip() for e in sub]
            sub = [e.split("#")[0].strip() for e in sub]
            sub = [e for e in sub if len(e) > 0]

            dic = {}
            for line in sub:
                c += 1

                # --- read preferences / settings

                if line.startswith('_'):
                    pkey, pvalue = [e.strip() for e in line.split(':', 1)]
                    if first:
                        gpref[pkey[1:]] = pvalue
                    else:
                        dic[pkey] = pvalue
                    continue

                # --- split line

                line = line.split(':')
                line = [e.strip() for e in line]
                if len(line) < 2:
                    continue

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
                    dic[line[0]] = ":".join(line[1:])

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
                        print "WARNING: session %s - folder %s: %s specified in %s does not exist! Check your paths!" % (dic['id'], field, dic[field], os.path.basename(filename))


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


def getSubjectList(listString, filter=None, sessionids=None, sessionsfolder=None, verbose=False):
    '''
    getSubjectList(listString, filter=None, sessionids=None, sessionsfolder=None, verbose=False)

    An internal function for getting a list of subjects as an array of dictionaries in
    the form: [{'id': <subject id>, [... other keys]}, {'id': <subject id>, [... other keys]}].

    The provided listString can be:

    * a comma, space or pipe separated list of subject id codes,
    * a path to a batch file (identified by .txt extension),
    * a path to a *.list file (identified by .list extension).

    In the first cases, the dictionary will include only subject ids, in the second all the
    other information present in the batch file, in the third lists of specified files, e.g.:
    [{'id': <subject id>, 'file': [<first file>, <second file>], 'roi': [<first file>], ...}, ...]

    If filter is provided (not None), only subjects that match the filter will be returned.
    If sessionids is provided (not None), only subjects with matching id will be returned.
    If sessionsfolder is provided (not None), subjects from a listString will be treated as
    glob patterns and all folders that match the pattern in the sessionsfolder will be returned
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

        if sessionsfolder is None:
            slist = [{'id': e} for e in slist]

        else:
            nlist = []
            for s in slist:
                nlist += glob.glob(os.path.join(sessionsfolder, s))
            slist = [{'id': os.path.basename(e)} for e in nlist]

    if sessionids is not None and sessionids.strip() is not "":
        sessionids = re.split(' +|,|\|', sessionids)
        slist = [e for e in slist if e['id'] in sessionids]

    if filter is not None and filter.strip() is not "":
        try:
            filters = [[f.strip() for f in e.split(':')] for e in filter.split("|")]
        except:
            raise ge.CommandFailed("getSubjectList", "Invalid filter parameter", "The provided filter parameter is invalid: '%s'" % (filter), "The parameter should be a '|' separated  string of <key>:<value> pairs!", "Please adjust the parameter!")
            
        if any([len(e) != 2 for e in filters]):
            raise ge.CommandFailed("getSubjectList", "Invalid filter parameter", "The provided filter parameter is invalid: '%s'" % (filter), "The parameter should be a '|' separated  string of <key>:<value> pairs!", "Please adjust the parameter!")

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

    reference  = args.get('reference')
    logfolder  = args.get('logfolder')
    basefolder = args.get('basefolder')
    sessionsfolder = args.get('sessionsfolder')
    sourcefolder = args.get('sourcefolder')
    folder = args.get('folder')

    if sessionsfolder:
        sessionsfolder = os.path.abspath(sessionsfolder)

    if basefolder is None:
        if sessionsfolder:
            basefolder = os.path.dirname(sessionsfolder)
        else:
            for f in [os.path.abspath(e) for e in [logfolder, sourcefolder, folder, reference, "."] if e]:
                if f and not basefolder:
                    while os.path.dirname(f) and os.path.dirname(f) != '/':
                        f = os.path.dirname(f)
                        if os.path.exists(os.path.join(f, '.qunexstudy')):
                            basefolder = f
                            break
                        elif os.path.exists(os.path.join(f, '.mnapstudy')):
                            basefolder = f
                            break

    if logfolder is None:
        logfolder = os.path.abspath(".")
        if basefolder:
            logfolder = os.path.join(basefolder, 'processing', 'logs')

    return {'basefolder': basefolder, 'sessionsfolder': sessionsfolder, 'logfolder': logfolder}


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
                    if 'shell' in call and call['shell']:
                        running.append({'call': call, 'sout': sout, 'p': subprocess.Popen(call['args'], stdout=sout, stderr=sout, bufsize=0, shell=True)})
                    else:
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
    written to that file. Where there might be two alternative options of results
    e.g. difference because of AP/PA direction, then the alternative is to 
    be provided in the same line separated by a pipe '|'
    '''
 
    # --- open the report if needed:

    if report:
        if type(report) is types.FileType:
            rout = report
            fileClose = False
        else:
            fileClose = True
            try:
                if append:
                    rout = open(report, 'a')
                else:
                    rout = open(report, 'w')
            except:
                raise ge.CommandFailed("checkFiles", "Report file could not be opened", "Failed to open a report file for writing: %s" % (report), "Please check your settings and paths!")
        print >> rout, "\n#-----------------------------------------\n# Full file check report\n# . denotes file present\n# X denotes file absent\n"

    # --- initial tests

    if not os.path.exists(testFolder):
        print >> rout, "The folder to be tested does not exist: %s \nPlease check your settings and paths!" % (testFolder)
        print >> rout, "\n#-----------------=== End Full File Report ===----------------------"
        if fileClose:
            rout.close()
        raise ge.CommandFailed("checkFiles", "Folder to test does not exist", "The folder to be tested does not exist: %s" % (testFolder), "Please check your settings and paths!")

    if not os.path.exists(specFile):
        print >> rout, "The specification file to test folder against does not exist: %s\nPlease check your settings and paths!" % (specFile)
        print >> rout, "\n#-----------------=== End Full File Report ===----------------------"
        if fileClose:
            rout.close()
        raise ge.CommandFailed("checkFiles", "Specification file does not exist", "The specification file to test folder against does not exist: %s" % (specFile), "Please check your settings and paths!")

    # --- read the spec

    files = open(specFile, 'r').read()

    if fields:
        for key, value in fields:
            files = files.replace('{%s}' % (key), value)

    files = [[f.strip().split() for f in e.split('|')] for e in files.split('\n') if len(e) and not e.startswith('#')]

    # --- test the files

    present = []
    missing = []
    for testfiles in files:
        fileMissing = True
        for testfile in testfiles:
            test = [testFolder] + testfile
            tfile = os.path.join(*test)
            if os.path.exists(tfile):
                present.append(tfile)
                fileMissing = False
                if report:
                    print >> rout, ". " + tfile
                break
        if fileMissing:
            missing.append(tfile)
            if report:
                print >> rout, "X " + tfile

    if report:
        print >> rout, "\n#-----------------=== End Full File Report ===----------------------"
        if fileClose:
            rout.close()

    status = len(missing) == 0

    return status, present, missing


def printAndLog(*args, **kwargs):
    '''
    Prints all that is given as nonpositional argument to the standard output.
    For keyword arguments:

    * file     ... prints to the file
    * write    ... creates a file and writes to it
    * append   ... opens a file and appends to it
    * silent   ... whether to not print to stdout
    * end      ... how to end ['\n']
    '''

    silent = kwargs.get('silent', False)
    file   = kwargs.get('file', None)
    write  = kwargs.get('write', None)
    append = kwargs.get('append', None)
    end    = kwargs.get('end', '\n')

    if write:
        write = open(write, 'w')
    if append:
        append = open(append, 'a')

    for element in args + (end, ):
        if not silent:
            print element, 
        for out in [append, write, file]:
            if out:
                print >> out, element,
    
    for toclose in [append, write]:
        if toclose:
            toclose.close()



def getLogFile(folders=None, tags=None):
    """
    Creates a log file in the comlogs folder and returns the name and the file handle.
    It tries to find the correct location for the log based on the provided folders.
    
    Arguments:
    - folders  ... a dictionary with the known paths
    - tags     ... an array of strings to use to create the filename

    Returns
    - filename     ... the path to the log file
    - file handle  ... the file handle of the open file

    ---
    Written by Grega Repovš, 2019-05-29
    """

    folders = deduceFolders(folders)

    if 'logfolder' not in folders:
        raise ge.CommandFailed("getLogFile", "Logfolder not found" , "Could not deduce the location of the log folder based on the provided information!")

    if isinstance(tags, basestring) or tags is None:
        tags = [logtags]

    logstamp = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%s")
    logname  = tags + [logstamp]
    logname  = [e for e in logname if e]
    logname  = "_".join(logname)
    logname  = os.path.join(folders['logfolder'], 'comlogs', "tmp_%s.log" % (logname))
    logfile  = open(logname, 'w')

    return logname, logfile


def closeLogFile(logfile=None, logname=None, status="done"):
    """
    Closes the logfile and swaps the 'tmp_', 'done_', 'error_', 'incomplete_' at the start of the logname to the
    provided status.

    ---
    Written by Grega Repovš, 2019-05-29
    """

    if logfile:
        logfile.close()

    if logname:
        logfolder, newname = os.path.split(logname)
        newname = re.sub('^(tmp_|done_|error_|incomplete_|)', status + '_', newname)
        newfile = os.path.join(logfolder, newname)
        os.rename(logname, newfile)

    return newfile


def underscore(s):
    s = s + "\n" + "".join(['=' for e in range(len(s))])
    return s


def linkOrCopy(source, target):
    """
    linkOrCopy - documentation not yet available.
    """
    if os.path.exists(source):
        try:
            if os.path.exists(target):
                if os.path.samefile(source, target):
                    return
                else:
                    os.remove(target)
            if os.path.islink(source):
                linkto = os.readlink(source)
                os.symlink(linkto, target)
            else:
                os.link(source, target)
        except:
            shutil.copy2(source, target)


def moveLinkOrCopy(source, target, action=None, r=None, status=None, name=None, prefix=None):
    """
    moveLinkOrCopy - documentation not yet available.
    """
    if action is None:
        action = 'link'
    if status is None:
        status = True
    if name is None:
        name = source
    if prefix is None:
        prefix = ""

    if os.path.exists(source):

        if not os.path.exists(os.path.dirname(target)):
            try:
                os.makedirs(os.path.dirname(target))
            except:
                if r is None:
                    return False
                else:
                    return (False, "%s%sERROR: %s could not be %sed, target folder could not be created, check permissions! " % (r, prefix, name, action))

        if action == 'link':
            try:
                if os.path.exists(target):
                    if os.path.samefile(source, target):
                        if r is None:
                            return status
                        else:
                            return (status, "%s%s%s already mapped" % (r, prefix, name))
                    else:
                        os.remove(target)
                os.link(source, target)
                if r is None:
                    return status
                else:
                    return (status, "%s%s%s mapped" % (r, prefix, name))
            except:
                action = 'copy'

        if action == 'copy':
            try:
                shutil.copy2(source, target)
                if r is None:
                    return status
                else:
                    return (status, "%s%s%s copied" % (r, prefix, name))
            except:
                if r is None:
                    return False
                else:
                    return (False, "%s%sERROR: %s could not be copied, check permissions! " % (r, prefix, name))

        if action == 'move':
            try:
                shutil.move(source, target)
                if r is None:
                    return status
                else:
                    return (status, "%s%s%s moved" % (r, prefix, name))
            except:
                if r is None:
                    return False
                else:
                    return (False, "%s%sERROR: %s could not be moved, check permissions! " % (r, prefix, name))

    else:
        if r is None:
            return False
        else:
            return (False, "%s%sERROR: %s could not be %sed, source file does not exist [%s]! " % (r, prefix, name, action, source))

def createSubjectFile(command, sfolder, session, subject)
    """
    Creates the generic, non pipeline specific, subject file.

    ---
    Written by Jure Demšar, 2020-06-09
    """
    # open fifle
    sfile = os.path.join(sfolder, 'session.txt')
    if os.path.exists(sfile):
        if overwrite == 'yes':
            os.remove(sfile)
            print "--> removed existing session.txt file"
        else:
            raise ge.CommandFailed(command, "session.txt file already present!", "A session.txt file alredy exists [%s]" % (sfile), "Please check or set parameter 'overwrite' to 'yes' to rebuild it!")

    sout = open(sfile, 'w')
    print >> sout, 'id:', session
    print >> sout, 'subject:', subject
     
    # bids
    bfolder = os.path.join(sfolder, 'bids')
    if os.path.exist(bfolder):
        print >> sout, 'bids:', bfolder

    # nii
    nfolder = os.path.join(sfolder, 'nii')
    if os.path.exist(bfolder):
        print >> sout, 'raw_data:', nfolder

    # hcp
    hfolder = os.path.join(sfolder, 'hcp')
    print >> sout, 'hcp:', hfolder

    # empty line
    print >> sout

    # return
    return sout
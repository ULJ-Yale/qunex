#!/usr/bin/env python
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


def readSubjectData(filename, verbose=False):
    '''
    readSubjectData(filename, verbose=False)

    An internal function for reading subjects.txt files. It reads the file and
    returns a list of subjects with the information on images and the additional
    parameters specified in the header.

    '''
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
            sub = [e for e in sub if len(e) > 0]
            sub = [e for e in sub if e[0] != "#"]

            dic = {}
            images = {}
            for line in sub:
                c += 1
                line = line.split(':')
                line = [e.strip() for e in line]

                # --- read global preferences / settings

                if len(line[0]) > 0:
                    if line[0][0] == "_":
                        gpref[line[0][1:]] = line[1]

                # --- read ima data

                if line[0].isdigit():
                    image = {}
                    image['ima'] = line[0]
                    for e in line:
                        m = nsearch.match(e)
                        if m:
                            image[m.group(1)] = m.group(2)
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
        print "\n\n=====================================================\nERROR: There was an error with the subjects.txt file in line %d:\n---> %s\n\n--------\nError raised:\n" % (c, line)
        raise

    return slist, gpref



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
                sout = open(call['sout'], 'a', 1)
                print >> sout, "Starting log for %s at %s\nThe command being run: \n>> %s\n" % (call['name'], str(datetime.datetime.now()).split('.')[0], " ".join(call['args']))
                running.append({'call': call, 'sout': sout, 'p': subprocess.Popen(call['args'], stdout=sout, stderr=sout, bufsize=0)})
                print prepend + "started running %s at %s, track progress in %s" % (call['name'], str(datetime.datetime.now()).split('.')[0], call['sout'])
                continue

        # --- check if a process finished
        done = []
        for n in range(len(running)):
            running[n]['sout'].flush()

            if running[n]['p'].poll() is not None:
                running[n]['sout'].close()
                print prepend + "finished running %s (exit code: %d), log in %s" % (running[n]['call']['name'], running[n]['p'].poll(), running[n]['call']['sout'])
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











#!/opt/local/bin/python2.7

import re
import os.path

def readSubjectData(filename, verbose=False):
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
            sub = [e for e in sub if len(e)>0]
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
                #elif "data" not in dic:
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

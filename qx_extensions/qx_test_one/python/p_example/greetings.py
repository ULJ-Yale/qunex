#!/usr/bin/env python
# encoding: utf-8

import os
import os.path
import sys

# print "This should cause an error."

if "QUNEXPATH" in os.environ:
    sys.path.append(os.path.join(os.environ['QUNEXPATH'], 'python', 'qx_utilities'))
    import general.exceptions as ge
    from processing.core import *

else:
    exit(1)


def greet_all(sinfo, options, overwrite=False, thread=0):
    '''
    ``greet_all [... processing options]``

    Greets all sessions with the name provided as --p_name.

    --p_old_name is mapped to --p_name
    --p_last_name is deprecated
    '''

    report = {'boldgreeted': 0, 'boldmissing': 0, "boldskipped": 0}

    r = "\n ---------------------------------------------"
    r += "\nSession id: %s \n[started on %s]" % (sinfo['id'], datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    r = "\n ---------------------------------------------"

    doOptionsCheck(options, sinfo, 'greet_all')
    f = getFileNames(sinfo, options)

    bolds, bskip, report['boldskipped'], r = useOrSkipBOLD(sinfo, options, r)

    for boldnum, boldname, boldtask, boldinfo in bolds:

        r += "\n\nWorking on: " + boldname + " ..."

        # --- filenames
        f = getFileNames(sinfo, options)
        f.update(getBOLDFileNames(sinfo, boldname, options))

        if os.path.exists(f['bold']):
            r += '\n ... %s greets bold: %s kindly' % (options['p_name'], f['bold'])
            report['boldgreeted'] += 1
        else:
            r += '\n ... ops, found missing bold: %s' % (f['bold'])
            report['boldmissing'] += 1

    r += "\n\nBold greeting completed on %s\n---------------------------------------------------------" % (datetime.now().strftime("%A, %d. %B %Y %H:%M:%S"))
    rstatus = "BOLDS greeted: %(boldgreeted)2d, missing: %(boldmissing)2d, skipped: %(boldskipped)2d" % (report)

    print(r)
    return (r, (sinfo['id'], rstatus, report['boldmissing']))


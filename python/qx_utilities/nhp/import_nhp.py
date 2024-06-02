#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``import_nhp.py``

Functions for importing non-human primate (NHP) data into QuNex:

--import_nhp      Maps NHP dMRI data to QuNex structure.

The commands are accessible from the terminal using the gmri utility.
"""

"""
Copyright (c) Grega Repovs and Jure Demsar.
All rights reserved.
"""

# general imports
import os
import shutil
import zipfile
import tarfile
import glob
import re
from datetime import datetime

# qx imports
import general.exceptions as ge
import general.core as gc


def map_to_qunex(file, sessionsfolder, sessions, overwrite):
    """
    Maps a file to QuNex NHP data structure.
    """

    # log prefix
    prefix = "        "

    # remove trailing /
    try:
        if sessionsfolder[-1] == "/":
            sessionsfolder = sessionsfolder[:-1]
    except:
        pass

    # find separator
    if "\\" in file:
        pathsep = "\\"
    else:
        pathsep = "/"

    # extract file info
    try:
        # split
        file_split = file.split(pathsep)

        if "dMRI" not in file_split:
            print(prefix + "---> skipping %s, not a dMRI file" % (file))
            return False
        else:
            session = file_split[-3]
            # skip session
            if sessions and session not in sessions:
                return False

            # store data
            data_file = file_split[-1]
    except:
        print("ERROR: Could not parse file:", file)
        return False

    # target folder and file
    tfile = os.path.join(sessionsfolder, session, "NHP", "dMRI", data_file)
    print(prefix + "---> Processing session %s, file %s" % (session, data_file))

    # overwrite?
    if os.path.exists(tfile):
        if overwrite == "yes" or overwrite is True:
            print(prefix + "---> file %s already exists: deleting ..." % (tfile))
            os.remove(tfile)
        else:
            print(prefix + "---> file %s already exists: skipping ..." % (tfile))
            return False

    return [session, tfile]


def import_nhp(
    sessionsfolder=None,
    inbox=None,
    sessions=None,
    action="link",
    overwrite="no",
    archive="move",
):
    """
    ``import_nhp [sessionsfolder=.] [inbox=<sessionsfolder>/inbox/NHP] [sessions=""] [action=link] [overwrite=no] [archive=move]``

    Maps NHP data to the QuNex Suite file structure.

    INPUTS
    ======

    --sessionsfolder    The sessions folder where all the sessions are to be
                        mapped to. It should be a folder within the
                        <study folder>. [.]

    --inbox             The location of the NHP dataset. It can be a folder
                        that contains the NHP datasets or compressed `.zip`
                        or `.tar.gz` packages that contain a single
                        session or a multi-session dataset. For instance the user
                        can specify "<path>/<nhp_file>.zip" or "<path>" to
                        a folder that contains multiple packages. The default
                        location where the command will look for a NHP dataset
                        is [<sessionsfolder>/inbox/NHP].

    --sessions          An optional parameter that specifies a comma or pipe
                        separated list of sessions from the inbox folder to be
                        processed. Regular expression patterns can be used.
                        If provided, only packets or folders within the inbox
                        that match the list of sessions will be processed. If
                        `inbox` is a file `sessions` will not be applied.
                        Note: the session will match if the string is found
                        within the package name or the session id. So
                        "NHP" with match any zip file that contains string
                        "NHP" or any session id that contains "NHP"!

    --action            How to map the files to QuNex structure. ["link"]
                        The following actions are supported:

                        - link (files will be mapped by creating hard links if
                          possible, otherwise they will be copied)
                        - copy (files will be copied)
                        - move (files will be moved)

    --overwrite         The parameter specifies what should be done with
                        data that already exists in the locations to which NHP
                        data would be mapped to. ["no"] Options are:

                        - no (do not overwrite the data and skip processing of
                          the session)
                        - yes (remove exising files in `nii` folder and redo the
                          mapping)

    --archive           What to do with the files after they were mapped.
                        ["move"] Options are:

                        - leave (leave the specified archive where it is)
                        - move (move the specified archive to
                          `<sessionsfolder>/archive/NHP`)
                        - copy (copy the specified archive to
                          `<sessionsfolder>/archive/NHP`)
                        - delete (delete the archive after processing if no
                          errors were identified)

                        Please note that there can be an
                        interaction with the `action` parameter. If files are
                        moved during action, they will be missing if `archive`
                        is set to "move" or "copy".

    OUTPUTS
    =======

    After running the `import_nhp` command the NHP dataset will be mapped
    to the QuNex folder structure and image files will be prepared for further
    processing along with required metadata.

    - dMRI images for each session will be stored in:

        ``<sessionsfolder>/<session>/dMRI``

    USE
    ===

    The `import_nhp` command first inspects the location of the NHP dataset
    (specified by the `inbox` parameter) for suitable data. When looking for
    suitable data QuNex looks for dMRI subfolder inside each of the <session>
    folders (whether in the `inbox` folder or in archived data). Meaning that
    the data inside `inbox` folder or achives should be structured as:

        ``/<session>/<dMRI>/<image files>``

    EXAMPLE CALL
    ============

    ::

        qunex import_nhp sessionsfolder=myStudy/sessions inbox=myData/NHP overwrite=yes
    """

    print("Running import_nhp")
    print("==================")

    # check inputs
    if action not in ["link", "copy", "move"]:
        raise ge.CommandError(
            "import_nhp",
            "Invalid action specified",
            "%s is not a valid action!" % (action),
            "Please specify one of: leave, copy, link, move!",
        )

    if archive not in ["leave", "move", "copy", "delete"]:
        raise ge.CommandError(
            "import_nhp",
            "Invalid dataset archive option",
            "%s is not a valid option for dataset archive option!" % (archive),
            "Please specify one of: move, copy, delete!",
        )

    if sessionsfolder is None:
        sessionsfolder = os.path.abspath(".")

    if inbox is None:
        inbox = os.path.join(sessionsfolder, "inbox", "NHP")

    all_ok = True
    errors = ""

    # check for folders
    if not os.path.exists(os.path.join(sessionsfolder, "inbox", "NHP")):
        os.makedirs(os.path.join(sessionsfolder, "inbox", "NHP"))
        print("---> creating inbox NHP folder")

    if not os.path.exists(os.path.join(sessionsfolder, "archive", "NHP")):
        os.makedirs(os.path.join(sessionsfolder, "archive", "NHP"))
        print("---> creating archive NHP folder")

    # identification of files
    if sessions:
        sessions = [e.strip() for e in re.split(r" +|\| *|, *", sessions)]

    print("---> identifying files in %s" % (inbox))

    source_files = []

    # iterate through folders and find relevant files
    if os.path.exists(inbox):
        if os.path.isfile(inbox):
            source_files = [inbox]
        elif os.path.isdir(inbox):
            for path, _, files in os.walk(inbox):
                for file in files:
                    filepath = os.path.join(path, file)
                    if sessions:
                        for session in sessions:
                            if re.search(session, file):
                                source_files.append(filepath)
                    else:
                        source_files.append(filepath)
        else:
            raise ge.CommandFailed(
                "import_nhp",
                "Invalid inbox",
                "%s is neither a file or a folder!" % (inbox),
                "Please check your path!",
            )
    else:
        raise ge.CommandFailed(
            "import_nhp",
            "Inbox does not exist",
            "The specified inbox [%s] does not exist!" % (inbox),
            "Please check your path!",
        )

    if not source_files:
        raise ge.CommandFailed(
            "import_nhp",
            "No files found",
            "No files were found to be processed at the specified inbox [%s]!"
            % (inbox),
            "Please check your path!",
        )

    # mapping data to sessions" folders
    print("---> mapping files to QuNex NHP folders")
    report = {}
    for file in source_files:
        if file.endswith(".zip"):
            print("    ---> processing zip package [%s]" % (file))

            try:
                z = zipfile.ZipFile(file, "r")
                for sf in z.infolist():
                    if sf.filename[-1] != "/":
                        result = map_to_qunex(
                            sf.filename, sessionsfolder, sessions, overwrite
                        )
                        if result:
                            tfile = result[1]
                            fdata = z.read(sf)
                            fout = open(tfile, "wb")
                            fout.write(fdata)
                            fout.close()

                            # append mapped file
                            if not result[0] in report:
                                report[result[0]] = [tfile]
                            else:
                                report[result[0]].append(tfile)
                z.close()

                print("        ---> done!")
            except:
                print(
                    "           ERROR: Processing of zip package failed. Please check the package!"
                )
                errors += "\n    .. Processing of package %s failed!" % (file)
                all_ok = False
                raise

        elif ".tar" in file or ".tgz" in file:
            print("   ---> processing tar package [%s]" % (file))

            try:
                tar = tarfile.open(file)
                for member in tar.getmembers():
                    if member.isfile():
                        result = map_to_qunex(
                            member.name, sessionsfolder, sessions, overwrite
                        )
                        if result:
                            tfile = result[1]
                            fobj = tar.extractfile(member)
                            fdata = fobj.read()
                            fobj.close()
                            fout = open(tfile, "wb")
                            fout.write(fdata)
                            fout.close()

                            # append mapped file
                            if not result[0] in report:
                                report[result[0]] = [tfile]
                            else:
                                report[result[0]].append(tfile)
                tar.close()

                print("        ---> done!")
            except:
                print(
                    "           ERROR: Processing of tar package failed. Please check the package!"
                )
                errors += "\n    .. Processing of package %s failed!" % (file)
                all_ok = False

        else:
            result = map_to_qunex(file, sessionsfolder, sessions, overwrite)
            if result:
                tfile = result[1]
                status, msg = gc.moveLinkOrCopy(
                    file, tfile, action, r="", prefix="    .. "
                )
                all_ok = all_ok and status
                if not status:
                    errors += msg
                else:
                    # append mapped file
                    if not result[0] in report:
                        report[result[0]] = [tfile]
                    else:
                        report[result[0]].append(tfile)

    # ---> archiving the dataset
    if errors:
        print("   ---> The following errors were encountered when mapping the files:")
        print(errors)
    else:
        if os.path.isfile(inbox) or not os.path.samefile(
            inbox, os.path.join(sessionsfolder, "inbox", "NHP")
        ):
            try:
                if archive == "move":
                    print("---> moving dataset to archive")
                    shutil.move(inbox, os.path.join(sessionsfolder, "archive", "NHP"))
                elif archive == "copy":
                    print("---> copying dataset to archive")
                    shutil.copy2(inbox, os.path.join(sessionsfolder, "archive", "NHP"))
                elif archive == "delete":
                    print("---> deleting dataset")
                    if os.path.isfile(inbox):
                        os.remove(inbox)
                    else:
                        shutil.rmtree(inbox)
            except:
                print("---> %s failed!" % (archive))
        else:
            files = glob.glob(os.path.join(inbox, "*"))
            for file in files:
                try:
                    if archive == "move":
                        print("---> moving dataset to archive")
                        shutil.move(
                            file, os.path.join(sessionsfolder, "archive", "NHP")
                        )
                    elif archive == "copy":
                        print("---> copying dataset to archive")
                        shutil.copy2(
                            file, os.path.join(sessionsfolder, "archive", "NHP")
                        )
                    elif archive == "delete":
                        print("---> deleting dataset")
                        if os.path.isfile(file):
                            os.remove(file)
                        else:
                            shutil.rmtree(file)
                except:
                    print("---> %s of %s failed!" % (archive, file))

    if not all_ok:
        raise ge.CommandFailed(
            "import_nhp", "Some actions failed", "Please check report!"
        )

    # final report and session.txt creation
    if len(report) > 0:
        print("\nFinal report\n============\n")

        for s in report:
            # print session info
            print("Session %s: " % s)

            # basic data
            sfolder = os.path.join(sessionsfolder, s)
            sfile = os.path.join(sfolder, "session_nhp.txt")
            subjectid = s.split("_")[0]

            # create session.txt
            sout = gc.createSessionFile(
                "import_nhp", sfolder, s, subjectid, overwrite, prefix="    "
            )

            # create session_nhp.txt
            if os.path.exists(sfile):
                if overwrite == "yes" or overwrite is True:
                    os.remove(sfile)
                    print("    ---> removed existing session_nhp.txt file")
                else:
                    raise ge.CommandFailed(
                        "import_nhp",
                        "session_nhp.txt file already present!",
                        "A session_nhp.txt file alredy exists [%s]" % (sfile),
                        "Please check or set parameter 'overwrite' to 'yes' to rebuild it!",
                    )

            sout_nhp = open(sfile, "w")
            gc.print_qunex_header(file=sout_nhp)
            print("#", file=sout_nhp)
            print("session:", s, file=sout_nhp)
            print("subject:", subjectid, file=sout_nhp)
            print("raw_data:", inbox, file=sout_nhp)
            print("nhp:", sfolder, file=sout_nhp)
            print(file=sout_nhp)

            # file info
            i = 1
            for f in report[s]:
                # report
                print("    ---> mapped file %s" % f)

                # add to subject
                out = "%02d: %s" % (i, f)
                print(out, file=sout)
                print(out, file=sout_nhp)

                # increase index
                i = i + 1

            # for nicer output
            print("")

#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``import_utils.py``

Helpers for the ``import_dicom`` command: packet discovery and session id
extraction, selection of the packets to process, archiving of processed
packets, and parsing and rendering of the import log.
"""

# Copyright (c) Grega Repovs. All rights reserved.

import csv
import glob
import os
import re
import shutil

import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl
from qx_utilities.dicom.dicom_archive import _RE_TAR, _RE_ZIP
from qx_utilities.dicom.dicom_utils import _safe_rmtree, match_all


def _import_parse_logfile(logfile, _log=None):
    """Parse the ``logfile`` specification into a packet_name -> session map."""
    if logfile is None or logfile == "":
        return None

    log = dict([[f.strip() for f in e.split(":")] for e in logfile.split("|")])
    if not all(e in log for e in ["path", "subject_id", "packet_name"]):
        raise ge.CommandFailed(
            "import_dicom",
            "Missing information in logfile",
            "Please provide all information in the logfile specification! [%s]" % (logfile),
        )
    try:
        for key in [e for e in log if e in ["packet_name", "subject_id", "session_name"]]:
            log[key] = int(log[key]) - 1
    except Exception:
        raise ge.CommandFailed(
            "import_dicom",
            "Invalid logfile specification",
            "Please create a valid logfile specification! [%s]" % (logfile),
        )
    if not os.path.exists(log["path"]):
        raise ge.CommandFailed(
            "import_dicom",
            "Logfile does not exist",
            "The specified logfile does not exist:",
            log["path"],
            "Please check your paths!",
        )

    has_session = "session_name" in log
    gl.log_or_console(_log).step("Reading acquisition log [%s]." % (log["path"]))
    sessions_info = {}
    with open(log["path"]) as f:
        delimiter = "," if log["path"].split(".")[-1] == "csv" else "\t"
        reader = csv.reader(f, delimiter=delimiter, quoting=csv.QUOTE_NONE if delimiter == "\t" else csv.QUOTE_MINIMAL)
        for line in reader:
            try:
                subj = line[log["subject_id"]]
                sname = line[log["session_name"]] if has_session else None
                sessions_info[line[log["packet_name"]]] = {
                    "subjectid": subj,
                    "sessionname": sname,
                    "sessionid": "%s_%s" % (subj, sname) if has_session else subj,
                    "packetname": line[log["packet_name"]],
                }
            except Exception:
                pass
    return sessions_info


def _import_has_results(sessionsfolder, sessionid):
    sf = os.path.join(sessionsfolder, sessionid)
    return os.path.exists(os.path.join(sf, "dicom")) or os.path.exists(os.path.join(sf, "nii"))


def _import_extract_session(pname, getid, empty):
    """Extract subject/session from a packet name using the nameformat regex."""
    ms = getid.search(pname)
    if not (ms and ms.groupdict().get("subject_id")):
        return None
    subj = ms.group("subject_id")
    sname = ms.group("session_name") if ms.groupdict().get("session_name") else None
    session = dict(empty)
    session.update(
        {
            "subjectid": subj,
            "sessionname": sname,
            "sessionid": "%s_%s" % (subj, sname) if sname else subj,
            "packetname": pname,
        }
    )
    return session


def _import_discover(sessionsfolder, sessions_list, masterinbox, pattern, nameformat, sessions_info, _log=None):
    """Identify packets/session folders to process and bucket them for reporting."""
    log = gl.log_or_console(_log)

    packets = {"ok": [], "nolog": [], "bad": [], "exist": [], "skip": [], "invalid": []}
    empty = {"subjectid": None, "sessionname": None, "sessionid": None, "packetname": None}

    if masterinbox:
        # the "---> " each of these carried is the record's own prefix now
        report_set = [
            ("ok", "Found the following packets to process:"),
            ("nolog", "These packets do not match with the log and they won't be processed"),
            ("bad", "For these packets a packet name could not be identified and they won't be processed:"),
            ("invalid", "For these packets the packet name could not parsed and they won't be processed:"),
            ("exist", "The session folder for these packages already has results:"),
            ("skip", "These packages do not match list of sessions and will be skipped:"),
        ]
        if not os.path.exists(masterinbox):
            raise ge.CommandFailed("import_dicom", "Master inbox does not exist", f"A folder {masterinbox} does not exist.", "Please check your path!")
        if not os.path.isdir(masterinbox):
            raise ge.CommandFailed("import_dicom", "Master inbox is not a folder", f"{masterinbox} is not a folder.", "Please check your path!")

        log.step("Checking for packets in %s" % (os.path.abspath(masterinbox)))
        log.detail("using regular expression '%s'" % (pattern))
        log.detail("extracting subject id using regular expression '%s'" % (nameformat))
        try:
            getop = re.compile(pattern)
        except Exception:
            raise ge.CommandFailed("import_dicom", "Invalid pattern", "Coud not parse the provided regular expression pattern: '%s'" % (pattern), "Please check and correct it!")
        try:
            getid = re.compile(nameformat)
        except Exception:
            raise ge.CommandFailed("import_dicom", "Invalid nameformat", "Coud not parse the provided regular expression pattern: '%s'" % (nameformat), "Please check and correct it!")

        for afile in glob.glob(os.path.join(masterinbox, "*")):
            m = getop.search(os.path.basename(afile))
            if not m:
                continue
            if not ("packet_name" in m.groupdict() and m.group("packet_name")):
                packets["bad"].append((afile, dict(empty)))
                continue
            pname = m.group("packet_name")

            if sessions_info is not None:
                if pname not in sessions_info:
                    session = dict(empty)
                    session["packetname"] = pname
                    packets["nolog"].append((afile, session))
                    continue
                session = dict(sessions_info[pname])
            else:
                session = _import_extract_session(pname, getid, empty)
                if session is None:
                    session = dict(empty)
                    session["packetname"] = pname
                    packets["invalid"].append((afile, session))
                    continue

            if sessions_list and not any(match_all(e, session["sessionid"]) for e in sessions_list):
                packets["skip"].append((afile, session))
                continue
            if _import_has_results(sessionsfolder, session["sessionid"]):
                packets["exist"].append((afile, session))
                continue
            packets["ok"].append((afile, session))

    else:
        report_set = [
            ("ok", "Found the following folders to process:"),
            ("invalid", "For these folders the folder name could not parsed and they won't be processed:"),
            ("exist", "These folders have existing results:"),
        ]
        log.step("Checking for folders to process in '%s'" % (os.path.abspath(sessionsfolder)))
        getid = re.compile(nameformat)

        sfolders = []
        for sessionid in sessions_list or []:
            sfolders += glob.glob(os.path.join(sessionsfolder, sessionid))
        for sfolder in sorted(set(sfolders)):
            pname = os.path.basename(sfolder)
            session = _import_extract_session(pname, getid, empty)
            if session is None:
                session = dict(empty)
                session["packetname"] = pname
                packets["invalid"].append((sfolder, session))
                continue
            session["sessionid"] = pname  # folder name is authoritative in session mode
            archives = []
            for tarchive in ["*.zip", "*.tar", "*.tar.*", "*.tgz"]:
                archives += glob.glob(os.path.join(sfolder, "inbox", tarchive))
            session["archives"] = list(archives)

            if os.path.exists(os.path.join(sfolder, "dicom")) or os.path.exists(os.path.join(sfolder, "nii")):
                packets["exist"].append((sfolder, session))
                continue
            packets["ok"].append((sfolder, session))

    return packets, report_set


def _import_report_packets(packets, report_set, overwrite, _log=None):
    """Report the discovery findings for each packet bucket."""
    log = gl.log_or_console(_log)

    for tag, message in report_set:
        if not packets[tag]:
            continue
        with log.section(message):
            for afile, session in packets[tag]:
                base = os.path.basename(afile)
                if session["sessionname"]:
                    log.info("subject: %s, session: %s ... %s <= %s <- %s" % (session["subjectid"], session["sessionname"], session["sessionid"], session["packetname"], base))
                elif session["subjectid"]:
                    log.info("subject: %s ... %s <= %s <- %s" % (session["subjectid"], session["sessionid"], session["packetname"], base))
                elif session["sessionid"]:
                    log.info("%s <= %s <- %s" % (session["sessionid"], session["packetname"], base))
                elif session["packetname"]:
                    log.info("%s <= %s <- %s" % ("????", session["packetname"], base))
                else:
                    log.info("%s <= %s <- %s" % ("????", "????", base))
            if tag == "exist":
                if overwrite:
                    log.detail("Since overwrite is set the folders will be removed and replaced")
                else:
                    log.detail("To process them, remove or rename the existing subject folders or set `overwrite` to 'yes'")


def _import_select_to_process(packets, masterinbox, sessionsfolder, check, overwrite, test, _log=None):
    """Apply the check/test/overwrite rules and return the packets to process.

    Returns None when the command should stop without processing (test mode).
    Raises CommandFailed/CommandNull when nothing is found, per ``check``.
    """
    log = gl.log_or_console(_log)

    n_to_process = len(packets["ok"]) + (len(packets["exist"]) if overwrite else 0)

    if n_to_process and test:
        log.step("To process them, remove the --test option!")
        return None

    if not n_to_process:
        where = ("master inbox [%s]" % os.path.abspath(masterinbox)) if masterinbox else ("session folder [%s]" % os.path.abspath(sessionsfolder))
        what = "packets" if masterinbox else "sessions"
        if check.lower() == "any":
            raise ge.CommandFailed("import_dicom", "No %s found to process" % what, "No %s were found to be processed in the %s!" % (what, where), "Please check your data!")
        raise ge.CommandNull("import_dicom", "No %s found to process" % what, "No %s were found to be processed in the %s!" % (what, where))

    if overwrite and packets["exist"]:
        log.step("Cleaning existing data in folders:")
        for afile, session in packets["exist"]:
            sfolder = os.path.join(sessionsfolder, session["sessionid"])
            log.detail(sfolder)
            for sub in ("nii", "dicom"):
                rmfolder = os.path.join(sfolder, sub)
                if os.path.exists(rmfolder):
                    _safe_rmtree(rmfolder, _log=log)
        packets["ok"] += packets["exist"]

    return packets["ok"]


def _resolve_packet_sources(afile, session, masterinbox, sfolder):
    """Return the source path(s) the engine should read for a packet."""
    if masterinbox:
        return [afile]
    if session.get("archives"):
        return list(session["archives"])
    return [os.path.join(sfolder, "inbox")]


def _archive_packet(sources, afolder, archive, masterinbox, verbose, _log=None):
    """Move/copy/delete processed packages per the ``archive`` setting."""
    log = gl.log_or_console(_log)

    notes = []
    if archive == "leave":
        return notes

    for p in sources:
        is_archive = bool(_RE_ZIP.search(p) or _RE_TAR.search(p))
        if not (masterinbox or is_archive):
            continue
        ptype = "folder" if os.path.isdir(p) else "archive"
        target = os.path.join(afolder, os.path.basename(p))

        if archive == "move":
            if os.path.exists(target):
                notes.append("WARNING: %s already exists in archive and it was not moved!" % os.path.basename(p))
                log.warning("%s already exists in archive and it will not be moved!" % os.path.basename(p))
            else:
                log.detail("moving %s to archive" % os.path.basename(p))
                shutil.move(p, target)
        elif archive == "copy":
            if os.path.exists(target):
                notes.append("WARNING: %s already exists in archive and it was not copied!" % os.path.basename(p))
                log.warning("%s already exists in archive and it will not be copied!" % os.path.basename(p))
            else:
                log.detail("copying %s to archive" % os.path.basename(p))
                if ptype == "folder":
                    shutil.copytree(p, target)
                else:
                    shutil.copy2(p, afolder)
        elif archive == "delete":
            log.detail("deleting packet [%s]" % os.path.basename(p))
            if ptype == "folder":
                _safe_rmtree(p, _log=log)
            else:
                os.remove(p)
    return notes


def _import_normalize_args(sessionsfolder, sessions, masterinbox, pattern, nameformat, tool, add_image_type, verbose, overwrite):
    """Validate and normalise import_dicom arguments; returns a normalised tuple."""
    if tool not in ["auto", "dcm2niix", "dcm2nii", "dicm2nii"]:
        raise ge.CommandError("import_dicom", "Incorrect tool specified", "The tool specified for conversion to nifti (%s) is not valid!" % (tool), "Please use one of dcm2niix, dcm2nii, dicm2nii or auto!")

    verbose_b = verbose.lower() == "yes" if isinstance(verbose, str) else bool(verbose)
    overwrite_b = overwrite if isinstance(overwrite, bool) else overwrite.lower() == "yes"

    if sessionsfolder is None:
        sessionsfolder = "."
    if masterinbox is None:
        masterinbox = os.path.join(sessionsfolder, "inbox", "MR")
    if isinstance(masterinbox, str) and masterinbox.lower() == "none":
        masterinbox = None
        if not sessions:
            raise ge.CommandError("import_dicom", "Sessions parameter not specified", "If `masterinbox` is set to 'none' the `sessions` has to list sessions to process!", "Please check your command!")

    if pattern is None:
        pattern = r"(?P<packet_name>.*?)(?:\.zip$|\.tar$|\.tgz$|\.tar\..*$|$)"
    if nameformat is None:
        nameformat = r"(?P<subject_id>.*)"

    try:
        add_image_type = 0 if add_image_type in (None, "") else int(add_image_type)
    except Exception:
        raise ge.CommandError("import_dicom", "Misspecified add_image_type", "The add_image_type argument value could not be converted to integer! [%s]" % (add_image_type), "Please check command instructions!")

    sessions_list = re.split(r", *", sessions) if sessions else None
    return sessionsfolder, masterinbox, pattern, nameformat, add_image_type, sessions_list, verbose_b, overwrite_b


def _import_final_report(report, _log=None):
    """Record the final success/failure report and raise if any packet failed."""
    log = gl.log_or_console(_log)

    log.blank()
    log.info("Final report\n============")
    if report["ok"]:
        log.blank()
        log.step("Successfully processed:")
        for afile, session, notes in report["ok"]:
            log.detail("%s [%s]" % (session["sessionid"], afile))
            for note in notes:
                log.detail(note, depth=1)
    if report["failed"]:
        log.blank()
        log.step("Failed to process:")
        for afile, session, notes in report["failed"]:
            log.error("%s [%s]" % (session["sessionid"], afile))
            for note in notes:
                log.detail(note, depth=1)
        raise ge.CommandFailed("import_dicom", "Some packages failed to process", "Please check report!")

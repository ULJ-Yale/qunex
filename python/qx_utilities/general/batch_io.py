#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``batch_io.py``

Reads batch and list files and selects sessions from them. This is the one
implementation of that job in the suite — `general/core.py` wraps it as
`resolve_sessions()`, and `bin/qunex_container` gets a spliced copy of this
file.

Because of that splice it imports **nothing from QuNex**: the container runs on
a login node, in the host python, with no QuNex on the path. It therefore also
raises its own `BatchError` rather than `general.exceptions`; `resolve_sessions`
translates that into the QuNex error types. `tests/test_batch_io.py` holds the
module to the stdlib.
"""

import fnmatch
import glob
import os
import re
from collections import UserList
from copy import deepcopy


class BatchError(ValueError):
    """An unreadable or absent batch file, or a malformed filter."""


# ------------------------------------------------------------------------------
#                                                              SessionList class


class SessionList(UserList):
    """
    ``SessionList``

    A list subclass for session and subject data.
    """

    def __init__(self, initialdata=None):
        if initialdata is None:
            initialdata = []
        super().__init__(initialdata)

    def copy(self):
        """
        ``copy()``

        Returns a deep copy of the SessionList.
        """
        return SessionList(deepcopy(self.data))

    def filter_by_key(self, key, value):
        """
        ``filter_by_key(key, value)``

        Filter the SessionList by key and value.
        - If value is a list, matches any of the values.
        - Values may be glob patterns (*, ?, [a-z]).
        """

        def matches(item_value, pattern):
            # exact match for non-strings
            if not isinstance(item_value, str):
                return item_value == pattern

            # glob match for strings
            return item_value == pattern or fnmatch.fnmatchcase(item_value, pattern)

        # normalize value to a list
        if isinstance(value, str):
            values = [e.strip() for e in value.split(",")]
        else:
            values = list(value)

        return SessionList(
            [
                deepcopy(e)
                for e in self.data
                if isinstance(e, dict)
                and key in e
                and any(matches(e[key], v) for v in values)
            ]
        )

    def filter_by_string(self, filter):
        """
        Filter the SessionList by a filter string.

        - Use '|' between <key>:<value> pairs for OR
        Example: "group:pat*|task:rest"

        - Use '&' between <key>:<value> pairs for AND
        Example: "group:pat*&task:r?st"

        Values are treated as globs (fnmatch):
        * matches any chars, ? matches one char, [abc] matches one char in set.

        Only one operator type may be used. An empty filter selects everything.
        """
        if filter is None or filter.strip() == "":
            return self.copy()

        fstr = filter.strip()

        has_or = "|" in fstr
        has_and = "&" in fstr
        if has_or and has_and:
            raise BatchError(
                "The provided filter parameter is invalid: '%s'. Use either '|' "
                "(OR) or '&' (AND), but not both." % (filter)
            )

        op = "|" if has_or else ("&" if has_and else None)
        parts = [fstr] if op is None else fstr.split(op)

        filters = [[p.strip() for p in e.split(":", 1)] for e in parts]

        if any(len(e) != 2 or e[0] == "" or e[1] == "" for e in filters):
            raise BatchError(
                "The provided filter parameter is invalid: '%s'. It should be a "
                "'%s' separated string of <key>:<value> pairs."
                % (filter, op if op else "(single)")
            )

        def matches(item, key, pattern):
            if not (isinstance(item, dict) and key in item):
                return False

            v = item[key]

            # exact match for non-strings
            if not isinstance(v, str):
                return v == pattern

            # for strings: exact or glob match
            # (fnmatchcase is case-sensitive and does not depend on OS)
            return v == pattern or fnmatch.fnmatchcase(v, pattern)

        filtered_data = []
        for s in self.data:
            if op == "&":
                ok = all(matches(s, key, pattern) for key, pattern in filters)
            else:
                ok = any(matches(s, key, pattern) for key, pattern in filters)

            if ok:
                filtered_data.append(deepcopy(s))

        return SessionList(filtered_data)

    def get_list_by_key(self, key, sep=","):
        """
        ``get_list_by_key(key, sep=",")``

        Compile a list of unique values for the specified key. By default it returns
        a comma separated string. If sep is None or empty string, it returns a list.
        """
        if sep is None or sep == "":
            return list(
                dict.fromkeys(str(item[key]) for item in self.data if key in item)
            )
        else:
            return sep.join(
                list(dict.fromkeys(str(item[key]) for item in self.data if key in item))
            )

    def group_by_key(self, key):
        """
        ``group_by_key(key)``

        Groups the SessionList by the specified key. Returns a list of SessionLists.
        """
        groups = {}

        for item in self.data:
            if isinstance(item, dict) and key in item:
                group_value = item[key]
                groups.setdefault(group_value, []).append(deepcopy(item))

        return [SessionList(items) for items in groups.values()]

    def dont_have_key(self, key):
        """
        ``dont_have_key(key)``

        Reports the items that do not have the specified key or have it as None or empty.
        Returns list of such items.
        """
        return SessionList([item for item in self.data if not _has_value(item, key)])

    def have_key(self, key):
        """
        ``have_key(key)``

        Returns all the items that have the specified key with a value that is not None or empty.
        Returns list of such items.
        """
        return SessionList([item for item in self.data if _has_value(item, key)])


def _has_value(item, key):
    """Does item carry key with a non-empty value?"""
    return (
        isinstance(item, dict)
        and key in item
        and item[key] is not None
        and item[key].strip() != ""
    )


# ------------------------------------------------------------------------------
#                           Read session data from batch.txt or session.txt file


def _read_file(filename):
    """Returns the content of filename, raising BatchError if it can not be read."""
    try:
        with open(filename, "r") as f:
            return f.read()
    except OSError as e:
        raise BatchError("Could not read the batch file [%s]: %s" % (filename, e))


def read_batch(filename, verbose=False):
    """
    ``read_batch(filename, verbose=False)``

    Reads a `batch.txt` or `session.txt` file and returns a tuple of the list of
    session records and the parameters specified in the header. Raises
    BatchError if the file can not be read or parsed.
    """

    s = _read_file(filename)
    s = s.replace("\r", "\n")
    s = s.replace("\n\n", "\n")
    s = re.sub("^#.*?\n", "", s)

    s = s.split("\n---")
    s = [e for e in s if len(e) > 10]

    nsearch = re.compile(r"(.*?)\((.*)\)")
    csearch = re.compile(r"c([0-9]+)$")

    slist = []
    header = {}

    c = 0
    raw = ""
    # first "session" is the parameters block
    first = True
    try:
        for sub in s:
            sub = sub.split("\n")
            sub = [e.strip() for e in sub]
            sub = [e.split("#")[0].strip() for e in sub]
            sub = [e for e in sub if len(e) > 0]

            dic = {}
            for line in sub:
                c += 1
                raw = line

                # --- read preferences / settings
                if line.startswith("--"):
                    pkey, pvalue = [e.strip() for e in line.split(":", 1)]
                    if first:
                        header[pkey[2:]] = pvalue
                    else:
                        dic[pkey] = pvalue
                    continue

                elif line.startswith("_") or line.startswith("-"):
                    pkey, pvalue = [e.strip() for e in line.split(":", 1)]
                    if first:
                        header[pkey[1:]] = pvalue
                    else:
                        dic[pkey] = pvalue
                    continue

                # --- split line
                line = line.split(":")
                line = [e.strip() for e in line]
                if len(line) < 2:
                    continue

                # --- read ima data
                if line[0].isdigit():
                    image = {}
                    image["ima"] = line[0]
                    remove = []
                    for e in line:
                        m = nsearch.match(e)
                        if m:
                            image[m.group(1).strip()] = m.group(2).strip()
                            remove.append(e)

                    for e in remove:
                        line.remove(e)

                    ni = len(line)
                    if ni > 1:
                        image["name"] = line[1]
                    if ni > 2 and ("bold" in image["name"]) or ("DWI" in image["name"]):
                        image["task"] = line[2]
                    if ni > 3:
                        image["ext"] = line[3]

                    dic[line[0]] = image

                # --- read conc data
                elif csearch.match(line[0]):
                    conc = {}
                    conc["cnum"] = line[0]
                    for e in line:
                        m = nsearch.match(e)
                        if m:
                            conc[m.group(1).strip()] = m.group(2).strip()
                            line.remove(e)

                    ni = len(line)
                    if ni < 3:
                        raise AssertionError(
                            "Not enough values in conc definition line!"
                        )

                    conc["label"] = line[1]
                    conc["conc"] = line[2]
                    conc["fidl"] = line[3]
                    dic[line[0]] = conc

                # --- read rest of the data
                else:
                    dic[line[0]] = ":".join(line[1:])

            if len(dic) > 0:
                if ("id" not in dic) and ("session" not in dic):
                    if verbose:
                        print(
                            "WARNING: There is a record missing an id field and is being omitted from processing."
                        )
                else:
                    if "id" in dic and "session" not in dic:
                        dic["session"] = dic["id"]
                    elif "session" in dic and "id" not in dic:
                        dic["id"] = dic["session"]
                    slist.append(dic)

                    # check paths
                    if verbose:
                        for field in ["dicom", "raw_data", "data", "hpc"]:
                            if field in dic and not os.path.exists(dic[field]):
                                print(
                                    "WARNING: session %s - folder %s: %s specified in %s does not exist! Check your paths!"
                                    % (
                                        dic["id"],
                                        field,
                                        dic[field],
                                        os.path.basename(filename),
                                    )
                                )

            # done with the parameters block
            first = False

    except Exception as e:
        raise BatchError(
            "There was an error with the batch file [%s] in line %d:\n---> %s\n"
            "Error raised: %s" % (filename, c, raw, e)
        )

    return slist, header


# ------------------------------------------------------------------------------
#                                              Read session data from .list file


def read_list(filename, verbose=False):
    """
    ``read_list(filename, verbose=False)``

    Reads a `*.list` file and returns a list of sessions, each with the provided
    list of files. Raises BatchError if the file can not be read.
    """

    slist = []
    session = {}

    for line in _read_file(filename).split("\n"):
        if line.strip()[:1] == "#":
            continue

        line = [e.strip() for e in line.split(":")]

        if len(line) == 2:
            if line[0] == "session id":
                if session != {}:
                    slist.append(session.copy())
                session = {}
                session["id"] = line[1]

            else:
                if line[0] in session:
                    session[line[0]].append(line[1])
                else:
                    session[line[0]] = [line[1]]
    slist.append(session)

    return slist


# ------------------------------------------------------------------------------
#                                                   Select sessions from a source


def _split_sessions(sessions):
    """Splits a comma, space or pipe separated session specification into a list."""
    if sessions is None:
        return []
    return [e.strip() for e in re.split(r" +|,|\|", sessions.strip()) if e.strip()]


def resolve(
    batchfile=None, sessions=None, filter=None, sessionsfolder=None, verbose=False
):
    """
    ``resolve(batchfile=None, sessions=None, filter=None, sessionsfolder=None, verbose=False)``

    Reads the source of the sessions and selects within it. Returns a tuple of
    the SessionList of the selected sessions and the parameters specified in the
    batch file header.

    `batchfile` is read as a `*.list` file if it has that extension and as a
    batch file otherwise. A `*.list` given through `sessions` is the source of
    the sessions when there is no batch file and selects within one when there
    is. With no batch file at all, `sessions` names the sessions themselves.

    Raises BatchError on a file that can not be read or a malformed filter.
    """

    records = []
    header = {}

    if batchfile and batchfile.strip():
        batchfile = batchfile.strip()
        if re.match(r".*\.list$", batchfile):
            records = read_list(batchfile, verbose=verbose)
        else:
            records, header = read_batch(batchfile, verbose=verbose)

    # a `*.list` file is a session specification, so it can also arrive through
    # sessions: it is the source of the sessions when there is no batch file,
    # and selects within one when there is
    if sessions and re.match(r"^\s*\S+\.list\s*$", sessions):
        list_records = read_list(sessions.strip(), verbose=verbose)
        if records:
            sessions = ",".join([e["id"] for e in list_records if "id" in e])
        else:
            records, sessions = list_records, None

    slist = select_sessions(
        records, sessions=sessions, filter=filter, sessionsfolder=sessionsfolder
    )

    return slist, header


def select_sessions(records, sessions=None, filter=None, sessionsfolder=None):
    """
    ``select_sessions(records, sessions=None, filter=None, sessionsfolder=None)``

    Returns the SessionList of records the session specification and the filter
    select.

    `sessions` is a comma, space or pipe separated list of session ids or globs
    (`*`, `?`, `[abc]`), `filter` a '&' or '|' separated string of <key>:<value>
    pairs. An empty `sessions` or `filter` selects everything.

    When `records` is empty, `sessions` names the sessions themselves: they are
    matched against the folders in `sessionsfolder` when one is given, and taken
    as plain ids when it is not.
    """
    ids = _split_sessions(sessions)

    if records:
        slist = SessionList(records)
        if ids:
            slist = slist.filter_by_key("id", ids)

    elif sessionsfolder:
        folders = []
        for pattern in ids:
            folders += glob.glob(os.path.join(sessionsfolder, pattern))
        slist = SessionList([{"id": os.path.basename(e)} for e in sorted(folders)])

    else:
        slist = SessionList([{"id": e} for e in ids])

    return slist.filter_by_string(filter)

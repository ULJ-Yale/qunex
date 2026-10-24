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

Three more jobs live here because the launcher does them on the host as well:
making absolute the paths a command line names before the run knows its study
(`anchor_command_line`), leaving out what a run unsets from a batch file
(`without_unset`, which `general/commands_support.py` re-exports), and reading
what the shell code of a command line exports (`bash_post_exports`).

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
import shlex
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

    The folders a record names (`hcp`, `raw_data`, ...) are returned as they
    are written, which is relative to the session's folder: this module does
    not know where that is. `general/core.resolve_sessions` resolves them, and
    with `verbose` warns about the ones that do not exist; here `verbose` only
    warns about a record without an id.
    """

    s = _read_file(filename)
    s = s.replace("\r", "\n")
    s = s.replace("\n\n", "\n")
    s = re.sub("^#.*?\n", "", s)

    # the first block is the header, whatever its length: dropping a short one
    # made the first session the header, and its own overrides the study's. An
    # empty header leaves the text starting with the separator itself
    s = re.split(r"(?:^|\n)---", s)
    s = s[:1] + [e for e in s[1:] if e.strip()]

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
#                                                     Paths a command line names

# the commands whose `--studyfolder` names the study they create rather than
# one they work in: everything they are given is taken from the current folder.
# With their deprecated names, which the container launcher is given as typed
CREATES_STUDY = (
    "create_study",
    "manage_study",
    "copy_study",
    "createStudy",
    "manageStudy",
)

# a `--sessions` value that names a file of sessions rather than the sessions
LIST_FILE = re.compile(r"^\s*\S+\.list\s*$")

# what a command line names that is read before the study is known, and is
# taken from the study the command line names
READ_EARLY = ("batchfile", "recipe_file")


def run_path(path, base=None):
    """
    ``run_path(path, base=None)``

    A path a run is given, made absolute: environment variables and `~` are
    expanded, and a relative path is taken from `base` -- the study the run
    works in -- or from the current folder when there is none. An empty value,
    and anything that is not a string (a flag given without a value), is
    returned as it is.
    """
    if not isinstance(path, str) or not path.strip():
        return path

    path = os.path.expanduser(os.path.expandvars(path.strip()))
    return os.path.normpath(os.path.join(base or os.getcwd(), path))


def anchor_command_line(args, command=None, study=None):
    """
    ``anchor_command_line(args, command=None, study=None)``

    What a command line names that is read before the run knows every study it
    may name -- a batch file header and a recipe can name one too -- made
    absolute:

    - `studyfolder` from the current folder, and so `logstatus`, a file the
      caller reads;
    - `sessionsfolder` from the study the command line names. Named without
      one it is left as it is typed: `process.merge_options` settles it once
      the batch file header is read, which can name the study it is in;
    - `batchfile`, a `.list` file given to `sessions` and `recipe_file` from
      the study the command line names, else from the folder a sessions folder
      it names is in, else from `study` -- a study known from elsewhere, the
      one `run_recipe`'s recipe names -- else from the current folder.

    A command that creates its study (`CREATES_STUDY`) takes all of them from
    the current folder.

    Returns:
        a copy of `args` with those values absolute, and the study the files
        were taken from (None when that was the current folder).
    """
    args = dict(args)
    creates = command in CREATES_STUDY

    if args.get("studyfolder") or args.get("sessionsfolder") or creates:
        study = None

    if isinstance(args.get("studyfolder"), str) and args["studyfolder"].strip():
        args["studyfolder"] = run_path(args["studyfolder"])
        if not creates:
            study = args["studyfolder"]
            if isinstance(args.get("sessionsfolder"), str):
                args["sessionsfolder"] = run_path(args["sessionsfolder"], study)

    if study is None and not creates and isinstance(args.get("sessionsfolder"), str):
        if args["sessionsfolder"].strip():
            # left relative, for a study the header may name, but what it says
            args["sessionsfolder"] = os.path.expanduser(
                os.path.expandvars(args["sessionsfolder"].strip())
            )
            study = os.path.dirname(run_path(args["sessionsfolder"]))

    for key in READ_EARLY:
        if key in args:
            args[key] = run_path(args[key], study)

    sessions = args.get("sessions")
    if isinstance(sessions, str) and LIST_FILE.match(sessions):
        args["sessions"] = run_path(sessions, study)

    if "logstatus" in args:
        args["logstatus"] = run_path(args["logstatus"])

    return args, study


# ------------------------------------------------------------------------------
#                                                  Select sessions from a source


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
    if sessions and LIST_FILE.match(sessions):
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


# ------------------------------------------------------------------------------
#                                            Not taking what the batch file says
#
# A batch file states parameters for every command of a study, and since the
# header reaches every command class, a name it states can land somewhere its
# author did not have in mind -- `targetfile` is declared by four commands that
# write four different files. These say "not from there", one per batch tier,
# and they are run level parameters, so they can be written on the command line
# and at every level of a recipe.
UNSET_BATCH_HEADER = "unset_batch_header_parameters"
UNSET_BATCH_SESSION = "unset_batch_session_parameters"


def unset_patterns(stated):
    """
    ``unset_patterns(stated)``

    The patterns an unset states: a name, a comma separated list of them, or an
    array -- the forms a recipe's `unset_parameters` already takes, so there is
    one convention rather than two. An empty list states nothing, which is how
    a step opts back in under a run wide `all`. So does a flag given without a
    value (`--unset_batch_header_parameters` alone): it names nothing.
    """
    if stated is None or isinstance(stated, bool):
        return []
    if isinstance(stated, str):
        stated = stated.split(",")
    return [str(pattern).strip() for pattern in stated if str(pattern).strip()]


def is_unset(name, patterns):
    """
    ``is_unset(name, patterns)``

    Whether any of `patterns` unsets `name`. A pattern is a parameter name, a
    glob over parameter names (`hcp_*`), `*`, or `all` -- the last being the
    spelling QuNex uses for "every one of them" elsewhere, and free here since
    no command declares a parameter of that name.

    `fnmatchcase` rather than `fnmatch`, as in `SessionList`: the answer must
    not depend on the operating system. `_` is not a metacharacter, so `hcp_*`
    matches what it looks like it matches.
    """
    return any(
        pattern in ("all", "*") or name == pattern or fnmatch.fnmatchcase(name, pattern)
        for pattern in patterns
    )


def without_unset(options, patterns):
    """
    ``without_unset(options, patterns)``

    The options left once the patterns have taken out what they name, and the
    names they took. The names are returned because a pattern is not a list: a
    run has to be able to say what `hcp_*` removed on the day it ran, rather
    than leaving a reader to work it out from the release it ran on.
    """
    if not options or not patterns:
        return options, []

    unset = sorted(key for key in options if is_unset(key, patterns))

    return {key: value for key, value in options.items() if key not in unset}, unset


# ------------------------------------------------------------------------------
#                                     What the shell code of a command line sets
#
# A recipe's `{{$NAME}}` label can be set by shell code run before the command
# -- qunex_container's --bash_post, a scheduled run's --bash -- rather than by
# the environment the run starts in. Where a run logs is decided before that
# code runs, so the variables it exports are read from it here, for the
# launcher on the host and for `gmri` alike.

# what bash takes as it is written -- a quoted or escaped `$`, backtick or `~`
# -- marked by `_shell_text` with characters no command line holds, and read
# back by `_shell_value`
_LITERAL = {"$": "\x00", "`": "\x01", "~": "\x02"}
_WRITTEN = {marker: char for char, marker in _LITERAL.items()}


def _shell_text(text):
    """
    ``_shell_text(text)``

    The shell code `text` as `_shell_statements` reads it: without comments
    -- from a `#` that begins a word, outside quotes, to the end of its line;
    a `#` inside a word, or quoted, is no comment -- and with each `$`,
    backtick and `~` that bash takes as it is written, quoted or escaped,
    marked (`_LITERAL`).

    Raises:
        ValueError: when `text` holds a character used as a mark.
    """
    if any(marker in text for marker in _WRITTEN):
        raise ValueError("the shell code holds a character used as a mark")

    kept, quote, escaped, comment, word_start = [], None, False, False, True
    for char in text:
        if comment:
            if char != "\n":
                continue
            comment = False
        elif escaped:
            escaped = False
            if char in "$`" or (char == "~" and quote is None):
                # in place of the backslash, which bash takes away
                kept[-1], word_start = _LITERAL[char], False
                continue
        elif quote == "'":
            if char == quote:
                quote = None
            else:
                char = _LITERAL.get(char, char)
        elif quote == '"':
            if char == quote:
                quote = None
            elif char == "\\":
                escaped = True
            elif char == "~":
                char = _LITERAL[char]
        elif char == "\\":
            escaped = True
        elif char in "'\"":
            quote = char
        elif char == "#" and word_start:
            comment = True
            continue
        kept.append(char)
        word_start = not (quote or escaped) and char in " \t\r\n;&|()<>"
    return "".join(kept)


def _shell_statements(text):
    """
    ``_shell_statements(text)``

    The simple statements of the shell code `text` that run in the shell
    itself, each as the list of its words, quotes taken away (`_shell_text`),
    and whether it surely runs. Not one in a pipeline, nor one in the
    background -- a `&` puts there the whole list of statements joined by
    `&&` and `||` it ends. Each command is taken to succeed: a statement after
    `&&` runs, and one after `||`, which runs only when what comes before it
    fails, may run. A line break ends a statement as `;` does, except right
    after `&&`, `||` or `|`.

    Raises:
        ValueError: on a quote that is not closed.
    """
    lexer = shlex.shlex(_shell_text(text), posix=True, punctuation_chars=";&|\n")
    lexer.commenters = ""
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True

    # the lists of statements joined by `&&`, `||` and `|`, each statement
    # with what joins it to the next
    lists, current, words = [], [], []
    for token in list(lexer) + [";"]:
        if not token or not set(token) <= set(";&|\n"):
            words.append(token)
            continue
        joins = next((mark for mark in ("||", "&&", "|", "&") if mark in token), ";")
        if not words and set(token) == {"\n"} and current:
            if current[-1][1] in ("&&", "||", "|"):
                continue
        current.append((words, joins))
        words = []
        if joins in (";", "&"):
            lists.append(current)
            current = []

    statements = []
    for current in lists:
        if current[-1][1] == "&":
            continue
        joined = ";"
        for words, joins in current:
            if words and "|" not in (joined, joins):
                statements.append((words, joined != "||"))
            joined = joins
    return statements


# a word of shell code that sets a variable; in its value, a reference to a
# variable, or a mark of what is taken as it is written
_SHELL_ASSIGNMENT = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)(\+?)=(.*)", re.S)
_SHELL_REFERENCE = re.compile(
    r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))|([\x00-\x02])"
)


def _shell_value(value, variables):
    """
    ``_shell_value(value, variables)``

    `value`, the right of an assignment, as bash expands it, when the host can
    tell: written out, or referring with `$NAME` or `${NAME}` to one of
    `variables`; a `~` that begins it is `$HOME`. None for a value made any
    other way -- by a command (`$(...)`, a backtick) or another expansion
    (`${NAME:-...}`, `$1`, `~user`) -- and for one that refers to a variable
    `variables` does not hold.
    """
    if value == "~" or value.startswith("~/"):
        value = "${HOME}" + value[1:]

    found = _SHELL_REFERENCE.findall(value)
    referred = [braced or bare for braced, bare, _ in found if braced or bare]
    other = _SHELL_REFERENCE.sub("", value)
    if (
        "$" in other
        or "`" in other
        or value.startswith("~")
        or ":~" in value
        or any(name not in variables for name in referred)
    ):
        return None

    def expanded(match):
        braced, bare, mark = match.groups()
        return _WRITTEN[mark] if mark else variables[braced or bare]

    return _SHELL_REFERENCE.sub(expanded, value)


def _builtin_operands(words):
    """
    ``_builtin_operands(words)``

    The options and the operands of the builtin that `words` call, as bash
    tells them apart: the options come first, until `--` or the first word
    that is not one.
    """
    operands, flags = words[1:], ""
    while operands and operands[0].startswith("-") and operands[0] != "-":
        option = operands.pop(0)
        if option == "--":
            break
        flags += option[1:]
    return flags, operands


def bash_post_exports(bash_post, environ=None):
    """
    ``bash_post_exports(bash_post, environ=None)``

    What the `export` statements of shell code run before a command set for
    it -- `qunex_container`'s --bash_post inside the container, a scheduled
    run's --bash on the node -- as far as can be told before that code runs
    (`_shell_value`), the variables of `environ` -- the environment unless
    another is given -- and those the code set before taken as known. Only a statement that
    runs in the shell that runs the command counts (`_shell_statements`), and
    whatever a sourced file sets is not seen. `unset` and `export -n` take an
    export back, a later assignment changes what is exported, and an array is
    never exported.
    """
    if not isinstance(bash_post, str) or not bash_post.strip():
        return {}

    try:
        statements = _shell_statements(bash_post)
    except ValueError:
        return {}

    known = dict(os.environ if environ is None else environ)
    assigned, arrays, exports = set(), set(), {}

    def forget(name):
        known.pop(name, None)
        exports.pop(name, None)
        assigned.discard(name)

    for words, surely in statements:
        assignments = [m for m in map(_SHELL_ASSIGNMENT.match, words) if m]
        flags, operands = _builtin_operands(words)
        array = [m.group(1) for m in assignments if m.group(3).startswith("(")]
        if array or not surely:
            # the words of an array are not told apart from the statement's,
            # and a statement that may not run sets what it sets or not
            touched = [m.group(1) for m in assignments]
            if words[0] in ("export", "unset"):
                touched += operands
            for name in touched:
                forget(name)
            arrays.update(array)
            continue

        if words[0] == "unset":
            # `-f` unsets a function, not a variable
            if "f" not in flags:
                for name in operands:
                    forget(name)
                    arrays.discard(name)
            continue
        if words[0] == "export" and "f" not in flags:
            mode = "unexport" if "n" in flags else "export"
        elif len(assignments) == len(words):
            # variables of the shell, for what refers to them later
            mode, operands = "assign", words
        else:
            continue

        # an export's words are expanded before it runs, assignments one by one
        before = dict(known)
        for word in operands:
            match = _SHELL_ASSIGNMENT.match(word)
            if match is None:
                if mode == "export" and word in assigned:
                    exports[word] = known[word]
                elif mode == "unexport":
                    exports.pop(word, None)
                continue

            name, append, value = match.groups()
            variables = known if mode == "assign" else before
            if append or name in arrays:
                value = None
            else:
                value = _shell_value(value, variables)
            if value is None:
                # set, to a value the host can not tell
                forget(name)
                continue

            known[name] = value
            assigned.add(name)
            if mode == "unexport":
                exports.pop(name, None)
            elif mode == "export" or name in exports:
                exports[name] = value

    return exports

#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Does this file still render the same runlog?

A development tool, not a test -- the name does not match ``test_*``, so pytest
does not collect it. It answers the one question the ``raw()`` retirement (N9)
keeps asking: a call site was rewritten from ``log.raw("\\n---> ERROR: ...")``
to ``log.error("...")``; does the report still read the same?

It cannot answer that by running the commands -- they need a study and an HCP
installation -- so it reads instead. Both revisions of a file are parsed with
``ast``, walked in source order, and every log call is turned into a record of

- the **rendered template**: what :func:`general.log.report._render` -- imported,
  never reimplemented, so this cannot drift from the renderer -- spells for that
  call's depth and severity, with every interpolated slot (a ``%s``/``%d``
  conversion, an f-string ``{...}``, an opaque argument) collapsed to ``‹›``; and
- the **argument expressions**, ``ast.unparse``d, so a rewrite that drops, adds
  or reorders a slot is caught rather than hidden. Unparsing is also what makes
  the comparison survive the f-string restyle: ``"%s" % path`` and ``f"{path}"``
  both unparse their slot to ``path``.

Depth is tracked lexically through ``indent()``/``dedent()``/``with section()``,
so a conversion landing inside a nested block is rendered at the depth it will
actually print at.

The helpers that are *handed* message text -- ``check_for_file`` and
``check_for_files``, whose ``ok=``/``bad=`` arguments are log call sites in
everything but spelling (OI-12) -- are modelled too, one record per message.
This is the ``log.check_for_file(...)`` call form; a direct
``pc.check_for_file(log, ...)`` shifts the arguments along by one and is read
as if it were the wrapped form, which is harmless while the only such calls are
the wrapper itself and its tests, where no message is a literal.

An empty diff *is* the proof that a byte-identical conversion changed nothing.
A non-empty one is the exact list of user-visible changes to review.

Usage::

    cd $QUNEXREPO/python
    tests/log_render_diff.py qx_utilities/hcp/hcp_fmri_volume.py
    tests/log_render_diff.py --rev master qx_utilities/hcp/*.py

Exits non-zero if any file's rendering changed.
"""

import argparse
import ast
import difflib
import os
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from qx_utilities.general.log.report import (  # noqa: E402
    PREFIXES,
    RAW,
    REPORT_RULE,
    _render,
)

# stands in for anything interpolated at run time: its value cannot be known
# here, only that there is a hole and where it sits
SLOT = "‹›"

# the only %-conversions in the tree (census, §13.2 finding 3): %s, %d,
# %(name)s -- no %r, no %f, no flags, no widths, no %%
# ponytail: a %% would be mis-read as a slot; add it here if one ever appears
CONVERSION = re.compile(r"%(\([^)]*\))?[sd]")

# methods that append to a log, by the severity they record with
LEVELS = set(PREFIXES)

# helpers that take message text and log it on the caller's behalf, so a call
# site contributes one record per message argument rather than none. Each
# message is (positional index, keyword, the keyword naming its level, the
# level used when that keyword is absent) -- the shape OI-12 gives
# `check_for_file` / `check_for_files`.
WRAPPERS = {
    "check_for_file": (
        (1, "ok", "ok_level", "detail"),
        (2, "bad", "bad_level", "detail"),
    ),
    "check_for_files": (
        (1, "ok", "ok_level", "detail"),
        (2, "bad", "bad_level", "detail"),
    ),
}


def _method(node):
    """The attribute name of ``x.name(...)``, or None."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _template(node):
    """The message a call renders, with every interpolated slot as ``SLOT``."""
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, str) else SLOT
    if isinstance(node, ast.JoinedStr):
        return "".join(_template(part) for part in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        return CONVERSION.sub(SLOT, _template(node.left))
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _template(node.left) + _template(node.right)
    return SLOT


def _slots(node):
    """The expressions filling the slots, in the order they are interpolated."""
    if isinstance(node, ast.Constant):
        return []
    if isinstance(node, ast.JoinedStr):
        return [s for part in node.values for s in _slots(part)]
    if isinstance(node, ast.FormattedValue):
        return [ast.unparse(node.value)]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
        right = node.right
        operands = right.elts if isinstance(right, ast.Tuple) else [right]
        return _slots(node.left) + [ast.unparse(o) for o in operands]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _slots(node.left) + _slots(node.right)
    if node is None:
        return []
    return [ast.unparse(node)]


def _const_int(node, default=None):
    """A call's first positional argument when it is an integer literal."""
    if node.args and isinstance(node.args[0], ast.Constant):
        if isinstance(node.args[0].value, int):
            return node.args[0].value
    return default


def _keyword_int(node, name, default=0):
    """An integer keyword argument's literal value."""
    for kw in node.keywords:
        if kw.arg == name and isinstance(kw.value, ast.Constant):
            if isinstance(kw.value.value, int):
                return kw.value.value
    return default


def _keyword_str(node, name, default):
    """A string keyword argument's literal value."""
    for kw in node.keywords:
        if kw.arg == name and isinstance(kw.value, ast.Constant):
            if isinstance(kw.value.value, str):
                return kw.value.value
    return default


def _argument(node, position, keyword):
    """A call's argument, given either positionally or by keyword."""
    for kw in node.keywords:
        if kw.arg == keyword:
            return kw.value
    return node.args[position] if len(node.args) > position else None


class _Records(ast.NodeVisitor):
    """Collects one rendered record per log call, grouped by function."""

    def __init__(self):
        self.by_function = {}
        self._scope = []
        self._depth = 0

    # ------------------------------------------------------------- recording

    def _emit(self, depth, severity, message, slots=()):
        line = repr(_render(max(0, depth), severity, message))
        if slots:
            line += "  <- " + ", ".join(slots)
        name = ".".join(self._scope) or "<module>"
        self.by_function.setdefault(name, []).append(line)

    def _level(self, node, severity):
        message = node.args[0] if node.args else None
        # `detail` renders one level deeper than it is called at (report.py)
        extra = 1 if severity == "detail" else 0
        depth = self._depth + _keyword_int(node, "depth") + extra
        self._emit(depth, severity, _template(message), _slots(message))

    def _raw(self, node):
        text = node.args[0] if node.args else None
        # raw always records at depth 0, whatever the log's depth is
        self._emit(0, RAW, _template(text), _slots(text))

    def _wrapper(self, node, messages):
        """
        One record per message a helper is handed (`check_for_file` & co).

        A message that opens with a newline is spelling its own line -- the
        marker and the indent are in the text, and the helper passes it through
        verbatim -- so it renders as ``raw``. One that does not is a message
        for a level method, at the level its ``*_level`` keyword names. That is
        exactly the before and after of the OI-12 conversion, which is what
        lets one instrument compare the two revisions.
        """
        for position, keyword, level_keyword, default in messages:
            message = _argument(node, position, keyword)
            if message is None:
                continue
            template = _template(message)
            if template.startswith("\n"):
                self._emit(0, RAW, template, _slots(message))
                continue
            level = _keyword_str(node, level_keyword, default)
            # `detail` renders one level deeper than it is called at (report.py)
            extra = 1 if level == "detail" else 0
            self._emit(self._depth + extra, level, template, _slots(message))

    # ---------------------------------------------------------------- scopes

    def visit_FunctionDef(self, node):
        self._scope.append(node.name)
        outer, self._depth = self._depth, 0
        self.generic_visit(node)
        self._depth = outer
        self._scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self._scope.append(node.name)
        self.generic_visit(node)
        self._scope.pop()

    def visit_With(self, node):
        outer = self._depth
        closers = []
        for item in node.items:
            call = item.context_expr
            name = _method(call)
            if name == "section":
                self._level(call, "step")
                self._depth += 1
            elif name == "framed":
                title = call.args[0] if call.args else None
                self._emit(
                    0, RAW,
                    "\n\n" + REPORT_RULE + "\n" + _template(title) + "\n\n",
                    _slots(title),
                )
                closers.append("\n" + REPORT_RULE + "\n")
            else:
                self.visit(call)
        for statement in node.body:
            self.visit(statement)
        for text in reversed(closers):
            self._emit(0, RAW, text)
        self._depth = outer

    visit_AsyncWith = visit_With

    # ----------------------------------------------------------------- calls

    def visit_Call(self, node):
        name = _method(node)
        if name in LEVELS:
            self._level(node, name)
        elif name == "raw":
            self._raw(node)
        elif name in WRAPPERS:
            self._wrapper(node, WRAPPERS[name])
        elif name == "blank":
            self._emit(0, RAW, "\n" * _const_int(node, 1))
        elif name == "indent":
            self._depth = max(0, self._depth + _const_int(node, 1))
        elif name == "dedent":
            self._depth = max(0, self._depth - _const_int(node, 1))
        self.generic_visit(node)


def records(source):
    """Map function name -> the rendered records that function logs."""
    walk = _Records()
    walk.visit(ast.parse(source))
    return walk.by_function


def diff_sources(old, new, label=""):
    """Unified diff of two revisions' records, per function. Empty if equal."""
    before, after = records(old), records(new)
    lines = []
    for name in list(before) + [n for n in after if n not in before]:
        lines += difflib.unified_diff(
            before.get(name, []),
            after.get(name, []),
            fromfile="%s:%s (%s)" % (label, name, "before"),
            tofile="%s:%s (%s)" % (label, name, "after"),
            lineterm="",
        )
    return lines


def _at_revision(rev, path):
    """The file as of `rev`. ``<rev>:./<path>`` resolves against the cwd."""
    return subprocess.run(
        ["git", "show", "%s:./%s" % (rev, os.path.relpath(path))],
        capture_output=True, text=True, check=True,
    ).stdout


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Report how a file's rendered runlog changed."
    )
    parser.add_argument("files", nargs="+", help="python files to compare")
    parser.add_argument(
        "--rev", default="HEAD",
        help="revision the worktree is compared against (default: HEAD)",
    )
    args = parser.parse_args(argv)

    changed = False
    for path in args.files:
        lines = diff_sources(
            _at_revision(args.rev, path), pathlib.Path(path).read_text(), path
        )
        if lines:
            changed = True
            print("\n".join(lines))
        else:
            print("%s: rendering unchanged" % path)
    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main())

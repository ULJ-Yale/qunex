# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Static check that every ``log.<wrapper>(...)`` call site matches its signature.

The runlog wrappers in ``general/log.py`` are called from deep inside processing
branches that only execute against real data, so a call built for the old
report-string API -- a stray ``r=``, a positional ``overwrite``, a ``run=``
where the wrapper wants ``command=`` -- raises ``TypeError`` only once a real
pipeline reaches it, hours into a run. The executors catch that ``TypeError``
and report the unit as failed, so the mistake surfaces as a bogus pipeline
failure rather than as a bug. This walks the AST of every Python source in the
tree and binds each call against the real signature instead.
"""

import ast
import inspect
import os
import warnings

import pytest

import qx_utilities.general.core as gc
import qx_utilities.processing.core as pc
from qx_utilities.general.log import ReportLog, SessionLog

PYTHON_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# entry points without a .py extension still have to be checked
EXTRA_SOURCES = [os.path.join(PYTHON_ROOT, "qx_utilities", "gmri")]

# wrapper name -> (function, **kwargs target, argument names the wrapper itself
# already supplies to that target)
WRAPPERS = {
    "run_external": (
        ReportLog.run_external,
        pc.run_external_for_file,
        {"checkfile", "run", "description", "r"},
    ),
    "check_run": (ReportLog.check_run, None, set()),
    "check_for_file": (ReportLog.check_for_file, None, set()),
    "check_for_files": (ReportLog.check_for_files, None, set()),
    "link_or_copy": (ReportLog.link_or_copy, None, set()),
    "use_or_skip_bold": (ReportLog.use_or_skip_bold, None, set()),
    "pipeline_command": (ReportLog.pipeline_command, None, set()),
    "command_failed": (ReportLog.command_failed, None, set()),
    "section": (ReportLog.section, None, set()),
    "finish": (SessionLog.finish, None, set()),
    "result": (SessionLog.result, None, set()),
    "close": (SessionLog.close, None, set()),
}

# how many values each wrapper returns, for the tuple-unpacking check
ARITY = {
    "run_external": 3,
    "check_run": 3,
    "check_for_files": 2,
    "use_or_skip_bold": 3,
    "finish": 2,
    "result": 2,
    "check_for_file": 1,
    "link_or_copy": 1,
}


def _sources():
    """Every Python source in the tree, including extension-less entry points."""
    found = []
    for dirpath, dirnames, filenames in os.walk(PYTHON_ROOT):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        found += [
            os.path.join(dirpath, f) for f in filenames if f.endswith(".py")
        ]
    return sorted(found + [p for p in EXTRA_SOURCES if os.path.exists(p)])


def _log_calls(tree):
    """Yield every ``log.<wrapper>(...)`` call node in a parsed module."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "log"
            and func.attr in WRAPPERS
        ):
            yield node


def _check_binding(call, name):
    """Bind a call against its wrapper signature, returning a problem or None."""
    wrapper, target, supplied = WRAPPERS[name]

    if any(isinstance(a, ast.Starred) for a in call.args):
        return None
    if any(k.arg is None for k in call.keywords):
        return None

    signature = inspect.signature(wrapper)
    parameters = signature.parameters
    takes_kwargs = any(p.kind is p.VAR_KEYWORD for p in parameters.values())

    # the wrapper is looked up on the class, so `self` needs a slot
    args = [None] * (len(call.args) + 1)
    kwargs = {}
    passthrough = []
    for keyword in call.keywords:
        named = keyword.arg in parameters and (
            parameters[keyword.arg].kind is not parameters[keyword.arg].VAR_KEYWORD
        )
        if named or not takes_kwargs:
            kwargs[keyword.arg] = None
        else:
            passthrough.append(keyword.arg)

    try:
        signature.bind(*args, **kwargs)
    except TypeError as e:
        return "log.%s(...) does not match its signature %s: %s" % (
            name,
            signature,
            e,
        )

    # arguments swallowed by **kwargs still have to fit the wrapped function
    if target is not None:
        target_parameters = inspect.signature(target).parameters
        for arg in passthrough:
            if arg in supplied:
                return (
                    "log.%s(...) passes '%s=', which the wrapper already supplies "
                    "to %s (TypeError: multiple values)" % (name, arg, target.__name__)
                )
            if arg not in target_parameters:
                return "log.%s(...) passes '%s=', which %s does not accept" % (
                    name,
                    arg,
                    target.__name__,
                )
    return None


def _check_unpacking(assign, name):
    """Check `a, b = log.wrapper(...)` against how many values it returns."""
    expected = ARITY.get(name)
    if expected is None:
        return None
    for target in assign.targets:
        if not isinstance(target, (ast.Tuple, ast.List)):
            continue
        if any(isinstance(e, ast.Starred) for e in target.elts):
            continue
        if len(target.elts) != expected:
            return "log.%s(...) returns %d value(s), unpacked into %d" % (
                name,
                expected,
                len(target.elts),
            )
    return None


def _scan(path):
    with open(path, encoding="utf-8") as f:
        source = f.read()
    # this test is about call signatures, so a SyntaxWarning in the source (an
    # invalid escape in a docstring, say) must not stop the scan -- pytest.ini
    # turns warnings into errors, which would make ast.parse raise here
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        tree = ast.parse(source, path)

    problems = []
    for call in _log_calls(tree):
        problem = _check_binding(call, call.func.attr)
        if problem:
            problems.append("%s:%d %s" % (path, call.lineno, problem))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        func = node.value.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "log"
            and func.attr in WRAPPERS
        ):
            problem = _check_unpacking(node, func.attr)
            if problem:
                problems.append("%s:%d %s" % (path, node.value.lineno, problem))
    return problems


@pytest.mark.parametrize("path", _sources(), ids=lambda p: os.path.relpath(p, PYTHON_ROOT))
def test_log_call_sites_match_their_signatures(path):
    problems = _scan(path)
    assert not problems, "\n".join(problems)


def test_scanner_catches_a_broken_call(tmp_path):
    """The scanner must actually fail on the three shapes seen in the wild."""
    broken = tmp_path / "broken.py"
    broken.write_text(
        "log.run_external(checkfile=None, run=comm, description='d')\n"
        "log.run_external(f, comm, 'd', overwrite, thread=t)\n"
        "log.run_external(f, comm, 'd', overwrite=True, r=log.text)\n"
    )
    assert len(_scan(str(broken))) == 3


def test_wrapped_targets_are_the_expected_helpers():
    """Guard the assumption that the wrappers still delegate where we think."""
    assert callable(pc.run_external_for_file)
    assert callable(gc.link_or_copy)

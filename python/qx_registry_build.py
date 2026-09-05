# encoding: utf-8

# SPDX-FileCopyrightText: 2024 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Build-time half of the command registry: scans python/matlab/bash source for
qx_command docstrings and writes qx_commands.yaml. Imported only by the
build_qx_registry command; the per-call runtime path lives in qx_registry.py.
"""

from __future__ import annotations

import ast
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
try:
    from qx_utilities.general import exceptions as ge
    from qx_utilities.general.log import LOGGING_MODES
    from qx_utilities.general.parsing import flag
except ModuleNotFoundError:
    from general import exceptions as ge
    from general.log import LOGGING_MODES
    from general.parsing import flag
from qx_registry import (
    ArgInfo,
    CommandInfo,
    Registry,
    DEFAULT_CORE_REGISTRY_BASENAME,
    DEFAULT_EXTENSION_REGISTRY_FILENAME,
    _now_utc_iso,
    registry_from_obj,
    load_registry_yaml,
    extension_folders,
    EXTENSION_FOLDERS_ENV,
)

DEBUG = True
_WARNINGS = []
_PARAM_HEADER_RE = re.compile(r"^\s*Parameters:\s*$")
_RET_HEADER_RE = re.compile(r"^\s*Returns:\s*$")
_SECTION_HEADER_RE = re.compile(r"^\s*[A-Z][A-Za-z0-9_ ]+:\s*$")
_WS_RE = re.compile(r"\s+")
_GENERATED_AT_RE = re.compile(r'^\s*"?generated_at"?\s*:.*\n', re.M)
_ENTRY_RE = re.compile(r"^\s*--(?P<name>[A-Za-z_]\w*)\s*\((?P<spec>[^)]*)\)\s*(?P<colon>:?)\s*$")
_DEFAULT_RE = re.compile(r"\bdefault\b\s*(?:=|:)?\s*(.+)\s*$", re.IGNORECASE)

_QX_MARKERS = {
    ".. qx_command:",
    ".. qx-command:",
    "..  qx_command:",
    ".. qx:",
    ".. qunex:",
    ".. qunex-command:",
    ".. qunex_command:",
}


def normalize_text_one_line(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = s.strip()
    if not s:
        return None
    return _WS_RE.sub(" ", s)


def _warn(msg: str) -> None:
    print(f"    => WARNING: {msg}")
    _WARNINGS.append(msg)


def _strip_quotes(s: str) -> str:
    s = s.strip()
    if (len(s) >= 2) and ((s[0] == s[-1]) and s[0] in ("'", '"')):
        return s[1:-1]
    return s


def _parse_type_default(spec: str) -> Tuple[Optional[str], Optional[str]]:
    """
    spec examples:
      "str | vector"
      "str | vector, default 'abc'"
      "int, default 20"
      "str, default '.'"
      "str|vector, default=foo"

    Returns: (type_str, default_str)
    """
    if not spec or not spec.strip():
        return None, None

    # Split only on the first comma: everything before is "type", everything after can contain more commas
    head, sep, tail = spec.partition(",")
    type_str = head.strip() or None

    default_str: Optional[str] = None
    if sep:
        # Look for "default ..." anywhere in the tail (robust if tail contains extra commas)
        m = _DEFAULT_RE.search(tail)
        if m:
            default_str = _strip_quotes(m.group(1).strip())

    return type_str, default_str


def _short_paragraph(lines: list[str]) -> Optional[str]:
    """
    Return text up to first empty line. If first line is empty, return None.
    """
    out: list[str] = []
    for ln in lines:
        if ln.strip() == "":
            break
        out.append(ln.rstrip())
    txt = "\n".join(out).strip()
    return txt or None


def _parse_entry_section(
    lines: list[str],
    header_re: re.Pattern[str],
    *,
    kind: str,
    file: Path,
    func_name: str,
    with_default: bool,
) -> list[ArgInfo]:
    """Parse a Parameters:/Returns: section into ArgInfo entries.

    Parameters and Returns share the same ``--name (spec): description`` layout;
    they differ only in whether a default is kept and in the warning label.
    """
    # locate the section header and the lines that follow it
    sec: Optional[list[str]] = None
    base_indent = 0
    for i, ln in enumerate(lines):
        if header_re.match(ln):
            base_indent = len(ln) - len(ln.lstrip())
            sec = lines[i + 1 :]
            break
    if sec is None:
        return []

    out: list[ArgInfo] = []
    i = 0
    while i < len(sec):
        ln = sec[i]
        if ln.strip() == "":
            i += 1
            continue

        indent = len(ln) - len(ln.lstrip())
        # stop on a top-level new section header (same indent as the header or less)
        if indent <= base_indent and _SECTION_HEADER_RE.match(ln):
            break

        m = _ENTRY_RE.match(ln)
        if not m:
            i += 1
            continue

        name = m.group("name")
        a_type, a_default = _parse_type_default(m.group("spec"))
        if not with_default:
            a_default = None

        if not m.group("colon"):
            _warn(f"{file}:{func_name}: {kind} '--{name}' missing trailing ':'")

        # description: consume until next entry OR next top-level section header
        desc_lines: list[str] = []
        i += 1
        while i < len(sec):
            ln2 = sec[i]
            if ln2.strip() == "":
                desc_lines.append("")   # preserve paragraph boundary for _short_paragraph()
                i += 1
                continue

            indent2 = len(ln2) - len(ln2.lstrip())
            if _ENTRY_RE.match(ln2):
                break
            if indent2 <= base_indent and _SECTION_HEADER_RE.match(ln2):
                break

            desc_lines.append(ln2.strip())
            i += 1

        a_desc = normalize_text_one_line(_short_paragraph(desc_lines))
        out.append(ArgInfo(name=name, type=a_type, default=a_default, description=a_desc))

    return out


def parse_command_docstring(doc: str, *, file: Path, func_name: str) -> tuple[
    Optional[str], Optional[str], dict[str, str], list[ArgInfo], list[ArgInfo]
]:
    """
    Returns:
      call, description, qx_meta, param_entries, return_entries

    Errors are raised as ValueError with a message; caller will catch and skip.
    """
    if not doc or not doc.strip():
        raise ValueError("missing docstring")

    lines = doc.splitlines()

    # 1) call line: first line containing ``...``
    call = None
    for ln in lines:
        s = ln.strip()
        if s.startswith("``") and s.endswith("``") and len(s) >= 4:
            call = s[2:-2].strip()
            break

    if call is None:
        raise ValueError("missing example call line using ``...``")

    # 2) description paragraph: starts after call line; take up to first empty line
    call_idx = next(i for i, ln in enumerate(lines) if ln.strip().startswith("``") and ln.strip().endswith("``"))
    tail = lines[call_idx + 1 :]

    # skip leading empty lines
    while tail and tail[0].strip() == "":
        tail.pop(0)

    description = normalize_text_one_line(_short_paragraph(tail))

    # 3) qx meta (type, aliases) block; not mandatory, no error if missing
    qx_meta = parse_qx_block_from_docstring(doc)

    # 4) parse Parameters and Returns sections (ignore everything else)
    params = _parse_entry_section(
        lines, _PARAM_HEADER_RE, kind="parameter", file=file, func_name=func_name, with_default=True
    )
    rets = _parse_entry_section(
        lines, _RET_HEADER_RE, kind="return", file=file, func_name=func_name, with_default=False
    )

    return call, description, qx_meta, params, rets


def _normalize_rst_marker(line: str) -> str:
    s = line.lstrip()
    if not s.startswith(".."):
        return s
    # Collapse any extra whitespace after ".."
    return ".. " + s[2:].lstrip()


def parse_qx_block_from_docstring(doc: str) -> Dict[str, str]:
    """
    Parse a reST comment block inside a docstring, allowing indentation:

    |   .. qx_command:
    |      type: utility
    |      aliases: a, b

    The marker may be indented in the docstring.
    """
    if not doc:
        return {}

    lines = doc.splitlines()
    meta: Dict[str, str] = {}

    i = 0
    while i < len(lines):
        raw = lines[i].rstrip("\n")
        stripped = _normalize_rst_marker(raw)
        if not (stripped.startswith(".. ") and stripped.strip() in _QX_MARKERS):
            i += 1
            continue

        # indentation level of marker line
        marker_indent = len(raw) - len(raw.lstrip())
        i += 1

        while i < len(lines):
            raw2 = lines[i].rstrip("\n")
            if raw2.strip() == "":
                i += 1
                continue

            indent2 = len(raw2) - len(raw2.lstrip())

            # Stop when we return to marker indent or less (new section / paragraph)
            if indent2 <= marker_indent:
                break

            entry = raw2.lstrip()
            if ":" in entry:
                k, v = entry.split(":", 1)
                k = k.strip()
                v = v.strip()
                if k:
                    meta[k] = v
            i += 1

        # continue scanning; later blocks override earlier keys
        continue

    return meta


def parse_aliases(value: Optional[str]) -> Tuple[str, ...]:
    """
    Accepts:
      aliases: a,b,c
      aliases: a, b, c
      aliases: [a, b, c]
    """
    if not value:
        return ()
    s = value.strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1].strip()
    parts = [p.strip() for p in s.split(",")]
    return tuple(p for p in parts if p)


def unparse_annotation(node: Optional[ast.AST]) -> Optional[str]:
    if node is None:
        return None
    try:
        return ast.unparse(node).strip()
    except Exception:
        return None


def python_function_args(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> Tuple[Tuple[str, Optional[str]], ...]:
    """
    Returns ordered tuples: (arg_name, annotation_type_str_or_None)
    Includes: posonlyargs, args, kwonlyargs
    Excludes: *args and **kwargs as named args (consistent with earlier)
    """
    out: List[Tuple[str, Optional[str]]] = []

    def add(a: ast.arg) -> None:
        out.append((a.arg, unparse_annotation(a.annotation)))

    for a in fn.args.posonlyargs:
        add(a)
    for a in fn.args.args:
        add(a)
    for a in fn.args.kwonlyargs:
        add(a)

    return tuple(out)


def module_name_from_file(pyfile: Path, root: Path) -> str:
    """
    /root/qx_utilities/general/bids.py -> qx_utilities.general.bids
    /root/qx_utilities/general/__init__.py -> qx_utilities.general
    """
    rel = pyfile.resolve().relative_to(root.resolve())
    parts = list(rel.parts)
    if not parts:
        raise ge.CommandFailed('module_name_from_file', f"unexpected path: {pyfile}")

    if parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    if parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(parts)


def iter_files(root: Path, suffix: str, *, exclude_dirs: Tuple[str, ...] = ("__pycache__", ".git", "tests")) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for fn in filenames:
            if fn.endswith(suffix):
                yield Path(dirpath) / fn


_BASH_USAGE_DEF_RE = re.compile(r"^\s*usage\s*\(\s*\)\s*\{\s*$")


_BASH_HEREDOC_START_RE = re.compile(
    r"^\s*cat\s*<<(?P<strip>-?)\s*(?P<q>['\"]?)(?P<tag>[A-Za-z0-9_]+)(?P=q)\s*$"
)


def _bash_usage_heredoc(text: str) -> Optional[str]:
    """Extract the documentation text embedded in a bash script's usage() heredoc.

    We look for:

        usage() {
            cat << EOF
            ...doc...
        EOF

    Returns the heredoc body (without the delimiter lines), or None.
    """

    lines = text.splitlines()
    usage_idx: Optional[int] = None
    for i, ln in enumerate(lines):
        if _BASH_USAGE_DEF_RE.match(ln):
            usage_idx = i
            break
    if usage_idx is None:
        return None

    # Find the heredoc start within usage()
    start_idx: Optional[int] = None
    tag: Optional[str] = None
    strip_tabs = False
    for j in range(usage_idx, len(lines)):
        m = _BASH_HEREDOC_START_RE.match(lines[j])
        if not m:
            continue
        start_idx = j
        tag = m.group("tag")
        strip_tabs = bool(m.group("strip"))
        break

    if start_idx is None or tag is None:
        return None

    body: List[str] = []
    k = start_idx + 1
    while k < len(lines):
        ln = lines[k]
        check = ln.lstrip("\t") if strip_tabs else ln
        if check.strip() == tag:
            break
        body.append(ln)
        k += 1

    if not body:
        return None
    return "\n".join(body).strip("\n")


def index_bash_commands(bash_root: Path, *, source_id: str) -> List[CommandInfo]:
    """Find commands in .sh files under bash_root.

    A file is considered a command if its usage() heredoc contains a qx metadata
    block (.. qx_command:).
    """

    bash_root = bash_root.resolve()
    out: List[CommandInfo] = []

    for shfile in iter_files(bash_root, ".sh"):
        try:
            text = shfile.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = shfile.read_text(errors="replace")

        doc = _bash_usage_heredoc(text)
        if not doc:
            continue

        qx_meta = parse_qx_block_from_docstring(doc)
        if not qx_meta:
            continue

        func_name = shfile.stem

        try:
            call, desc, _qx_meta2, doc_params, doc_returns = parse_command_docstring(
                doc, file=shfile, func_name=func_name
            )
        except ValueError as e:
            _warn(f"{shfile}:{func_name}: invalid usage() doc block: {e}; command excluded")
            continue

        # For bash commands the call line is typically just ``<command>``.
        call_token = (call or "").strip().split()[0] if call else ""
        cmd_name = (qx_meta.get("name") or call_token or func_name).strip()
        aliases = parse_aliases(qx_meta.get("aliases"))
        cmd_type = qx_meta.get("type")
        cmd_logging = parse_logging(qx_meta.get("logging"), f"{shfile}:{func_name}")

        rel_path = shfile.relative_to(bash_root).as_posix()

        if DEBUG:
            print(f"    -> registering {rel_path}")

        out.append(
            CommandInfo(
                name=cmd_name,
                aliases=aliases,
                path=rel_path,            # .sh location relative to bash_root
                language="bash",
                call=call,
                description=desc,
                type=cmd_type,
                args=tuple(),
                options=tuple(doc_params),
                returns=tuple(doc_returns),
                origin=source_id,
                logging=cmd_logging,
            )
        )

    return out


def index_python_commands(root: Path, *, source_id: str) -> List[CommandInfo]:
    root = root.resolve()
    out: List[CommandInfo] = []

    for pyfile in iter_files(root, ".py"):
        try:
            source = pyfile.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            source = pyfile.read_text(errors="replace")

        try:
            tree = ast.parse(source, filename=str(pyfile))
        except SyntaxError as e:
            _warn(f"{pyfile}: SyntaxError skipped: {e}")
            continue

        mod_name = module_name_from_file(pyfile, root)

        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            raw_doc = ast.get_docstring(node, clean=False) or ""
            if not raw_doc.strip():
                continue

            # command marker: require qx block OR (per your new format) require Parameters section presence?
            # We'll require the .. qx_command block OR at least Parameters section + call line.
            # But spec says required format includes .. qx_command. We'll treat missing qx block as NOT a command.
            meta = parse_qx_block_from_docstring(raw_doc)
            if not meta:
                continue  # not a command

            # Skip python doc-stubs that document a non-python (e.g. bash) command:
            # those are registered from their real source (.sh/.m). Registering them
            # here too would force language="python" and collide on the command name.
            declared_lang = (meta.get("language") or "python").strip().lower()
            if declared_lang != "python":
                if DEBUG:
                    print(f"    -> skipping {mod_name}.{node.name} (declares language: {declared_lang})")
                continue

            func_name = node.name

            try:
                call, desc, qx_meta, doc_params, doc_returns = parse_command_docstring(
                    raw_doc, file=pyfile, func_name=func_name
                )
            except ValueError as e:
                _warn(f"{pyfile}:{func_name}: invalid command docstring: {e}; command excluded")
                continue

            cmd_name = (qx_meta.get("name") or func_name).strip()  # still optional if you ever add it
            aliases = parse_aliases(qx_meta.get("aliases"))
            cmd_type = qx_meta.get("type")
            cmd_logging = parse_logging(qx_meta.get("logging"), f"{pyfile}:{func_name}")

            # Signature args (ordered) + annotations. A leading underscore
            # marks a parameter the caller passes and the user must not: a
            # command's report log is threaded in by whatever invoked it, and
            # is neither settable nor meaningful on the command line. Dropping
            # it here keeps it out of `args`, which is what `Command.has_arg`
            # reads when gmri decides where a `--name=value` goes.
            #
            # This is also why the log parameter is `_log` and not `log`:
            # `--log` is a live user-facing parameter (comlog retention,
            # defaulted in general/process.py and remapped for every command in
            # commands_support.py before dispatch), so a `log` in a signature
            # would make `has_arg("log")` true and route `--log=keep` into the
            # command instead of into the comlog policy. `tests/
            # test_registry_drift.py` asserts no built `args` entry starts
            # with an underscore.
            sig_args = tuple(
                (n, t) for n, t in python_function_args(node) if not n.startswith("_")
            )
            sig_names = [n for n, _ in sig_args]
            has_options = "options" in sig_names

            # Build lookup from doc params by name
            doc_map: Dict[str, ArgInfo] = {a.name: a for a in doc_params}

            # args list in signature order (excluding options itself? keep it as real arg)
            args: List[ArgInfo] = []
            for n, ann_t in sig_args:
                doc_a = doc_map.get(n)
                # annotation wins over doc type
                a_type = ann_t if ann_t is not None else (doc_a.type if doc_a else None)
                a_default = doc_a.default if doc_a else None
                a_desc = doc_a.description if doc_a else None
                args.append(ArgInfo(name=n, type=a_type, default=a_default, description=a_desc))

            # extras from doc_params not in signature
            extras = [a for a in doc_params if a.name not in sig_names]
            options: List[ArgInfo] = []
            if extras:
                if has_options:
                    options.extend(extras)
                    # _warn(f"{pyfile}:{func_name}: doc Parameters not in signature routed to 'options': {[a.name for a in extras]}")
                    if DEBUG:
                        print(f"       adding options: {[a.name for a in extras]}")
                else:
                    _warn(f"{pyfile}:{func_name}: doc Parameters not in signature ignored (no 'options' arg): {[a.name for a in extras]}")

            impl_path = f"{mod_name}.{func_name}"

            if DEBUG:
                print(f"    -> registering {impl_path}")

            out.append(
                CommandInfo(
                    name=cmd_name,
                    aliases=aliases,
                    path=impl_path,
                    language="python",
                    call=call,
                    description=desc,
                    type=cmd_type,
                    args=tuple(args),
                    options=tuple(options),
                    returns=tuple(doc_returns),
                    origin=source_id,
                    logging=cmd_logging,
                )
            )

    return out


_MATLAB_FUNC_RE = re.compile(
    r"""^\s*function\s+
        (?:(?P<out>\[[^\]]*\]|\w+)\s*=\s*)?
        (?P<name>[A-Za-z]\w*)
        (?:\s*\(\s*(?P<args>[^)]*)\s*\))?
        \s*$
    """,
    re.VERBOSE,
)


def _strip_matlab_comment_prefix(line: str) -> str:
    s = line.lstrip()
    if not s.startswith("%"):
        return line
    s = s[1:]
    if s.startswith(" "):
        s = s[1:]
    return s


def _matlab_parse_outputs(out_str: Optional[str]) -> List[str]:
    if not out_str:
        return []
    s = out_str.strip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [x.strip() for x in inner.split(",") if x.strip()]
    return [s]


def _matlab_parse_args(arg_str: Optional[str]) -> List[str]:
    if not arg_str:
        return []
    s = arg_str.strip()
    if not s:
        return []
    parts = [x.strip() for x in s.split(",") if x.strip()]
    # treat varargin like **kwargs: exclude from named args list
    parts = [p for p in parts if p not in ("varargin",)]
    return parts


def _matlab_help_block_after_function(text: str) -> Optional[str]:
    """
    Return the contiguous MATLAB help comment block immediately following
    the first function definition line. De-comments '%' prefixes.
    """
    lines = text.splitlines()
    func_idx = None
    for i, ln in enumerate(lines):
        if _MATLAB_FUNC_RE.match(ln):
            func_idx = i
            break
    if func_idx is None:
        return None

    # collect consecutive comment lines after function line
    out: List[str] = []
    i = func_idx + 1
    while i < len(lines):
        ln = lines[i]
        if ln.strip() == "":
            # keep blank lines inside help block only if we already started
            if out:
                out.append("")
                i += 1
                continue
            i += 1
            continue

        if ln.lstrip().startswith("%"):
            out.append(_strip_matlab_comment_prefix(ln).rstrip("\n"))
            i += 1
            continue

        # stop at first real code line
        break

    if not out:
        return None
    return "\n".join(out)


def index_matlab_commands(matlab_root: Path, *, source_id: str) -> List[CommandInfo]:
    """
    Find commands in .m files under matlab_root.

    A file is considered a command if it contains a qx metadata block in comments.
    Function name/args/returns are taken from the MATLAB 'function' line.
    Types for args/returns come from doc metadata args/returns (if provided).
    command.path is the relative path to the .m file where the function was found.
    """
    matlab_root = matlab_root.resolve()
    out: List[CommandInfo] = []

    for mfile in iter_files(matlab_root, ".m"):
        try:
            text = mfile.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = mfile.read_text(errors="replace")

        # Parse function signature (name, args, outs)
        func_name = None
        func_args: List[str] = []
        func_outs: List[str] = []

        for line in text.splitlines():
            m = _MATLAB_FUNC_RE.match(line)
            if not m:
                continue
            func_name = m.group("name")
            func_args = _matlab_parse_args(m.group("args"))
            func_outs = _matlab_parse_outputs(m.group("out"))
            # treat varargin/varargout as **kwargs / variadic returns: ignore as named
            func_args = [a for a in func_args if a not in ("varargin",)]
            func_outs = [o for o in func_outs if o not in ("varargout",)]
            break

        if not func_name:
            continue

        # Get MATLAB "docstring" (help block)
        doc = _matlab_help_block_after_function(text)
        if not doc:
            continue

        # Determine if it's a command: requires qx_command block
        qx_meta = parse_qx_block_from_docstring(doc)
        if not qx_meta:
            continue

        # Parse the docstring format (call, description, Parameters, Returns)
        try:
            call, desc, _qx_meta2, doc_params, doc_returns = parse_command_docstring(
                doc, file=mfile, func_name=func_name
            )
        except ValueError as e:
            _warn(f"{mfile}:{func_name}: invalid command docstring: {e}; command excluded")
            continue

        cmd_name = (qx_meta.get("name") or func_name).strip()
        aliases = parse_aliases(qx_meta.get("aliases"))
        cmd_type = qx_meta.get("type")
        cmd_logging = parse_logging(qx_meta.get("logging"), f"{mfile}:{func_name}")

        # Map doc params/returns by name
        doc_param_map: Dict[str, ArgInfo] = {a.name: a for a in doc_params}
        doc_ret_map: Dict[str, ArgInfo] = {r.name: r for r in doc_returns}

        # Args in function order, types/default/desc from doc if available
        args: List[ArgInfo] = []
        for a in func_args:
            da = doc_param_map.get(a)
            args.append(
                ArgInfo(
                    name=a,
                    type=da.type if da else None,
                    default=da.default if da else None,
                    description=da.description if da else None,
                )
            )

        # Warn about doc params not in signature
        extra_doc_args = [a.name for a in doc_params if a.name not in func_args]
        if extra_doc_args:
            _warn(f"{mfile}:{func_name}: doc Parameters not in function signature ignored: {extra_doc_args}")

        # Returns: if function outputs exist, use that order; else use doc order
        returns: List[ArgInfo] = []
        if func_outs:
            for r in func_outs:
                dr = doc_ret_map.get(r)
                returns.append(
                    ArgInfo(
                        name=r,
                        type=dr.type if dr else None,
                        default=None,
                        description=dr.description if dr else None,
                    )
                )
            extra_doc_rets = [r.name for r in doc_returns if r.name not in func_outs]
            if extra_doc_rets:
                _warn(f"{mfile}:{func_name}: doc Returns not in function outputs ignored: {extra_doc_rets}")
        else:
            returns = list(doc_returns)

        rel_path = mfile.relative_to(matlab_root).as_posix()

        if DEBUG:
            print(f"    -> registering {rel_path}")

        out.append(
            CommandInfo(
                name=cmd_name,
                aliases=aliases,
                path=rel_path,            # .m location
                language="matlab",
                call=call,
                description=desc,
                type=cmd_type,
                args=tuple(args),
                options=tuple(),          # matlab has no 'options' routing
                returns=tuple(returns),
                origin=source_id,
                logging=cmd_logging,
            )
        )

    return out


def parse_logging(value: Optional[str], where: str) -> Optional[str]:
    """Read the optional `logging:` field of a qx_command block.

    Values match --logging: none | comlog | runlog | both. An unrecognised
    value is dropped with a warning rather than silently disabling a
    command's logs at runtime.
    """
    if not value:
        return None
    mode = value.strip().lower()
    if mode not in LOGGING_MODES:
        _warn(f"{where}: invalid 'logging: {value}' in qx block; expected one of {', '.join(sorted(LOGGING_MODES))}; ignored")
        return None
    return mode


def validate_command_types(commands: List[CommandInfo]) -> List[CommandInfo]:
    """Drop commands lacking a 'type:' in their qx block; warn on each.

    Runtime dispatch (gmri, scheduler) assumes every registered command has a
    type, so enforce that invariant at build time rather than crash later.
    """
    valid: List[CommandInfo] = []
    for c in commands:
        if not c.type:
            _warn(f"{c.path}: command '{c.name}' has no 'type:' in its qx block; command excluded")
            continue
        valid.append(c)
    return valid


def validate_unique_tokens(commands: List[CommandInfo]) -> None:
    used: Dict[str, CommandInfo] = {}

    def claim(token: str, cmd: CommandInfo, kind: str) -> None:
        if token in used:
            prev = used[token]
            raise ge.CommandFailed('validate_unique_tokens',
                f"Duplicate command token '{token}' ({kind}).\n"
                f"Already used by: {prev.name} ({prev.language}, {prev.origin}, {prev.path})\n"
                f"Conflicts with:  {cmd.name} ({cmd.language}, {cmd.origin}, {cmd.path})")
        used[token] = cmd

    for c in commands:
        claim(c.name, c, "name")
        for a in c.aliases:
            claim(a, c, "alias")


def command_to_obj(c: CommandInfo) -> Dict[str, Any]:
    obj = {
        "name": c.name,
        "aliases": list(c.aliases),
        "path": c.path,
        "language": c.language,
        "call": c.call,
        "description": c.description,
        "type": c.type,
        "args": [{"name": a.name, "type": a.type, "default": a.default, "description": normalize_text_one_line(a.description)} for a in c.args],
        "options": [{"name": a.name, "type": a.type, "default": a.default, "description": normalize_text_one_line(a.description)} for a in c.options],
        "returns": [{"name": r.name, "type": r.type, "default": r.default, "description": normalize_text_one_line(r.description)} for r in c.returns],
        "origin": c.origin,
    }
    # emitted only when the command states one: a `logging: null` on each of the
    # ~160 commands would swamp every future diff of the registry
    if c.logging:
        obj["logging"] = c.logging
    return obj


def registry_to_obj(commands: List[CommandInfo], *, source_id: str) -> Dict[str, Any]:
    return {
        "version": 1,
        "generated_at": _now_utc_iso(),
        "source": {"id": source_id},
        "commands": [command_to_obj(c) for c in sorted(commands, key=lambda x: x.name)],
    }


def _drop_generated_at(text: str) -> str:
    return _GENERATED_AT_RE.sub("", text, count=1)


def write_registry_file(path: Path, obj: Dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import yaml  # type: ignore
    except ImportError:
        text = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    else:
        # only the import falls back to JSON; a serialization error must surface,
        # not silently write JSON into a .yaml file
        dumper = getattr(yaml, "CSafeDumper", yaml.SafeDumper)
        text = yaml.dump(obj, Dumper=dumper, sort_keys=False, allow_unicode=True, width=120, indent=4)

    # generated_at is the one field that differs on every build, so writing it
    # unconditionally would put a diff in front of everyone who rebuilds and
    # leave the CI rebuild committing a timestamp on every run. when nothing
    # else moved, leave the committed file as it stands
    if path.exists() and _drop_generated_at(path.read_text(encoding="utf-8")) == _drop_generated_at(text):
        return

    path.write_text(text, encoding="utf-8")


def _get_qunexpath() -> Path:
    qunexpath = os.environ.get("QUNEXPATH", "").strip()
    if not qunexpath:
        raise ge.CommandError('build_qx_registry', "QUNEXPATH is not set.")
    return Path(qunexpath).resolve()


def build_registry_yaml(commands: List[CommandInfo], *, out: Path, source_id: str) -> Registry:
    commands = validate_command_types(commands)
    validate_unique_tokens(commands)
    obj = registry_to_obj(commands, source_id=source_id)
    write_registry_file(out, obj)
    return registry_from_obj(obj)


def _report_extensions() -> List[Path]:
    """
    The extensions QuNex can see, with what somebody needs in order to pick one.

    Printed rather than returned to the caller, because this is what a person
    gets when they ask `build_qx_extensions` what is there. It goes to stdout:
    the stdout-is-a-routing-table rule applies to `gmri -available`, not to a
    command's own output.
    """
    folders = extension_folders()

    if not folders:
        print("\n--> No extensions found.")
        print("    QuNex looks under $QUNEXPATH/qx_extensions, under $TOOLS/qx_extensions,")
        print(f"    and under every folder named in ${EXTENSION_FOLDERS_ENV}. That variable")
        print("    names the folder that *holds* the qx_<name> folders, not the extension.")
        return folders

    print(f"\n--> Extensions QuNex can see ({len(folders)}):")
    name_width = max(len(f.name) for f in folders)
    path_width = max(len(str(f)) for f in folders)
    for folder in folders:
        registry = folder / DEFAULT_EXTENSION_REGISTRY_FILENAME
        state = "registry built" if registry.exists() else "no registry yet"
        print(f"    {folder.name:<{name_width}}  {str(folder):<{path_width}}  [{state}]")

    print("\n--> Name the ones to build:")
    print("        qunex build_qx_extensions --extensions=<name>[,<name>...]")
    print("    or build every one of them:")
    print("        qunex build_qx_extensions --extensions=all")

    return folders


def build_qx_extensions(*, extensions: Optional[str] = None):
    """
    ``build_qx_extensions(extensions=None)``

    Build the command registry of one or more extensions, and leave the QuNex
    installation's own registry as it is.

    An extension's registry is what makes its commands visible to QuNex, so it
    has to be built once before the extension can be used, and again whenever a
    command is added, renamed or re-documented.

    This is what an extension author wants, and inside a container it is usually
    the only thing that will work: the installation's own registry lives on the
    container image, which is read only.

    Which extensions to build has to be said. Run with no ``--extensions``, or
    with ``--extensions=check``, it builds nothing and lists the extensions
    QuNex can see.

    ..  qx_command:
        type: utility

    Parameters:
        --extensions (str, default ''):
            Which extensions to build, as a comma separated list of names given
            with or without the qx_ prefix. 'all' builds every extension found.
            'check', or leaving it out, builds nothing and lists the extensions
            QuNex can see.

    Returns:
        --registry (tuple):
            A tuple with elements: (core_registry, built_extensions), as
            build_qx_registry returns them. (None, []) on a listing run.
    """
    named = (extensions or "").strip()

    if not named or named.lower() == "check":
        _report_extensions()

        # asked for deliberately, `check` is a question that was answered; an
        # omitted parameter is a usage error, so that a script that meant to
        # build is told rather than carrying on as though it had
        if named:
            return None, []

        raise ge.CommandFailed(
            'build_qx_extensions',
            "No extensions named",
            "Name one or more with --extensions=<name>, or --extensions=all for all of them.",
        )

    return build_qx_registry(build_core=False, extensions=named)


def _select_extensions(extensions: Optional[str], folders: List[Path]) -> List[Path]:
    """
    The extension folders a build covers, out of the ones QuNex can see.

    `extensions` is a comma separated list of names, each given with or without
    the `qx_` prefix; `all` -- alone or among others -- and an empty value both
    mean every extension found.

    A name matching nothing is an error rather than a quiet no-op. A typo would
    otherwise be indistinguishable from a successful build, and only turn up
    later as `Requested command is not supported`, a long way from its cause.
    """
    wanted = [e.strip() for e in (extensions or "").replace(";", ",").split(",") if e.strip()]

    if not wanted or any(w.lower() == "all" for w in wanted):
        return folders

    by_name = {f.name[len("qx_") :]: f for f in folders}

    selected: Dict[str, Path] = {}
    unknown: List[str] = []
    for name in wanted:
        key = name[len("qx_") :] if name.startswith("qx_") else name
        if key in by_name:
            selected[key] = by_name[key]
        else:
            unknown.append(name)

    if unknown:
        raise ge.CommandFailed(
            'build_qx_registry',
            "Unknown extension(s): %s" % ", ".join(unknown),
            "Extensions found: %s" % (", ".join(sorted(by_name)) or "none"),
        )

    return [selected[key] for key in sorted(selected)]


def build_qx_registry(
    *,
    core_python_root: Optional[str | Path] = None,
    core_registry_yaml: Optional[str | Path] = None,
    build_core: bool = True,
    build_extensions: bool = True,
    extensions: Optional[str] = None,
    extension_registry_filename: str = DEFAULT_EXTENSION_REGISTRY_FILENAME,
    extension_python_subdir: str = "python",
    extension_matlab_subdir: str = "matlab",
    extension_bash_subdir: str = "bash",
) -> Tuple[Registry, List[Tuple[str, Path]]]:
    """
    ``build_qx_registry()``

    Build core registry at $QUNEXPATH/qx_commands.yaml (python + matlab + bash for core),
    and build each extension registry at <ext_root>/qx_commands.yaml (python + matlab + bash if present).

    An extension is found under $QUNEXPATH/qx_extensions, under $TOOLS/qx_extensions,
    or under a folder named in $QUNEXEXTENSIONSFOLDERS. Its registry is written beside
    its code and is what makes its commands visible to QuNex, so an extension has to be
    built once before it can be used.

    ..  qx_command:
        type: utility

    Parameters:
        --core_python_root (str, default ''):
            The folder to index the core python commands from. Defaults to
            $QUNEXPATH/python.

        --core_registry_yaml (str, default ''):
            The file to write the core registry to. Defaults to
            $QUNEXPATH/qx_commands.yaml.

        --build_core (str, default 'yes'):
            Whether to build the core registry. Set to 'no' to leave the core
            registry alone and build only the extensions, which is what an
            extension author wants and what a read-only installation requires.

        --build_extensions (str, default 'yes'):
            Whether to build the registry of every extension found. Set to 'no'
            to build only core.

        --extensions (str, default ''):
            Which extensions to build, as a comma separated list of names given
            with or without the qx_ prefix. 'all', or leaving it out, builds
            every extension found. A name matching no extension is an error
            naming the extensions that were found.

        --extension_registry_filename (str, default 'qx_commands.yaml'):
            The name of the registry file written inside each extension.

        --extension_python_subdir (str, default 'python'):
            The folder inside an extension holding its python commands.

        --extension_matlab_subdir (str, default 'matlab'):
            The folder inside an extension holding its MATLAB commands.

        --extension_bash_subdir (str, default 'bash'):
            The folder inside an extension holding its bash commands.

    Returns:
        --registry (tuple):
            A tuple with elements: (core_registry, built_extensions) where
            built_extensions = [(extension_id, registry_yaml_path), ...]
    """
    qunex_root = _get_qunexpath()

    # both arrive as strings when they come from the command line, where
    # `--build_core=no` has to mean no rather than a non-empty string
    build_core = flag(build_core)
    build_extensions = flag(build_extensions)

    if core_python_root is None:
        core_python_root = qunex_root / "python"
    core_python_root = Path(core_python_root).resolve()

    if core_registry_yaml is None:
        core_registry_yaml = qunex_root / DEFAULT_CORE_REGISTRY_BASENAME
    core_registry_yaml = Path(core_registry_yaml).resolve()

    if build_core:
        if not core_python_root.exists():
            raise ge.CommandFailed('build_qx_registry', f"Core python root not found: {core_python_root}")

        # Core: python
        print(f"--> Building core python command registry from {core_python_root}")
        core_cmds = index_python_commands(core_python_root, source_id="core")

        # Core Matlab
        # if DEBUG: print(f"--> Checking for core matlab commands in {qunex_root / 'matlab'}")
        matlab_root = qunex_root / "matlab"
        if matlab_root.exists():
            core_cmds.extend( index_matlab_commands(matlab_root, source_id="core"))

        # Core Bash
        bash_root = qunex_root / "bash"
        if bash_root.exists():
            core_cmds.extend(index_bash_commands(bash_root, source_id="core"))

        core_reg = build_registry_yaml(core_cmds, out=core_registry_yaml, source_id="core")

    else:
        # left as it stands, and read back so that the return says what QuNex
        # will actually run. Building an extension used to rewrite the core
        # registry as a side effect, which an extension author does not want
        # and a read-only installation does not allow
        if not core_registry_yaml.exists():
            raise ge.CommandFailed(
                'build_qx_registry',
                f"Core registry not found: {core_registry_yaml}",
                "It has to be built once before an extension can be built on its own.",
            )
        print(f"--> Leaving the core command registry as it is: {core_registry_yaml}")
        core_reg = load_registry_yaml(core_registry_yaml)

    built_exts: Dict[str, Path] = {}

    if not build_extensions:
        return core_reg, []

    # `extension_folders()` is the same answer the runtime resolves against, so
    # an extension present under several roots is built in the one copy QuNex
    # will actually load. Walking the roots here instead wrote a registry into
    # every copy, including the ones nothing would ever read
    for ext_root in _select_extensions(extensions, extension_folders()):
        ext_name = ext_root.name[len("qx_") :].strip()
        if not ext_name:
            continue
        ext_id = f"extension:{ext_name}"

        cmds: List[CommandInfo] = []

        py_root = ext_root / extension_python_subdir
        if py_root.exists() and py_root.is_dir():
            cmds.extend(index_python_commands(py_root, source_id=ext_id))

        m_root = ext_root / extension_matlab_subdir
        if m_root.exists() and m_root.is_dir():
            cmds.extend(index_matlab_commands(m_root, source_id=ext_id))

        b_root = ext_root / extension_bash_subdir
        if b_root.exists() and b_root.is_dir():
            cmds.extend(index_bash_commands(b_root, source_id=ext_id))

        if not cmds:
            continue  # nothing to build yet

        out_yaml = (ext_root / extension_registry_filename).resolve()
        build_registry_yaml(cmds, out=out_yaml, source_id=ext_id)
        built_exts[ext_id] = out_yaml

    built = sorted(built_exts.items(), key=lambda x: x[0])

    print("\n----------------------------------------------------------------\nRegistry built!")

    if not built:
        print("\n--> No extension registries were built: no extension was found with commands in it.")
    if built:
        label = "extension registry" if len(built) == 1 else "extension registries"
        if build_core:
            print(f"\n--> In addition to core, built {len(built)} {label}:")
        else:
            print(f"\n--> Built {len(built)} {label}:")
        for ext_id, path in built:
            print(f"    - {ext_id}: {path}")
    if _WARNINGS:
        print(f"--> {len(_WARNINGS)} warning(s) reported:")
        for msg in _WARNINGS:
            print(f"    => {msg}")

    return core_reg, built

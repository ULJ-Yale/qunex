# CLAUDE.md

Guidance for Claude Code when working in the QuNex repository.

## What this is

QuNex (Quantitative Neuroimaging Environment & ToolboX) is a multi-language framework
for organizing, preprocessing, QA-ing, and analyzing neuroimaging data. The codebase is
mixed-language (Python, Bash, MATLAB/Octave, R) and historically inconsistent. **Prefer
pragmatic, focused improvements over strict rewrites.**

- Version: see `VERSION.md` (currently 1.5.0). `qx_library` is a git submodule (see `.gitmodules`).
- Docs: https://qunex.readthedocs.io · Forum: https://forum.qunex.yale.edu
- License: GPL-3.0-or-later (REUSE-compliant; every file carries SPDX headers — preserve them).

## Repository layout

- `bin/` — front-end launchers. `bin/qunex` (bash) is the main CLI entry point; it dispatches
  to language-specific implementations and to the Python `gmri` driver. Note: several Python
  entry points have **no `.py` extension** — `python/qx_utilities/gmri` and `bin/qunex*container*`.
  A codebase-wide rename or symbol sweep that globs `*.py` will silently miss them (and `.py`
  files outside `python/qx_utilities` such as `python/qx_registry*.py`); include them explicitly.
- `python/qx_utilities/` — Python implementation, the bulk of active development:
  - `general/` — core utilities, parsing, sessions, DICOM/BIDS/NIfTI, scheduler, `gmri` driver,
    and `log.py` (the suite-wide runlog; see **Command logging** below).
  - `processing/` — preprocessing workflows (`workflow.py`, `dwi.py`, `fs.py`, `fsl.py`, ...).
    `processing/core.py` holds the low-level report/run primitives (`run_external_for_file`,
    `check_run`, `check_for_file`, `check_for_files`, `use_or_skip_bold`) that `general/log/`
    wraps — these take the log object and write into it; they do not take or return a report
    string.
  - `hcp/`, `nhp/`, `qa/`, `templates/` — HCP pipelines, non-human-primate, QA, templates.
    In `hcp/`, each processing command lives in its own `hcp_<command>.py` file (e.g.
    `hcp_pre_freesurfer.py`, `hcp_fmri_volume.py`); shared code is in `hcp_utils.py` (option
    checks, BOLD/gdc parsing, denoising executors), `hcp_paths.py` (`get_hcp_paths`), `qc_hcp.py`
    (visual QC), `import_hcp.py`/`export_hcp.py`/`setup_hcp.py`. There is no `process_hcp.py`.
  - `qx_registry.py` / `qx_registry_build.py` — the command registry. Commands are discovered
    automatically from `.. qx_command:` blocks in python/matlab/bash docstrings; there is no
    hand-maintained command list. Add a command by writing its docstring block, then rebuild
    with `qunex build_qx_registry` (which regenerates `qx_commands.yaml`). `tests/test_registry_drift.py`
    fails if the committed `qx_commands.yaml` is stale — after adding/renaming/moving a command
    (or changing its docstring/path), rebuild and commit the yaml. Renaming a registered function
    changes its command name; preserve the old name via `aliases:` in the `qx_command` block.
- `python/tests/` — pytest suite (`test_data/` holds fixtures).
- `bash/qx_utilities/` — Bash implementations (DWI, FC, QC, turnkey, XNAT, ...).
- `matlab/` — `qx_mri`, `qx_utilities`, `qx_mice` (MATLAB/Octave functions).
- `r/qx_utilities/` — R scripts (movement/stats/fidl).
- `env/` — environment setup (`qunex_environment.sh` sets `TOOLS`, `QUNEXPATH`, `PYTHONPATH`, etc.).
- `qx_library/` — submodule with data, etc, seccomp profiles, MATLAB tests.

## Working style

- Make focused, minimal changes that solve the requested task. No broad refactors unless asked.
- Preserve existing behavior, CLI flags, and output formats unless a change is required.
- Match the style of nearby code in the file you edit. Keep code readable and testable.
- Never revert unrelated working-tree changes. Avoid renaming public commands/functions
  unless requested. Keep backward compatibility for user-facing CLI and pipeline behavior.

## Python

Size targets (tiered — exceed only for legacy code or urgent fixes; **call out and justify any
hard-cap breach in your final summary**):

- File: preferred ≤ 500 lines, hard cap ≤ 1000 lines.
- Function: preferred ≤ 50 lines, hard cap ≤ 100 lines. Split into helpers when practical.

Quality:

- Type hints for new public functions and complex helpers; concise docstrings for non-trivial
  public functions.
- Explicit error handling with actionable messages. Avoid hidden side effects and global state.
- Prefer `except Exception:` over a bare `except:` (a bare except also swallows KeyboardInterrupt).
- Keep imports clean and grouped. The package uses absolute `qx_utilities.*` imports
  (e.g. `import qx_utilities.general.core as gc`), introduced with the command registry —
  `pythonpath = python` is set in `pytest.ini` at the repository root. Do not add flat
  imports (`from general import core as gc`); there are none left in the tree.
- Before deleting a seemingly-unused function, confirm it is not a dynamic/external entrypoint:
  registered commands (a `.. qx_command:` docstring, called via the registry) and the
  `@qx_process` extension decorator in `general/extensions.py` (used by out-of-tree extensions
  loaded via `$QXEXTENSIONSPY`) look unused in-tree but must not be removed.

## Command logging (runlog vs comlog)

QuNex keeps two log layers. The **comlog** is the raw stdout/stderr of each external pipeline
call, written by `processing/core.py`. The **runlog** is the human-readable per-session summary a
command returns to `general/process.py`, which writes it to `Log-<command>-<timestamp>.log` and
prints it. `general/log/` owns the runlog:

- Build the runlog with a `SessionLog` (session/subject commands) or a `ReportLog` (per-BOLD /
  per-group executors and QC helpers), **not** by threading a local `r` string. Use the level
  methods (`log.step`/`log.detail`/`log.warning`/`log.error`), `log.pipeline_command(cmd)`, and
  the wrappers `log.run_external(...)`, `log.check_run(...)`, `log.check_for_file(...)`,
  `log.use_or_skip_bold(...)`, `log.link_or_copy(...)` — these hand the log to the `core.py`
  primitives, which write into it.
- `pc.ExternalFailed` carries the **error message alone**; everything that led up to it is
  already in the log. An `except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:`
  handler appends it with `log.raw(str(errormessage))` — never re-adopt a whole report.
- A command returns its **log object** — never a `(text, status)` pair. `general/process.py`
  writes it with `log.write_to(run)` and reads `log.status`, the **three-field**
  `(session_id, summary, failed)` triple derived on read. State the summary either with
  `SessionLog.finish(report, failed=..., pipeline=...)` / `log.result(report, failed, name)`
  (both return `self`, so `return log.finish(...)` is the usual form) or by assigning
  `log.report` / `log.failed` and `return log`. A study-level command need not name itself:
  a log with no `sid` is filed under the command name.
- `helper_that_builds_report(..., log)` should take the `log` and append in place, not take and
  return an `r` string. A **command** called as a step of another one takes the caller's log as
  `_log` and reports into it (`processing/fs.py`'s `check_for_freesurfer_data`): building a
  second log to copy across duplicates it in the comlog and hides its errors from the caller.
- A command making **more than one** external call opens **one comlog for all of them**:

  ```python
  with log.combined_comlog(options, "run_freesurfer_full_segmentation", thread=sinfo["id"]):
      ...                                   # every log.run_external(...) inside writes into it
  ```

  The block names the comlog after the command, attaches it for the whole body, counts the calls
  made inside, and closes it once — honouring `--log` at that one site instead of at every call.
  So a `log.run_external(...)` inside a block passes only what the call *is*: `thread=`,
  `remove=`, `task=`, `logfolder=` and `logtags=` describe a comlog being opened and are inert
  there. Nothing is opened under `--test`. External output never reaches the runlog: `trace()`
  writes to the comlog and never to the log's records, so the traffic is one way by construction.
  `hcp/qc_hcp.py` is the deliberate exception — its jobs run in a `ProcessPoolExecutor` and
  cannot share one open file, so its 11 sites keep per-call comlogs and `remove=True`.

## Comment style

- Use `#` for inline comments and `"""` for docstrings.
- Use lowercase text for inline comments.
- Use plain comment start, no dashes (# -) or arrows (# --->) unless part of a structured message.
- A module has exactly one leading `"""..."""` docstring. Put copyright/author lines in `#`
  comments after it, not in a second bare `"""..."""` string — a second string statement before
  the imports triggers E402 across the whole file.

## Linting and testing

Ruff is the default Python linter. At the end of Python changes, run and report:

```bash
ruff check python
```

Run tests from the `python` folder (testpaths and pythonpath are configured in `pytest.ini`):

```bash
cd python && pytest                       # full suite
cd python && pytest tests/test_dicom.py   # single file
cd python && pytest -k <target>           # targeted
```

Note: `pytest.ini` sets `filterwarnings = error`, so warnings fail tests (DeprecationWarning is
ignored). A `SyntaxWarning` (e.g. an invalid escape like `\_` in a docstring) will fail collection
once the module recompiles — fix these (`\\_` or raw strings), don't ignore them. Add or update
tests for bug fixes and behavior changes when feasible. If tests are skipped (slow / data /
dependency unavailable), explicitly state what was not run.

The full suite runs ~6 minutes; run it in the background and keep working. `ruff check python`
should be **clean** — the tree is at zero findings; keep it there.

Dry-run testing: processing commands support `run="test"` (the `--test` flag), which resolves
inputs, builds the pipeline command and reports what it *would* do without executing anything.
This is the cheap, dependency-free way to test option handling and the runlog. `tests/utils.py`
provides `default_options(**overrides)` (builds the full option surface from `process.arglist`,
the same table the CLI parses) and `build_hcp_session(root)` (a minimal session tree). See
`tests/test_hcp_dryrun.py` for the per-command pattern and `tests/test_log.py` for the log class.

Refactors that must preserve behavior: verify with a before/after oracle — run the pre-change and
post-change code on the same fixture (in `--test` mode) and require identical normalized output
(strip timestamps/tmp paths/traceback line numbers). This caught real regressions during the
logging refactor that the suite alone did not.

Do not fix only issues created by you — fix everything you notice. Fix pre-existing issues as well.

## Multi-language guardrails

- Bash: keep scripts POSIX-friendly unless the file already depends on Bash-specific features.
- MATLAB/R: preserve existing function signatures and I/O conventions.
- Do not introduce new runtime dependencies without clear need.

## Final response checklist

Include in your summary: what changed (brief); validation performed (`ruff` + tests); any
line-count/function-size exceptions with rationale; and follow-up suggestions only when useful.

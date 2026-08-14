# CLAUDE.md

Guidance for Claude Code when working in the QuNex repository.

## What this is

QuNex (Quantitative Neuroimaging Environment & ToolboX) is a multi-language framework
for organizing, preprocessing, QA-ing, and analyzing neuroimaging data. The codebase is
mixed-language (Python, Bash, MATLAB/Octave) and historically inconsistent. **Prefer
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
    and the `log/` package (the suite-wide runlog — `report.py`, `context.py`, `settings.py`;
    see **Command logging** below).
  - `processing/` — preprocessing workflows (`workflow.py`, `dwi.py`, `fs.py`, `fsl.py`, ...).
    `processing/core.py` holds the low-level report/run primitives (`run_external_for_file`,
    `check_run`, `check_for_file`, `check_for_files`, `use_or_skip_bold`, and the comlog
    lifecycle `open_comlog`/`close_log`/`combined_comlog`) — these take the log object as
    `_log` and write into it; they do not take or return a report string. They are **not**
    wrapped by `general/log/`: the log package is a leaf (see **Command logging**).
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
- `env/` — environment setup (`qunex_environment.sh` sets `TOOLS`, `QUNEXPATH`, `PYTHONPATH`, etc.).
- `qx_library/` — submodule with data, etc, seccomp profiles, MATLAB tests.

## Sister repos

- ../qunex.wiki - Core QuNex Wiki (documentation and tutorials).
- ../qunexsdk - QuNex SDK with additional dev related code (acceptance testing, container building, devops).
- ../qunexsdk-wiki - QuNex SDK Wiki (SDK Wiki).

Assure that relevant content in sister repos is always updated and brought up to speed when making code changes. This is especially important with larger/architectural changes.

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
  methods (`log.step`/`log.detail`/`log.warning`/`log.error`), `log.action(word, message, run)`
  for a line that has to read as "Test running ..." under `--test`, and
  `log.pipeline_command(cmd)`.
- **`general/log/` is a leaf: it imports nothing from the tree but `general/exceptions` and
  `general/parsing`, and everything else imports it.** So the run/check helpers are called where
  they live, with the log as the **last, keyword-only** argument:

  ```python
  status = pc.check_for_file(f["t1"], "present", "missing", _log=log)
  gc.link_or_copy(source, target, _log=log)
  ```

  `pc.run_external_for_file`, `pc.check_run`, `pc.check_for_file`, `pc.check_for_files`,
  `pc.use_or_skip_bold` and `gc.link_or_copy` all take `*, _log=None`. `tests/test_log_is_a_leaf.py`
  fails if an import back into the tree reappears anywhere in the package, function bodies
  included — that is how thirteen lazy imports accumulated before.
- **A log parameter is named `_log`, never `log`.** The plain name is taken: `process.arglist`
  carries `["log", "keep", str]`, so `options["log"]` is the comlog retention setting. The name
  says what the parameter is; the default says whether it is required — a private executor that
  is meaningless without a log keeps `_log` as a required positional.
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
- `helper_that_builds_report(..., _log)` should take the log and append in place, not take and
  return an `r` string. A **command** called as a step of another one takes the caller's log as
  `_log` and reports into it (`processing/fs.py`'s `check_for_freesurfer_data`): building a
  second log to copy across duplicates it in the comlog and hides its errors from the caller.
- A command making **more than one** external call opens **one comlog for all of them**:

  ```python
  with pc.combined_comlog(
      log, options, "run_freesurfer_full_segmentation", thread=sinfo["id"]
  ):
      ...  # every pc.run_external_for_file(..., _log=log) inside
  ```

  The block names the comlog after the command, attaches it to the log for the whole body, counts
  the calls made inside, and closes it once — honouring `--log` at that one site instead of at
  every call. A call inside the block picks the comlog up off the log it is given, so it passes
  only what the call *is*: `thread=`, `remove=`, `task=`, `logfolder=` and `logtags=` describe a
  comlog being opened and are inert there. Nothing is opened under `--test`. External output never reaches the runlog: `trace()`
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
ruff check python bin/qunex_container
```

(`bin/qunex_container` is named explicitly because it is python with no `.py` extension, so
ruff's own discovery skips it. It is also generated — see **Generated files** below.)

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

**A development shell has the QuNex environment sourced; `.github/workflows/tests.yml` does
not.** It runs the suite on a bare checkout, so anything reading `TOOLS`, `QUNEXPATH`,
`QUNEXREPO` or another suite variable passes locally and fails there. Check with the workflow's
own command before pushing:

```bash
env -u TOOLS -u QUNEXPATH -u QUNEXREPO pytest --ignore=python/tests/test_fc_functions.py -q
```

(`test_fc_functions` needs the `qx_library` submodule the workflow does not check out; tests
needing external binaries skip themselves. The lint job pins a ruff version — match it.) When
this catches something, **fix what reads the variable rather than adding a fixture that sets
it**: a fixture turns CI green and leaves the failure waiting for anyone who imports QuNex
without the environment. `general/log/report.py`'s `get_qunex_version` is the pattern — it
resolves `VERSION.md` from its own source tree, falls back to `$TOOLS/$QUNEXREPO`, and returns
`unknown` rather than raising, because that string heads every log file. Where a test genuinely
needs a variable, it sets it itself: `tests/test_registry_drift.py` and
`tests/test_gmri_dispatch.py` both point `QUNEXPATH` at the repository root.

Dry-run testing: processing commands support `run="test"` (the `--test` flag), which resolves
inputs, builds the pipeline command and reports what it *would* do without executing anything.
This is the cheap, dependency-free way to test option handling and the runlog. `tests/utils.py`
provides `default_options(**overrides)` (builds the full option surface from `process.arglist`,
the same table the CLI parses) and `build_hcp_session(root)` (a minimal session tree). See
`tests/test_hcp_dryrun.py` for the per-command pattern and `tests/test_log.py` for the log class.

**`--test` is a contract each command has to keep, and nothing enforces it.** There is no shared
gate: a command that never reads `options["run"]` does the work regardless of the flag, and both
`processing/fs.py` (4 commands) and `processing/workflow.py` (5) shipped that way — copying files,
invoking FSL/R/MATLAB, and in two cases deleting existing outputs a dry run then never
regenerated. When writing or reviewing a processing command:

- guard every side effect — external calls, copies and links, deletions, `os.makedirs`, image
  writes, and a file lock, which writes a `.lock`;
- **report what would have happened** rather than falling silent: `... test, not run: <command>`,
  `test, not copied:`, `test, not removed:`. A dry run that guards its work but says nothing is
  not worth running. `fs.py`'s `_run_external`/`_copy` and `workflow.py`'s
  `_run_external`/`_link_or_copy`/`_remove` are the helpers that spell this once per file;
- watch for a check that reads what the guarded step would have written. Both files had one, and
  in each the dry run reported a failure and returned before naming the tools it would have run —
  the check belongs inside the branch that does the work.

`tests/test_fs_dryrun.py` and `tests/test_workflow_dryrun.py` are the pattern: nothing executed,
no file written/changed/removed, and the tool still named. Note they compare **files only** —
`pc.get_session_folders` creates the session skeleton whenever it resolves paths, for every
processing command in the tree, and that is out of scope for a per-command dry-run fix.

Refactors that must preserve behavior: verify with a before/after oracle — run the pre-change and
post-change code on the same fixture (in `--test` mode) and require identical normalized output
(strip timestamps/tmp paths/traceback line numbers). This caught real regressions during the
logging refactor that the suite alone did not.

Do not fix only issues created by you — fix everything you notice. Fix pre-existing issues as well.

## Generated files

Two files are generated from the source around them and committed alongside it. Rebuild and
commit both when you touch what they are built from:

```bash
qunex build_qx_registry     # qx_commands.yaml, from the qx_command docstrings
qunex build_qx_container    # bin/qunex_container, from general/batch_io.py and VERSION.md
```

- `qx_commands.yaml` — the command registry. Rebuilding is idempotent: `generated_at` is the one
  field that moves on every build, and `write_registry_file` keeps the committed timestamp when
  nothing else changed, so a no-op rebuild leaves no diff.
- `bin/qunex_container` — the launcher that runs on the login node, outside the container, in the
  host python. It can not import QuNex, so `qx_container_build.py` splices `general/batch_io.py`
  into it. The splice writes three things: the `# Version <x> [QIO]` line in the header, from
  `VERSION.md`; the imports batch_io needs, **merged into the container's own import block** at
  the top, which is what keeps the file free of E402/F811; and the module body, between the
  `BEGIN GENERATED`/`END GENERATED` markers. Only that body region is off limits by hand — the
  import block is ordinary code the command adds to and never prunes, so an import that stops
  being needed is removed by deleting it there.

`.github/workflows/generated.yml` rebuilds both on every pull request and pushes the result back
to the branch (a fork's token is read only, so there it reports and fails instead).
`tests/test_registry_drift.py` and `tests/test_container_drift.py` are the backstop.

## Multi-language guardrails

- Bash: keep scripts POSIX-friendly unless the file already depends on Bash-specific features.
- MATLAB: preserve existing function signatures and I/O conventions.
- Do not introduce new runtime dependencies without clear need.
- There is no R in the tree. `r-base` stays in the container for ICA-FIX, and `run_recipe`
  still dispatches user-supplied `.R` scripts, but no QuNex code is written in R.

## Final response checklist

Include in your summary: what changed (brief); validation performed (`ruff` + tests); any
line-count/function-size exceptions with rationale; and follow-up suggestions only when useful.

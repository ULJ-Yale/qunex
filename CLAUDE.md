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
  to language-specific implementations and to the Python `gmri` driver.
- `python/qx_utilities/` — Python implementation, the bulk of active development:
  - `general/` — core utilities, parsing, sessions, DICOM/BIDS/NIfTI, scheduler, `gmri` driver.
  - `processing/` — preprocessing workflows (`workflow.py`, `dwi.py`, `fs.py`, `fsl.py`, ...).
  - `hcp/`, `nhp/`, `qa/`, `templates/` — HCP pipelines, non-human-primate, QA, templates.
  - `qx_registry.py` / `qx_registry_build.py` — the command registry. Commands are discovered
    automatically from `.. qx_command:` blocks in python/matlab/bash docstrings; there is no
    hand-maintained command list. Add a command by writing its docstring block, then rebuild
    with `qunex build_qx_registry` (which regenerates `qx_commands.yaml`).
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
- Keep imports clean and grouped. Note: the package uses flat imports (e.g.
  `from general import core as gc`) — `pythonpath = python/qx_utilities` is set in `pytest.ini`.

## Comment style

- Use `#` for inline comments and `"""` for docstrings.
- Use lowercase text for inline comments.
- Use plain comment start, no dashes (# -) or arrows (# --->) unless part of a structured message.

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
ignored). Add or update tests for bug fixes and behavior changes when feasible. If tests are
skipped (slow / data / dependency unavailable), explicitly state what was not run.

## Multi-language guardrails

- Bash: keep scripts POSIX-friendly unless the file already depends on Bash-specific features.
- MATLAB/R: preserve existing function signatures and I/O conventions.
- Do not introduce new runtime dependencies without clear need.

## Final response checklist

Include in your summary: what changed (brief); validation performed (`ruff` + tests); any
line-count/function-size exceptions with rationale; and follow-up suggestions only when useful.

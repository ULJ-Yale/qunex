# Copilot Instructions for QuNex Repo

This repository is mixed-language (Python, Bash, MATLAB, R) and historically inconsistent.
Prefer pragmatic improvements over strict rewrites.

## Core Working Style

- Make focused, minimal changes that solve the requested task.
- Do not perform broad refactors unless explicitly requested.
- Preserve existing behavior, CLI flags, and output formats unless a change is required.
- Match the style of nearby code in the file you edit.
- Keep code readable and testable; avoid clever one-liners.

## Strictness Policy (Messy-Repo Mode)

Use this tiered policy:

- Preferred target: follow all guide limits below.
- Allowed exception: exceed preferred limits when touching legacy code or urgent bugfixes.
- Hard cap: do not exceed hard caps without explicitly stating why in your final summary.

## Python Size Limits

For new or significantly rewritten Python code:

- File length preferred: <= 500 lines
- File length hard cap: <= 1000 lines
- Function length preferred: <= 50 lines
- Function length hard cap: <= 100 lines

If a function/file must exceed preferred limits, split into helper functions where practical.
If hard caps are exceeded, call it out and justify.

## Python Quality Rules

- Use type hints for new public functions and complex internal helpers.
- Add concise docstrings for non-trivial public functions.
- Prefer explicit error handling with actionable messages.
- Avoid hidden side effects and global state changes.
- Keep imports clean and grouped.

## Linting and Validation

Ruff is the default linter for Python.

At the end of Python changes, always run a linter check and report result:

```bash
ruff check python
```

If only a specific file was changed, you may run Ruff on that file first, but still prefer final full check when feasible.

When tests are relevant, run targeted tests first, then broader tests if needed:

```bash
pytest python/tests -k <target>
```

## Testing Guidance

- Add or update tests for bug fixes and behavior changes when feasible.
- Prefer targeted tests close to the changed functionality.
- If tests are skipped (slow/unavailable data/dependency), explicitly state what was not run.

## Multi-Language Guardrails

- Bash: keep scripts POSIX-friendly unless file already depends on Bash-specific features.
- MATLAB/R: preserve existing function signatures and I/O conventions.
- Do not introduce new runtime dependencies without clear need.

## Safe Edit Rules

- Never revert unrelated changes in the working tree.
- Avoid renaming public commands/functions unless requested.
- Keep backward compatibility for user-facing CLI and pipeline behavior.

## Output Expectations for Copilot

In final responses, include:

- What changed (brief)
- Validation performed (`ruff` and tests)
- Any limit exceptions (line-count/function-size) and rationale
- Follow-up suggestions only when useful

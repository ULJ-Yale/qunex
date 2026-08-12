#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Guard against a stale committed ``qx_commands.yaml``.

A merge once left ``run_recipe`` and ``check_study`` out of the committed
registry (the yaml pointed at a moved/renamed function). This test rebuilds the
core registry from the current source tree and fails if it disagrees with the
committed ``qx_commands.yaml`` — the fix is always to run
``qunex build_qx_registry`` and commit the result.
"""

from pathlib import Path

import yaml

import qx_registry_build

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_committed_registry_matches_rebuild(tmp_path, monkeypatch):
    committed_path = REPO_ROOT / "qx_commands.yaml"
    assert committed_path.exists(), f"missing {committed_path}"

    # build core (python + matlab + bash) from this tree into a temp file
    monkeypatch.setenv("QUNEXPATH", str(REPO_ROOT))
    out = tmp_path / "qx_commands.yaml"
    qx_registry_build.build_qx_registry(core_registry_yaml=out, build_extensions=False)

    committed = {c["name"]: c for c in yaml.safe_load(committed_path.read_text())["commands"]}
    rebuilt = {c["name"]: c for c in yaml.safe_load(out.read_text())["commands"]}

    missing = sorted(set(committed) - set(rebuilt))
    added = sorted(set(rebuilt) - set(committed))
    changed = sorted(n for n in set(committed) & set(rebuilt) if committed[n] != rebuilt[n])

    assert not (missing or added or changed), (
        "qx_commands.yaml is out of date — run `qunex build_qx_registry` and commit.\n"
        f"  missing from rebuild: {missing}\n"
        f"  new in rebuild: {added}\n"
        f"  changed: {changed}"
    )


def test_no_registered_argument_starts_with_an_underscore():
    """
    The underscore rule, which is what makes ``_log`` unsettable.

    A command opts into a report log by declaring ``_log=None``, and
    ``qx_registry_build`` drops underscore-prefixed signature parameters so
    ``Command.has_arg`` stays false for them. Were one to reach the registry it
    would become a CLI parameter taking a ``ReportLog`` and receiving a string.
    """
    commands = yaml.safe_load((REPO_ROOT / "qx_commands.yaml").read_text())["commands"]

    leaked = [
        "%s --%s" % (c["name"], a["name"])
        for c in commands
        for a in (c.get("args") or [])
        if a["name"].startswith("_")
    ]

    assert not leaked, "underscore-prefixed parameters reached the registry: %s" % leaked

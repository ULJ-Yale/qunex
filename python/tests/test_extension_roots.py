#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Where QuNex looks for extensions, and what an extension command resolves against.

Two defects are pinned here. The folders variable was spelled
`QUNEXEXTENSIONSFOLDERS` in the shell and `QUNEXEXTENSIONFOLDERS` here, so a root
named in only one of them was half registered. And a bash command carried a path
relative to the registry it came from, which nothing resolved against anything
but `$QUNEXPATH`, so an extension's scripts were looked for in the core install.
"""

from pathlib import Path

import pytest

import qx_registry
import qx_utilities.general.run_bash as gb


def _registry_yaml(folder: Path, *, source_id: str, name: str, path: str) -> Path:
    """A one-command registry file at the root of what it describes."""
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / "qx_commands.yaml"
    out.write_text(
        "version: 1\n"
        "generated_at: '2026-01-01T00:00:00Z'\n"
        "source:\n"
        f"    id: {source_id}\n"
        "commands:\n"
        f"    -   name: {name}\n"
        f"        path: {path}\n"
        "        language: bash\n"
        "        type: utility\n"
        f"        origin: {source_id}\n",
        encoding="utf-8",
    )
    return out


@pytest.fixture
def clean_env(monkeypatch):
    """No suite variables, no warnings remembered from another test."""
    for name in (
        "QUNEXPATH",
        "TOOLS",
        qx_registry.EXTENSION_FOLDERS_ENV,
        qx_registry.EXTENSION_FOLDERS_ENV_DEPRECATED,
    ):
        monkeypatch.delenv(name, raising=False)
    qx_registry._warned.clear()
    yield
    qx_registry._warned.clear()


# ==============================================================================
#                                                          the search roots (E1)


def test_canonical_spelling_is_read(clean_env, monkeypatch, tmp_path):
    root = tmp_path / "extensions"
    root.mkdir()
    monkeypatch.setenv(qx_registry.EXTENSION_FOLDERS_ENV, str(root))

    assert qx_registry.extension_search_roots() == [root.resolve()]


def test_deprecated_spelling_is_read_and_says_so(clean_env, monkeypatch, tmp_path, capsys):
    root = tmp_path / "extensions"
    root.mkdir()
    monkeypatch.setenv(qx_registry.EXTENSION_FOLDERS_ENV_DEPRECATED, str(root))

    assert qx_registry.extension_search_roots() == [root.resolve()]

    captured = capsys.readouterr()
    assert qx_registry.EXTENSION_FOLDERS_ENV_DEPRECATED in captured.err
    assert qx_registry.EXTENSION_FOLDERS_ENV in captured.err
    # `bin/qunex.sh` reads `gmri -available` off stdout as its routing table
    assert captured.out == ""


def test_both_spellings_give_one_root(clean_env, monkeypatch, tmp_path):
    """How an installation migrates: set the new name beside the old one."""
    root = tmp_path / "extensions"
    root.mkdir()
    monkeypatch.setenv(qx_registry.EXTENSION_FOLDERS_ENV, str(root))
    monkeypatch.setenv(qx_registry.EXTENSION_FOLDERS_ENV_DEPRECATED, str(root))

    assert qx_registry.extension_search_roots() == [root.resolve()]


def test_a_root_that_is_not_there_warns_and_is_skipped(clean_env, monkeypatch, tmp_path, capsys):
    there = tmp_path / "extensions"
    there.mkdir()
    monkeypatch.setenv(
        qx_registry.EXTENSION_FOLDERS_ENV, "%s:%s" % (tmp_path / "nowhere", there)
    )

    assert qx_registry.extension_search_roots() == [there.resolve()]
    assert "nowhere" in capsys.readouterr().err


def test_the_fixed_roots_come_first_and_do_not_warn(clean_env, monkeypatch, tmp_path, capsys):
    """$QUNEXPATH and $TOOLS are absent on most installations; that is not news."""
    monkeypatch.setenv("QUNEXPATH", str(tmp_path / "qunex"))
    monkeypatch.setenv("TOOLS", str(tmp_path / "tools"))

    roots = qx_registry.extension_search_roots()

    assert roots == [
        (tmp_path / "qunex" / "qx_extensions"),
        (tmp_path / "tools" / "qx_extensions"),
    ]
    assert capsys.readouterr().err == ""


# ==============================================================================
#                                            the root a command resolves against


def test_a_loaded_command_knows_the_folder_it_came_from(tmp_path):
    ext = tmp_path / "qx_example"
    yaml_path = _registry_yaml(
        ext, source_id="extension:example", name="example_bash_greet", path="greet.sh"
    )

    registry = qx_registry.load_registry_yaml(yaml_path)

    assert registry.commands[0].root == str(ext)


def test_core_and_extension_records_keep_their_own_roots(clean_env, monkeypatch, tmp_path):
    core = tmp_path / "qunex"
    core_yaml = _registry_yaml(core, source_id="core", name="core_cmd", path="core.sh")
    ext = tmp_path / "extensions" / "qx_example"
    _registry_yaml(ext, source_id="extension:example", name="ext_cmd", path="ext.sh")

    monkeypatch.setenv(qx_registry.EXTENSION_FOLDERS_ENV, str(tmp_path / "extensions"))
    merged, _tokens = qx_registry.load_qx_registry(core_registry_path=core_yaml)

    roots = {c.name: c.root for c in merged.commands}
    assert roots == {"core_cmd": str(core), "ext_cmd": str(ext.resolve())}


# ==============================================================================
#                                              the bash script it resolves (E2)


def test_a_bash_command_is_looked_for_under_its_own_root(tmp_path, capsys, monkeypatch):
    """
    The script is not written, so `run` reports it missing and returns before
    running anything -- the path in that message is what is under test.
    """
    monkeypatch.setenv("QUNEXPATH", str(tmp_path / "qunex"))
    ext = tmp_path / "qx_example"
    yaml_path = _registry_yaml(
        ext, source_id="extension:example", name="example_bash_greet", path="greet.sh"
    )
    command = qx_registry.load_registry_yaml(yaml_path).commands[0]

    assert gb.run(command, {}) == 1

    reported = capsys.readouterr().out
    assert str(ext / "bash" / "greet.sh") in reported
    assert str(tmp_path / "qunex") not in reported


def test_a_command_with_no_root_still_falls_back_to_qunexpath(tmp_path, capsys, monkeypatch):
    """A record built by hand rather than loaded -- which only a test does."""
    monkeypatch.setenv("QUNEXPATH", str(tmp_path / "qunex"))
    command = qx_registry.CommandInfo(
        name="core_bash_command",
        aliases=(),
        path="core.sh",
        language="bash",
        call=None,
        description=None,
        type="utility",
        args=(),
        options=(),
        returns=(),
        origin="core",
    )

    assert gb.run(command, {}) == 1
    assert str(tmp_path / "qunex" / "bash" / "core.sh") in capsys.readouterr().out

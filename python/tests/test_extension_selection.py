#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Choosing which extensions a build covers.

`build_qx_registry` used to build every extension it could see, in every root it
could see it in. Naming one is what an extension author wants -- and what a
misspelt name does matters as much: a selection that quietly matched nothing
would look exactly like a build that worked.
"""

from pathlib import Path

import pytest

import qx_registry
import qx_registry_build as qb
from qx_utilities.general import exceptions as ge

from .test_extension_roots import _registry_yaml


def _extension(root: Path, name: str) -> Path:
    """An extension folder with one indexable bash command in it."""
    ext = root / f"qx_{name}"
    (ext / "bash").mkdir(parents=True, exist_ok=True)
    (ext / "bash" / f"{name}_greet.sh").write_text(
        "#!/bin/bash\n"
        "usage() {\n"
        "    cat << EOF\n"
        f"``{name}_greet``\n"
        "\n"
        "..  qx_command:\n"
        "    type: utility\n"
        "EOF\n"
        "}\n",
        encoding="utf-8",
    )
    return ext


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
#                                                            what gets selected


def _folders(tmp_path, *names):
    root = tmp_path / "extensions"
    root.mkdir(exist_ok=True)
    return [_extension(root, name) for name in names]


def test_nothing_named_is_every_extension(tmp_path):
    folders = _folders(tmp_path, "one", "two")

    assert qb._select_extensions(None, folders) == folders
    assert qb._select_extensions("", folders) == folders


def test_all_is_every_extension(tmp_path):
    folders = _folders(tmp_path, "one", "two")

    assert qb._select_extensions("all", folders) == folders
    assert qb._select_extensions("ALL", folders) == folders


def test_all_among_others_is_still_every_extension(tmp_path):
    """`all,one` asks for everything; reading it as a name would be perverse."""
    folders = _folders(tmp_path, "one", "two")

    assert qb._select_extensions("one,all", folders) == folders


def test_a_bare_name_selects_one(tmp_path):
    one, two = _folders(tmp_path, "one", "two")

    assert qb._select_extensions("one", [one, two]) == [one]


def test_the_qx_prefix_is_accepted(tmp_path):
    """The folder is called `qx_one`, so that is what a person will type."""
    one, two = _folders(tmp_path, "one", "two")

    assert qb._select_extensions("qx_one", [one, two]) == [one]


def test_several_names_select_several(tmp_path):
    one, two, three = _folders(tmp_path, "one", "two", "three")

    assert qb._select_extensions("one, qx_three", [one, two, three]) == [one, three]


def test_a_name_repeated_selects_it_once(tmp_path):
    one, two = _folders(tmp_path, "one", "two")

    assert qb._select_extensions("one,qx_one", [one, two]) == [one]


def test_an_unknown_name_is_an_error_listing_what_was_found(tmp_path):
    one, two = _folders(tmp_path, "one", "two")

    with pytest.raises(ge.CommandFailed) as raised:
        qb._select_extensions("thre", [one, two])

    # `report` is error plus hints, which is what the error formatter prints;
    # `str()` carries only the first line of it
    reported = "\n".join(raised.value.report)
    assert "thre" in reported
    # the point of the error: the name that was meant is in front of the user
    assert "one" in reported and "two" in reported


def test_an_unknown_name_with_no_extensions_at_all_still_reports(tmp_path):
    with pytest.raises(ge.CommandFailed) as raised:
        qb._select_extensions("one", [])

    assert "none" in "\n".join(raised.value.report)


# ==============================================================================
#                                                     and through the build (E4)


def _core(tmp_path):
    """A core install with a registry, which building extensions alone reads."""
    core = tmp_path / "qunex"
    _registry_yaml(core, source_id="core", name="check_study", path="check.sh")
    return core


def test_the_build_covers_only_the_named_extension(clean_env, monkeypatch, tmp_path):
    core = _core(tmp_path)
    root = tmp_path / "extensions"
    root.mkdir()
    one = _extension(root, "one")
    two = _extension(root, "two")

    monkeypatch.setenv("QUNEXPATH", str(core))
    monkeypatch.setenv(qx_registry.EXTENSION_FOLDERS_ENV, str(root))

    _, built = qb.build_qx_registry(build_core=False, extensions="one")

    assert [ext_id for ext_id, _ in built] == ["extension:one"]
    assert (one / "qx_commands.yaml").exists()
    assert not (two / "qx_commands.yaml").exists()


def test_the_build_without_a_selection_covers_everything(clean_env, monkeypatch, tmp_path):
    """`build_qx_registry` keeps building every extension when told nothing."""
    core = _core(tmp_path)
    root = tmp_path / "extensions"
    root.mkdir()
    one = _extension(root, "one")
    two = _extension(root, "two")

    monkeypatch.setenv("QUNEXPATH", str(core))
    monkeypatch.setenv(qx_registry.EXTENSION_FOLDERS_ENV, str(root))

    _, built = qb.build_qx_registry(build_core=False)

    assert [ext_id for ext_id, _ in built] == ["extension:one", "extension:two"]
    assert (one / "qx_commands.yaml").exists()
    assert (two / "qx_commands.yaml").exists()


def test_an_extension_in_two_roots_is_built_where_it_will_be_loaded(
    clean_env, monkeypatch, tmp_path
):
    """
    The runtime resolves a duplicated extension to the last root; the build now
    agrees with it. Walking the roots wrote a registry into both copies, and the
    one under the earlier root was never going to be read.
    """
    core = _core(tmp_path)
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    shadowed = _extension(first, "one")
    winning = _extension(second, "one")

    monkeypatch.setenv("QUNEXPATH", str(core))
    monkeypatch.setenv(
        qx_registry.EXTENSION_FOLDERS_ENV, "%s:%s" % (first, second)
    )

    _, built = qb.build_qx_registry(build_core=False)

    assert [ext_id for ext_id, _ in built] == ["extension:one"]
    assert (winning / "qx_commands.yaml").exists()
    assert not (shadowed / "qx_commands.yaml").exists()


def test_an_unknown_name_stops_the_build(clean_env, monkeypatch, tmp_path):
    core = _core(tmp_path)
    root = tmp_path / "extensions"
    root.mkdir()
    one = _extension(root, "one")

    monkeypatch.setenv("QUNEXPATH", str(core))
    monkeypatch.setenv(qx_registry.EXTENSION_FOLDERS_ENV, str(root))

    with pytest.raises(ge.CommandFailed):
        qb.build_qx_registry(build_core=False, extensions="tow")

    assert not (one / "qx_commands.yaml").exists()


# ==============================================================================
#                                              the command an author is given


def test_no_selection_lists_and_refuses_to_build(clean_env, monkeypatch, tmp_path, capsys):
    """
    The listing is the guidance, and the non-zero exit is for the script that
    meant to build: silently doing nothing would surface much later, as
    `Requested command is not supported`, a long way from its cause.
    """
    core = _core(tmp_path)
    root = tmp_path / "extensions"
    root.mkdir()
    one = _extension(root, "one")

    monkeypatch.setenv("QUNEXPATH", str(core))
    monkeypatch.setenv(qx_registry.EXTENSION_FOLDERS_ENV, str(root))

    with pytest.raises(ge.CommandFailed):
        qb.build_qx_extensions()

    out = capsys.readouterr().out
    assert "qx_one" in out
    assert "no registry yet" in out
    assert "--extensions=all" in out
    assert not (one / "qx_commands.yaml").exists()


def test_check_lists_and_is_not_a_failure(clean_env, monkeypatch, tmp_path, capsys):
    """`check` is a question that was answered, so it is a clean return."""
    core = _core(tmp_path)
    root = tmp_path / "extensions"
    root.mkdir()
    one = _extension(root, "one")

    monkeypatch.setenv("QUNEXPATH", str(core))
    monkeypatch.setenv(qx_registry.EXTENSION_FOLDERS_ENV, str(root))

    assert qb.build_qx_extensions(extensions="check") == (None, [])

    assert "qx_one" in capsys.readouterr().out
    assert not (one / "qx_commands.yaml").exists()


def test_the_listing_says_which_extensions_are_already_built(
    clean_env, monkeypatch, tmp_path, capsys
):
    core = _core(tmp_path)
    root = tmp_path / "extensions"
    root.mkdir()
    _extension(root, "built")
    _extension(root, "fresh")

    monkeypatch.setenv("QUNEXPATH", str(core))
    monkeypatch.setenv(qx_registry.EXTENSION_FOLDERS_ENV, str(root))

    qb.build_qx_extensions(extensions="built")
    capsys.readouterr()

    qb.build_qx_extensions(extensions="check")

    listed = {
        line.split()[0]: line
        for line in capsys.readouterr().out.split("\n")
        if line.startswith("    qx_")
    }
    assert "registry built" in listed["qx_built"]
    assert "no registry yet" in listed["qx_fresh"]


def test_no_extensions_at_all_says_where_qunex_looked(
    clean_env, monkeypatch, tmp_path, capsys
):
    """
    The mistake this catches: naming the extension itself rather than the
    folder holding it, which leaves QuNex looking at a root with nothing in it.
    """
    core = _core(tmp_path)
    empty = tmp_path / "extensions"
    empty.mkdir()

    monkeypatch.setenv("QUNEXPATH", str(core))
    monkeypatch.setenv(qx_registry.EXTENSION_FOLDERS_ENV, str(empty))

    with pytest.raises(ge.CommandFailed):
        qb.build_qx_extensions()

    out = capsys.readouterr().out
    assert "No extensions found" in out
    assert qx_registry.EXTENSION_FOLDERS_ENV in out


def test_building_extensions_leaves_the_core_registry_alone(
    clean_env, monkeypatch, tmp_path
):
    core = _core(tmp_path)
    core_registry = core / "qx_commands.yaml"
    before = core_registry.read_text()

    root = tmp_path / "extensions"
    root.mkdir()
    _extension(root, "one")

    monkeypatch.setenv("QUNEXPATH", str(core))
    monkeypatch.setenv(qx_registry.EXTENSION_FOLDERS_ENV, str(root))

    qb.build_qx_extensions(extensions="all")

    assert core_registry.read_text() == before

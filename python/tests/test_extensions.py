#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
What an extension declares, how its commands are reached, and what a run says
about where its command came from.

Where extensions are searched for, and what a command resolves its files
against, are in `test_extension_roots.py`.
"""

import sys

import pytest

import qx_registry
import qx_utilities.general.commands_support as gcs
import qx_utilities.general.extensions as ge
import qx_utilities.general.process as gp

from .test_extension_roots import _registry_yaml


# ==============================================================================
#                          the python folder reaches sys.path without qx_modules


@pytest.fixture
def restore_sys_path():
    """`load_extensions` appends to `sys.path` and never takes anything off."""
    before = list(sys.path)
    yield
    sys.path[:] = before


def test_the_python_folder_is_added_without_qx_modules(
    restore_sys_path, monkeypatch, tmp_path
):
    """
    A python command's registry path is dotted relative to this folder and
    nothing else ever adds it, so gating it on `qx_modules` left an extension
    whose commands were listed and dispatched and then failed to import.
    """
    py = tmp_path / "qx_example" / "python"
    py.mkdir(parents=True)
    monkeypatch.setenv("QXEXTENSIONSPY", str(py))

    ge.load_extensions()

    assert str(py) in sys.path


def test_qx_modules_still_imports_what_it_lists(restore_sys_path, monkeypatch, tmp_path):
    py = tmp_path / "qx_example" / "python"
    py.mkdir(parents=True)
    (py / "qx_example_declarations.py").write_text(
        "arglist = [['example_declared', 'yes', str]]\n", encoding="utf-8"
    )
    (py / "qx_modules").write_text("# a comment\n\nqx_example_declarations\n", encoding="utf-8")
    monkeypatch.setenv("QXEXTENSIONSPY", str(py))
    monkeypatch.setattr(ge, "module_names", [])
    monkeypatch.setattr(ge, "modules", {})

    ge.load_extensions()

    assert ge.compile_list("arglist") == [["example_declared", "yes", str]]


# ==============================================================================
#                                                    what an arglist entry says


def test_a_four_element_entry_gets_its_default_and_its_converter(monkeypatch):
    """
    The form the extension documentation teaches, with a description last.
    Reading three-element entries only left a parameter declared this way with
    no default and no type at all, which a command then read as a `KeyError`.
    """
    monkeypatch.setattr(
        gp, "arglist", gp.arglist + [["example_times", "2", int, "How many times."]]
    )

    options, sources, _stated = gp.merge_options("example_hello", {})

    assert options["example_times"] == 2
    assert sources["example_times"] == "default"


def test_a_three_element_entry_is_unchanged(monkeypatch):
    monkeypatch.setattr(gp, "arglist", gp.arglist + [["example_times", "3", int]])

    options, _sources, _stated = gp.merge_options("example_hello", {})

    assert options["example_times"] == 3


def test_a_converter_that_can_not_be_called_is_reported_and_skipped(monkeypatch, capsys):
    """
    This runs over the whole arglist on every invocation of every command, so a
    declaration QuNex can not honour has to cost one line rather than the run.
    A parameter annotation reaching here as the converter is how it happens.
    """
    monkeypatch.setattr(
        gp, "arglist", gp.arglist + [["example_annotated", "raw", "int", "Annotated."]]
    )

    options, _sources, _stated = gp.merge_options("example_hello", {})

    assert options["example_annotated"] == "raw"
    assert "example_annotated" in capsys.readouterr().err


def test_a_heading_is_still_a_heading(monkeypatch):
    monkeypatch.setattr(gp, "arglist", gp.arglist + [["# ---- example settings"]])

    options, _sources, _stated = gp.merge_options("example_hello", {})

    assert "# ---- example settings" not in options


def test_qx_process_declares_the_parameters_it_wraps(monkeypatch):
    """
    The decorator no longer registers a command -- a docstring block and a
    registry build do that -- but the keyword arguments of what it wraps still
    reach `arglist`, which is the one thing it was still doing. The entries it
    writes carry a description, so they are the four-element form above.
    """
    monkeypatch.setattr(ge, "arglist", [])

    @ge.qx_process()
    def example_greet_sessions(sinfo, options, example_times: int = 2, overwrite=False, thread=0):
        return None

    # `options` is the dictionary the command is handed, not a parameter
    assert ge.arglist == [["example_times", 2, int, ""]]


def test_qx_process_says_no_when_the_signature_is_wrong(monkeypatch, capsys):
    monkeypatch.setattr(ge, "arglist", [])

    @ge.qx_process()
    def not_a_processing_command(options, overwrite=False, thread=0):
        return None

    assert ge.arglist == []
    assert "not_a_processing_command" in capsys.readouterr().out


# ==============================================================================
#                                              the routing table `bin/qunex.sh`


def test_an_alias_is_offered_for_routing(tmp_path, monkeypatch):
    """
    `bin/qunex.sh` matches the typed word against this list, so a command whose
    alias is missing from it answers "Requested command is not supported" while
    `gmri`, which resolves through the token map, runs it.
    """
    core = tmp_path / "qunex"
    core_yaml = _registry_yaml(core, source_id="core", name="dwi_f99", path="f99.sh")
    core_yaml.write_text(
        core_yaml.read_text(encoding="utf-8").replace(
            "        language: bash\n", "        language: bash\n        aliases:\n            - f99\n"
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv(qx_registry.EXTENSION_FOLDERS_ENV, raising=False)
    monkeypatch.delenv(qx_registry.EXTENSION_FOLDERS_ENV_DEPRECATED, raising=False)
    monkeypatch.delenv("TOOLS", raising=False)
    monkeypatch.setenv("QUNEXPATH", str(core))

    registry = qx_registry.load_command_registry(core_registry_path=core_yaml)

    assert set(registry.gmri_commands()) == {"dwi_f99", "f99"}


def test_run_turnkey_is_still_kept_out(tmp_path, monkeypatch):
    core = tmp_path / "qunex"
    core_yaml = _registry_yaml(
        core, source_id="core", name="run_turnkey", path="run_turnkey.sh"
    )
    monkeypatch.delenv(qx_registry.EXTENSION_FOLDERS_ENV, raising=False)
    monkeypatch.delenv(qx_registry.EXTENSION_FOLDERS_ENV_DEPRECATED, raising=False)
    monkeypatch.delenv("TOOLS", raising=False)
    monkeypatch.setenv("QUNEXPATH", str(core))

    registry = qx_registry.load_command_registry(core_registry_path=core_yaml)

    assert registry.gmri_commands() == []


# ==============================================================================
#                                        what the run says about its own command


def _load(tmp_path, monkeypatch, *, ext_command):
    """Core with `check_study`, and an extension providing `ext_command`."""
    core = tmp_path / "qunex"
    core_yaml = _registry_yaml(core, source_id="core", name="check_study", path="check.sh")
    ext = tmp_path / "extensions" / "qx_example"
    _registry_yaml(ext, source_id="extension:example", name=ext_command, path="ext.sh")

    monkeypatch.delenv("TOOLS", raising=False)
    monkeypatch.delenv(qx_registry.EXTENSION_FOLDERS_ENV_DEPRECATED, raising=False)
    monkeypatch.setenv("QUNEXPATH", str(core))
    monkeypatch.setenv(qx_registry.EXTENSION_FOLDERS_ENV, str(tmp_path / "extensions"))

    return qx_registry.load_command_registry(core_registry_path=core_yaml)


def test_a_core_command_says_nothing(tmp_path, monkeypatch):
    registry = _load(tmp_path, monkeypatch, ext_command="example_hello")

    assert gcs.report_origin(registry.require("check_study")) == ""


def test_an_extension_command_names_its_extension(tmp_path, monkeypatch):
    registry = _load(tmp_path, monkeypatch, ext_command="example_hello")

    reported = gcs.report_origin(registry.require("example_hello"))

    assert "example_hello" in reported
    assert "extension example" in reported
    assert "replacing" not in reported


def test_an_override_says_what_it_replaced(tmp_path, monkeypatch):
    """
    The case with no other signal: same name, same parameter table, same runlog.
    """
    registry = _load(tmp_path, monkeypatch, ext_command="check_study")

    reported = gcs.report_origin(registry.require("check_study"))

    assert "replacing the core command of the same name" in reported


def test_the_banner_carries_the_line(tmp_path, monkeypatch):
    registry = _load(tmp_path, monkeypatch, ext_command="check_study")
    command = registry.require("check_study")

    banner = gcs.report_parameters(command, {"sessions": "s01"}, {"sessions": "command line"})

    assert "is provided by extension example" in banner
    assert banner.index("provided by extension") < banner.index("Parameters for")

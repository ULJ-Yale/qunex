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

import os
import sys

import pytest

import qx_registry
import qx_utilities.general.commands_support as gcs
import qx_utilities.general.extensions as ge
import qx_utilities.general.matlab as gm
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


@pytest.fixture
def extension_root(monkeypatch, tmp_path):
    """An empty extensions root, the only one QuNex searches."""
    root = tmp_path / "extroot"
    root.mkdir()
    for name in ("QUNEXPATH", "TOOLS", "QXEXTENSIONSPY",
                 qx_registry.EXTENSION_FOLDERS_ENV_DEPRECATED):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(qx_registry.EXTENSION_FOLDERS_ENV, str(root))
    monkeypatch.setattr(ge, "module_names", [])
    monkeypatch.setattr(ge, "modules", {})
    return root


def test_the_python_folder_is_added_without_qx_modules(restore_sys_path, extension_root):
    """
    A python command's registry path is dotted relative to this folder and
    nothing else ever adds it, so gating it on `qx_modules` left an extension
    whose commands were listed and dispatched and then failed to import.
    """
    py = extension_root / "qx_example" / "python"
    py.mkdir(parents=True)

    ge.load_extensions()

    assert str(py) in sys.path


def test_an_extension_is_found_without_the_environment(restore_sys_path, extension_root):
    """
    Inside a container the environment script is sourced once -- every later
    source returns immediately -- so an extension installed after the container
    started is in none of the variables it exports. The search roots answer the
    same question without the environment.
    """
    py = extension_root / "qx_example" / "python"
    py.mkdir(parents=True)

    assert ge.extension_python_folders() == [str(py)]

    ge.load_extensions()
    assert str(py) in sys.path


def test_qxextensionspy_is_not_read(restore_sys_path, extension_root, monkeypatch, tmp_path):
    """
    It lists what the environment script found when it was sourced, which may
    be a copy the registry no longer reads, or a folder in no root at all.
    """
    stray = tmp_path / "elsewhere" / "qx_stray" / "python"
    stray.mkdir(parents=True)
    monkeypatch.setenv("QXEXTENSIONSPY", str(stray))

    assert ge.extension_python_folders() == []


def test_only_the_winning_copy_reaches_sys_path(
    restore_sys_path, extension_root, monkeypatch, tmp_path
):
    """
    With the same extension in two roots the registry reads the copy in the
    later root, so that is the copy whose code is imported -- even when the
    environment script, sourced before the later root was named, exported the
    other copy in `QXEXTENSIONSPY`.
    """
    first = tmp_path / "first" / "qx_example" / "python"
    second = extension_root / "qx_example" / "python"
    for py in (first, second):
        py.mkdir(parents=True)
        (py / "qx_modules").write_text("qx_example_declarations\n", encoding="utf-8")
    (first / "qx_example_declarations.py").write_text(
        "arglist = [['from_first', 'yes', str]]\n", encoding="utf-8"
    )
    (second / "qx_example_declarations.py").write_text(
        "arglist = [['from_second', 'yes', str]]\n", encoding="utf-8"
    )
    monkeypatch.setenv("QXEXTENSIONSPY", str(first))
    monkeypatch.setenv(
        qx_registry.EXTENSION_FOLDERS_ENV, f"{tmp_path / 'first'}:{extension_root}"
    )
    monkeypatch.delitem(sys.modules, "qx_example_declarations", raising=False)

    ge.load_extensions()

    assert str(second) in sys.path
    assert str(first) not in sys.path
    # imported once, so its declarations are gathered once
    assert ge.compile_list("arglist") == [["from_second", "yes", str]]
    sys.modules.pop("qx_example_declarations", None)


def test_qx_modules_still_imports_what_it_lists(restore_sys_path, extension_root, monkeypatch):
    py = extension_root / "qx_example" / "python"
    py.mkdir(parents=True)
    (py / "qx_example_declarations.py").write_text(
        "arglist = [['example_declared', 'yes', str]]\n", encoding="utf-8"
    )
    (py / "qx_modules").write_text("# a comment\n\nqx_example_declarations\n", encoding="utf-8")
    monkeypatch.delitem(sys.modules, "qx_example_declarations", raising=False)

    ge.load_extensions()

    assert ge.compile_list("arglist") == [["example_declared", "yes", str]]
    sys.modules.pop("qx_example_declarations", None)


# ==============================================================================
#                                  an extension's own packages, added at dispatch


@pytest.fixture
def isolated_imports(restore_sys_path):
    """Forget the throwaway modules a test imports, so the next one imports afresh."""
    yield
    for name in [m for m in sys.modules if m.startswith("qx_example_")]:
        del sys.modules[name]


def _package_folder(extension):
    return extension / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}"


def _extension_command(extension, *, imports, origin="extension:example"):
    """An extension whose one command returns `VALUE` of the module it imports."""
    py = extension / "python"
    py.mkdir(parents=True, exist_ok=True)
    (py / "qx_example_cmd.py").write_text(
        f"from {imports} import VALUE\n\ndef run():\n    return VALUE\n", encoding="utf-8"
    )
    if str(py) not in sys.path:
        sys.path.append(str(py))
    return qx_registry.CommandInfo(
        name="example_run", aliases=(), path="qx_example_cmd.run", language="python",
        call=None, description=None, type="utility", args=(), options=(), returns=(),
        origin=origin, root=str(extension),
    )


def _module(folder, name, value):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{name}.py").write_text(f"VALUE = {value!r}\n", encoding="utf-8")


def test_loading_adds_no_package_folder(isolated_imports, extension_root):
    """Every run loads the extensions; a core command must not see their packages."""
    extension = extension_root / "qx_example"
    (extension / "python").mkdir(parents=True)
    _module(_package_folder(extension), "qx_example_dep", "extension")

    ge.load_extensions()

    assert str(_package_folder(extension)) not in sys.path


def test_a_dispatched_command_finds_its_packages_after_qunexs(isolated_imports, tmp_path):
    extension = tmp_path / "qx_example"
    _module(_package_folder(extension), "qx_example_dep", "extension")
    command = _extension_command(extension, imports="qx_example_dep")

    assert qx_registry.load_python_callable(command)() == "extension"

    position = sys.path.index(str(_package_folder(extension)))
    site_packages = [i for i, p in enumerate(sys.path) if p.endswith("site-packages")]
    assert site_packages and all(i < position for i in site_packages)


def test_qunexs_copy_of_a_package_wins(isolated_imports, tmp_path):
    """An extension adds what QuNex lacks; it never replaces what QuNex has."""
    qunex = tmp_path / "qunex_site"
    _module(qunex, "qx_example_shared", "qunex")
    sys.path.insert(0, str(qunex))
    extension = tmp_path / "qx_example"
    _module(_package_folder(extension), "qx_example_shared", "extension")
    command = _extension_command(extension, imports="qx_example_shared")

    assert qx_registry.load_python_callable(command)() == "qunex"


def test_a_folder_for_another_python_is_not_used(isolated_imports, tmp_path):
    extension = tmp_path / "qx_example"
    other = extension / "lib" / "python2.7"
    _module(other, "qx_example_dep", "extension")
    command = _extension_command(extension, imports="qx_example_dep")

    with pytest.raises(Exception):
        qx_registry.load_python_callable(command)

    assert str(other) not in sys.path


def test_only_the_dispatched_extensions_packages_are_added(isolated_imports, tmp_path):
    extension = tmp_path / "qx_example"
    _module(_package_folder(extension), "qx_example_dep", "extension")
    other = tmp_path / "qx_other"
    _module(_package_folder(other), "qx_example_other_dep", "other")
    command = _extension_command(extension, imports="qx_example_dep")

    qx_registry.load_python_callable(command)

    assert str(_package_folder(other)) not in sys.path


def test_a_core_command_adds_no_package_folder(isolated_imports, tmp_path):
    core = tmp_path / "qunex"
    _module(core / "python", "qx_example_core_dep", "core")
    _module(_package_folder(core), "qx_example_unused", "unused")
    command = _extension_command(core, imports="qx_example_core_dep", origin="core")

    assert qx_registry.load_python_callable(command)() == "core"
    assert str(_package_folder(core)) not in sys.path


# ==============================================================================
#                                          a missing dependency says what to do


def test_a_missing_dependency_names_the_package_and_the_install(isolated_imports, tmp_path):
    command = _extension_command(tmp_path / "qx_example", imports="qx_example_missing")

    with pytest.raises(qx_registry.ge.CommandFailed) as failed:
        qx_registry.load_python_callable(command)

    report = " ".join(failed.value.report)
    assert "'qx_example_missing'" in report
    assert "qunex install_qx_extension_dependencies --extensions=example" in report
    assert isinstance(failed.value.__cause__, ModuleNotFoundError)


def test_a_missing_module_of_the_extensions_own_is_left_alone(isolated_imports, tmp_path):
    """A broken path inside the extension is not a dependency to install."""
    extension = tmp_path / "qx_example"
    package = extension / "python" / "qx_example_pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    command = _extension_command(extension, imports="qx_example_pkg.absent")

    with pytest.raises(ModuleNotFoundError):
        qx_registry.load_python_callable(command)


def test_a_core_commands_missing_module_is_left_alone(isolated_imports, tmp_path):
    command = _extension_command(tmp_path / "qunex", imports="qx_example_missing", origin="core")

    with pytest.raises(ModuleNotFoundError):
        qx_registry.load_python_callable(command)


def test_a_qx_modules_import_failure_is_reported_on_stderr(
    isolated_imports, extension_root, capsys
):
    """`bin/qunex.sh` reads `gmri -available` from stdout as its routing table."""
    py = extension_root / "qx_example" / "python"
    py.mkdir(parents=True)
    (py / "qx_example_declarations.py").write_text(
        "import qx_example_missing\n", encoding="utf-8"
    )
    (py / "qx_modules").write_text("qx_example_declarations\n", encoding="utf-8")

    ge.load_extensions()

    out, err = capsys.readouterr()
    assert out == ""
    assert "qx_example_declarations" in err
    assert "'qx_example_missing' is not one of them" in err


# ==============================================================================
#                                        what an extension puts in the environment


@pytest.fixture
def clean_extension_env(monkeypatch, tmp_path):
    """An extensions root with one extension in it, and nothing inherited."""
    extension = tmp_path / "extroot" / "qx_example"
    (extension / "bin").mkdir(parents=True)
    (extension / "lib").mkdir()

    for name in ("QUNEXPATH", "TOOLS", "QXEXTENSIONSPY",
                 qx_registry.EXTENSION_FOLDERS_ENV_DEPRECATED,
                 "QXEXAMPLEPATH", "QXEXAMPLELIB", "QXEXAMPLEBIN"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv(qx_registry.EXTENSION_FOLDERS_ENV, str(tmp_path / "extroot"))
    monkeypatch.setenv("PATH", "/usr/bin")

    return extension


def test_an_extensions_bin_folder_reaches_path(clean_extension_env, monkeypatch):
    """
    A script in `bin` is not a QuNex command -- it is callable by name from
    anything that inherits the environment, which is what an extension's own
    code does. The environment script puts it there when it is sourced, and in
    a container that is once, before any extension is installed.
    """
    ge.register_extension_paths()

    binaries = str(clean_extension_env / "bin")
    assert os.environ["PATH"].split(os.pathsep)[0] == binaries
    assert os.environ["QXEXAMPLEBIN"] == binaries


def test_an_extension_is_named_in_the_environment(clean_extension_env):
    ge.register_extension_paths()

    assert os.environ["QXEXAMPLEPATH"] == str(clean_extension_env)
    assert os.environ["QXEXAMPLELIB"] == str(clean_extension_env / "lib")


def test_the_bin_folder_is_added_once(clean_extension_env):
    ge.register_extension_paths()
    ge.register_extension_paths()

    binaries = str(clean_extension_env / "bin")
    assert os.environ["PATH"].split(os.pathsep).count(binaries) == 1


def test_an_extension_without_lib_or_bin_names_only_itself(clean_extension_env):
    (clean_extension_env / "bin").rmdir()
    (clean_extension_env / "lib").rmdir()

    ge.register_extension_paths()

    assert os.environ["QXEXAMPLEPATH"] == str(clean_extension_env)
    assert "QXEXAMPLEBIN" not in os.environ
    assert "QXEXAMPLELIB" not in os.environ


# ==============================================================================
#                                       where an extension's matlab code is found


def _matlab_command(tmp_path, *, origin, matlabpaths=None):
    ext = tmp_path / "qx_example"
    matlab = ext / "matlab"
    matlab.mkdir(parents=True)
    if matlabpaths is not None:
        (matlab / "extra").mkdir()
        (matlab / "matlabpaths").write_text(matlabpaths, encoding="utf-8")

    return qx_registry.CommandInfo(
        name="example_matlab_greet",
        aliases=(),
        path="example_matlab_greet.m",
        language="matlab",
        call=None,
        description=None,
        type="matlab",
        args=(),
        options=(),
        returns=(),
        origin=origin,
        root=str(ext),
    )


def test_an_extension_matlab_command_finds_its_own_folder(tmp_path):
    command = _matlab_command(tmp_path, origin="extension:example")

    assert gm.extension_matlab_folders(command) == [str(tmp_path / "qx_example" / "matlab")]


def test_matlabpaths_adds_what_it_lists(tmp_path):
    command = _matlab_command(tmp_path, origin="extension:example", matlabpaths="extra\n\n")

    matlab = tmp_path / "qx_example" / "matlab"
    assert gm.extension_matlab_folders(command) == [str(matlab), str(matlab / "extra")]


def test_a_core_matlab_command_is_left_to_the_environment(tmp_path):
    command = _matlab_command(tmp_path, origin="core")

    assert gm.extension_matlab_folders(command) == []


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

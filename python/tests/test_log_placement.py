# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Where a run logs, and where it takes its relative paths from: the one rule,
``general.folders.run_folders``, that every entry point follows.

A run keeps all its logs in one folder, decided once where the run is started
and handed to everything the run starts. The rule used to be spelled four
times -- the log package's ``log_folder``, ``deduce_folders``' own fallbacks,
``run_recipe``'s precedence and ``qunex_container``'s ``run_logs_folder`` --
and the four disagreed. ``bin/qunex_container`` carries a copy of
``general/folders.py``, so the launcher on the host decides with this code as
well.

A relative path, a relative ``--logfolder`` among them, is taken from the study
the run knows once that study exists, else from the current folder: a study
holding nothing but the logs of a run is one that does not exist yet.

The log package takes what the rule decides: ``RunContext`` logs in the folder
it is handed, under the run's name, and the log settings read the settings
files the rule reads. And the launcher, on the host, places every run where
``gmri`` places it, from the same tiers and the same settings files, reading a
recipe's labels from what ``--bash_post`` exports as well.
"""

import os
from pathlib import Path

import pytest
import yaml

import qx_utilities.general.batch_io as bio
import qx_utilities.general.commands_support as gcs
import qx_utilities.general.exceptions as ge
import qx_utilities.general.folders as gf
import qx_utilities.general.log as gl
import qx_utilities.general.log.settings as ls
import qx_utilities.general.placement as gpl
import qx_utilities.general.recipe as gr
from tests import utils

REPO_ROOT = Path(__file__).resolve().parents[2]

TS = "2026-10-22_10.00.00.000000"

# the user settings files the log settings read, as their module names them --
# taken here, before the fixture below points the log settings at a file of
# its own
LOG_SETTINGS_PATHS = tuple(ls.USER_SETTINGS_PATHS)


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    """A home and a current folder of their own, and no user settings file."""
    home = tmp_path / "home"
    home.mkdir()
    (tmp_path / "cwd").mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.chdir(tmp_path / "cwd")
    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", [str(home / ".qunex_settings.yaml")])
    yield
    gl.set_active(None)


def study(path, marked=True, header=None):
    """A study with two sessions and a batch file, its header as given."""
    (path / "sessions" / "S1").mkdir(parents=True)
    (path / "sessions" / "S2").mkdir(parents=True)
    (path / "processing").mkdir()
    if marked:
        (path / ".qunexstudy").write_text("")
    lines = ["_%s: %s" % item for item in (header or {}).items()]
    (path / "processing" / "batch.txt").write_text(
        "\n".join(lines + ["---", "session: S1", "---", "session: S2", ""])
    )
    return path


# ------------------------------------------------------------------- the rule


def test_a_run_is_filed_under_its_command_or_recipe():
    assert gf.run_name("hcp_freesurfer") == "hcp_freesurfer"
    assert gf.run_name("hcp_freesurfer", {"recipe": "r"}) == "hcp_freesurfer"
    assert gf.run_name("run_recipe", {"recipe_file": "f", "recipe": "r"}) == (
        "run_recipe_r"
    )
    assert gf.run_name("run_recipe", {"steps": "create_study"}) == "run_recipe_steps"
    assert gf.run_name("run_recipe") == "run_recipe_steps"
    assert gf.run_name("run_recipe", {"recipe_file": "f"}) == "run_recipe"
    assert gf.run_name("run_recipe", {"recipe_file": "f", "recipe": "a/b"}) == (
        "run_recipe_a_b"
    ), "a recipe's name is one folder name, whatever it holds"


def test_a_named_study_places_the_run_in_its_logs_folder(tmp_path):
    named = str(tmp_path / "s")
    given = []

    def settings(folder):
        given.append(folder)
        return gf.LogPlacement("default", "home")

    placed = gf.run_folders("cmd", [{"studyfolder": named}], TS, settings=settings)

    assert placed.logfolder == str(tmp_path / "s" / "logs" / (TS + "_cmd"))
    assert (placed.name, placed.studyfolder, placed.known) == ("cmd", named, True)
    assert placed.base is None, "the study does not exist yet"
    assert given == [named], "the settings are the named study's"
    assert placed.settings == ("default", "home")

    study(tmp_path / "s", marked=False)
    placed = gf.run_folders("cmd", [{"studyfolder": named}], TS)

    assert placed.base == named, "once it does, marked or not"
    assert placed.logfolder == str(tmp_path / "s" / "logs" / (TS + "_cmd"))


def test_a_named_sessions_folder_places_the_run_in_its_study_marked_or_not(tmp_path):
    for marked in (True, False):
        s = study(tmp_path / ("marked" if marked else "unmarked"), marked=marked)

        placed = gf.run_folders("cmd", [{"sessionsfolder": str(s / "sessions")}], TS)

        assert (placed.studyfolder, placed.known, placed.base) == (
            str(s),
            True,
            str(s),
        ), marked
        assert placed.logfolder == str(s / "logs" / (TS + "_cmd"))


def test_the_named_study_beats_the_one_a_sessions_folder_is_in(tmp_path):
    placed = gf.run_folders(
        "cmd",
        [
            {
                "studyfolder": str(tmp_path / "a"),
                "sessionsfolder": str(tmp_path / "b" / "sessions"),
            }
        ],
        TS,
    )

    assert placed.studyfolder == str(tmp_path / "a")


def test_the_command_line_beats_the_recipe_which_beats_the_header(tmp_path):
    cli, rec, hdr = ({"studyfolder": str(tmp_path / n)} for n in "abc")

    assert gf.run_folders("c", [cli, rec, hdr], TS).studyfolder == str(tmp_path / "a")
    assert gf.run_folders("c", [{}, rec, hdr], TS).studyfolder == str(tmp_path / "b")
    assert gf.run_folders("c", [{}, {}, hdr], TS).studyfolder == str(tmp_path / "c")

    cli, rec, hdr = ({"logfolder": str(tmp_path / n)} for n in "xyz")

    assert gf.run_folders("c", [cli, rec, hdr], TS).logfolder == str(tmp_path / "x")
    assert gf.run_folders("c", [None, rec, hdr], TS).logfolder == str(tmp_path / "y")
    assert gf.run_folders("c", [{}, None, hdr], TS).logfolder == str(tmp_path / "z")


def test_a_logfolder_the_header_states_places_the_run(tmp_path):
    """It was reported as applied in the parameter banner, and ignored."""
    s = study(tmp_path / "s")
    header = {"studyfolder": str(s), "logfolder": "hdrlogs"}

    assert gf.run_folders("c", [{}, {}, header], TS).logfolder == str(s / "hdrlogs")
    assert gf.run_folders(
        "c", [{}, {}, {"logfolder": str(tmp_path / "x")}], TS
    ).logfolder == str(tmp_path / "x")


def test_a_deprecated_name_counts_as_the_name_it_has_now(tmp_path):
    s = study(tmp_path / "s", marked=False)
    other = study(tmp_path / "o", marked=False)

    for name in ("basefolder", "subjectsfolder"):
        placed = gf.run_folders("c", [{name: str(s / "sessions")}], TS)
        assert (placed.studyfolder, placed.known) == (str(s), True), name

    marked = study(tmp_path / "m")
    placed = gf.run_folders("c", [{"sfolder": str(marked / "sessions" / "S1")}], TS)
    assert (placed.studyfolder, placed.known) == (str(marked), False)

    # within one tier, as QuNex remaps the names of the command line: a later
    # name wins, and a deprecated one with no value is dropped rather than
    # taking the value of the name it has now away
    for tier in (
        {"basefolder": str(s / "sessions"), "sessionsfolder": str(other / "sessions")},
        {"sessionsfolder": str(other / "sessions"), "basefolder": str(s / "sessions")},
        {"sessionsfolder": str(other / "sessions"), "basefolder": ""},
        {"subjectsfolder": str(s / "sessions"), "basefolder": None},
    ):
        remapped = gcs.check_deprecated_parameters(dict(tier), "c")
        assert gf.placement_parameters(tier) == {
            "sessionsfolder": remapped["sessionsfolder"]
        }, tier


def test_a_deprecated_command_is_filed_under_the_name_it_has_now(capsys):
    """
    gmri files a run under the name a deprecated one has now; the container
    launcher, given the name as typed, filed it under the old one, and did not
    take a deprecated name of create_study for a command that creates its
    study. Both read the names from the rule's own table.
    """
    assert gf.run_name("fc_ComputeSeedMaps") == "fc_compute_seedmaps"
    assert gf.run_name("FC_COMPUTESEEDMAPS") == "fc_compute_seedmaps"
    assert gf.run_name("hcp_freesurfer") == "hcp_freesurfer"
    for new, olds in gf.DEPRECATED_COMMANDS.items():
        for old in olds:
            assert gf.current_command(old) == gcs.check_deprecated_commands(old), old
    for new in ("create_study", "manage_study", "copy_study"):
        for old in gf.DEPRECATED_COMMANDS.get(new, []):
            assert old in bio.CREATES_STUDY, old


def test_the_folder_aliases_are_the_ones_qunex_remaps():
    """
    The container launcher can not import `commands_support`, so the rule
    keeps its own copy of the deprecated names it reads; a name QuNex comes to
    remap onto a parameter that places a run has to be in it as well.
    """
    for old, new in gf.FOLDER_ALIASES.items():
        assert gcs.deprecated_parameters[old] == new, old

    def targets(new):
        if isinstance(new, dict):
            return {key for key in new if key != "default"} | {new.get("default")}
        return {new}

    missed = [
        old
        for old, new in gcs.deprecated_parameters.items()
        if targets(new) & set(gf.PLACEMENT_PARAMETERS) and old not in gf.FOLDER_ALIASES
    ]
    assert not missed, missed


def test_an_unnamed_run_is_in_the_study_marked_at_or_above_the_current_folder(
    tmp_path, monkeypatch
):
    s = study(tmp_path / "s")
    monkeypatch.chdir(s / "sessions" / "S1")

    placed = gf.run_folders("c", [{}], TS)

    assert placed.studyfolder == str(s)
    assert not placed.known, "found by its marker, not named"
    assert placed.base is None, "relative paths are taken from where it is run"
    assert placed.logfolder == str(s / "logs" / (TS + "_c"))


def test_a_folder_the_run_names_inside_a_marked_study_places_it(tmp_path):
    s = study(tmp_path / "s")

    for hint in gf.STUDY_HINTS:
        placed = gf.run_folders("c", [{hint: str(s / "sessions" / "S1")}], TS)
        assert (placed.studyfolder, placed.known) == (str(s), False), hint

    # `--logfolder=legacy` names a layout, not a folder to look for a study
    # from, even when the current folder holds a study of that name
    study(tmp_path / "cwd" / "legacy")
    placed = gf.run_folders("c", [{"logfolder": "legacy"}], TS)

    assert placed.studyfolder is None
    assert placed.logfolder == str(tmp_path / "home" / "qunex_logs" / (TS + "_c"))


def test_an_unmarked_parent_is_never_a_study_for_the_logs(tmp_path, monkeypatch):
    """`merge_options` gives a command the current folder's parent; the logs
    never go to a folder nobody named and nothing marks."""
    s = study(tmp_path / "s", marked=False)
    monkeypatch.chdir(s / "sessions")

    placed = gf.run_folders("c", [{}], TS)

    assert placed.studyfolder is None
    assert placed.logfolder == str(tmp_path / "home" / "qunex_logs" / (TS + "_c"))


@pytest.mark.parametrize(
    "outside, expected",
    [
        pytest.param("home", "home/qunex_logs", id="home"),
        pytest.param("cwd", "cwd", id="cwd"),
        pytest.param("{tmp}/elsewhere", "elsewhere", id="absolute"),
        pytest.param("elsewhere", "cwd/elsewhere", id="relative"),
        pytest.param("~/mine", "home/mine", id="tilde"),
    ],
)
def test_outside_a_study_the_outside_study_setting_decides(tmp_path, outside, expected):
    setting = outside.format(tmp=tmp_path)

    placed = gf.run_folders(
        "c", [{}], TS, settings=lambda _: gf.LogPlacement("default", setting)
    )

    assert (placed.studyfolder, placed.base) == (None, None)
    assert placed.logfolder == str(tmp_path / expected / (TS + "_c"))


LEGACY_BY = [
    pytest.param(
        {"logfolder": "legacy"}, gf.LogPlacement("default", "home"), id="flag"
    ),
    pytest.param({}, gf.LogPlacement("legacy", "home"), id="setting"),
]


@pytest.mark.parametrize("stated, settings", LEGACY_BY)
def test_legacy_is_the_study_processing_logs(tmp_path, stated, settings):
    named = dict(stated, studyfolder=str(tmp_path / "s"))

    placed = gf.run_folders("c", [named], TS, settings=lambda _: settings)

    assert placed.logfolder == str(tmp_path / "s" / "processing" / "logs")


@pytest.mark.parametrize("stated, settings", LEGACY_BY)
def test_legacy_outside_a_study_is_an_ordinary_run_outside_one(
    tmp_path, stated, settings
):
    """It used to be the current folder itself, a sixth place for the logs."""
    placed = gf.run_folders("c", [stated], TS, settings=lambda _: settings)

    assert placed.logfolder == str(tmp_path / "home" / "qunex_logs" / (TS + "_c"))


def test_a_relative_logfolder_is_taken_from_where_relative_paths_are(
    tmp_path, monkeypatch
):
    """
    From the study the run knows, once the study exists and when the run is
    not creating it, else from the current folder -- the folder the run takes
    every other relative path from. A study holding only the logs of an
    earlier run does not exist yet.
    """
    cwd = tmp_path / "cwd"
    existing = study(tmp_path / "s", marked=False)
    logged = tmp_path / "logged"
    (logged / "logs" / ("%s_create_study" % TS)).mkdir(parents=True)

    named = gf.run_folders(
        "c", [{"studyfolder": str(existing), "logfolder": "mine"}], TS
    )
    assert (named.logfolder, named.base) == (str(existing / "mine"), str(existing))

    for folder in (tmp_path / "new", logged):
        placed = gf.run_folders(
            "c", [{"studyfolder": str(folder), "logfolder": "mine"}], TS
        )
        assert (placed.known, placed.base) == (True, None), folder
        assert placed.logfolder == str(cwd / "mine"), folder

    creating = gf.run_folders(
        "create_study",
        [{"studyfolder": str(existing), "logfolder": "mine"}],
        TS,
        creating=True,
    )
    assert (creating.logfolder, creating.base) == (str(cwd / "mine"), None)

    nobody = gf.run_folders("c", [{"logfolder": "mine"}], TS)
    assert (nobody.studyfolder, nobody.base) == (None, None)
    assert nobody.logfolder == str(cwd / "mine")

    marked = study(tmp_path / "m")
    monkeypatch.chdir(marked / "sessions")
    found = gf.run_folders("c", [{"logfolder": "mine"}], TS)
    assert (found.studyfolder, found.known, found.base) == (str(marked), False, None)
    assert found.logfolder == str(marked / "sessions" / "mine")


def test_a_folder_holding_only_logs_is_a_study_that_does_not_exist_yet(tmp_path):
    """
    A run's logs are written into the study it names before its command runs:
    a study that they alone made is not one a second run, or a job the first
    one submitted, takes its relative paths from.
    """
    # not the current folder either, which `os.listdir(None)` would list
    (tmp_path / "cwd" / "a_file").write_text("")
    (tmp_path / "a_file").write_text("")
    (tmp_path / "empty").mkdir()
    (tmp_path / "logs_only" / "logs" / "a_run").mkdir(parents=True)
    (tmp_path / "legacy_logs_only" / "processing" / "logs").mkdir(parents=True)
    (tmp_path / "both" / "logs").mkdir(parents=True)
    (tmp_path / "both" / "processing" / "logs").mkdir(parents=True)

    for folder in (None, "", "missing", "a_file", "empty", "logs_only", "both"):
        path = str(tmp_path / folder) if folder else folder
        assert not gf.study_exists(path), folder
    assert not gf.study_exists(str(tmp_path / "legacy_logs_only"))

    (tmp_path / "marked" / "logs").mkdir(parents=True)
    (tmp_path / "marked" / ".qunexstudy").write_text("")
    (tmp_path / "in_use" / "sessions").mkdir(parents=True)
    (tmp_path / "batched" / "processing" / "logs").mkdir(parents=True)
    (tmp_path / "batched" / "processing" / "batch.txt").write_text("")
    # a `processing` the logs did not make
    (tmp_path / "odd").mkdir()
    (tmp_path / "odd" / "processing").write_text("")

    for folder in ("marked", "in_use", "batched", "odd"):
        assert gf.study_exists(str(tmp_path / folder)), folder


def test_an_empty_value_is_not_stated_and_tilde_and_variables_are_expanded(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("QX_PLACED", str(tmp_path / "s"))

    assert (
        gf.placement_parameters({"studyfolder": "", "logfolder": "  ", "folder": 1})
        == {}
    )
    assert gf.run_folders("c", [{"studyfolder": ""}], TS).studyfolder is None
    assert gf.run_folders(
        "c", [{"studyfolder": ""}, {"studyfolder": str(tmp_path / "r")}], TS
    ).studyfolder == str(tmp_path / "r"), "an empty value leaves the next tier's"

    assert gf.placement_parameters(
        {
            "studyfolder": "$QX_PLACED",
            "sessionsfolder": " ${QX_PLACED}/sessions ",
            "logfolder": "~/logs",
        }
    ) == {
        "studyfolder": str(tmp_path / "s"),
        "sessionsfolder": str(tmp_path / "s" / "sessions"),
        "logfolder": str(tmp_path / "home" / "logs"),
    }
    assert gf.run_folders("c", [{"logfolder": "~/logs"}], TS).logfolder == str(
        tmp_path / "home" / "logs"
    )


def test_the_settings_are_validated_and_the_study_overrides_the_user():
    assert gf.placement_settings() == ("default", "home")
    assert gf.placement_settings({"layout": "legacy"}, {"layout": "nested"}) == (
        "nested",
        "home",
    )
    assert gf.placement_settings(
        {"outside_study": "cwd"}, None, {"layout": "legacy"}
    ) == (
        "legacy",
        "cwd",
    )

    # in the words the log settings use, so the launcher says what QuNex says
    for section in ({"layout": "flat"}, {"layout": None}, {"outside_study": 3}):
        with pytest.raises(ge.CommandError) as resolved:
            ls.settings_to_log_settings(section)
        with pytest.raises(gf.PlacementError) as placed:
            gf.placement_settings(section)
        assert str(placed.value) in resolved.value.hints, section

    with pytest.raises(gf.PlacementError, match="mapping"):
        gf.placement_settings({"layout": "legacy"}, "layout: legacy")


def test_the_user_settings_files_are_the_ones_that_exist(tmp_path):
    home = tmp_path / "home"
    assert gf.user_settings_files() == []

    (home / ".qunex_settings.yaml").write_text("")
    (home / "qunex").mkdir()
    (home / "qunex" / "qunex_settings.yaml").write_text("")
    expected = [
        str(home / ".qunex_settings.yaml"),
        str(home / "qunex" / "qunex_settings.yaml"),
    ]

    assert gf.user_settings_files() == expected
    assert gf.user_settings_files(str(home)) == expected


def test_the_recipe_tier_is_global_then_recipe_less_what_it_unsets():
    data = {
        "global_parameters": {
            "studyfolder": "/a",
            "logfolder": "/l",
            "sessionsfolder": "/a/sessions",
            "folder": "/f",
        },
        "recipes": {
            "r": {
                "parameters": {
                    "studyfolder": "{{$QX_LEFT_AS_WRITTEN}}",
                    "-logfolder": None,
                    "unset_parameters": "sessionsfolder, folder",
                },
                "commands": [],
            },
            "listed": {"parameters": {"unset_parameters": ["logfolder"]}},
            "own": {"commands": ["create_study"]},
        },
    }

    assert gf.recipe_parameters(data, "r") == {"studyfolder": "{{$QX_LEFT_AS_WRITTEN}}"}
    assert gf.recipe_parameters(data, "listed") == {
        "studyfolder": "/a",
        "sessionsfolder": "/a/sessions",
        "folder": "/f",
    }
    assert gf.recipe_parameters(data, "own") == data["global_parameters"]
    assert gf.recipe_parameters(data, "missing") == {}
    assert gf.recipe_parameters(None, "r") == {}

    # a section that is not a mapping states nothing: `run_recipe` says what
    # is wrong with the file, not the reading that places the run
    for malformed in (None, ["studyfolder", "/a"], "studyfolder: /a"):
        data = {
            "global_parameters": malformed,
            "recipes": {"r": {"parameters": malformed}},
        }
        assert gf.recipe_parameters(data, "r") == {}, malformed


def test_a_label_is_injected_and_a_missing_one_is_an_error(monkeypatch):
    monkeypatch.setenv("QX_LABEL", "/y")
    monkeypatch.delenv("QX_NOT_SET_ANYWHERE", raising=False)

    assert gf.inject_labels("{{$QX_LABEL}}/study", {"QX_LABEL": "/x"}) == "/x/study"
    assert gf.inject_labels("{{$QX_LABEL}}/study") == "/y/study", "the environment"
    assert gf.inject_labels("{{$A}}/{{$B}}", {"A": "a", "B": "b"}) == "a/b"
    for value in ("plain", "{{ not closed", 3, None):
        assert gf.inject_labels(value, {}) == value

    with pytest.raises(gf.PlacementError) as missing:
        gf.inject_labels("{{$QX_NOT_SET_ANYWHERE}}/x")
    assert str(missing.value) == (
        "Cannot inject values marked with double curly braces in the recipe. "
        "Label [{{$QX_NOT_SET_ANYWHERE}}] not found in system environment variables."
    ), "as run_recipe has always said it"
    for value in ("{{NO_DOLLAR}}", "{{}}", "{{$A\n}}"):
        with pytest.raises(gf.PlacementError):
            gf.inject_labels(value, {"NO_DOLLAR": "x", "A": "a"})

    # a label is found as the recipe's external steps find one, so the two
    # can not read one value differently
    for value in ("{{$A}}/{{$B}}", "{{{$A}}}", "{{$A\n}}", "}} {{$A", "x{{y{{$A}}}}"):
        assert gf._LABEL.findall(value) == gr._find_enclosed_substrings(value), value


def test_the_recipe_placement_leaves_out_what_its_labels_can_not_resolve(monkeypatch):
    """
    The container launcher reads the recipe on the host, which may not hold a
    variable the run will: a label it can not resolve does not place the run,
    and the caller is told, rather than stopped.
    """
    monkeypatch.delenv("QX_STUDY", raising=False)
    monkeypatch.delenv("QX_NOT_SET_ANYWHERE", raising=False)
    data = {
        "global_parameters": {
            "basefolder": "{{$QX_STUDY}}/sessions",
            "hcp_processing_mode": "HCPStyleData",
            "logfolder": "{{$QX_NOT_SET_ANYWHERE}}/logs",
        },
        "recipes": {
            "r": {"commands": ["create_study"], "parameters": {"folder": "inbox"}}
        },
    }

    parameters, unresolved = gf.recipe_placement(data, "r", {"QX_STUDY": "/s"})

    assert parameters == {"sessionsfolder": "/s/sessions", "folder": "inbox"}
    assert [name for name, _ in unresolved] == ["logfolder"]
    assert "[{{$QX_NOT_SET_ANYWHERE}}]" in unresolved[0][1]
    assert gf.recipe_placement(data, "missing") == ({}, [])

    # the name that wins is the one that can not be resolved: the value it
    # took the place of does not place the run instead
    data["global_parameters"] = {
        "sessionsfolder": "/a/sessions",
        "subjectsfolder": "{{$QX_NOT_SET_ANYWHERE}}",
    }
    parameters, unresolved = gf.recipe_placement(data, "r", {})
    assert parameters == {"folder": "inbox"}
    assert [name for name, _ in unresolved] == ["sessionsfolder"]


# ------------------------------------------------- the log package follows it


def test_the_settings_files_are_the_ones_the_log_settings_read(tmp_path, monkeypatch):
    """
    QuNex reads the settings files with the log settings, and the container
    launcher, which can not import them, with `general.folders`: the two have
    to read the same files, and take the same values for the two settings
    that place a run.
    """
    assert LOG_SETTINGS_PATHS == gf.USER_SETTINGS_PATHS
    assert ls.STUDY_SETTINGS_FILE == gf.STUDY_SETTINGS_FILE
    assert tuple(ls.LAYOUTS) == gf.LAYOUTS
    assert tuple(ls.OUTSIDE_STUDY) == gf.OUTSIDE_STUDY

    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", list(LOG_SETTINGS_PATHS))
    home = tmp_path / "home"
    for path in gf.USER_SETTINGS_PATHS:
        settings_file = home / path[2:]
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        settings_file.write_text("logging:\n  layout: nested\n")

        assert gf.user_settings_files() == [str(settings_file)], path
        assert ls.user_settings_file() == str(settings_file), path
        settings_file.unlink()


def test_the_runlog_is_filed_under_the_run_name_and_echoes_the_command(tmp_path):
    """
    A recipe's runlog is filed under the recipe, in the folder its entry point
    decided, while the call it echoes is the one that was made: `qunex
    run_recipe`, not `qunex run_recipe_r`.
    """
    folder = tmp_path / "f"
    run = gl.RunContext(
        "run_recipe",
        {"recipe": "r"},
        gl.LogSettings(),
        timestamp=TS,
        name="run_recipe_r",
        logfolder=str(folder),
    )

    header = run.header()
    run.final_report([("r", "done", 0)])

    assert (run.name, run.logfolder) == ("run_recipe_r", str(folder))
    assert run.comlogfolder == str(folder / "comlogs")
    assert run.path == str(folder / ("Log-run_recipe_r-%s.log" % TS))
    with open(run.path) as runlog:
        written = runlog.read()
    for text in (header, written):
        assert "qunex run_recipe" in text
        assert "qunex run_recipe_r" not in text
    assert "Final report for command run_recipe\n" in written


# ---------------------------------------------- qunex_container, on the host


@pytest.fixture(scope="module")
def container():
    return utils.load_container()


def write_recipe(path, recipe="r", **global_parameters):
    """A recipe file holding one recipe, with the global parameters given."""
    path.write_text(
        yaml.safe_dump(
            {
                "global_parameters": global_parameters,
                "recipes": {recipe: {"commands": ["create_study"]}},
            }
        )
    )
    return str(path)


def gmri_places(command, args, header):
    """
    Where `gmri` places a run: its command line remapped and anchored, the
    recipe file read once, and the header less what the run unsets from it.
    """
    args = gcs.check_deprecated_parameters(dict(args), command)
    anchored, recipe, _, _ = gpl.anchor(command, args)
    header, _ = gpl.without_unset(dict(header), anchored, command)
    return gpl.place_run(command, anchored, header, TS, recipe=recipe).logfolder


def container_places(container, command, args, header, bash_post=None):
    """Where the launcher places it on the host, as its `main` does."""
    environ = {**os.environ, **container.bash_post_exports(bash_post)}
    anchored, recipe, _, _ = container.host_anchor(command, dict(args), environ)
    placed = container.host_placement(
        command, anchored, dict(header), TS, recipe=recipe
    )
    return placed.logfolder


# the shapes of run `placement_cases` builds
PLACED = [
    "named study",
    "unmarked sessions folder",
    "deprecated sessions folder",
    "deprecated name with no value in the header",
    "study only in the header",
    "relative logfolder only in the header",
    "study only in the recipe",
    "command line beats recipe",
    "recipe beats header",
    "marked study above the cwd",
    "outside a study",
    "outside_study cwd in the user settings",
    "study settings layout legacy",
    "logfolder legacy",
    "relative logfolder with a named study",
    "relative logfolder with no study",
    "header study unset",
    "an unset that names nothing",
    "create_study with a relative logfolder",
    "study holding only logs with a relative logfolder",
    "relative recipe file in the command line study",
]


def placement_cases(root):
    """
    Each shape of run as (command, command line, batch file header, the
    folder it logs in), with its folders made in `root`; the run is started
    in `root/cwd`, the isolated current folder.
    """
    named = study(root / "named")
    unmarked = study(root / "unmarked", marked=False)
    headed = study(root / "headed")
    in_recipe = study(root / "in_recipe")
    legacy = study(root / "legacy")
    (legacy / "qunex_settings.yaml").write_text("logging:\n    layout: legacy\n")
    logs_only = root / "logs_only"
    (logs_only / "logs").mkdir(parents=True)
    (named / "recipes").mkdir()
    write_recipe(named / "recipes" / "r.yaml", logfolder="rlogs")
    recipe = {
        "recipe_file": write_recipe(root / "rec.yaml", studyfolder=str(in_recipe))
    }
    recipe["recipe"] = "r"
    batch = str(headed / "processing" / "batch.txt")
    cwd, home = root / "cwd", root / "home"

    def run(folder, name):
        return str(folder / "logs" / ("%s_%s" % (TS, name)))

    return {
        "named study": (
            "hcp_freesurfer",
            {"studyfolder": str(named)},
            {},
            run(named, "hcp_freesurfer"),
        ),
        "unmarked sessions folder": (
            "dwi_dtifit",
            {"sessionsfolder": str(unmarked / "sessions")},
            {},
            run(unmarked, "dwi_dtifit"),
        ),
        "deprecated sessions folder": (
            "dwi_dtifit",
            {"subjectsfolder": str(unmarked / "sessions")},
            {},
            run(unmarked, "dwi_dtifit"),
        ),
        "deprecated name with no value in the header": (
            "dwi_dtifit",
            {"batchfile": batch},
            {"sessionsfolder": str(unmarked / "sessions"), "basefolder": ""},
            run(unmarked, "dwi_dtifit"),
        ),
        "study only in the header": (
            "dwi_dtifit",
            {"batchfile": batch},
            {"studyfolder": str(headed)},
            run(headed, "dwi_dtifit"),
        ),
        "relative logfolder only in the header": (
            "dwi_dtifit",
            {"batchfile": batch},
            {"studyfolder": str(headed), "logfolder": "hdrlogs"},
            str(headed / "hdrlogs"),
        ),
        "study only in the recipe": (
            "run_recipe",
            recipe,
            {},
            run(in_recipe, "run_recipe_r"),
        ),
        "command line beats recipe": (
            "run_recipe",
            {**recipe, "studyfolder": str(named)},
            {},
            run(named, "run_recipe_r"),
        ),
        "recipe beats header": (
            "run_recipe",
            {**recipe, "batchfile": batch},
            {"studyfolder": str(headed)},
            run(in_recipe, "run_recipe_r"),
        ),
        "marked study above the cwd": (
            "general_find_peaks",
            {},
            {},
            run(named, "general_find_peaks"),
        ),
        "outside a study": (
            "general_find_peaks",
            {},
            {},
            str(home / "qunex_logs" / (TS + "_general_find_peaks")),
        ),
        "outside_study cwd in the user settings": (
            "general_find_peaks",
            {},
            {},
            str(cwd / (TS + "_general_find_peaks")),
        ),
        "study settings layout legacy": (
            "general_find_peaks",
            {"studyfolder": str(legacy)},
            {},
            str(legacy / "processing" / "logs"),
        ),
        "logfolder legacy": (
            "dwi_dtifit",
            {"studyfolder": str(named), "logfolder": "legacy"},
            {},
            str(named / "processing" / "logs"),
        ),
        "relative logfolder with a named study": (
            "dwi_dtifit",
            {"studyfolder": str(named), "logfolder": "mine"},
            {},
            str(named / "mine"),
        ),
        "relative logfolder with no study": (
            "dwi_dtifit",
            {"logfolder": "mine"},
            {},
            str(cwd / "mine"),
        ),
        "header study unset": (
            "dwi_dtifit",
            {"batchfile": batch, "unset_batch_header_parameters": "studyfolder"},
            {"studyfolder": str(headed)},
            str(home / "qunex_logs" / (TS + "_dwi_dtifit")),
        ),
        "an unset that names nothing": (
            "dwi_dtifit",
            {"batchfile": batch, "unset_batch_header_parameters": True},
            {"studyfolder": str(headed)},
            run(headed, "dwi_dtifit"),
        ),
        "create_study with a relative logfolder": (
            "create_study",
            {"studyfolder": str(named), "logfolder": "mine"},
            {},
            str(cwd / "mine"),
        ),
        "study holding only logs with a relative logfolder": (
            "dwi_dtifit",
            {"studyfolder": str(logs_only), "logfolder": "mine"},
            {},
            str(cwd / "mine"),
        ),
        "relative recipe file in the command line study": (
            "run_recipe",
            {"studyfolder": "../named", "recipe_file": "recipes/r.yaml", "recipe": "r"},
            {},
            str(named / "rlogs"),
        ),
    }


@pytest.mark.parametrize("shape", PLACED)
def test_the_container_places_every_run_where_gmri_places_it(
    tmp_path, monkeypatch, container, shape
):
    """
    The launcher decides on the host, before the run starts, and hands the
    folder to the command in the container. It used to decide by a rule of
    its own, and for most of these shapes chose another folder than the
    command would have.
    """
    command, args, header, expected = placement_cases(tmp_path)[shape]
    if shape == "marked study above the cwd":
        monkeypatch.chdir(tmp_path / "named" / "sessions" / "S1")
    if shape == "outside_study cwd in the user settings":
        (tmp_path / "home" / ".qunex_settings.yaml").write_text(
            "logging:\n    outside_study: cwd\n"
        )

    assert gmri_places(command, args, header) == expected
    assert container_places(container, command, args, header) == expected


def test_a_recipe_label_bash_post_exports_places_the_run(
    tmp_path, monkeypatch, container, capsys
):
    """
    The Quick Start: the study its recipe names is a label that only
    --bash_post sets, inside the container. The launcher reads the export,
    and places the run in the study the Quick Start says it logs in.
    """
    monkeypatch.delenv("STUDY_FOLDER", raising=False)
    quickstart = tmp_path / "quickstart"
    args = {
        "recipe_file": write_recipe(
            tmp_path / "recipe.yaml", "quick_start", studyfolder="{{$STUDY_FOLDER}}"
        ),
        "recipe": "quick_start",
    }
    bash_post = "export STUDY_FOLDER=%s;export RAW_DATA=/x" % quickstart
    expected = str(quickstart / "logs" / (TS + "_run_recipe_quick_start"))

    placed = container.host_placement("run_recipe", args, {}, TS, bash_post=bash_post)

    assert placed.logfolder == expected
    assert container_places(container, "run_recipe", args, {}, bash_post) == expected
    assert "WARNING" not in capsys.readouterr().out

    monkeypatch.setenv("STUDY_FOLDER", str(quickstart))
    assert gmri_places("run_recipe", args, {}) == expected, (
        "where gmri places it in the container, where the variable is set"
    )

#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Precedence and validation of the ``logging:`` settings.

``resolve_logging`` folds five sources into one answer -- defaults, the user
file, the study file, the command's registry field and ``--logging`` -- and
getting the order wrong is invisible: the run simply logs somewhere the user
did not ask for, or does not log at all. Each layer is pinned here against
the one below it.
"""

from types import SimpleNamespace

import pytest

import qx_utilities.general.exceptions as ge
from qx_utilities.general.log import LogSettings, load_settings, resolve_logging
from qx_utilities.general.log import settings as ls


@pytest.fixture(autouse=True)
def no_user_settings(tmp_path, monkeypatch):
    """Point the user settings search at an empty temp folder.

    Without this every test would read the settings file of whoever runs the
    suite.
    """
    monkeypatch.setattr(
        ls, "USER_SETTINGS_PATHS", [str(tmp_path / "user" / "qunex_settings.yaml")]
    )
    return tmp_path


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def command(logging=None, type="utility"):
    """A stand-in for the registry entry of a command."""
    return SimpleNamespace(logging=logging, type=type)


# ------------------------------------------------------------------ defaults


def test_defaults_apply_when_nothing_is_configured():
    assert resolve_logging("some_command", {}) == LogSettings()


def test_defaults_are_runlog_and_comlog_on():
    assert LogSettings() == LogSettings(
        enabled=True, runlog=True, comlog=True, outside_study="home", layout="default"
    )


# --------------------------------------------------------------- the files


def test_user_settings_are_read(tmp_path, monkeypatch):
    user = write(tmp_path / "user" / "qunex_settings.yaml", "logging:\n  comlog: false\n")
    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", [str(user)])

    assert resolve_logging("some_command", {}).comlog is False


def test_study_settings_override_the_user_file_key_by_key(tmp_path, monkeypatch):
    user = write(
        tmp_path / "user" / "qunex_settings.yaml",
        "logging:\n  comlog: false\n  layout: legacy\n",
    )
    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", [str(user)])
    study = tmp_path / "study"
    write(study / "qunex_settings.yaml", "logging:\n  comlog: true\n")

    resolved = resolve_logging("some_command", {}, studyfolder=str(study))

    assert resolved.comlog is True
    # the study set one key; the user's other keys survive
    assert resolved.layout == "legacy"


def test_more_than_one_user_settings_file_is_an_error(tmp_path, monkeypatch):
    first = write(tmp_path / "a" / "qunex_settings.yaml", "logging: {}\n")
    second = write(tmp_path / "b" / "qunex_settings.yaml", "logging: {}\n")
    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", [str(first), str(second)])

    with pytest.raises(ge.CommandError) as raised:
        resolve_logging("some_command", {})

    message = "\n".join(raised.value.report)
    assert str(first) in message and str(second) in message


def test_a_settings_file_without_a_logging_section_is_fine(tmp_path, monkeypatch):
    user = write(tmp_path / "user" / "qunex_settings.yaml", "something_else:\n  a: 1\n")
    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", [str(user)])

    assert resolve_logging("some_command", {}) == LogSettings()
    assert load_settings()["something_else"] == {"a": 1}


def test_an_empty_settings_file_is_fine(tmp_path, monkeypatch):
    user = write(tmp_path / "user" / "qunex_settings.yaml", "")
    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", [str(user)])

    assert load_settings() == {}


# ---------------------------------------------------------------- --logging


@pytest.mark.parametrize(
    "mode, expected",
    [
        ("none", (False, False, False)),
        ("comlog", (True, False, True)),
        ("runlog", (True, True, False)),
        ("full", (True, True, True)),
    ],
)
def test_logging_modes_map_onto_the_three_switches(mode, expected):
    resolved = resolve_logging("some_command", {"logging": mode})

    assert (resolved.enabled, resolved.runlog, resolved.comlog) == expected


def test_logging_wins_over_the_settings_files(tmp_path, monkeypatch):
    user = write(tmp_path / "user" / "qunex_settings.yaml", "logging:\n  enabled: false\n")
    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", [str(user)])

    assert resolve_logging("some_command", {"logging": "full"}).enabled is True


def test_logging_wins_over_the_commands_own_field():
    resolved = resolve_logging(
        "some_command", {"logging": "full"}, qx_command=command(logging="none")
    )

    assert resolved.enabled is True


def test_an_unknown_logging_mode_is_rejected():
    with pytest.raises(ge.CommandError):
        resolve_logging("some_command", {"logging": "sometimes"})


# --------------------------------------------------------- command opt-outs


def test_the_registry_logging_field_applies():
    resolved = resolve_logging("some_command", {}, qx_command=command(logging="none"))

    assert resolved.enabled is False


def test_the_registry_field_beats_the_settings_files(tmp_path, monkeypatch):
    user = write(tmp_path / "user" / "qunex_settings.yaml", "logging:\n  runlog: true\n")
    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", [str(user)])

    resolved = resolve_logging("some_command", {}, qx_command=command(logging="comlog"))

    assert resolved.runlog is False and resolved.comlog is True


def test_skip_commands_disables_a_named_command(tmp_path, monkeypatch):
    user = write(
        tmp_path / "user" / "qunex_settings.yaml",
        "logging:\n  skip_commands: [some_command]\n",
    )
    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", [str(user)])

    assert resolve_logging("some_command", {}).enabled is False
    assert resolve_logging("other_command", {}).enabled is True


def test_skip_types_disables_a_whole_command_type(tmp_path, monkeypatch):
    user = write(
        tmp_path / "user" / "qunex_settings.yaml", "logging:\n  skip_types: [utility]\n"
    )
    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", [str(user)])

    assert resolve_logging("some_command", {}, qx_command=command()).enabled is False
    assert (
        resolve_logging(
            "some_command", {}, qx_command=command(type="processing")
        ).enabled
        is True
    )


def test_log_commands_wins_over_both_skips(tmp_path, monkeypatch):
    user = write(
        tmp_path / "user" / "qunex_settings.yaml",
        "logging:\n"
        "  skip_types: [utility]\n"
        "  skip_commands: [some_command]\n"
        "  log_commands: [some_command]\n",
    )
    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", [str(user)])

    assert resolve_logging("some_command", {}, qx_command=command()).enabled is True


def test_the_legacy_skip_list_still_applies_to_unannotated_commands():
    import qx_utilities.general.commands_support as gcs

    legacy = gcs.logskip_commands[0]

    assert resolve_logging(legacy, {}).enabled is False


def test_a_logging_field_takes_a_command_off_the_legacy_skip_list():
    import qx_utilities.general.commands_support as gcs

    legacy = gcs.logskip_commands[0]

    assert resolve_logging(legacy, {}, qx_command=command(logging="full")).enabled is True


# --------------------------------------------------------------- validation


def test_a_non_boolean_switch_is_rejected(tmp_path, monkeypatch):
    user = write(tmp_path / "user" / "qunex_settings.yaml", "logging:\n  runlog: yes please\n")
    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", [str(user)])

    with pytest.raises(ge.CommandError):
        resolve_logging("some_command", {})


def test_an_unknown_layout_is_rejected(tmp_path, monkeypatch):
    user = write(tmp_path / "user" / "qunex_settings.yaml", "logging:\n  layout: by-date\n")
    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", [str(user)])

    with pytest.raises(ge.CommandError):
        resolve_logging("some_command", {})


def test_outside_study_takes_an_explicit_path(tmp_path, monkeypatch):
    user = write(
        tmp_path / "user" / "qunex_settings.yaml", "logging:\n  outside_study: /var/qxlogs\n"
    )
    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", [str(user)])

    assert resolve_logging("some_command", {}).outside_study == "/var/qxlogs"


def test_a_malformed_settings_file_is_reported(tmp_path, monkeypatch):
    user = write(tmp_path / "user" / "qunex_settings.yaml", "- just\n- a list\n")
    monkeypatch.setattr(ls, "USER_SETTINGS_PATHS", [str(user)])

    with pytest.raises(ge.CommandError):
        resolve_logging("some_command", {})


# ------------------------------------------------------------- the registry


def test_the_registry_only_carries_logging_when_a_command_states_one():
    import qx_registry_build as build
    from qx_registry import CommandInfo

    bare = CommandInfo(
        name="c", aliases=(), path="p", language="python", call=None,
        description=None, type="utility", args=(), options=(), returns=(),
        origin="core",
    )

    assert "logging" not in build.command_to_obj(bare)
    assert build.command_to_obj(
        CommandInfo(**{**bare.__dict__, "logging": "none"})
    )["logging"] == "none"


def test_an_invalid_registry_logging_value_is_dropped_with_a_warning():
    import qx_registry_build as build

    assert build.parse_logging("None ", "where") == "none"
    assert build.parse_logging("sometimes", "where") is None
    assert build.parse_logging(None, "where") is None

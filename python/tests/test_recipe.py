# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for ``general.recipe.run_recipe`` -- the top level of QuNex logging.

There were none before N7.5: the recipe had its own log folder deduction, its
own runlog, its own comlog naming and its own renames, and it decided whether a
step had worked by grepping the child's stdout for ``ERROR``. All of that is
gone, so what these pin is what replaced it -- the run's log folder, one comlog
per external step named by its exit status, the exit code as the verdict, and
the step's report read from the status record the recipe asked the step to
write.

QuNex steps are exercised against a fake ``qunex`` on the PATH: the recipe runs
its steps as a subprocess, so a script that records its arguments and writes a
status record is the whole of the contract on the other side of the boundary.
"""

import os
import stat
from pathlib import Path

import pytest
import yaml

import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl
import qx_utilities.general.log.settings as gls
import qx_utilities.general.recipe as gr

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def registry_of_this_tree(monkeypatch):
    """
    A recipe reads the command registry to know what its steps are, and the
    registry is loaded from ``$QUNEXPATH/qx_commands.yaml``. This tree carries
    its own, so the tests name it and run without the suite's environment --
    without this they pass only in a run where some other file has set it.
    """
    monkeypatch.setenv("QUNEXPATH", str(REPO_ROOT))


@pytest.fixture(autouse=True)
def no_user_settings(tmp_path, monkeypatch):
    """The user's own settings file must not decide what these tests see."""
    monkeypatch.setattr(
        gls, "USER_SETTINGS_PATHS", [str(tmp_path / "user" / "qunex_settings.yaml")]
    )


def write_script(path, body, mode=0o755):
    path.write_text(body)
    path.chmod(mode | stat.S_IRUSR)
    return str(path)


@pytest.fixture
def study(tmp_path):
    """A study folder, so the logs land where a real run would put them."""
    folder = tmp_path / "study"
    (folder / "sessions").mkdir(parents=True)
    (folder / ".qunexstudy").write_text("")
    return folder


def recipe_file(tmp_path, commands, parameters=None):
    path = tmp_path / "recipe.yaml"
    path.write_text(
        yaml.safe_dump(
            {"recipes": {"test": {"parameters": parameters or {}, "commands": commands}}}
        )
    )
    return str(path)


def run_folder(study):
    """The one folder the run created under <study>/logs."""
    folders = list((study / "logs").iterdir())
    assert len(folders) == 1, folders
    return folders[0]


def runlog(study):
    logs = list(run_folder(study).glob("Log-*.log"))
    assert len(logs) == 1, logs
    return logs[0].read_text()


# --------------------------------------------------------- external steps


def test_the_run_logs_to_a_stamped_folder_named_for_the_recipe(tmp_path, study):
    script = write_script(tmp_path / "ok.sh", "#!/bin/bash\necho hello\n")

    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, [{"external": {"path": script}}]),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    assert run_folder(study).name.endswith("_run_recipe_test")
    assert "RECIPE EXECUTION SUMMARY" in runlog(study)
    assert "external %s ... OK" % script in runlog(study)


def test_a_passing_external_step_leaves_a_done_comlog_with_its_output(tmp_path, study):
    script = write_script(tmp_path / "ok.sh", "#!/bin/bash\necho hello\n")

    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, [{"external": {"path": script}}]),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    comlogs = list((run_folder(study) / "comlogs").iterdir())
    assert len(comlogs) == 1
    assert comlogs[0].name.startswith("done_ok.sh_external_")
    assert "hello" in comlogs[0].read_text()


def test_a_failing_external_step_fails_the_recipe_and_leaves_an_error_comlog(
    tmp_path, study
):
    script = write_script(tmp_path / "bad.sh", "#!/bin/bash\necho boom\nexit 3\n")

    with pytest.raises(ge.CommandFailed):
        gr.run_recipe(
            recipe_file=recipe_file(tmp_path, [{"external": {"path": script}}]),
            recipe="test",
            eargs={"studyfolder": str(study)},
        )

    comlogs = list((run_folder(study) / "comlogs").iterdir())
    assert [c.name.startswith("error_") for c in comlogs] == [True]
    assert "boom" in comlogs[0].read_text()
    assert "run_recipe failed" in runlog(study)


def test_a_study_folder_holding_tmp_in_its_name_is_not_corrupted(tmp_path):
    """The old renames were substring replaces on the whole path (§9.2.2)."""
    study = tmp_path / "tmp_study"
    (study / "sessions").mkdir(parents=True)
    (study / ".qunexstudy").write_text("")
    script = write_script(tmp_path / "ok.sh", "#!/bin/bash\necho hello\n")

    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, [{"external": {"path": script}}]),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    comlogs = list((run_folder(study) / "comlogs").iterdir())
    assert comlogs[0].parents[3].name == "tmp_study"
    assert comlogs[0].name.startswith("done_")


# ------------------------------------------------------------ QuNex steps


@pytest.fixture
def fake_qunex(tmp_path, monkeypatch):
    """
    A ``qunex`` that records its call and writes the status record it is told
    to -- the child's half of the N7.10 contract, and nothing else.
    """
    calls = tmp_path / "calls.txt"
    bin_folder = tmp_path / "bin"
    bin_folder.mkdir()

    write_script(
        bin_folder / "qunex",
        """#!/bin/bash
echo "$@" >> %s
status=$(echo "$@" | tr ' ' '\\n' | sed -n 's/^--logstatus=//p')
mkdir -p "$(dirname "$status")"
cat > "$status" <<EOF
command: create_study
timestamp: stamp
runlog: /somewhere/Log-create_study.log
failed: ${QX_FAIL:-0}
sessions:
  - {id: S01, summary: "study created", failed: ${QX_FAIL:-0}}
EOF
exit ${QX_FAIL:-0}
"""
        % calls,
    )

    monkeypatch.setenv("PATH", "%s:%s" % (bin_folder, os.environ["PATH"]))
    return calls


def test_a_step_is_told_where_to_log_and_where_to_report(tmp_path, study, fake_qunex):
    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, ["create_study"]),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    call = fake_qunex.read_text()
    assert "--logfolder=%s" % run_folder(study) in call
    assert "--logstatus=%s" % (run_folder(study) / "status" / "01_create_study.yaml") in call


def test_the_recipe_report_is_compiled_from_the_step_records(tmp_path, study, fake_qunex):
    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, ["create_study"]),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    log = runlog(study)
    assert "---> Report for create_study" in log
    assert "... S01 ---> study created" in log
    assert "runlog: /somewhere/Log-create_study.log" in log


def test_a_failing_step_fails_the_recipe_by_its_exit_code(
    tmp_path, study, fake_qunex, monkeypatch
):
    monkeypatch.setenv("QX_FAIL", "1")

    with pytest.raises(ge.CommandFailed):
        gr.run_recipe(
            recipe_file=recipe_file(tmp_path, ["create_study"]),
            recipe="test",
            eargs={"studyfolder": str(study)},
        )

    log = runlog(study)
    assert "command create_study ... FAILED" in log
    assert "... S01 ---> study created" in log, "the failing step's report is still read"


def test_an_error_in_a_step_s_output_no_longer_fails_the_recipe(
    tmp_path, study, fake_qunex
):
    """The stdout grep over-fired on any line containing ERROR (§9.2.2)."""
    write_script(
        tmp_path / "bin" / "qunex",
        """#!/bin/bash
echo "ERROR: one session of many had trouble"
status=$(echo "$@" | tr ' ' '\\n' | sed -n 's/^--logstatus=//p')
mkdir -p "$(dirname "$status")"
printf 'command: create_study\\nfailed: 0\\nsessions: []\\n' > "$status"
exit 0
""",
    )

    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, ["create_study"]),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    assert "command create_study ... OK" in runlog(study)


def test_a_step_s_output_is_relayed_line_for_line(tmp_path, study, fake_qunex, capsys):
    """
    `readline` keeps the newline it read; printing the line added a second one
    and every step's output reached the console double spaced.
    """
    write_script(
        tmp_path / "bin" / "qunex",
        """#!/bin/bash
echo "---> first"
echo "---> second"
status=$(echo "$@" | tr ' ' '\\n' | sed -n 's/^--logstatus=//p')
mkdir -p "$(dirname "$status")"
printf 'command: create_study\\nfailed: 0\\nsessions: []\\n' > "$status"
exit 0
""",
    )

    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, ["create_study"]),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    assert "---> first\n---> second\n" in capsys.readouterr().out


def test_a_step_that_writes_no_record_is_reported_from_its_exit_code(
    tmp_path, study, monkeypatch
):
    bin_folder = tmp_path / "bin"
    bin_folder.mkdir()
    write_script(bin_folder / "qunex", "#!/bin/bash\necho done\nexit 0\n")
    monkeypatch.setenv("PATH", "%s:%s" % (bin_folder, os.environ["PATH"]))

    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, ["create_study"]),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    assert "create_study: completed; no status record written" in runlog(study)
    assert "command create_study ... OK" in runlog(study)


def test_a_failing_step_that_writes_no_record_is_not_reported_as_silent(
    tmp_path, study, monkeypatch
):
    """
    A record can be missing because the step was killed -- the case no care
    inside the child covers. The recipe used to say "no status reported" and
    leave it there, while its own summary called the step FAILED.
    """
    bin_folder = tmp_path / "bin"
    bin_folder.mkdir()
    write_script(bin_folder / "qunex", "#!/bin/bash\necho boom\nexit 4\n")
    monkeypatch.setenv("PATH", "%s:%s" % (bin_folder, os.environ["PATH"]))

    with pytest.raises(ge.CommandFailed):
        gr.run_recipe(
            recipe_file=recipe_file(tmp_path, ["create_study"]),
            recipe="test",
            eargs={"studyfolder": str(study)},
        )

    log = runlog(study)
    assert "create_study: failed with exit code 4; no status record written" in log
    assert "command create_study ... FAILED" in log


# ------------------------------------------------- what a step is passed


def test_a_parameter_a_step_cannot_take_is_named_rather_than_dropped(
    tmp_path, study, fake_qunex, capsys
):
    """
    A parameter written against a command that cannot take it was deleted
    without a word, so a recipe with a typo in it ran, reported success, and
    did something other than what it said.
    """
    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path, [{"create_study": {"hcp_brainsize": 170}}]
        ),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    warning = "hcp_brainsize is not a parameter of create_study"
    assert warning in capsys.readouterr().out
    assert warning in runlog(study)
    assert "hcp_brainsize" not in fake_qunex.read_text(), "and it is still not passed"


def test_a_recipe_wide_parameter_a_step_cannot_take_is_dropped_in_silence(
    tmp_path, study, fake_qunex, capsys
):
    """
    The recipe level parameters are stated for every command of the run, the
    way a batch file's header is: one a command cannot take was meant for
    another command, and warning about it once per step would be noise.
    """
    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path, ["create_study"], parameters={"hcp_brainsize": 170}
        ),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    assert "hcp_brainsize" not in capsys.readouterr().out
    assert "hcp_brainsize" not in fake_qunex.read_text()


# ------------------------------------------------------- label injection


def test_a_label_is_injected_before_the_recipe_deduces_its_own_folders(
    tmp_path, study, fake_qunex, monkeypatch
):
    """
    `{{$VAR}}` used to be injected into each step's parameters only, which is
    after the recipe resolved the folders it derives from the same values --
    so the recipe logged to a folder literally named `{{$VAR}}` while every
    step it ran logged to the study.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("QX_TEST_STUDY", str(study))

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path, ["create_study"], {"studyfolder": "{{$QX_TEST_STUDY}}"}
        ),
        recipe="test",
        eargs={},
    )

    assert "RECIPE EXECUTION SUMMARY" in runlog(study)
    assert not (tmp_path / "{{$QX_TEST_STUDY}}").exists()


def test_a_step_s_record_is_read_from_where_the_step_was_told_to_write_it(
    tmp_path, study, fake_qunex, monkeypatch
):
    """
    The status path was derived from the uninjected log folder and injected on
    its way into `--logstatus`, so the step wrote its record where the recipe
    did not look and every step reported "no status reported".
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("QX_TEST_STUDY", str(study))

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path, ["create_study"], {"studyfolder": "{{$QX_TEST_STUDY}}"}
        ),
        recipe="test",
        eargs={},
    )

    assert "---> Report for create_study" in runlog(study)
    assert "... S01 ---> study created" in runlog(study)


# ----------------------------------------------------------------- layout


def test_nested_layout_gives_each_step_its_own_folder(tmp_path, study, fake_qunex):
    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, ["create_study", "create_study"]),
        recipe="test",
        eargs={"studyfolder": str(study)},
        log_settings=gl.LogSettings(layout="nested"),
    )

    call = fake_qunex.read_text()
    assert "--logfolder=%s" % (run_folder(study) / "01_create_study") in call
    assert "--logfolder=%s" % (run_folder(study) / "02_create_study") in call


def test_the_study_the_recipe_file_names_supplies_its_settings(
    tmp_path, study, fake_qunex
):
    """
    The caller resolved its settings before the recipe file was parsed, so a
    study only the recipe knows about gets a second look (OI-3).
    """
    (study / "qunex_settings.yaml").write_text("logging:\n    layout: nested\n")

    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, ["create_study"], {"studyfolder": str(study)}),
        recipe="test",
        log_settings=gl.LogSettings(),
    )

    assert "--logfolder=%s" % (run_folder(study) / "01_create_study") in fake_qunex.read_text()


def test_the_command_line_still_wins_over_the_study_settings(tmp_path, study):
    (study / "qunex_settings.yaml").write_text("logging:\n    enabled: false\n")
    script = write_script(tmp_path / "ok.sh", "#!/bin/bash\necho hello\n")

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path,
            [{"external": {"path": script}}],
            {"studyfolder": str(study), "logging": "full"},
        ),
        recipe="test",
        log_settings=gl.LogSettings(),
    )

    assert "external %s ... OK" % script in runlog(study)


def test_logging_off_runs_the_recipe_and_writes_no_log(tmp_path, study):
    script = write_script(tmp_path / "ok.sh", "#!/bin/bash\necho hello\n")

    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, [{"external": {"path": script}}]),
        recipe="test",
        eargs={"studyfolder": str(study)},
        log_settings=gl.LogSettings(enabled=False),
    )

    assert not (study / "logs").exists()

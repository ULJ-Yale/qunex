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

QuNex steps are exercised against a fake ``gmri`` on the PATH: the recipe runs
its steps as a subprocess, so a script that records its arguments and writes a
status record is the whole of the contract on the other side of the boundary.
"""

import os
from pathlib import Path

import pytest
import yaml

import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl
import qx_utilities.general.log.settings as gls
import qx_utilities.general.recipe as gr
from tests.utils import write_script

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


@pytest.fixture(autouse=True)
def default_settings():
    """
    `run_recipe` sets the process-wide settings; put them back after. A recipe
    run with logging off otherwise left every later test in the process with
    logging off, which `test_processing_core_report` fails on when it runs
    after this file.
    """
    yield
    gl.set_active(None)


@pytest.fixture
def study(tmp_path):
    """A study folder, so the logs land where a real run would put them."""
    folder = tmp_path / "study"
    (folder / "sessions").mkdir(parents=True)
    (folder / ".qunexstudy").write_text("")
    return folder


def recipe_file(tmp_path, commands, parameters=None, global_parameters=None):
    path = tmp_path / "recipe.yaml"
    recipe = {"recipes": {"test": {"parameters": parameters or {}, "commands": commands}}}
    if global_parameters is not None:
        recipe["global_parameters"] = global_parameters
    path.write_text(yaml.safe_dump(recipe))
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

def call_for(calls, command_name):
    """The line `fake_gmri` recorded for the step that ran that command."""
    lines = [
        line for line in calls.read_text().split("\n")
        if line.startswith(command_name + " ")
    ]
    assert len(lines) == 1, lines
    return lines[0]



# --------------------------------------------------------- external steps


def test_the_run_logs_to_a_stamped_folder_named_for_the_recipe(tmp_path, study, capsys):
    script = write_script(tmp_path / "ok.sh", "#!/bin/bash\necho hello\n")

    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, [{"external": {"path": script}}]),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    assert run_folder(study).name.endswith("_run_recipe_test")
    assert "RECIPE EXECUTION SUMMARY" in runlog(study)
    assert "external %s ... OK" % script in runlog(study)
    assert "\n---> Logs: %s\n" % run_folder(study) in capsys.readouterr().out, (
        "and says where, as every entry point does"
    )


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


@pytest.mark.parametrize(
    "path, parameters, error",
    [
        ("data.txt", {}, "External command type not supported"),
        ("ok.sh", {"url": "{{}}"}, "Cannot inject values"),
        ("ok.sh", {"url": "{{$QX_TEST_NOT_SET}}"}, "Cannot inject values"),
    ],
    ids=["a type it does not run", "an empty label", "a label nobody set"],
)
def test_an_external_step_that_can_not_be_run_ends_the_recipe_as_a_failed_one(
    tmp_path, study, monkeypatch, path, parameters, error
):
    """
    Each ended without the summary, so the runlog stopped short of saying the
    recipe failed; the empty label raised an IndexError.
    """
    monkeypatch.delenv("QX_TEST_NOT_SET", raising=False)
    script = write_script(tmp_path / path, "#!/bin/bash\necho hello\n")

    with pytest.raises(ge.CommandFailed, match=error):
        gr.run_recipe(
            recipe_file=recipe_file(
                tmp_path, [{"external": {"path": script, **parameters}}]
            ),
            recipe="test",
            eargs={"studyfolder": str(study)},
        )

    log = runlog(study)
    assert "external %s ... FAILED" % script in log
    assert "run_recipe failed" in log


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
def fake_gmri(tmp_path, monkeypatch):
    """
    A ``gmri`` that records its call and writes the status record it is told
    to -- the child's half of the N7.10 contract, and nothing else. A step is
    started as ``gmri``: the shell front end runs the same dispatcher, after
    preparation a QuNex step has no use for.
    """
    calls = tmp_path / "calls.txt"
    bin_folder = tmp_path / "bin"
    bin_folder.mkdir()

    write_script(
        bin_folder / "gmri",
        """#!/bin/bash
echo "$@" >> %s
echo "recipe parameters: ${QX_RECIPE_PARAMETERS}" >> %s
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
        % (calls, calls),
    )

    monkeypatch.setenv("PATH", "%s:%s" % (bin_folder, os.environ["PATH"]))
    return calls


def test_a_step_is_told_where_to_log_and_where_to_report(tmp_path, study, fake_gmri):
    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, ["create_study"]),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    call = fake_gmri.read_text()
    folder = run_folder(study)
    stamp = folder.name[: -len("_run_recipe_test")]
    assert "--logfolder=%s" % folder in call
    assert (
        "--logstatus=%s" % (folder / "status" / ("01_create_study-%s.yaml" % stamp))
        in call
    ), (
        "the record carries the recipe's stamp, so the recipes a run starts "
        "for its sessions, which share the folder, do not overwrite it"
    )


def test_the_recipe_report_is_compiled_from_the_step_records(tmp_path, study, fake_gmri):
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
    tmp_path, study, fake_gmri, monkeypatch
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
    tmp_path, study, fake_gmri
):
    """The stdout grep over-fired on any line containing ERROR (§9.2.2)."""
    write_script(
        tmp_path / "bin" / "gmri",
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


def test_a_step_s_output_is_relayed_line_for_line(tmp_path, study, fake_gmri, capsys):
    """
    `readline` keeps the newline it read; printing the line added a second one
    and every step's output reached the console double spaced.
    """
    write_script(
        tmp_path / "bin" / "gmri",
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
    write_script(bin_folder / "gmri", "#!/bin/bash\necho done\nexit 0\n")
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
    write_script(bin_folder / "gmri", "#!/bin/bash\necho boom\nexit 4\n")
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

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
    assert "--logfolder=%s" % run_folder(study) in call
    assert "--logstatus=%s" % (run_folder(study) / "status" / "01_create_study.yaml") in call


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


# ------------------------------------------------- what a step is passed


def test_a_parameter_a_step_cannot_take_is_named_rather_than_dropped(
    tmp_path, study, fake_gmri, capsys
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
    assert "hcp_brainsize" not in fake_gmri.read_text(), "and it is still not passed"


def test_a_recipe_wide_parameter_a_step_cannot_take_is_dropped_in_silence(
    tmp_path, study, fake_gmri, capsys
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
    assert "hcp_brainsize" not in fake_gmri.read_text()


def call_for(calls, command_name):
    """The line `fake_gmri` recorded for the step that ran that command."""
    lines = [
        line for line in calls.read_text().split("\n")
        if line.startswith(command_name + " ")
    ]
    assert len(lines) == 1, lines
    return lines[0]


def test_a_recipe_wide_batchfile_is_withheld_until_the_step_that_writes_it(
    tmp_path, study, fake_gmri
):
    """
    A recipe states `batchfile` for the whole run, but a recipe that builds one
    builds it partway through. The steps before `create_batch` would be handed
    a file that does not exist yet -- which is a hard error since the batch
    file stopped degrading to the session list -- and `create_batch` itself
    would be told to take its sessions from the file it is about to write.
    """
    batchfile = str(study / "processing" / "batch.txt")

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path,
            ["create_session_info", "create_batch", "create_conc"],
            parameters={"batchfile": batchfile},
        ),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    assert "--batchfile" not in call_for(fake_gmri, "create_session_info")
    assert "--batchfile" not in call_for(fake_gmri, "create_batch")
    assert "--batchfile=%s" % batchfile in call_for(fake_gmri, "create_conc")


def test_a_batchfile_written_against_a_step_reaches_it_even_so(
    tmp_path, study, fake_gmri
):
    """
    Only the run wide value is withheld. One written against the step itself
    names a batch file that step is meant to read, and always wins.
    """
    stated = str(tmp_path / "existing.txt")

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path,
            [{"create_session_info": {"batchfile": stated}}, "create_batch"],
            parameters={"batchfile": str(study / "processing" / "batch.txt")},
        ),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    assert "--batchfile=%s" % stated in call_for(fake_gmri, "create_session_info")


def test_a_recipe_that_starts_after_create_batch_is_given_the_batchfile(
    tmp_path, study, fake_gmri
):
    """
    `--startwith` drops the earlier steps, `create_batch` among them: the batch
    file exists by then, and the steps that are run do consume it.
    """
    batchfile = str(study / "processing" / "batch.txt")
    (study / "processing").mkdir()
    (study / "processing" / "batch.txt").write_text("---\nid: S01\n")

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path,
            ["create_batch", "create_conc"],
            parameters={"batchfile": batchfile},
        ),
        recipe="test",
        startwith="create_conc",
        eargs={"studyfolder": str(study)},
    )

    assert "--batchfile=%s" % batchfile in call_for(fake_gmri, "create_conc")


def test_a_run_wide_batchfile_nobody_writes_stops_the_recipe_before_it_starts(
    tmp_path, study, fake_gmri
):
    """
    Row 2. The recipe names a batch file no step of it creates, so a step that
    takes one is going to fail on it -- three steps and forty minutes in, if
    nothing says so now.
    """
    with pytest.raises(ge.CommandError, match="no step creates it"):
        gr.run_recipe(
            recipe_file=recipe_file(
                tmp_path,
                ["create_session_info", "setup_hcp"],
                parameters={"batchfile": str(study / "processing" / "batch.txt")},
            ),
            recipe="test",
            eargs={"studyfolder": str(study)},
        )


def test_a_batchfile_no_step_could_have_taken_does_not_stop_anything(
    tmp_path, study, fake_gmri
):
    """
    Row 2, narrowed: `import_dicom` and `create_study` declare no `batchfile`,
    so the value is inert for every step this recipe has and stopping over it
    would be stopping over nothing.
    """
    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path,
            ["create_study", "import_dicom"],
            parameters={"batchfile": str(study / "processing" / "batch.txt")},
        ),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    assert "--batchfile" not in fake_gmri.read_text()


def test_an_existing_batchfile_nobody_rewrites_reaches_every_step(
    tmp_path, study, fake_gmri
):
    """Row 3. Nothing to infer: the file is there and stays there."""
    (study / "processing").mkdir()
    batchfile = study / "processing" / "batch.txt"
    batchfile.write_text("---\nid: S01\n")

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path,
            ["create_session_info", "create_conc"],
            parameters={"batchfile": str(batchfile)},
        ),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    assert "--batchfile=%s" % batchfile in call_for(fake_gmri, "create_session_info")
    assert "--batchfile=%s" % batchfile in call_for(fake_gmri, "create_conc")


def test_an_existing_batchfile_that_is_rebuilt_warns_and_is_still_withheld(
    tmp_path, study, fake_gmri, capsys
):
    """
    Row 4. A re-run must do what the first run did, so the file left behind is
    treated as the one this run is about to write -- and said so, because an
    earlier step may have been meant to read what is there.
    """
    (study / "processing").mkdir()
    batchfile = study / "processing" / "batch.txt"
    batchfile.write_text("---\nid: S01\n")

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path,
            ["create_session_info", "create_batch", "create_conc"],
            parameters={"batchfile": str(batchfile)},
        ),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    warning = capsys.readouterr().out
    assert "already exists and is rewritten by" in warning
    assert "unset_parameters: batchfile" in warning, "and names the way to say so"
    assert "--batchfile" not in call_for(fake_gmri, "create_session_info")
    assert "--batchfile=%s" % batchfile in call_for(fake_gmri, "create_conc")


def test_a_create_batch_writing_elsewhere_withholds_nothing(
    tmp_path, study, fake_gmri
):
    """
    The question is which step writes *this path*, not whether there is a
    `create_batch` anywhere: one building a second batch file leaves the
    recipe's own alone.
    """
    (study / "processing").mkdir()
    batchfile = study / "processing" / "batch.txt"
    batchfile.write_text("---\nid: S01\n")

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path,
            [
                "create_session_info",
                {"create_batch": {"targetfile": str(study / "processing" / "hcp.txt")}},
            ],
            parameters={"batchfile": str(batchfile)},
        ),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    assert "--batchfile=%s" % batchfile in call_for(fake_gmri, "create_session_info")


# ------------------------------------------------- unsetting an inherited value


@pytest.mark.parametrize(
    "spelling",
    [
        {"unset_parameters": "batchfile"},
        {"unset_parameters": ["batchfile", "filter"]},
        {"unset_parameters": "batchfile, filter"},
        {"-batchfile": None},
    ],
    ids=["a name", "an array", "a comma separated list", "a - prefixed name"],
)
def test_a_step_does_not_inherit_what_it_unsets(tmp_path, study, fake_gmri, spelling):
    """
    A recipe states parameters for every step; a step that cannot use one has
    to be able to say so. Both spellings, and neither ever reaches a command.
    """
    step = {"create_conc": dict(spelling)}

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path, [step], parameters={"batchfile": "/nowhere/batch.txt"}
        ),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    call = call_for(fake_gmri, "create_conc")
    assert "--batchfile" not in call
    assert "unset_parameters" not in call and "---batchfile" not in call


def test_a_recipe_can_unset_for_every_step_it_has(tmp_path, study, fake_gmri):
    """
    Which is the answer for a file whose recipes split the work: the recipe
    that runs before the batch file exists says so once, and is then right
    however it is invoked.
    """
    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path,
            ["create_conc", "create_session_info"],
            parameters={"unset_parameters": "batchfile"},
            global_parameters={"batchfile": "/nowhere/batch.txt"},
        ),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    assert "--batchfile" not in call_for(fake_gmri, "create_conc")
    assert "--batchfile" not in call_for(fake_gmri, "create_session_info")


def test_an_unset_also_keeps_out_the_run_recipe_command_line(
    tmp_path, study, fake_gmri
):
    """
    The unset is about what the step can use, so it holds against every tier
    above it -- including the call that started the recipe, which otherwise
    wins over everything.
    """
    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, [{"create_conc": {"-batchfile": None}}]),
        recipe="test",
        eargs={"studyfolder": str(study), "batchfile": "/nowhere/batch.txt"},
    )

    assert "--batchfile" not in call_for(fake_gmri, "create_conc")


def test_an_empty_string_and_a_none_are_values_and_still_reach_the_step(
    tmp_path, study, fake_gmri
):
    """
    Why the unset is a key and a `-` prefix rather than an absent value:
    `img_suffix` and its kind default to the empty string, and `None` is a
    value commands document, so a recipe has to be able to state both.
    """
    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path, [{"create_conc": {"img_suffix": "", "concname": None}}]
        ),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    call = call_for(fake_gmri, "create_conc")
    assert "--img_suffix=" in call
    assert "--concname=None" in call


def test_a_global_unset_is_refused(tmp_path, study, fake_gmri):
    """
    Unsetting a parameter for every command of the run is the same as not
    writing it, so one written there is always a mistake and is named.
    """
    with pytest.raises(ge.CommandError, match="cannot be unset globally"):
        gr.run_recipe(
            recipe_file=recipe_file(
                tmp_path,
                ["create_conc"],
                global_parameters={"unset_parameters": "batchfile"},
            ),
            recipe="test",
            eargs={"studyfolder": str(study)},
        )


@pytest.mark.parametrize(
    "step, message",
    [
        ({"-batchfile": "/some/batch.txt"}, "both unset and given a value"),
        ({"batchfile": "/some/batch.txt", "-batchfile": None}, "both unset and stated"),
        ({"unset_parameters": 17}, "Invalid unset_parameters"),
    ],
    ids=["a - prefixed name with a value", "stated and unset", "a number"],
)
def test_a_contradictory_unset_is_a_recipe_error(
    tmp_path, study, fake_gmri, step, message
):
    with pytest.raises(ge.CommandError, match=message):
        gr.run_recipe(
            recipe_file=recipe_file(tmp_path, [{"create_conc": step}]),
            recipe="test",
            eargs={"studyfolder": str(study)},
        )


@pytest.mark.parametrize(
    "where",
    ["step", "recipe", "global"],
    ids=["against the step", "for the recipe", "for the whole run"],
)
def test_an_unset_of_the_batch_tiers_reaches_the_step_that_needs_it(
    tmp_path, study, fake_gmri, where
):
    """
    The batch unsets steer `gmri`, so a recipe passes them on rather than
    applying them. All nine utilities that take a batch file are narrowed by
    the passthrough rule -- none declares `sourcefolder` or `folder` -- so
    without an exception for them the parameters would be dropped for exactly
    the commands they exist for.

    Unlike `unset_parameters`, these are allowed at the global level: the
    header is not something the recipe supplies, so "no step of this run takes
    anything from it" is a statement about another file.
    """
    unset = {"unset_batch_header_parameters": "targetfile"}
    commands = [{"gather_behavior": dict(unset)} if where == "step" else "gather_behavior"]

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path,
            commands,
            parameters=unset if where == "recipe" else None,
            global_parameters=unset if where == "global" else None,
        ),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    assert "--unset_batch_header_parameters=targetfile" in call_for(
        fake_gmri, "gather_behavior"
    )


def test_a_step_is_told_which_of_its_parameters_came_from_the_recipe(
    tmp_path, study, fake_gmri
):
    """
    A command line carries values, never the tier they came from, and a step
    is a process of its own -- so the recipe names them in its environment and
    the step's own banner reports them as `recipe`.
    """
    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path, [{"create_study": {"folders": "standard"}}]
        ),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    named = [
        line for line in fake_gmri.read_text().split("\n")
        if line.startswith("recipe parameters:")
    ]
    assert named and "folders" in named[0], named
    assert "logstatus" in named[0], "the ones the recipe adds itself are named too"


# ------------------------------------------------------- label injection


def test_a_label_is_injected_before_the_recipe_deduces_its_own_folders(
    tmp_path, study, fake_gmri, monkeypatch
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
    tmp_path, study, fake_gmri, monkeypatch
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


def test_nested_layout_gives_each_step_its_own_folder(tmp_path, study, fake_gmri):
    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, ["create_study", "create_study"]),
        recipe="test",
        eargs={"studyfolder": str(study)},
        log_settings=gl.LogSettings(layout="nested"),
    )

    call = fake_gmri.read_text()
    assert "--logfolder=%s" % (run_folder(study) / "01_create_study") in call
    assert "--logfolder=%s" % (run_folder(study) / "02_create_study") in call


def test_the_study_the_recipe_file_names_supplies_its_settings(
    tmp_path, study, fake_gmri
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

    assert "--logfolder=%s" % (run_folder(study) / "01_create_study") in fake_gmri.read_text()


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

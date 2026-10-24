# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for ``general.recipe.run_recipe``: where a run and its steps log --
label injection before the recipe deduces its folders, the nested layout,
the study settings and logging mode a run logs by, the command line over the
recipe file for the study and log folder, and the log folder and status
record each step is handed. Split out of ``test_recipe.py``, whose fixtures
it copies and whose helpers it imports.
"""

import os

import pytest

import qx_utilities.general.log as gl
import qx_utilities.general.log.settings as gls
import qx_utilities.general.recipe as gr
from tests.test_recipe import REPO_ROOT, recipe_file, run_folder, runlog, call_for
from tests.utils import write_script


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
    A recipe that resolves its own settings -- one called without them; `gmri`
    resolves them for the study the recipe names before it calls it -- reads
    the settings of the study the recipe file names.
    """
    (study / "qunex_settings.yaml").write_text("logging:\n    layout: nested\n")

    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, ["create_study"], {"studyfolder": str(study)}),
        recipe="test",
    )

    assert "--logfolder=%s" % (run_folder(study) / "01_create_study") in fake_gmri.read_text()


def test_the_settings_a_recipe_is_handed_are_the_ones_it_logs_by(
    tmp_path, study, fake_gmri
):
    """
    Settings `gmri` resolved and handed over are used as they are: they were
    resolved for the study the run is placed in, the recipe's included.
    """
    (study / "qunex_settings.yaml").write_text("logging:\n    layout: nested\n")

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path, ["create_study"], {"studyfolder": str(study)}
        ),
        recipe="test",
        log_settings=gl.LogSettings(),
    )

    assert "--logfolder=%s " % run_folder(study) in fake_gmri.read_text()


@pytest.mark.parametrize("where", ["call", "recipe"])
def test_the_logging_mode_a_run_states_wins_over_the_study_settings(
    tmp_path, study, where
):
    """Stated on the call or in the recipe file, as `--logging` on a command line."""
    (study / "qunex_settings.yaml").write_text("logging:\n    enabled: false\n")
    script = write_script(tmp_path / "ok.sh", "#!/bin/bash\necho hello\n")

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path,
            [{"external": {"path": script}}],
            {
                "studyfolder": str(study),
                **({"logging": "full"} if where == "recipe" else {}),
            },
        ),
        recipe="test",
        eargs={"logging": "full"} if where == "call" else None,
    )

    assert "external %s ... OK" % script in runlog(study)


def test_logging_off_runs_the_recipe_and_writes_no_log(tmp_path, study, capsys):
    script = write_script(tmp_path / "ok.sh", "#!/bin/bash\necho hello\n")

    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, [{"external": {"path": script}}]),
        recipe="test",
        eargs={"studyfolder": str(study)},
        log_settings=gl.LogSettings(enabled=False),
    )

    assert not (study / "logs").exists()
    assert "---> Logs:" not in capsys.readouterr().out, (
        "nor names a folder it does not write"
    )


def test_nested_layout_gives_an_external_step_its_own_folder(tmp_path, study):
    script = write_script(tmp_path / "ok.sh", "#!/bin/bash\necho hello\n")

    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, [{"external": {"path": script}}]),
        recipe="test",
        eargs={"studyfolder": str(study)},
        log_settings=gl.LogSettings(layout="nested"),
    )

    comlogs = list(
        (run_folder(study) / "01_ok.sh" / "comlogs").glob("done_ok.sh_external_*.log")
    )
    assert len(comlogs) == 1 and "hello" in comlogs[0].read_text()
    assert not (run_folder(study) / "comlogs").exists(), "as a QuNex step's are"


# ---------------------------------------------- where the run and its steps log


def step_calls(calls, command_name):
    """The arguments of every call `fake_gmri` recorded for that command."""
    return [
        line.split()
        for line in calls.read_text().split("\n")
        if line.startswith(command_name + " ")
    ]


def test_the_command_line_outranks_the_recipe_file_for_the_study_and_the_log_folder(
    tmp_path, study, fake_gmri
):
    """
    The recipe file used to outrank the call for the recipe's own logs: a run
    told to work in one study logged in the one the recipe file names, and a
    log folder given on the command line gave way to the recipe's.
    """
    named = tmp_path / "named"
    path = recipe_file(
        tmp_path,
        ["create_study"],
        global_parameters={"studyfolder": str(named), "logfolder": "rlogs"},
    )

    gr.run_recipe(recipe_file=path, recipe="test", eargs={"studyfolder": str(study)})

    assert list((study / "rlogs").glob("Log-run_recipe_test-*.log")), (
        "a relative log folder is taken from the study the run works in"
    )
    assert (
        "--logfolder=%s" % (study / "rlogs") in step_calls(fake_gmri, "create_study")[0]
    )

    given = tmp_path / "given"
    gr.run_recipe(
        recipe_file=path,
        recipe="test",
        eargs={"studyfolder": str(study)},
        logfolder=str(given),
    )

    assert list(given.glob("Log-run_recipe_test-*.log"))
    assert "--logfolder=%s" % given in step_calls(fake_gmri, "create_study")[1]
    assert not named.exists(), "nothing is written to the study the call overrides"


def test_steps_never_inherit_the_run_logfolder_or_logstatus(tmp_path, study, fake_gmri):
    """
    A `logfolder` stated for the whole run, and a `logstatus` the call carries,
    place the recipe's own run. Every step is told the run's folder, and a
    status record of its own.
    """
    in_recipe, given = tmp_path / "in_recipe", tmp_path / "given"
    outer = tmp_path / "outer" / "status.yaml"

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path,
            ["create_study", "create_study"],
            global_parameters={"studyfolder": str(study), "logfolder": str(in_recipe)},
        ),
        recipe="test",
        logfolder=str(given),
        eargs={"logstatus": str(outer)},
    )

    (runlog_file,) = given.glob("Log-run_recipe_test-*.log")
    stamp = runlog_file.name[len("Log-run_recipe_test-") : -len(".log")]

    calls = step_calls(fake_gmri, "create_study")
    assert len(calls) == 2
    for step, call in enumerate(calls, start=1):
        assert "--logfolder=%s" % given in call
        assert (
            "--logstatus=%s"
            % (given / "status" / ("%02d_create_study-%s.yaml" % (step, stamp)))
            in call
        )

    assert str(in_recipe) not in fake_gmri.read_text()
    assert str(outer) not in fake_gmri.read_text()
    assert not in_recipe.exists()


@pytest.mark.parametrize("where", ["call", "recipe"])
def test_under_nested_layout_a_run_wide_logfolder_never_reaches_a_step(
    tmp_path, study, fake_gmri, where
):
    """
    A `logfolder` the call carries among the parameters it hands the steps,
    or one the recipe file states for the whole run, is the run's folder:
    each step logs in a folder of its own inside it.
    """
    given = tmp_path / "given"
    stated = {"studyfolder": str(study)}
    if where == "recipe":
        stated["logfolder"] = str(given)

    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, ["create_study"], global_parameters=stated),
        recipe="test",
        eargs={"logfolder": str(given)} if where == "call" else None,
        log_settings=gl.LogSettings(layout="nested"),
    )

    (call,) = step_calls(fake_gmri, "create_study")
    assert "--logfolder=%s" % (given / "01_create_study") in call


def test_a_logfolder_stated_against_a_step_sends_only_that_step_elsewhere(
    tmp_path, study, fake_gmri
):
    elsewhere = tmp_path / "step_logs"

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path, [{"create_study": {"logfolder": str(elsewhere)}}, "create_study"]
        ),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    first, second = step_calls(fake_gmri, "create_study")
    assert "--logfolder=%s" % elsewhere in first
    assert "--logfolder=%s" % run_folder(study) in second
    assert any(
        argument.startswith(
            "--logstatus=%s" % (run_folder(study) / "status" / "01_create_study-")
        )
        for argument in first
    ), "and it still reports to the recipe"


def test_two_recipes_in_one_folder_write_distinct_status_records(
    tmp_path, study, fake_gmri
):
    """
    The recipes a run starts for its sessions share its folder. Their records
    were all `status/<NN>_<step>.yaml`, so each overwrote the one before.
    """
    shared = tmp_path / "shared"

    for _ in range(2):
        gr.run_recipe(
            recipe_file=recipe_file(tmp_path, ["create_study"]),
            recipe="test",
            eargs={"studyfolder": str(study)},
            logfolder=str(shared),
        )

    assert len(list((shared / "status").glob("01_create_study-*.yaml"))) == 2


def test_the_batch_file_a_step_writes_is_the_one_the_call_names(
    tmp_path, study, fake_gmri
):
    """
    A value the call that starts the recipe states wins over the one a step
    states, so `create_batch` writes the `targetfile` the call names -- and
    the recipe's batch file, that same file, is withheld until it has. It was
    predicted from the step's own value, which the step never got.
    """
    batchfile = study / "processing" / "batch.txt"

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path,
            [
                "list_sessions",
                {
                    "create_batch": {
                        "targetfile": str(study / "processing" / "other.txt")
                    }
                },
                "create_conc",
            ],
            parameters={"batchfile": str(batchfile)},
        ),
        recipe="test",
        eargs={"studyfolder": str(study), "targetfile": str(batchfile)},
    )

    assert "--batchfile" not in call_for(fake_gmri, "list_sessions")
    assert "--targetfile=%s" % batchfile in call_for(fake_gmri, "create_batch")
    assert "--batchfile=%s" % batchfile in call_for(fake_gmri, "create_conc")

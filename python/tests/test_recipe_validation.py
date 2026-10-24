# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for ``general.recipe``: the recipe file's own tier as ``gmri`` reads
it (``recipe_folders``), what is not a recipe -- a parameter without a
value, a malformed recipe file, a folder -- and dry runs that name their
external and utility steps and run none. Split out of ``test_recipe.py``,
whose fixtures it copies and whose helpers it imports.
"""

import os

import pytest

import qx_utilities.general.exceptions as ge
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


# --------------------------------------------------------- the recipe tier


def test_recipe_folders_reads_the_folders_a_recipe_names(tmp_path, monkeypatch, capsys):
    """
    The recipe file's tier, as `gmri` reads it before it places a run: what
    places a run, its labels injected and the two folders settled. A label
    the environment does not hold leaves its value out, and says so, rather
    than stopping a submission whose jobs may set it.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("QX_TEST_STUDY", "labelled")
    monkeypatch.delenv("QX_TEST_UNSET", raising=False)

    path = recipe_file(
        tmp_path,
        ["create_study"],
        parameters={"logfolder": "{{$QX_TEST_UNSET}}/logs", "sessionsfolder": "data"},
        global_parameters={"studyfolder": "{{$QX_TEST_STUDY}}", "overwrite": "yes"},
    )
    assert gr.recipe_folders(path, "test") == {
        "studyfolder": str(tmp_path / "labelled"),
        "sessionsfolder": str(tmp_path / "labelled" / "data"),
    }, "the sessions folder is taken from the study"
    err = capsys.readouterr().err
    assert "WARNING" in err and "[{{$QX_TEST_UNSET}}]" in err
    assert "The recipe's logfolder does not place this run" in err

    path = recipe_file(
        tmp_path,
        ["create_study"],
        parameters={
            "basefolder": "other/sessions",
            "logfolder": "rlogs",
            "sfolder": "in",
        },
    )
    assert gr.recipe_folders(path, "test") == {
        "sessionsfolder": str(tmp_path / "other" / "sessions"),
        "logfolder": "rlogs",
        "sourcefolder": "in",
    }, "a deprecated name is read as its name now; the hints are left as written"

    (tmp_path / "broken.yaml").write_text("recipes: [unclosed\n")
    for unread in [
        (str(tmp_path / "missing.yaml"), "test"),
        (str(tmp_path / "broken.yaml"), "test"),
        (str(tmp_path), "test"),
        (path, "other"),
        (path, None),
        (None, "test"),
        (True, "test"),
    ]:
        assert gr.recipe_folders(*unread) == {}, unread


# ------------------------------------------------- what is not a recipe


@pytest.mark.parametrize(
    "name", ["recipe_file", "recipe", "steps", "startwith", "logfolder"]
)
def test_a_parameter_given_without_a_value_is_said_to_be_invalid(tmp_path, study, name):
    """
    `gmri` reads a bare `--recipe_file` -- or one a space split from its value
    -- as True, which `run_recipe` opened as the file descriptor 1: it read
    its own standard output, said it could not parse it, and closed it.
    """
    args = {"recipe_file": recipe_file(tmp_path, ["create_study"]), "recipe": "test"}
    args[name] = True

    with pytest.raises(ge.CommandError, match="Invalid parameter value"):
        gr.run_recipe(eargs={"studyfolder": str(study)}, **args)

    os.fstat(1)


@pytest.mark.parametrize(
    "text, error",
    [
        ("", "Recipes not found"),
        ("recipes:\n  - test\n", "Recipes not found"),
        ("recipes:\n  test:\n", "missing commands specification"),
        ("recipes:\n  test:\n    commands:\n", "missing commands specification"),
        (
            "global_parameters:\nrecipes:\n  test:\n    parameters:\n"
            "    commands: [create_study]\n",
            None,
        ),
        (
            "global_parameters: [a, b]\nrecipes:\n  test:\n    commands: [create_study]\n",
            "Invalid global_parameters",
        ),
        (
            "recipes:\n  test:\n    parameters: yes\n    commands: [create_study]\n",
            "Invalid parameters",
        ),
    ],
    ids=[
        "an empty file",
        "recipes not a mapping",
        "nothing under the recipe",
        "nothing under its commands",
        "empty parameter sections",
        "global parameters not a mapping",
        "recipe parameters not a mapping",
    ],
)
def test_a_malformed_recipe_file_is_reported(tmp_path, study, fake_gmri, text, error):
    """These raised a bare TypeError or ValueError from deep in the parsing."""
    path = tmp_path / "recipe.yaml"
    path.write_text(text)

    if error is None:
        gr.run_recipe(
            recipe_file=str(path), recipe="test", eargs={"studyfolder": str(study)}
        )
        assert "command create_study ... OK" in runlog(study), "a section may be empty"
        return

    with pytest.raises(ge.CommandFailed, match=error):
        gr.run_recipe(
            recipe_file=str(path), recipe="test", eargs={"studyfolder": str(study)}
        )


def test_a_folder_is_not_a_recipe_file(tmp_path):
    with pytest.raises(ge.CommandFailed, match="recipe file does not exist"):
        gr.run_recipe(recipe_file=str(tmp_path), recipe="test")


@pytest.mark.parametrize("unset", [False, True], ids=["header", "unset"])
def test_called_on_its_own_it_is_placed_by_the_batch_file_header_too(
    tmp_path, monkeypatch, unset
):
    """
    Called on its own, with no log folder handed in, it placed itself from the
    call and the recipe file alone: a study named only in the header of the
    batch file it was given did not hold its logs, which a run of `gmri
    run_recipe` given the same batch file put there.
    """
    study = tmp_path / "study"
    (study / "processing").mkdir(parents=True)
    batch = study / "processing" / "batch.txt"
    batch.write_text("_studyfolder: %s\n---\nid: S1\n" % study)
    (tmp_path / "home").mkdir()
    (tmp_path / "work").mkdir()
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.chdir(tmp_path / "work")
    script = write_script(tmp_path / "ok.sh", "#!/bin/bash\necho hello\n")
    eargs = {"batchfile": str(batch)}
    if unset:
        eargs["unset_batch_header_parameters"] = "studyfolder"

    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, [{"external": {"path": script}}]),
        recipe="test",
        eargs=eargs,
    )

    logs = tmp_path / "home" / "qunex_logs" if unset else study / "logs"
    (folder,) = logs.iterdir()
    assert folder.name.endswith("_run_recipe_test")
    assert (study / "logs").exists() is not unset


# ------------------------------------------------------------ dry runs


@pytest.mark.parametrize("stated", ["call", "recipe"])
def test_a_dry_run_names_an_external_step_and_runs_none(tmp_path, study, stated):
    """
    `run_recipe --test` ran an external step for real: it reads no --test, and
    the recipe never looked.
    """
    script = write_script(tmp_path / "ext.sh", "#!/bin/bash\ntouch \"$PWD/RAN.txt\"\n")
    eargs = {"studyfolder": str(study)}
    parameters = {}
    if stated == "call":
        eargs["test"] = True
    else:
        parameters["test"] = True

    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path, [{"external": {"path": script, "x": "1"}}], parameters=parameters
        ),
        recipe="test",
        eargs=eargs,
    )

    assert not (study / "RAN.txt").exists()
    assert not (run_folder(study) / "comlogs").exists(), "and opened no comlog"
    log = runlog(study)
    assert "test, not run: bash %s --x=1 (in %s)" % (script, study) in log
    assert "external %s ... test, not run" % script in log


def test_a_dry_run_names_a_utility_step_and_starts_none(tmp_path, study, fake_gmri):
    """
    A utility that does not take --test had it dropped as a parameter it does
    not declare, and ran: create_batch wrote its batch file in a dry run.
    """
    gr.run_recipe(
        recipe_file=recipe_file(tmp_path, ["create_study", "dwi_dtifit", "hcp_icafix"]),
        recipe="test",
        eargs={"studyfolder": str(study), "sessions": "S01", "test": True},
    )

    calls = fake_gmri.read_text()
    assert "create_study " not in calls
    log = runlog(study)
    assert "---> test, not run:\n\n     qunex create_study" in log
    assert "command create_study ... test, not run" in log
    assert "--test" not in log.split("qunex create_study", 1)[1].split("qunex ")[0]
    # the steps that are handed --test still are: a processing step, and a
    # bash step, which gmri names rather than runs
    assert "--test" in call_for(fake_gmri, "dwi_dtifit")
    assert "--test" in call_for(fake_gmri, "hcp_icafix")

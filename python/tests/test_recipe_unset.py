# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for ``general.recipe.run_recipe``: unsetting an inherited value -- a
step or a whole recipe keeping a parameter out of what it inherits, the
global and contradictory unsets that are refused, and how a step is told
which of its parameters came from the recipe. Split out of
``test_recipe.py``, whose fixtures it copies and whose helpers it imports.
"""

import os

import pytest

import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl
import qx_utilities.general.log.settings as gls
import qx_utilities.general.recipe as gr
from tests.test_recipe import REPO_ROOT, recipe_file, call_for
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

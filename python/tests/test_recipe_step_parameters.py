# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for ``general.recipe.run_recipe``: what a step is passed -- the
scheduler it is said to be submitted with, the recipe and recipe-wide
parameters it can and cannot take, what a bash step is handed and asked about,
and when a recipe-wide batch file is withheld from a step until the step that
writes it has run. Split out of ``test_recipe.py``, whose fixtures it copies
and whose helpers it imports.
"""

import os

import pytest

import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl
import qx_utilities.general.log.settings as gls
import qx_utilities.general.recipe as gr
from tests.test_recipe import REPO_ROOT, recipe_file, runlog, call_for
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


# ------------------------------------------------- what a step is passed


def test_a_scheduler_stated_for_a_step_is_said_to_submit_it(
    tmp_path, study, fake_gmri, capsys
):
    """
    The warning said the scheduler would be ignored, while the step was handed
    it and its `gmri` submitted the jobs -- which the recipe does not wait for.
    """
    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path, [{"hcp_pre_freesurfer": {"scheduler": "SLURM,time=1"}}]
        ),
        recipe="test",
        eargs={"studyfolder": str(study)},
    )

    assert "--scheduler=SLURM,time=1" in call_for(fake_gmri, "hcp_pre_freesurfer")
    warning = (
        "WARNING: the scheduler parameter stated for hcp_pre_freesurfer in the "
        "recipe file submits this step to the scheduler: run_recipe does not wait"
    )
    assert warning in capsys.readouterr().out
    assert warning in runlog(study)


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


def test_a_bash_step_is_handed_what_it_declares_and_what_it_is_told(
    tmp_path, study, fake_gmri
):
    """
    A bash script was handed every parameter of the recipe. One it does not
    know made several of them print their usage and exit 0, so the step
    reported success with nothing done; they now stop on it, so the recipe
    keeps what the script cannot take away from it.
    """
    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path,
            [{"dwi_dtifit": {"species": "macaque", "not_documented": "x"}}],
            parameters={"hcp_brainsize": 170, "overwrite": "yes"},
        ),
        recipe="test",
        eargs={"studyfolder": str(study), "sessions": "S01"},
    )

    call = call_for(fake_gmri, "dwi_dtifit")
    assert "--hcp_brainsize" not in call, "meant for another step"
    assert "--overwrite=yes" in call, "declared by the script"
    assert "--species=macaque" in call
    assert "--not_documented=x" in call, (
        "stated against the step itself, so meant for it even if its usage "
        "does not document it"
    )
    assert "--sessions=S01" in call and "--studyfolder=%s" % study in call, (
        "and what gmri needs to run it over the sessions"
    )


def test_a_recipe_wide_parameter_a_bash_script_reads_still_reaches_it(
    tmp_path, study, fake_gmri
):
    """
    run_qc reads `--bolds` although its usage text documents `--bolddata`, and
    `--bolds` wins over it. The bash narrowing kept only what the script
    declares, so a recipe stating `bolds` once for the whole run lost it
    without a word and run_qc fell back to every BOLD. A script that neither
    declares nor reads a run-wide parameter is still not handed it: the
    case-parsed scripts stop on an option they do not know.
    """
    gr.run_recipe(
        recipe_file=recipe_file(
            tmp_path,
            [
                {"run_qc": {"modality": "BOLD", "boldsuffix": "Atlas"}},
                {"dwi_dtifit": {"species": "macaque"}},
            ],
            global_parameters={"bolds": "MOTOR|SOCIAL", "overwrite": "yes"},
        ),
        recipe="test",
        eargs={"studyfolder": str(study), "sessions": "S01"},
    )

    run_qc = call_for(fake_gmri, "run_qc")
    assert "--bolds=MOTOR|SOCIAL" in run_qc, "run_qc reads it as an alias"
    assert "--modality=BOLD" in run_qc and "--overwrite=yes" in run_qc

    dtifit = call_for(fake_gmri, "dwi_dtifit")
    assert "--bolds" not in dtifit, "dwi_dtifit neither declares nor reads it"
    assert "--overwrite=yes" in dtifit, "but what it declares still reaches it"


def test_a_bash_script_is_asked_which_undocumented_names_it_reads(tmp_path):
    """
    `_read_by_script` counts a name as read when the script matches it as a
    case branch or looks it up quoted, and nothing more: not a name that only
    prefixes another, not one in a script it can not read.
    """
    (tmp_path / "bash" / "qx_utilities").mkdir(parents=True)
    (tmp_path / "bash" / "qx_utilities" / "fake.sh").write_text(
        "#!/bin/bash\n"
        "case $1 in\n"
        "    --boldruns=*) runs=${1#*=} ;;\n"
        "esac\n"
        'BOLDS=$(opts_GetOpt "--bolds" "$@")\n'
        "# --mentioned only in a comment\n"
    )

    class Command:
        root = str(tmp_path)
        path = "qx_utilities/fake.sh"

    names = {"bolds", "boldruns", "bold", "mentioned", "other"}
    assert gr._read_by_script(Command(), names) == {"bolds", "boldruns"}
    assert gr._read_by_script(Command(), set()) == set()

    Command.path = "qx_utilities/missing.sh"
    assert gr._read_by_script(Command(), names) == set(), (
        "a script that can not be read is taken to read nothing more"
    )


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

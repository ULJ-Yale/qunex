# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for what ``gmri`` does around a command, rather than for the command.

``gmri`` is a script without a ``.py`` extension, so it is loaded by path.
What is pinned here is the run level bookkeeping: a run writes the status
record a parent process asked it for. `run_recipe` is that parent today, and
it reads the record to report what each of its steps did.
"""

import fnmatch
import importlib.machinery
import importlib.util
import os
from pathlib import Path

import pytest
import yaml

import qx_utilities.general.log as gl
import qx_utilities.general.log.context as glc
import qx_utilities.general.log.settings as gls

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def registry_of_this_tree(monkeypatch):
    """
    Dispatching a command reads the command registry, which is loaded from
    ``$QUNEXPATH/qx_commands.yaml``. This tree carries its own committed
    registry, so the tests name it and run without the suite's environment.
    """
    monkeypatch.setenv("QUNEXPATH", str(REPO_ROOT))


@pytest.fixture(autouse=True)
def no_user_settings(tmp_path, monkeypatch):
    """The user's own settings file must not decide what these tests see."""
    monkeypatch.setattr(
        gls, "USER_SETTINGS_PATHS", [str(tmp_path / "user" / "qunex_settings.yaml")]
    )


@pytest.fixture(autouse=True)
def one_run_per_test(monkeypatch):
    """
    `_status_written` is per process, which is per run everywhere but here:
    the suite runs many in one process, so each test starts having written
    nothing.
    """
    monkeypatch.setattr(glc, "_status_written", False)


@pytest.fixture(scope="module")
def gmri():
    path = os.path.join(os.path.dirname(__file__), "..", "qx_utilities", "gmri")
    loader = importlib.machinery.SourceFileLoader("gmri_under_test", path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def test_a_single_utility_call_writes_the_status_record_it_was_asked_for(
    gmri, tmp_path
):
    """
    The sessions loop and `process.run` both wrote one; a utility command run
    as a single call wrote none, so every utility step of a recipe was
    reported as "no status reported" however well it went.
    """
    status = tmp_path / "status.yaml"

    gmri.runCommand(
        "create_study",
        {"studyfolder": str(tmp_path / "study"), "logstatus": str(status)},
    )

    record = yaml.safe_load(status.read_text())
    assert record["command"] == "create_study"
    assert record["failed"] == 0
    assert record["sessions"][0]["summary"].startswith("completed")
    assert (tmp_path / "study" / "sessions").is_dir(), "the command still ran"


def test_a_bash_command_reports_what_its_exit_code_said(gmri, tmp_path, monkeypatch):
    """
    The matlab and bash paths had the exit code and did nothing with it but
    print it, so such a step of a recipe had no status at all. The runner is
    stubbed: what is pinned is the record, not the pipeline behind it.

    A non-zero code also fails the run, the way it did at the shell front end
    (`bin/qunex.sh`'s `qunex_failed` exits 1) and the way every other command
    class does; this path used to exit 0 whatever the script said.
    """
    monkeypatch.setattr(
        gmri.gb, "run", lambda qx_command, args, run=None, session=None: 3
    )
    status = tmp_path / "status.yaml"

    with pytest.raises(gmri.ge.CommandFailed):
        gmri.runCommand(
            "dwi_dtifit",
            {"studyfolder": str(tmp_path / "study"), "logstatus": str(status)},
        )

    record = yaml.safe_load(status.read_text())
    assert record["failed"] == 1
    assert record["sessions"][0]["summary"] == "failed with exit code 3"


def test_a_bash_command_is_run_once_per_session_with_the_header_filled_in(
    gmri, tmp_path, monkeypatch
):
    """
    A bash script is written for one session, and the shell front end called it
    once per session, in the loop each of its wrappers sits in. It also passed it
    nothing the batch file's header said, because it never read one: the
    routing has to keep the first and add the second.
    """
    study = tmp_path / "study"
    (study / "sessions" / "S01").mkdir(parents=True)
    (study / "sessions" / "S02").mkdir(parents=True)
    (study / ".qunexstudy").write_text("")

    batch = tmp_path / "batch.txt"
    batch.write_text(
        "_sessionsfolder: %s\n_species: macaque\n_hcp_brainsize: 170\n"
        "---\nid: S01\nsubject: S01\n01: T1w\n"
        "---\nid: S02\nsubject: S02\n01: T1w\n" % (study / "sessions")
    )

    calls = []
    monkeypatch.setattr(
        gmri.gb,
        "run",
        lambda qx_command, args, run=None, session=None: calls.append((args, session))
        or 0,
    )

    gmri.runCommand("dwi_dtifit", {"batchfile": str(batch)})

    assert [session for _, session in calls] == ["S01", "S02"]
    assert calls[0][0]["species"] == "macaque", "the header filled the call in"
    assert "hcp_brainsize" not in calls[0][0], "with what the command declares"


def test_a_bash_comlog_is_named_the_way_run_turnkey_looks_for_it(gmri):
    """
    `run_turnkey` decides whether a step ran by globbing its log folder for
    `*<step name>*<session>*log`, and its QC steps are named after the command
    *and the modality* -- `run_qc_t1w`, `run_qc_bold`. So the name parts the
    shell front end put in a comlog are a contract, not decoration.
    """
    run_qc = gmri.qx_commands.get("run_qc")

    name = gmri.gb.comlog_name(run_qc, {"modality": "T1w"}, session="S01")

    assert name == "run_qc_t1w_S01"
    assert fnmatch.fnmatch(name + ".log", "*run_qc_t1w*S01*log")
    assert gmri.gb.comlog_name(run_qc, {}) == "run_qc", "and nothing else is added"


def test_a_bash_script_is_passed_the_run_parameters_it_declares(gmri, monkeypatch):
    """
    `run_bash` dropped the run level parameters a script did not declare and
    asked the *signature*, which a bash command does not have -- its parameters
    are documented ones -- so it dropped `--sessionsfolder` and `--batchfile`
    with `--parsessions`, and `dwi_dtifit` reached its script with no arguments
    at all.
    """
    ran = []
    monkeypatch.setattr(gmri.gb.gl, "run_and_log", lambda com, name, run=None: ran.append(com) or 0)
    monkeypatch.setattr(gmri.gb.os.path, "exists", lambda path: True)

    gmri.gb.run(
        gmri.qx_commands.get("dwi_dtifit"),
        {"sessionsfolder": "/study/sessions", "parsessions": "2", "batchfile": "b.txt"},
        session="S01",
    )

    assert "--sessionsfolder='/study/sessions'" in ran[0]
    assert "--sessions='S01'" in ran[0]
    assert "--parsessions" not in ran[0], "the run's parameters are not the script's"
    assert "--batchfile" not in ran[0], "nor is a file it cannot read"


def test_a_run_that_dies_still_reports_that_it_failed(gmri, tmp_path):
    """
    The record is written at the exit boundary for the runs that never build
    one. Without it the step that failed hardest was the one `run_recipe`
    could say least about.
    """
    status = tmp_path / "status.yaml"

    with pytest.raises(OSError):
        gmri.main(
            [
                "create_study",
                "--studyfolder=/dev/null/study",
                "--logstatus=%s" % status,
            ]
        )

    record = yaml.safe_load(status.read_text())
    assert record["failed"] == 1
    assert record["runlog"] is None, "there was no runlog to name"
    assert "Not a directory" in record["sessions"][0]["summary"]


def test_a_command_that_is_not_one_reports_that_it_failed(gmri, tmp_path):
    """A typo in a recipe exits rather than raises, and still has to report."""
    status = tmp_path / "status.yaml"

    with pytest.raises(SystemExit):
        gmri.main(["no_such_command", "--logstatus=%s" % status, "--x=1"])

    assert yaml.safe_load(status.read_text())["failed"] == 1


def test_a_batch_file_that_names_a_study_puts_the_runlog_in_that_study(
    gmri, tmp_path, monkeypatch
):
    """
    The whole reason the batch file is read before the logging is resolved.
    The header names the study; run from somewhere else entirely, the run
    still has to log itself inside it, or every batch run that names a study
    leaves its runlog wherever the user happened to be standing.
    """
    study = tmp_path / "study"
    (study / "sessions" / "S01").mkdir(parents=True)
    (study / ".qunexstudy").write_text("")

    batch = tmp_path / "batch.txt"
    batch.write_text(
        "_sessionsfolder: %s\n---\nid: S01\nsubject: S01\n01: T1w\n"
        % (study / "sessions")
    )

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    ran = []
    monkeypatch.setattr(
        gmri.gp,
        "run",
        lambda qx_command, args, sessions, options, sources, run: ran.append(run),
    )

    gmri.runCommand("hcp_pre_freesurfer", {"batchfile": str(batch)})

    assert ran, "the command was dispatched"
    assert ran[0].logfolder.startswith(str(study)), (
        "the runlog went to %s, not into the study the batch file named"
        % ran[0].logfolder
    )


def test_the_parameters_a_command_runs_with_are_reported_before_it_runs(
    gmri, tmp_path, capsys, monkeypatch
):
    """
    The banner names every parameter the command declares and where its value
    came from -- the diagnostic every failure mode this effort is about would
    have been visible in.
    """
    study = tmp_path / "study"
    (study / "sessions" / "S01").mkdir(parents=True)
    (study / ".qunexstudy").write_text("")

    batch = tmp_path / "batch.txt"
    batch.write_text(
        "_sessionsfolder: %s\n_hcp_brainsize: 170\n---\nid: S01\nsubject: S01\n01: T1w\n"
        % (study / "sessions")
    )

    monkeypatch.setattr(
        gmri.gp, "run", lambda qx_command, args, sessions, options, sources, run: None
    )

    gmri.runCommand(
        "hcp_pre_freesurfer", {"batchfile": str(batch), "hcp_t2": "NONE"}
    )

    banner = capsys.readouterr().out
    assert "Parameters for hcp_pre_freesurfer" in banner
    assert "hcp_brainsize" in banner and "170" in banner
    for line in banner.split("\n"):
        if line.split()[:1] == ["hcp_brainsize"]:
            assert line.endswith("batch file")
        if line.split()[:1] == ["hcp_t2"]:
            assert line.endswith("command line")
        if line.split()[:1] == ["hcp_prefs_brain_extraction_type"]:
            assert line.endswith("default")

    runlog = next((study / "logs").rglob("Log-*.log"))
    assert "hcp_brainsize" in runlog.read_text(), "and the same text in the runlog"


def test_a_batch_file_header_fills_in_what_a_command_was_not_told(
    gmri, tmp_path, monkeypatch, capsys
):
    """
    The brief's first problem: `import_dicom` declares `unzip` and `gzip`, the
    batch file states them for the whole study, and the two never met -- the
    header reached `process.run` and nothing else. What the user typed still
    wins over what the file says.
    """
    study = tmp_path / "study"
    (study / "sessions" / "S01").mkdir(parents=True)
    (study / ".qunexstudy").write_text("")

    batch = tmp_path / "batch.txt"
    batch.write_text(
        "_sessionsfolder: %s\n_unzip: no\n_gzip: folder\n---\nid: S01\nsubject: S01\n"
        "01: T1w\n" % (study / "sessions")
    )

    called = {}

    def record(function, args, run=None, tags=None):
        called.update(args)
        return gmri.gc.CallOutcome("import_dicom", 0, None, None)

    monkeypatch.setattr(gmri.gc, "run_with_log", record)

    gmri.runCommand("import_dicom", {"batchfile": str(batch), "unzip": "yes"})

    assert called["gzip"] == "folder", "the header filled in what nobody typed"
    assert called["unzip"] == "yes", "and never overrode what somebody did"

    banner = capsys.readouterr().out
    for line in banner.split("\n"):
        if line.split()[:1] == ["gzip"]:
            assert line.endswith("batch file"), "and the banner says where it came from"
        if line.split()[:1] == ["unzip"]:
            assert line.endswith("command line")


def test_a_run_started_at_gmri_gets_the_threads_the_shell_front_end_would_set(
    gmri, tmp_path, monkeypatch
):
    """
    `bin/qunex.sh` reads `--omp_threads`, or divides the cores by the
    parallelism asked for, and exports `OMP_NUM_THREADS` before it hands over.
    A run that starts at `gmri` -- a step of a recipe, a scheduler job -- got
    the machine default and oversubscribed the node.
    """
    monkeypatch.delenv("OMP_NUM_THREADS", raising=False)

    gmri.runCommand(
        "create_study", {"studyfolder": str(tmp_path / "a"), "omp_threads": "3"}
    )
    assert os.environ["OMP_NUM_THREADS"] == "3"

    monkeypatch.delenv("OMP_NUM_THREADS")
    gmri.runCommand("create_study", {"studyfolder": str(tmp_path / "b")})
    assert 1 <= int(os.environ["OMP_NUM_THREADS"]) <= gmri.gcs.MAX_OMP_THREADS

    monkeypatch.setenv("OMP_NUM_THREADS", "12")
    gmri.runCommand("create_study", {"studyfolder": str(tmp_path / "c")})
    assert os.environ["OMP_NUM_THREADS"] == "12", "an environment that states it wins"


def test_the_record_a_run_wrote_itself_is_not_overwritten_at_the_boundary(tmp_path):
    """
    `process.run` writes its per-session digest and *then* raises for the
    sessions that failed. The digest is the better record of the two.
    """
    status = tmp_path / "status.yaml"
    args = {"logstatus": str(status)}

    settings = gl.LogSettings()
    run = gl.RunContext("hcp_pre_freesurfer", args, settings, {"logfolder": str(tmp_path)})
    run.write_status([("S01", "PreFS failed", 1)])

    assert gl.write_failure_status(args, "hcp_pre_freesurfer", "died") is None
    assert yaml.safe_load(status.read_text())["sessions"][0]["id"] == "S01"

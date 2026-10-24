# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for ``general.log.context`` -- where a run's log files live, what their
names say, and what happens when logging is switched off.

The comlog status prefix is the piece users read most: an ``error_`` or a
lingering ``tmp_`` in a file listing is how a failed or interrupted call is
found, so the rename is pinned for every exit path, including the exception
one.
"""

import os
import subprocess

import pytest

import qx_utilities.general.core as gc
import qx_utilities.general.log as gl

STAMP = "2026-07-26_12.00.00.000000"


def settings(**kwargs):
    return gl.LogSettings(**kwargs)


def context(tmp_path, command="test_command", args=None, folders=None, **kwargs):
    return gl.RunContext(
        command,
        args or {},
        kwargs.pop("settings", settings()),
        folders if folders is not None else {"basefolder": str(tmp_path)},
        timestamp=STAMP,
        **kwargs,
    )


# ---------------------------------------------------------------- file names


def test_comlog_name_joins_the_parts_and_drops_the_empty_ones():
    assert gl.comlog_name("hcp_fmri_volume", None, "S01", "", STAMP) == (
        "hcp_fmri_volume_S01_%s.log" % STAMP
    )


def test_a_very_long_comlog_name_is_truncated():
    name = gl.comlog_name("x" * 300)

    assert name.endswith("(...).log")
    assert len(name) < 200


def test_call_echo_spells_the_call_as_it_would_be_typed():
    echo = gl.call_echo("hcp_fmri_volume", {"sessions": "batch.txt", "bolds": "all"})

    assert echo == 'qunex hcp_fmri_volume \\\n  --sessions="batch.txt" \\\n  --bolds="all"'


def test_call_echo_names_the_session_when_there_is_one():
    echo = gl.call_echo("hcp_fmri_volume", {}, session="S01")

    assert echo == "session: S01\nqunex hcp_fmri_volume"


# ------------------------------------------------------------- folder rules


def test_inside_a_study_logs_go_to_a_stamped_run_folder(tmp_path):
    run = context(tmp_path)

    assert run.logfolder == os.path.join(str(tmp_path), "logs", "%s_test_command" % STAMP)
    assert run.comlogfolder == os.path.join(run.logfolder, "comlogs")


def test_an_explicit_logfolder_wins(tmp_path):
    run = context(tmp_path, args={"logfolder": str(tmp_path / "elsewhere")})

    assert run.logfolder == str(tmp_path / "elsewhere")


def test_the_legacy_layout_uses_the_study_processing_logs(tmp_path):
    run = context(tmp_path, settings=settings(layout="legacy"))

    assert run.logfolder == os.path.join(str(tmp_path), "processing", "logs")


def test_outside_a_study_the_default_is_the_home_log_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))

    run = context(tmp_path, folders={})

    assert run.logfolder == os.path.join(
        str(tmp_path), "qunex_logs", "%s_test_command" % STAMP
    )


def test_outside_a_study_cwd_restores_the_old_behaviour(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    run = context(tmp_path, folders={}, settings=settings(outside_study="cwd"))

    assert run.logfolder == os.path.join(
        os.path.realpath(str(tmp_path)), "%s_test_command" % STAMP
    )


def test_outside_study_may_name_a_path(tmp_path):
    run = context(
        tmp_path, folders={}, settings=settings(outside_study=str(tmp_path / "logs_here"))
    )

    assert run.logfolder == os.path.join(
        str(tmp_path / "logs_here"), "%s_test_command" % STAMP
    )


def test_a_log_folder_a_tier_states_is_read_from_the_deduced_folders(
    tmp_path, monkeypatch
):
    """
    What the run states -- on the command line, in a recipe or in the batch
    file header -- comes in the deduced folders, with whether the run named
    its study. A relative log folder is taken from that study once it exists,
    as every other relative path of the run is; with a study found only by its
    marker it is taken from the current folder.
    """
    study = tmp_path / "study"
    (study / "sessions").mkdir(parents=True)
    (tmp_path / "elsewhere").mkdir()
    monkeypatch.chdir(tmp_path / "elsewhere")
    stated = {"logfolder": "rel"}

    named = context(
        tmp_path, folders={"basefolder": str(study), "known": True, "stated": stated}
    )
    found = context(
        tmp_path, folders={"basefolder": str(study), "known": False, "stated": stated}
    )

    assert named.logfolder == str(study / "rel")
    assert found.logfolder == os.path.join(os.getcwd(), "rel")

    # the arguments are read only when the folders do not say what was stated
    unstated = context(
        tmp_path,
        args={"logfolder": str(tmp_path / "ignored")},
        folders={"basefolder": str(study), "known": True, "stated": {}},
    )
    assert unstated.logfolder == str(study / "logs" / ("%s_test_command" % STAMP))


@pytest.mark.parametrize(
    "args, layout",
    [
        pytest.param({"logfolder": "legacy"}, "default", id="flag"),
        pytest.param({}, "legacy", id="setting"),
    ],
)
def test_the_legacy_layout_outside_a_study_logs_outside_it(
    tmp_path, monkeypatch, args, layout
):
    """
    `legacy` is a layout of a study's logs, `<study>/processing/logs`. Under it
    a run outside a study used to log in the current folder itself; it now
    gets a folder of its own where every run outside a study does.
    """
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.chdir(tmp_path)

    run = context(tmp_path, args=args, folders={}, settings=settings(layout=layout))
    here = context(
        tmp_path,
        args=args,
        folders={},
        settings=settings(layout=layout, outside_study="cwd"),
    )

    assert run.logfolder == os.path.join(
        str(tmp_path / "home"), "qunex_logs", "%s_test_command" % STAMP
    )
    assert here.logfolder == os.path.join(os.getcwd(), "%s_test_command" % STAMP)


# --------------------------------------------------------- where it started


def test_a_run_remembers_where_it_was_started(tmp_path, monkeypatch):
    """
    A run enters its study once it knows it, and a job it submits starts
    where the run was started -- so the run keeps that folder.
    """
    start = tmp_path / "start"
    start.mkdir()
    monkeypatch.chdir(start)

    assert context(tmp_path).startfolder == os.getcwd() == os.path.realpath(start)
    assert context(tmp_path, startfolder=str(tmp_path)).startfolder == str(tmp_path)

    # a folder that is gone is no folder to start a job in
    gone = tmp_path / "gone"
    gone.mkdir()
    monkeypatch.chdir(gone)
    gone.rmdir()

    assert context(tmp_path).startfolder is None
    assert context(tmp_path, startfolder=str(start)).startfolder == str(start)


# ------------------------------------------------------------------- runlog


def test_the_runlog_is_named_for_the_command_and_the_run(tmp_path):
    run = context(tmp_path)

    assert os.path.basename(run.path) == "Log-test_command-%s.log" % STAMP


def test_a_tag_marks_the_runlog_without_moving_the_folder(tmp_path):
    run = context(tmp_path, tag="long")

    assert os.path.basename(run.path) == "Log-test_command-long-%s.log" % STAMP
    assert run.logfolder.endswith("%s_test_command" % STAMP)


def test_the_header_is_written_first_and_returned(tmp_path):
    run = context(tmp_path, args={"sessions": "batch.txt"})

    header = run.header()

    assert "qunex test_command" in header
    assert '--sessions="batch.txt"' in header
    with open(run.path) as f:
        assert f.read() == header + "\n"


def test_reports_are_appended_not_rewritten(tmp_path):
    run = context(tmp_path)
    run.header()
    run.write("first\n")
    run.write("second\n")

    with open(run.path) as f:
        content = f.read()

    assert content.index("first") < content.index("second")
    assert content.startswith("# Generated by QuNex")


@pytest.mark.parametrize(
    "kwargs", [{"enabled": False}, {"runlog": False}]
)
def test_a_run_without_a_runlog_writes_nothing(tmp_path, kwargs):
    run = context(tmp_path, settings=settings(**kwargs))

    run.header()
    run.write("something")

    assert run.path is None
    assert not list(tmp_path.rglob("*.log"))


def test_the_final_report_sums_the_failures(tmp_path, capsys):
    run = context(tmp_path)
    run.final_report([("S01", "done", 0), ("S02", "done", 2)])

    assert "Not all tasks completed fully!" in capsys.readouterr().out
    with open(run.path) as f:
        assert "... S02 ---> done" in f.read()


def test_the_final_report_counts_and_groups_the_calls(tmp_path, capsys):
    """The manifest: how many of each, then who, then where to look."""
    run = context(tmp_path)
    run.final_report(
        [
            ("S01", "completed [log: a.log]", 0),
            ("S02", "no luck [log: b.log]", 1),
            ("S03", "the worker died", None),
        ]
    )

    out = capsys.readouterr().out
    assert "3 run, 1 successful, 1 failed, 1 did not complete" in out
    assert "Successful:\n     ... S01 ---> completed [log: a.log]" in out
    assert "Failed:\n     ... S02 ---> no luck [log: b.log]" in out
    assert "Did not complete:\n     ... S03 ---> the worker died" in out
    # a call that did not report leaves the overall verdict unknown
    assert "Success status not reported for some or all tasks" in out


def test_a_group_with_nothing_in_it_is_left_out(tmp_path, capsys):
    run = context(tmp_path)
    run.final_report([("S01", "completed", 0)])

    out = capsys.readouterr().out
    assert "1 run, 1 successful, 0 failed, 0 did not complete" in out
    assert "Failed:" not in out
    assert "Did not complete:" not in out


def test_the_final_report_ignores_unknown_but_reports_the_gap(tmp_path, capsys):
    run = context(tmp_path)
    run.final_report([("S01", "done", 0), ("Unknown", "Unknown", None)])

    out = capsys.readouterr().out
    assert "Unknown" not in out
    assert "Successful completion of all tasks" in out


# --------------------------------------------------------- finding the study


@pytest.mark.parametrize("start", [".", "sessions", "sessions/S01"])
def test_the_study_is_found_from_its_own_root_as_well_as_from_below(
    tmp_path, monkeypatch, start
):
    """The walk up used to skip the folder it started in."""
    (tmp_path / "sessions" / "S01").mkdir(parents=True)
    (tmp_path / ".qunexstudy").write_text("")

    monkeypatch.chdir(tmp_path / start)

    assert gc.deduce_folders({}) == {
        "basefolder": str(tmp_path),
        "known": False,
        "sessionsfolder": None,
        "stated": {},
    }, "found by its marker: the logs go there, but the run names no folder"


def test_a_folder_outside_any_study_still_deduces_none(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert gc.deduce_folders({}) == {
        "basefolder": None,
        "known": False,
        "sessionsfolder": None,
        "stated": {},
    }


# ---------------------------------------------------------- the status record


def test_no_status_is_written_unless_a_path_was_asked_for(tmp_path):
    run = context(tmp_path)

    assert run.write_status([("S01", "done", 0)]) is None
    assert not list(tmp_path.rglob("*.yaml"))


def test_the_status_record_carries_the_triples_and_the_failure_count(tmp_path):
    status = tmp_path / "status" / "01_hcp_pre_freesurfer.yaml"
    run = context(tmp_path, args={"logstatus": str(status)})

    run.write_status([("S01", "PreFS completed", 0), ("S02", "PreFS failed", 1)])

    record = gl.read_status(str(status))
    assert record["command"] == "test_command"
    assert record["timestamp"] == STAMP
    assert record["runlog"] == run.path
    assert record["failed"] == 1
    assert record["sessions"] == [
        {"id": "S01", "summary": "PreFS completed", "failed": 0},
        {"id": "S02", "summary": "PreFS failed", "failed": 1},
    ]


def test_a_command_that_reports_no_status_says_so_in_the_record(tmp_path):
    status = tmp_path / "status.yaml"
    run = context(tmp_path, args={"logstatus": str(status)})

    run.write_status([("Unknown", "Unknown", None)])

    record = gl.read_status(str(status))
    assert record["sessions"] == []
    assert record["failed"] == 0


def test_reading_a_record_that_was_never_written_is_not_an_error(tmp_path):
    assert gl.read_status(str(tmp_path / "missing.yaml")) is None


# ------------------------------------------------------------------ comlogs


def test_a_comlog_opens_as_tmp_and_closes_as_done(tmp_path):
    run = context(tmp_path)

    with run.comlog("hcp_fmri_volume", "S01", timestamp=STAMP) as comlog:
        assert os.path.basename(comlog.path).startswith("tmp_")
        comlog.write("output\n")

    assert os.path.basename(comlog.path) == (
        "done_hcp_fmri_volume_S01_%s.log" % STAMP
    )
    with open(comlog.path) as f:
        assert f.read() == "output\n"


def test_an_exception_leaves_an_error_comlog(tmp_path):
    run = context(tmp_path)
    comlog = run.comlog("hcp_fmri_volume", "S01", timestamp=STAMP)

    with pytest.raises(ValueError):
        with comlog:
            raise ValueError("boom")

    assert os.path.basename(comlog.path).startswith("error_")
    assert not os.path.exists(comlog.path.replace("error_", "tmp_"))


def test_a_comlog_can_be_closed_incomplete(tmp_path):
    run = context(tmp_path)
    comlog = run.comlog("hcp_fmri_volume", timestamp=STAMP).open()

    assert os.path.basename(comlog.close(status="incomplete")).startswith("incomplete_")


def test_a_comlog_can_be_removed_on_close(tmp_path):
    run = context(tmp_path)
    comlog = run.comlog("hcp_fmri_volume", timestamp=STAMP).open()
    opened = comlog.path

    assert comlog.close(remove=True) is None
    assert not os.path.exists(opened)


def test_closing_twice_does_not_rename_twice(tmp_path):
    run = context(tmp_path)
    comlog = run.comlog("hcp_fmri_volume", timestamp=STAMP).open()

    first = comlog.close(status="error")

    assert comlog.close(status="done") == first
    assert os.path.exists(first)


def test_the_thread_number_is_part_of_the_name(tmp_path):
    run = context(tmp_path)
    comlog = run.comlog("hcp_fmri_volume", "S01", thread=3, timestamp=STAMP)

    assert comlog.name == "hcp_fmri_volume_S01_3_%s.log" % STAMP


def test_a_name_replaces_the_tags(tmp_path):
    run = context(tmp_path)
    comlog = run.comlog("ignored", name="handmade", timestamp=STAMP)

    assert comlog.name == "handmade_%s.log" % STAMP


def test_a_comlog_handle_can_be_handed_to_subprocess(tmp_path):
    run = context(tmp_path)

    with run.comlog("echo_test", timestamp=STAMP) as comlog:
        subprocess.run(
            ["echo", "from the shell"], stdout=comlog.file, stderr=comlog.file
        )

    with open(comlog.path) as f:
        assert f.read() == "from the shell\n"


def test_capture_stdout_tees_print_into_the_comlog(tmp_path, capsys):
    run = context(tmp_path)

    with run.comlog("captured", timestamp=STAMP) as comlog:
        with comlog.capture_stdout():
            print("both places")

    assert "both places" in capsys.readouterr().out
    with open(comlog.path) as f:
        assert "both places" in f.read()


def test_without_the_tee_the_output_goes_to_the_comlog_only_and_goes_live(
    tmp_path, capsys
):
    """
    The parallel path's arrangement: no console, and the file is the live view.

    Reading the comlog *inside* the block is what pins the line buffering --
    with the default block buffer the file is still empty at that point, so a
    ``tail -f`` on it would show nothing until the call ended.
    """
    run = context(tmp_path)

    with run.comlog("redirected", timestamp=STAMP) as comlog:
        with comlog.capture_stdout(tee=False):
            print("comlog only")
            with open(comlog.path) as f:
                live = f.read()

    assert "comlog only" not in capsys.readouterr().out
    assert "comlog only" in live


def test_capture_stdout_restores_the_streams_after_an_exception(tmp_path):
    import sys

    run = context(tmp_path)
    before = sys.stdout

    with pytest.raises(ValueError):
        with run.comlog("captured", timestamp=STAMP) as comlog:
            with comlog.capture_stdout():
                raise ValueError("boom")

    assert sys.stdout is before


@pytest.mark.parametrize("kwargs", [{"enabled": False}, {"comlog": False}])
def test_a_disabled_comlog_writes_nothing_and_still_works(tmp_path, kwargs):
    run = context(tmp_path, settings=settings(**kwargs))

    with run.comlog("hcp_fmri_volume", "S01") as comlog:
        comlog.write("output")
        with comlog.capture_stdout():
            pass

    assert comlog.path is None
    assert comlog.file is None
    assert not list(tmp_path.rglob("*.log"))


# -------------------------------------------- external commands (matlab, bash)


def test_tee_writes_the_output_to_the_console_and_the_comlog(tmp_path, capfd):
    run = context(tmp_path)

    with run.comlog("teed", timestamp=STAMP) as comlog:
        assert comlog.tee("echo out; echo err 1>&2") == 0

    assert "out" in capfd.readouterr().out
    with open(comlog.path) as f:
        output = f.read()
    assert "out" in output and "err" in output


def test_run_and_log_names_the_comlog_by_the_exit_status(tmp_path):
    run = context(tmp_path)

    assert gl.run_and_log("exit 3", "a_matlab_command", run=run) == 3

    # one comlog, named by how the call ended
    comlogs = os.listdir(run.comlogfolder)
    assert len(comlogs) == 1 and comlogs[0].startswith("error_a_matlab_command")
    with open(run.path) as f:
        assert "ERROR running a_matlab_command" in f.read()


def test_run_and_log_records_a_successful_call_in_the_runlog(tmp_path):
    run = context(tmp_path)

    assert gl.run_and_log("echo hello", "a_bash_command", run=run) == 0

    with open(run.path) as f:
        runlog = f.read()
    assert "Successful completion of task" in runlog
    assert "done_a_bash_command" in runlog


def test_run_and_log_still_runs_the_command_without_a_run(tmp_path, capfd):
    assert gl.run_and_log("echo bare", "a_bash_command") == 0

    assert "bare" in capfd.readouterr().out
    assert not list(tmp_path.rglob("*.log"))


def test_comlog_folder_sits_under_the_log_folder_it_is_given(tmp_path):
    """
    The log package is handed the folder rather than deducing the study.

    Where a run logs is decided where the run starts, and a command that opens
    a comlog of its own is handed that folder: `gmri` hands it to a command
    that declares `logfolder`.
    """
    logfolder = os.path.join(str(tmp_path), "processing", "logs")

    assert gl.comlog_folder(logfolder) == os.path.join(logfolder, "comlogs")

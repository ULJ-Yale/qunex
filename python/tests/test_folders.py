# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for the study layout: the study folder as the parameter every other
folder is found from, and session files that record a session's folders
relative to the session's own folder.

Two rules are pinned here. A sessions folder that is named anywhere -- on the
command line, in a batch file's header, in a recipe -- is the one used; else it
is the `sessions` folder of the study folder; else the current folder, as it
always was. And a folder a session file records relatively is read back against
`<sessionsfolder>/<session id>`, while an absolute one, which is what every
study written before has, is used as it is.
"""

import os
from pathlib import Path

import pytest

import qx_utilities.general.commands_support as gcs
import qx_utilities.general.core as gc
import qx_utilities.general.exceptions as ge
import qx_utilities.general.folders as gf
import qx_utilities.general.log as gl
import qx_utilities.general.process as gp
import qx_utilities.general.recipe as gr
import qx_utilities.general.sessions as gs
import qx_utilities.general.utilities as gu
from tests.utils import default_options, load_container

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def registry_of_this_tree(monkeypatch):
    """The recipe module reads the registry this tree carries."""
    monkeypatch.setenv("QUNEXPATH", str(REPO_ROOT))


def make_study(root, sessions=()):
    """A study with its marker and the named session folders."""
    study = root / "study"
    (study / "sessions").mkdir(parents=True)
    (study / ".qunexstudy").write_text("")
    for session in sessions:
        (study / "sessions" / session).mkdir()
    return study


# ------------------------------------------------------------------------------
#                                                                   study layout


def test_a_named_sessions_folder_wins_over_the_study():
    assert gf.sessions_folder("/s", "/x/mine") == "/x/mine"
    assert gf.sessions_folder("/s") == os.path.join("/s", "sessions")
    assert gf.sessions_folder() == "."
    assert gf.sessions_folder(default=None) is None
    assert gf.sessions_folder("study") == os.path.join("study", "sessions"), (
        "returned as given, not made absolute"
    )


def test_the_study_is_named_or_is_where_the_sessions_folder_is(tmp_path):
    assert gf.study_folder(str(tmp_path / "s"), "/elsewhere/x") == str(tmp_path / "s")
    assert gf.study_folder(None, str(tmp_path / "s" / "sessions")) == str(tmp_path / "s")
    assert gf.study_folder(None, str(tmp_path / "s" / "sessions") + "/") == str(
        tmp_path / "s"
    ), "a trailing slash does not make the sessions folder its own study"
    assert gf.study_folder() is None
    assert gf.subjects_folder("/s") == os.path.join("/s", "subjects")
    assert gf.processing_folder("/s") == os.path.join("/s", "processing")


def test_a_study_is_found_from_inside_it(tmp_path):
    study = make_study(tmp_path, ["S01"])
    assert gf.find_study(study / "sessions" / "S01") == str(study)
    assert gf.find_study(study) == str(study), "the study root is inside the study"
    assert gf.find_study(tmp_path) is None

    legacy = tmp_path / "legacy"
    (legacy / "subjects").mkdir(parents=True)
    (legacy / ".mnapstudy").write_text("")
    assert gf.find_study(legacy / "subjects") == str(legacy)


def test_a_folder_inside_the_session_is_recorded_relative_to_it(tmp_path, monkeypatch):
    session = tmp_path / "sessions" / "S01"
    assert gf.session_relative(str(session / "hcp"), str(session)) == "hcp"
    assert gf.session_relative(str(session), str(session)) == "."
    assert gf.session_relative("", str(session)) == ""

    inbox = tmp_path / "inbox"
    assert gf.session_relative(str(inbox), str(session)) == str(inbox)

    monkeypatch.chdir(tmp_path)
    assert gf.session_relative("inbox", str(session)) == str(inbox), (
        "a folder outside the session is written absolute: a relative value "
        "is read back against the session folder"
    )


def test_a_relative_folder_is_read_back_against_the_session_folder():
    record = {
        "id": "S01",
        "hcp": "hcp",
        "raw_data": " nii ",
        "dicom": "/old/S01/dicom",
        "data": "~/4dfp",
        "bids": "",
        "nhp": ".",
        "group": "control",
        "1": {"name": "T1w"},
    }
    gf.resolve_session_folders(record, "/study/sessions/S01")

    assert record["hcp"] == "/study/sessions/S01/hcp"
    assert record["raw_data"] == "/study/sessions/S01/nii"
    assert record["nhp"] == "/study/sessions/S01"
    assert record["dicom"] == "/old/S01/dicom", "an absolute folder is used as it is"
    assert record["data"] == "~/4dfp"
    assert record["bids"] == ""
    assert record["group"] == "control", "only the folder fields are resolved"

    resolved = dict(record)
    gf.resolve_session_folders(record, "/somewhere/else")
    assert record == resolved, "resolving twice changes nothing"


def test_every_session_is_resolved_against_its_own_folder():
    sessions = [{"id": "S01", "hcp": "hcp"}, {"id": "S02", "hcp": "hcp"}, {"hcp": "hcp"}]
    gf.resolve_sessions_folders(sessions, "/study/sessions")

    assert [s["hcp"] for s in sessions] == [
        "/study/sessions/S01/hcp",
        "/study/sessions/S02/hcp",
        "hcp",
    ]


# ------------------------------------------------------------------------------
#                                                 the folders a run works with


def test_the_folders_a_run_deduces(tmp_path):
    study = str(tmp_path / "study")
    other = str(tmp_path / "other" / "sessions")

    folders = gc.deduce_folders({"studyfolder": study})
    assert folders["basefolder"] == study
    assert folders["sessionsfolder"] == os.path.join(study, "sessions")
    assert folders["known"] is True, "a study the run names is one it knows"
    assert folders["stated"] == {"studyfolder": study}
    assert "logfolder" not in folders, "where a run logs is run_folders' to say"

    folders = gc.deduce_folders({"studyfolder": study, "sessionsfolder": other})
    assert folders["sessionsfolder"] == other, "a named sessions folder wins"
    assert folders["basefolder"] == study, "and the study stays the named one"

    folders = gc.deduce_folders({"sessionsfolder": other})
    assert folders["basefolder"] == str(tmp_path / "other")
    assert folders["known"] is True, "so is the one a named sessions folder is in"

    folders = gc.deduce_folders({"basefolder": other})
    assert folders["sessionsfolder"] == other, (
        "the deprecated --basefolder is the sessions folder, not the study"
    )
    assert folders["basefolder"] == str(tmp_path / "other")
    assert folders["stated"] == {"sessionsfolder": other}, "under the name it has now"


def test_a_relative_sessions_folder_named_with_a_study_is_in_that_study(
    tmp_path, monkeypatch
):
    """
    As `process.merge_options` takes it, so that `--sessions` are matched in
    the sessions folder the command then works on. Named alone it is taken
    from the current folder, and names the study it is in.
    """
    monkeypatch.chdir(tmp_path)

    for named in (
        {"studyfolder": "study", "sessionsfolder": "sessions_v2"},
        {"studyfolder": str(tmp_path / "study"), "sessionsfolder": "sessions_v2"},
        {"studyfolder": "study", "basefolder": "sessions_v2"},
        {"sessionsfolder": "sessions_v2"},
        {"studyfolder": "study", "sessionsfolder": str(tmp_path / "x")},
    ):
        folders = gc.deduce_folders(named)
        # what `gmri` merges: the command line under the names in use
        remapped = gcs.check_deprecated_parameters(dict(named), "hcp_pre_freesurfer")
        options, _, _ = gp.merge_options("hcp_pre_freesurfer", remapped)

        assert folders["sessionsfolder"] == options["sessionsfolder"], named
        assert folders["basefolder"] == options["studyfolder"], named

    folders = gc.deduce_folders({"studyfolder": "study", "sessionsfolder": "../v2"})
    assert folders["sessionsfolder"] == str(tmp_path / "v2")


def test_a_run_inside_a_study_logs_into_it(tmp_path, monkeypatch):
    study = make_study(tmp_path, ["S01"])
    monkeypatch.chdir(study / "sessions" / "S01")

    folders = gc.deduce_folders({})
    assert folders["basefolder"] == str(study)
    assert folders["known"] is False, "found by its marker, not named"
    assert folders["sessionsfolder"] is None, (
        "a study found by its marker does not name a sessions folder: the run "
        "keeps working in the current folder, as it always did"
    )

    run = gl.RunContext("a_command", {}, gl.LogSettings(), folders, timestamp="ts")
    assert run.logfolder == os.path.join(str(study), "logs", "ts_a_command")


def test_the_study_alone_gives_the_sessions_folder(tmp_path):
    study = str(tmp_path / "study")
    options, sources, stated = gp.merge_options(
        "hcp_pre_freesurfer", {"studyfolder": study}
    )

    assert options["sessionsfolder"] == os.path.join(study, "sessions")
    assert sources["sessionsfolder"] == gcs.FROM_STUDYFOLDER
    assert stated["sessionsfolder"] == os.path.join(study, "sessions"), (
        "it is stated, so a command that declares it is handed it"
    )
    assert options["studyfolder"] == study


def test_the_study_is_where_the_named_sessions_folder_is(tmp_path):
    sessions = str(tmp_path / "study" / "sessions")
    options, sources, stated = gp.merge_options(
        "hcp_pre_freesurfer", {"sessionsfolder": sessions}
    )

    assert options["sessionsfolder"] == sessions
    assert options["studyfolder"] == str(tmp_path / "study")
    assert sources["studyfolder"] == "default"
    assert "studyfolder" not in stated, (
        "a derived study is never handed to a command as if somebody had named "
        "it: create_study takes the folder it creates"
    )


def test_a_named_sessions_folder_wins_in_whatever_tier_it_is_named(tmp_path):
    study = str(tmp_path / "study")
    elsewhere = str(tmp_path / "elsewhere")

    options, sources, _ = gp.merge_options(
        "hcp_pre_freesurfer", {"studyfolder": study, "sessionsfolder": elsewhere}
    )
    assert options["sessionsfolder"] == elsewhere
    assert options["studyfolder"] == study

    options, sources, _ = gp.merge_options(
        "hcp_pre_freesurfer", {"studyfolder": study}, {"sessionsfolder": elsewhere}
    )
    assert options["sessionsfolder"] == elsewhere, (
        "a sessions folder the batch file names beats one derived from the "
        "study the command line names"
    )
    assert sources["sessionsfolder"] == "batch file"

    options, sources, _ = gp.merge_options(
        "hcp_pre_freesurfer", {}, {"studyfolder": study}
    )
    assert options["sessionsfolder"] == os.path.join(study, "sessions")
    assert sources["sessionsfolder"] == gcs.FROM_STUDYFOLDER


def test_a_run_that_names_no_folder_works_in_the_current_one(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    options, sources, stated = gp.merge_options("hcp_pre_freesurfer", {})

    assert options["sessionsfolder"] == str(tmp_path)
    assert options["studyfolder"] == os.path.dirname(str(tmp_path))
    assert sources["sessionsfolder"] == "default"
    assert "sessionsfolder" not in stated


def test_a_run_from_a_study_root_that_names_no_folder_is_in_that_study(
    tmp_path, monkeypatch
):
    study = make_study(tmp_path, ["S01"])
    monkeypatch.chdir(study)

    options, _, _ = gp.merge_options("hcp_pre_freesurfer", {})

    assert options["studyfolder"] == str(study), (
        "the study its logs go to, not the folder above it"
    )
    assert options["sessionsfolder"] == str(study), "the current folder, as always"


@pytest.mark.parametrize(
    "named",
    [{}, {"studyfolder": "STUDY"}, {"sessionsfolder": "SESSIONS"},
     {"studyfolder": "STUDY", "sessionsfolder": "SESSIONS"}],
)
def test_the_test_options_settle_the_folders_as_a_run_does(tmp_path, monkeypatch, named):
    monkeypatch.chdir(tmp_path)
    named = {
        key: str(tmp_path / value.lower()) for key, value in named.items()
    }

    options, _, _ = gp.merge_options("hcp_pre_freesurfer", dict(named))
    mirrored = default_options(**named)

    assert mirrored["sessionsfolder"] == options["sessionsfolder"]
    assert mirrored["studyfolder"] == options["studyfolder"]


def test_an_empty_sessions_folder_is_one_nobody_named(tmp_path, monkeypatch):
    """
    `--sessionsfolder=` -- a recipe variable that expanded to nothing -- made
    merge_options work on the current folder while deduce_folders, which takes
    an empty value as not given, globbed and logged under the study's own.
    """
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    study = str(tmp_path / "study")

    options, sources, _ = gp.merge_options(
        "hcp_pre_freesurfer", {"studyfolder": study, "sessionsfolder": ""}
    )
    folders = gc.deduce_folders({"studyfolder": study, "sessionsfolder": ""})

    assert options["sessionsfolder"] == os.path.join(study, "sessions")
    assert sources["sessionsfolder"] == gcs.FROM_STUDYFOLDER
    assert folders["sessionsfolder"] == options["sessionsfolder"]
    assert options["studyfolder"] == folders["basefolder"] == study


def look_only(sinfo, options, overwrite=False, thread=0):
    """A processing command that does nothing but say it looked."""
    log = gl.ReportLog()
    log.step("looked at %s" % sinfo["id"])
    return log.result("looked", 0, sinfo["id"])


class LookOnly:
    """Stand-in for the registry entry `process.run` is handed."""

    name = "look_only"
    type = "processing/session"
    logging = None

    def load_callable(self):
        return look_only


def run_look_only(tmp_path, **args):
    """Drives the real `process.run` the way `gmri.runCommand` does."""
    batch = tmp_path / "batch.txt"
    batch.write_text("id: S01\nsubject: S01\n\n01: T1w\n")
    args = {"batchfile": str(batch), **args}
    qx_command = LookOnly()
    settings = gl.LogSettings()

    sessions, header = gc.resolve_sessions(
        batchfile=args["batchfile"], command=qx_command.name
    )
    options, sources, _ = gp.merge_options(qx_command.name, args, header)
    folders = gc.deduce_folders({**header, **args})
    run_context = gl.RunContext(qx_command.name, args, settings, folders)
    gl.set_active(settings)
    try:
        gp.run(qx_command, args, sessions, options, sources, run_context)
    finally:
        gl.set_active(None)
    return run_context


def test_a_dry_run_does_not_create_the_sessions_folder(tmp_path):
    study = tmp_path / "study"
    study.mkdir()
    (study / ".qunexstudy").write_text("")

    run_context = run_look_only(tmp_path, studyfolder=str(study), run="test")

    assert not (study / "sessions").exists()
    runlog = next(Path(run_context.logfolder).glob("Log-*.log")).read_text()
    assert "test, not created: %s" % (study / "sessions") in runlog


def test_a_run_in_a_study_that_does_not_exist_fails_with_a_message(tmp_path):
    """
    A mistyped --studyfolder ended in a bare FileNotFoundError traceback from
    os.mkdir; it is now a command failure that names the folder.
    """
    typo = tmp_path / "typo"

    with pytest.raises(ge.CommandFailed) as failure:
        run_look_only(
            tmp_path, studyfolder=str(typo), logfolder=str(tmp_path / "logs"),
            run="run",
        )

    assert failure.value.error == "Missing study folder"
    assert any(str(typo / "sessions") in hint for hint in failure.value.hints)
    assert not typo.exists()


def test_a_run_creates_a_missing_sessions_folder_in_its_study(tmp_path):
    study = tmp_path / "study"
    study.mkdir()
    (study / ".qunexstudy").write_text("")

    run_look_only(tmp_path, studyfolder=str(study), run="run")

    assert (study / "sessions").is_dir()


# ------------------------------------------------------------------------------
#                                                     sessions read from files


BATCH = """# a batch file
_hcp_brainsize: 150
---
session: S01
subject: S01
dicom: dicom
raw_data: nii
data: 4dfp
hcp: hcp
bids: /old/study/sessions/S01/bids

01: T1w
---
session: S02
subject: S02
hcp: hcp

01: T1w
"""


def test_a_batch_file_is_read_as_written(tmp_path):
    batch = tmp_path / "batch.txt"
    batch.write_text(BATCH)

    sessions, header = gc.read_batch(str(batch))
    assert sessions[0]["hcp"] == "hcp", "the reader does not know the sessions folder"
    assert header == {"hcp_brainsize": "150"}


def test_the_sessions_folders_are_resolved_against_the_sessions_folder(tmp_path):
    batch = tmp_path / "batch.txt"
    batch.write_text(BATCH)
    sessionsfolder = str(tmp_path / "study" / "sessions")

    sessions, _ = gc.resolve_sessions(batchfile=str(batch), sessionsfolder=sessionsfolder)
    s01, s02 = sessions

    assert s01["hcp"] == os.path.join(sessionsfolder, "S01", "hcp")
    assert s01["raw_data"] == os.path.join(sessionsfolder, "S01", "nii")
    assert s01["dicom"] == os.path.join(sessionsfolder, "S01", "dicom")
    assert s01["data"] == os.path.join(sessionsfolder, "S01", "4dfp")
    assert s01["bids"] == "/old/study/sessions/S01/bids", "absolute stays absolute"
    assert s02["hcp"] == os.path.join(sessionsfolder, "S02", "hcp")
    assert "raw_data" not in s02, "nothing is added"

    raw, _ = gc.resolve_sessions(
        batchfile=str(batch), sessionsfolder=sessionsfolder, resolve_folders=False
    )
    assert raw[0]["hcp"] == "hcp"

    unknown, _ = gc.resolve_sessions(batchfile=str(batch))
    assert unknown[0]["hcp"] == "hcp", "no sessions folder, nothing to resolve against"


def test_a_missing_folder_is_warned_about(tmp_path, capsys):
    batch = tmp_path / "batch.txt"
    batch.write_text(BATCH)

    gc.resolve_sessions(
        batchfile=str(batch), sessionsfolder=str(tmp_path / "sessions"), verbose=True
    )

    out = capsys.readouterr().out
    assert "folder hcp" in out, "hcp is checked too, not the 'hpc' it used to look for"


# ------------------------------------------------------------------------------
#                                                         what the writers write


def test_a_session_file_records_the_session_folders_relative_to_it(tmp_path):
    session = tmp_path / "sessions" / "S01"
    (session / "bids").mkdir(parents=True)
    (session / "nii").mkdir()

    gc.create_session_file("test", str(session), "S01", "S01", "no").close()

    text = (session / "session.txt").read_text()
    assert "bids: bids\n" in text
    assert "raw_data: nii\n" in text
    assert "hcp: hcp\n" in text
    assert str(tmp_path) not in text


def test_a_session_without_nifti_records_no_raw_data(tmp_path):
    session = tmp_path / "sessions" / "S01"
    (session / "bids").mkdir(parents=True)

    gc.create_session_file("test", str(session), "S01", "S01", "no").close()

    assert "raw_data" not in (session / "session.txt").read_text(), (
        "it was gated on the bids folder, not on the nii folder"
    )


def write_session_hcp(study, session, extra=""):
    folder = study / "sessions" / session
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "session_hcp.txt").write_text(
        "session: %s\nsubject: %s\nhcp: hcp\n%s\n01: T1w\n" % (session, session, extra)
    )


def test_a_batch_file_goes_to_the_study_and_names_nothing_absolute(tmp_path):
    study = make_study(tmp_path)
    for session in ["OP1", "OP10"]:
        write_session_hcp(study, session)

    gu.create_batch(studyfolder=str(study))

    batch = study / "processing" / "batch.txt"
    text = batch.read_text()
    assert "# Sessions folder: ../sessions\n" in text
    assert str(tmp_path) not in text, "a moved study keeps a valid batch file"

    sessions, _ = gc.resolve_sessions(
        batchfile=str(batch), sessionsfolder=str(study / "sessions")
    )
    assert [s["hcp"] for s in sessions] == [
        str(study / "sessions" / "OP1" / "hcp"),
        str(study / "sessions" / "OP10" / "hcp"),
    ]


def test_the_batch_file_goes_to_the_named_study_whatever_the_sessions_folder(tmp_path):
    study = make_study(tmp_path)
    elsewhere = tmp_path / "elsewhere" / "sessions"
    (elsewhere / "S01").mkdir(parents=True)
    (elsewhere / "S01" / "session_hcp.txt").write_text("session: S01\n\n01: T1w\n")

    gu.create_batch(studyfolder=str(study), sessionsfolder=str(elsewhere))

    assert (study / "processing" / "batch.txt").exists()
    assert gr._produced_path(
        "create_batch",
        "targetfile",
        {"studyfolder": str(study), "sessionsfolder": str(elsewhere)},
        {"basefolder": str(study)},
    ) == str(study / "processing" / "batch.txt"), (
        "a recipe predicts the file create_batch writes"
    )


def test_appending_a_session_leaves_the_ones_it_prefixes(tmp_path):
    study = make_study(tmp_path)
    for session in ["OP1", "OP10", "OP11"]:
        write_session_hcp(study, session)
    gu.create_batch(studyfolder=str(study))

    write_session_hcp(study, "OP1", extra="group: control\n")
    gu.create_batch(studyfolder=str(study), sessions="OP1", overwrite="append")

    sessions, _ = gc.resolve_sessions(batchfile=str(study / "processing" / "batch.txt"))
    ids = sorted(s["id"] for s in sessions)
    assert ids == ["OP1", "OP10", "OP11"], "appending OP1 used to remove OP10 and OP11"
    assert [s.get("group") for s in sessions if s["id"] == "OP1"] == ["control"]


def test_only_a_named_parameter_file_heads_the_batch_file(tmp_path):
    study = make_study(tmp_path)
    write_session_hcp(study, "OP1")
    specs = study / "sessions" / "specs"
    specs.mkdir(exist_ok=True)
    (specs / "parameters.txt").write_text("_hcp_processing_mode: unnamed\n")
    named = tmp_path / "named.txt"
    named.write_text("_hcp_processing_mode: named\n")
    batch = study / "processing" / "batch.txt"

    gu.create_batch(studyfolder=str(study))
    assert gc.read_batch(str(batch))[1] == {}, "a file nobody named is not used"

    gu.create_batch(studyfolder=str(study), paramfile=str(named), overwrite="yes")
    assert gc.read_batch(str(batch))[1] == {"hcp_processing_mode": "named"}


def test_a_named_parameter_file_that_is_missing_stops_create_batch(tmp_path):
    """
    A named parameter file that was not found used to be skipped with a note:
    the batch file was written without its header and the run succeeded.
    """
    study = make_study(tmp_path)
    write_session_hcp(study, "OP1")
    batch = study / "processing" / "batch.txt"
    missing = tmp_path / "specs" / "parameters.txt"

    with pytest.raises(ge.CommandFailed) as failed:
        gu.create_batch(studyfolder=str(study), paramfile=str(missing))
    assert str(missing) in " ".join(failed.value.report)
    assert not batch.exists(), "no batch file is written without its header"

    # appending leaves an existing header as it is, so the file is not read
    gu.create_batch(studyfolder=str(study))
    gu.create_batch(
        studyfolder=str(study), paramfile=str(missing), overwrite="append"
    )


def test_appending_keeps_every_block_a_session_has_in_the_run(tmp_path):
    """
    With two source files a session contributes two blocks. Append mode
    removed the session's existing block before each file it appended, so the
    second removal took out the block the first file had just written: append
    left one block where overwrite=yes leaves two.
    """
    study = make_study(tmp_path)
    for session in ["OP1", "OP2"]:
        folder = study / "sessions" / session
        folder.mkdir()
        for name, tag in [("session_hcp.txt", "hcp"), ("session.txt", "plain")]:
            (folder / name).write_text(
                "session: %s\nsubject: %s\nsrc: %s\n" % (session, session, tag)
            )

    batch = study / "processing" / "batch.txt"

    def blocks():
        sessions, _ = gc.read_batch(str(batch))
        return sorted((s["id"], s["src"]) for s in sessions)

    both = [("OP1", "hcp"), ("OP1", "plain"), ("OP2", "hcp"), ("OP2", "plain")]
    sources = "session_hcp.txt,session.txt"

    gu.create_batch(studyfolder=str(study), sourcefiles=sources, overwrite="yes")
    assert blocks() == both

    gu.create_batch(studyfolder=str(study), sourcefiles=sources, overwrite="append")
    assert blocks() == both, "replaced, neither lost nor doubled"

    gu.create_batch(
        studyfolder=str(study), sourcefiles=sources, overwrite="append", sessions="OP1"
    )
    assert blocks() == both


def test_a_session_block_is_removed_by_its_own_id(tmp_path):
    batch = tmp_path / "batch.txt"
    batch.write_text(
        "# header\n_x: 1\n"
        "\n---\nsession: OP1\nsubject: OP1\n"
        "\n---\nid: OP10\nsubject: OP10\n"
        "\n---\nid: OP1\nsubject: OP1\n"
    )

    gu.remove_session_block(str(batch), "OP1")

    sessions, header = gc.read_batch(str(batch))
    assert [s["id"] for s in sessions] == ["OP10"], "both spellings, and only OP1"
    assert header == {"x": "1"}


def test_a_pipeline_ready_session_file_is_copied_in_its_own_folder(
    tmp_path, monkeypatch
):
    study = make_study(tmp_path, ["S01"])
    session = study / "sessions" / "S01"
    (session / "session.txt").write_text(
        "session: S01\nsubject: S01\nhcp: hcp\nhcpready: true\n\n01: T1w\n"
    )
    mapping = tmp_path / "mapping.txt"
    mapping.write_text("T1w => T1w\n")

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    gu.create_session_info(
        sessions="S01", sessionsfolder=str(study / "sessions"), mapping=str(mapping)
    )

    assert (session / "session_hcp.txt").read_text() == (
        session / "session.txt"
    ).read_text()
    assert not (elsewhere / "session_hcp.txt").exists(), (
        "the copy was made between bare names, in the current folder"
    )


def merge_source(folder, session_id, bids=False):
    folder.mkdir(parents=True)
    (folder / "session.txt").write_text(
        "id: %s\nsubject: A\nhcp: /old/place/%s/hcp\nbids: /old/place/%s/bids\n"
        "institution: here\n\n1011:tag1:Scan1: TR(1.0)\n"
        % (session_id, session_id, session_id)
    )
    if bids:
        (folder / "bids").mkdir()
        (folder / "bids" / "sub.json").write_text("{}")


def test_a_merged_session_records_its_own_folders(tmp_path):
    study = make_study(tmp_path)
    merge_source(study / "sessions" / "A_1", "A_1", bids=True)
    merge_source(study / "sessions" / "A_2", "A_2")

    assert gs.merge_session(
        studyfolder=str(study), source="A_1,A_2", target="A", raw_data="copy"
    )

    text = (study / "sessions" / "A" / "session.txt").read_text()
    for line in ["dicom: dicom", "raw_data: nii", "data: 4dfp", "hcp: hcp", "bids: bids"]:
        assert line in [" ".join(e.split()) for e in text.split("\n")], line
    assert "/old/place" not in text, (
        "the sources' folders are not carried over: they name the sources"
    )
    assert "institution" in text, "the rest of their metadata still is"


def test_a_merge_finds_sessions_in_a_named_sessions_folder(tmp_path):
    study = make_study(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    merge_source(elsewhere / "B_1", "B_1")
    merge_source(elsewhere / "B_2", "B_2")

    assert gs.merge_session(
        studyfolder=str(study),
        sessionsfolder=str(elsewhere),
        source="B_1,B_2",
        target="B",
        raw_data="leave",
    )
    assert (elsewhere / "B" / "session.txt").exists()
    assert not (study / "sessions" / "B").exists()


# ------------------------------------------------------------------------------
#                                       the container launcher, outside the study


@pytest.fixture
def placed(tmp_path, monkeypatch):
    """
    Where the launcher places a run of `cmd` stamped `ts`, on the host, from
    its command line and a batch file header: started in `tmp_path`, outside
    any study, with a home folder of its own and so no user settings file.
    """
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.chdir(tmp_path)
    qc = load_container()

    def place(args, header=None):
        return qc.host_placement("cmd", args, header or {}, "ts").logfolder

    return place


def test_the_container_logs_into_the_study_the_run_names(tmp_path, placed):
    study = str(tmp_path / "study")
    other = make_study(tmp_path / "x")
    in_other = os.path.join(str(other), "logs", "ts_cmd")

    assert placed({"studyfolder": study}) == os.path.join(study, "logs", "ts_cmd")
    assert placed(
        {"studyfolder": study, "sessionsfolder": str(other / "sessions")}
    ) == os.path.join(study, "logs", "ts_cmd"), "the named study wins"
    assert placed({"sessionsfolder": str(other / "sessions")}) == in_other
    assert placed({"logfolder": "/given"}) == "/given"
    assert placed({}) == os.path.join(str(tmp_path / "home"), "qunex_logs", "ts_cmd"), (
        "with no study it is the folder QuNex logs such a run in, not ~/qunex"
    )


def test_the_container_logs_into_the_study_the_batch_file_header_names(
    tmp_path, placed
):
    """The launcher used to read only the command line, and logged in ~/qunex."""
    study = str(tmp_path / "study")
    other = make_study(tmp_path / "x")

    assert placed({}, {"studyfolder": study}) == os.path.join(study, "logs", "ts_cmd")
    assert placed({"studyfolder": str(other)}, {"studyfolder": study}) == os.path.join(
        str(other), "logs", "ts_cmd"
    ), "the command line wins over the header"
    assert placed(
        {"unset_batch_header_parameters": "studyfolder"}, {"studyfolder": study}
    ) == os.path.join(str(tmp_path / "home"), "qunex_logs", "ts_cmd"), (
        "not what the run says not to take from the header"
    )
    assert placed(
        {"unset_batch_header_parameters": True}, {"studyfolder": study}
    ) == os.path.join(study, "logs", "ts_cmd"), "a flag without a value unsets nothing"


def test_the_container_legacy_log_folder_is_the_study_processing_logs(tmp_path, placed):
    study = str(tmp_path / "study")

    assert placed({"studyfolder": study, "logfolder": "legacy"}) == os.path.join(
        study, "processing", "logs"
    ), "it used to be a folder named ./legacy"


def test_the_container_globs_sessions_in_the_study_sessions_folder():
    qc = load_container()
    assert qc.sessions_folder("/s", None, default=None) == os.path.join(
        "/s", "sessions"
    )
    assert qc.sessions_folder("/s", "/x", default=None) == "/x"
    assert qc.sessions_folder(None, "/x", default=None) == "/x"
    assert qc.sessions_folder(None, None, default=None) is None


def test_the_container_expands_only_the_globs_among_the_sessions(tmp_path):
    qc = load_container()
    study = make_study(tmp_path, ["S001", "S002", "T001"])
    folder = str(study / "sessions")

    assert qc.expand_session_globs("S001,S003", folder) == "S001,S003", (
        "a plain id is kept whether or not its folder exists yet"
    )
    assert qc.expand_session_globs("S0*", folder) == "S001,S002"
    assert qc.expand_session_globs("S00?|T001", folder) == "S001,S002,T001"
    assert qc.expand_session_globs("X*", folder) == "X*", (
        "a glob matching nothing is passed on as it was given"
    )
    assert qc.expand_session_globs("my.list", folder) == "my.list", (
        "a list file is read, not matched"
    )
    assert qc.expand_session_globs("S0*", None) == "S0*"
    assert qc.expand_session_globs(None, folder) is None


def run_container(qc, monkeypatch, tmp_path, *args):
    """
    Runs the launcher's main() with the container never started, and returns
    the commands it would have run in it.
    """
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    ran = []
    monkeypatch.setattr(qc.subprocess, "run", lambda *a, **k: ran.append(a[0]))
    qc.main(list(args) + ["--container=x.sif"])

    scripts = sorted(Path(tmp_path).rglob("qunex_container_command_*.sh"))
    return ran, [script.read_text() for script in scripts]


@pytest.mark.parametrize("command", ["import_dicom", "hcp_freesurfer"])
def test_the_container_keeps_named_sessions_that_do_not_exist_yet(
    tmp_path, capsys, command
):
    """
    With --studyfolder alone the launcher matched every named id against the
    study's sessions folder, so `--sessions=S001,S002` with only S001 there
    imported S001 alone, and a scheduled run of a fresh study was one job
    rather than one per session.
    """
    qc = load_container()
    study = make_study(tmp_path, ["S001"])

    qc.main([
        command, "--studyfolder=%s" % study, "--sessions=S001,S002",
        "--container=x.sif", "--parinfo", "--scheduler=SLURM,time=1:00:00",
        "--parsessions=1",
    ])

    out = capsys.readouterr().out
    assert "Job #1 will run sessions: S001" in out
    assert "Job #2 will run sessions: S002" in out


@pytest.mark.parametrize("name", ["sessionsfolder", "subjectsfolder", "basefolder"])
def test_the_container_globs_sessions_in_a_sessions_folder_named_any_way(
    tmp_path, capsys, name
):
    """
    A deprecated name of the sessions folder names the sessions folder, as
    QuNex reads it. The launcher read only the name it has now, matched no
    session, and scheduled one job for all of them.
    """
    qc = load_container()
    study = make_study(tmp_path, ["S001", "S002"])

    qc.main([
        "hcp_freesurfer", "--%s=%s" % (name, study / "sessions"),
        "--sessions=S00*", "--container=x.sif", "--parinfo",
        "--scheduler=SLURM,time=1:00:00",
    ])

    out = capsys.readouterr().out
    assert "Job #1 will run sessions: S001" in out
    assert "Job #2 will run sessions: S002" in out


def test_the_container_splits_a_fresh_study_into_one_job_per_session(
    tmp_path, capsys
):
    qc = load_container()
    study = make_study(tmp_path)

    qc.main([
        "import_dicom", "--studyfolder=%s" % study, "--sessions=S001,S002",
        "--container=x.sif", "--parinfo", "--scheduler=SLURM,time=1:00:00",
        "--parsessions=1",
    ])

    out = capsys.readouterr().out
    assert "schedule 2 jobs" in out
    assert "Job #2 will run sessions: S002" in out


def test_the_container_hands_an_unscheduled_run_every_named_session(
    tmp_path, monkeypatch
):
    qc = load_container()
    study = make_study(tmp_path, ["S001"])

    ran, scripts = run_container(
        qc, monkeypatch, tmp_path,
        "import_dicom", "--studyfolder=%s" % study, "--sessions=S001,S002",
    )

    assert len(ran) == 1 and len(scripts) == 1
    assert '--sessions="S001,S002"' in scripts[0]


@pytest.mark.parametrize(
    "command, sessions, expected",
    [
        ("hcp_freesurfer", "S0*", '--sessions="S001,S002"'),
        ("import_dicom", "S0*", '--sessions="S0*"'),
        ("import_dicom", ".*_baseline", '--sessions=".*_baseline"'),
    ],
    ids=["a processing glob", "an import glob", "an import regex"],
)
def test_the_container_globs_the_sessions_of_everything_but_an_import(
    tmp_path, monkeypatch, command, sessions, expected
):
    """
    An import's --sessions names sessions that do not exist yet, or patterns
    over the inbox, so nothing it names is matched against the study.
    """
    qc = load_container()
    study = make_study(tmp_path, ["S001", "S002", "X1_baseline"])

    _, scripts = run_container(
        qc, monkeypatch, tmp_path,
        command, "--studyfolder=%s" % study, "--sessions=%s" % sessions,
    )

    assert len(scripts) == 1
    assert expected in scripts[0], scripts[0]


def test_the_container_reads_a_list_file_given_as_the_sessions(
    tmp_path, monkeypatch
):
    qc = load_container()
    study = make_study(tmp_path, ["S001"])
    listfile = tmp_path / "my.list"
    listfile.write_text("session id: S001\nsession id: S002\n")

    _, scripts = run_container(
        qc, monkeypatch, tmp_path,
        "hcp_freesurfer", "--studyfolder=%s" % study, "--sessions=%s" % listfile,
    )

    assert len(scripts) == 1
    assert '--sessions="S001,S002"' in scripts[0], scripts[0]

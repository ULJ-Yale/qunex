# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Regression tests for ``hcp_temporal_ica``, the HCP group command.

They cover what it reports and links: its group folder, into which it links
the average dataset from where ``hcp_make_average_dataset`` makes it, and the
folders and links it replaces, keeps or refuses to write over. The session
steps (``hcp_prep_long``, ``hcp_make_average_dataset``,
``hcp_long_transmit_bias``, ``hcp_long_msmall``) are covered in
``test_hcp_long_dryrun_steps.py``.

Nothing external runs: a dry run builds the command only, and a real run gets
a stub in place of ``pc.run_external_for_file``.
"""

import os
import re

import pytest

import qx_utilities.general.core as gc
import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_make_average_dataset import hcp_make_average_dataset
from qx_utilities.hcp.hcp_temporal_ica import hcp_temporal_ica

from .utils import build_hcp_session, default_options

GROUP = "grp"


@pytest.fixture
def study(tmp_path, monkeypatch):
    """
    A study with sessions s1 and s2 of subject subj-01, the options to run a
    command on it, and a stub in place of the external call that records the
    scripts it was asked to run.
    """
    monkeypatch.setenv("HCPPIPEDIR", str(tmp_path / "hcppipedir"))
    monkeypatch.setenv("QUNEXPATH", str(tmp_path / "qunexpath"))

    root = tmp_path / "study"
    sinfos = []
    for sid in ("s1", "s2"):
        sinfo, sessionsfolder = build_hcp_session(str(root), session_id=sid)
        sinfos.append(sinfo)

    calls = []
    outcome = {"failed": 0}

    def fake_run_external_for_file(tfile, comm, *args, **kwargs):
        calls.append(os.path.basename(comm.split()[0]))
        return None, "done", outcome["failed"]

    monkeypatch.setattr(pc, "run_external_for_file", fake_run_external_for_file)

    def options(run, **overrides):
        return default_options(
            run=run,
            studyfolder=str(root),
            comlogs=str(tmp_path / "comlogs"),
            logfolder=str(tmp_path / "logs"),
            **overrides,
        )

    class Study:
        pass

    s = Study()
    s.root = root
    s.sessionsfolder = sessionsfolder
    s.sessions = gc.SessionList(sinfos)
    s.options = options
    s.calls = calls
    s.outcome = outcome
    return s


def session_hcp(study, sid):
    """The folder a session's link points to: <session>/hcp/<session>."""
    return os.path.join(study.sessionsfolder, sid, "hcp", sid)


def tree(root):
    """Every entry under root, with where each link points."""
    entries = set()
    for folder, dirs, files in os.walk(root):
        for name in dirs + files:
            path = os.path.join(folder, name)
            target = os.readlink(path) if os.path.islink(path) else None
            entries.add((os.path.relpath(path, root), target))
    return entries


# ------------------------------------------------------------ hcp_temporal_ica


def tica_options(study, run, **overrides):
    """The options that let a multi-session tICA reach its command."""
    return study.options(
        run,
        hcp_outgroupname=GROUP,
        hcp_tica_bolds="BOLD_1",
        hcp_tica_surfregname="MSMAll",
        hcp_icafix_highpass="0",
        hcp_tica_timepoints="100",
        hcp_tica_num_wishart="6",
        hcp_matlab_mode="interpreted",
        **overrides,
    )


def made_average_dataset(study):
    """
    The folder MakeAverageDataset.sh writes the average dataset into: the
    --group-average-name folder of the --study-folder hcp_make_average_dataset
    hands it, as its dry run names them.
    """
    log = hcp_make_average_dataset(
        study.sessions, study.options("test", hcp_outgroupname=GROUP)
    )
    args = dict(re.findall(r'--([\w-]+)="([^"]*)"', log.text))
    return os.path.join(args["study-folder"], args["group-average-name"])


def make_average_dataset_output(study, folder=None, registration="MSMAll"):
    """
    What MakeAverageDataset.sh writes, by default where it writes it: the
    average wmparc tICA reads, and the vertex areas of a registration. Returns
    the folder.
    """
    folder = folder or made_average_dataset(study)
    mni = os.path.join(folder, "MNINonLinear")
    os.makedirs(os.path.join(mni, "fsaverage_LR32k"))
    open(os.path.join(mni, f"{GROUP}_Averagewmparc.nii.gz"), "w").close()
    va = f"{GROUP}.midthickness_{registration}_va.32k_fs_LR.dscalar.nii"
    open(os.path.join(mni, "fsaverage_LR32k", va), "w").close()
    return folder


def group_folder(study):
    """The group folder of a multi-session run, which tICAPipeline.sh reads."""
    return os.path.join(study.sessionsfolder, GROUP, GROUP)


def test_temporal_ica_dry_run_says_it_can_be_run(study):
    """
    The dry run asked check_run(None, ...), which always answers 'done', so
    a multi-session --test reported 'HCP temporal ICA finished'.
    """
    average = make_average_dataset_output(study)
    before = tree(study.root)

    log = hcp_temporal_ica(study.sessions, tica_options(study, "test"))

    assert log.status == ("s1,s2", "HCP temporal ICA can be run", 0)
    assert "HCP temporal ICA can be run" in log.text
    assert "finished" not in log.text
    assert study.calls == []

    # the group folder is named, not made, and the sessions and the average
    # dataset are not linked
    group_dir = os.path.join(study.sessionsfolder, GROUP)
    assert f"test, not created: {group_dir}" in log.text
    for sid in ("s1", "s2"):
        target = os.path.join(group_dir, sid)
        assert f"test, not linked: {target} -> {session_hcp(study, sid)}" in log.text
    assert f"test, not linked: {group_folder(study)} -> {average}" in log.text
    assert not os.path.lexists(group_dir)
    assert tree(study.root) == before


def test_temporal_ica_runs_on_the_average_dataset_where_it_was_made(study):
    """
    MakeAverageDataset.sh writes into the <group> folder of the study folder
    hcp_make_average_dataset hands it, <sessions>/average_dataset/<group>/<group>,
    and tICA looked for it one level higher: a multi-session run could never
    start. tICAPipeline.sh reads the dataset from its own group folder, so that
    is where it is linked, and a later step uses the link as it is.
    """
    average = make_average_dataset_output(study)

    log = hcp_temporal_ica(study.sessions, tica_options(study, "run"))

    assert log.status == ("s1,s2", "done", 0)
    assert study.calls == ["tICAPipeline.sh"]
    assert os.readlink(group_folder(study)) == average

    log = hcp_temporal_ica(
        study.sessions,
        tica_options(
            study,
            "run",
            hcp_tica_starting_step="CleanData",
            hcp_tica_stop_after_step="CleanData",
        ),
    )

    assert log.status == ("s1,s2", "done", 0)
    assert study.calls == ["tICAPipeline.sh", "tICAPipeline.sh"]
    assert os.readlink(group_folder(study)) == average


def test_temporal_ica_dry_run_names_no_link_already_in_place(study):
    """
    The dry run reported every link as one it would make, also those an
    earlier run had made.
    """
    make_average_dataset_output(study)
    hcp_temporal_ica(study.sessions, tica_options(study, "run"))
    before = tree(study.root)

    log = hcp_temporal_ica(study.sessions, tica_options(study, "test"))

    assert log.status == ("s1,s2", "HCP temporal ICA can be run", 0)
    assert "test, not linked" not in log.text
    assert tree(study.root) == before


def test_temporal_ica_without_the_average_dataset_cannot_be_run(study):
    log = hcp_temporal_ica(study.sessions, tica_options(study, "run"))

    assert log.status == ("s1,s2", "HCP temporal ICA cannot be run", 1)
    wmparc = os.path.join(
        made_average_dataset(study), "MNINonLinear", f"{GROUP}_Averagewmparc.nii.gz"
    )
    assert f"{wmparc} does not exist!" in log.text
    assert f"run hcp_make_average_dataset with --hcp_outgroupname={GROUP}" in log.text
    assert study.calls == []
    # and nothing is left in the way of the link a later run makes
    assert not os.path.lexists(group_folder(study))


def test_temporal_ica_takes_an_average_dataset_of_any_registration(study):
    """
    The check looked for the MSMAll 32k vertex areas, which
    hcp_make_average_dataset writes only with --hcp_mad_regname=MSMAll and a
    32k mesh; tICA reads the average wmparc, written whatever the registration.
    """
    make_average_dataset_output(study, registration="MSMSulc")

    log = hcp_temporal_ica(study.sessions, tica_options(study, "run"))

    assert log.status == ("s1,s2", "done", 0)
    assert study.calls == ["tICAPipeline.sh"]


def test_temporal_ica_replaces_the_empty_group_folder_a_failed_run_left(study):
    """
    The run that could not find the average dataset still made an empty
    <group>/MNINonLinear, which stood in the way of the link.
    """
    average = make_average_dataset_output(study)
    group = group_folder(study)
    os.makedirs(os.path.join(group, "MNINonLinear"))
    before = tree(study.root)

    log = hcp_temporal_ica(study.sessions, tica_options(study, "test"))

    assert log.status == ("s1,s2", "HCP temporal ICA can be run", 0)
    assert f"test, not removed: {group}" in log.text
    assert f"test, not linked: {group} -> {average}" in log.text
    assert tree(study.root) == before

    log = hcp_temporal_ica(study.sessions, tica_options(study, "run"))

    assert log.status == ("s1,s2", "done", 0)
    assert f"removed empty folder: {group}" in log.text
    assert os.readlink(group) == average


def test_temporal_ica_keeps_the_empty_group_folder_for_a_missing_dataset(study, tmp_path):
    """A link that cannot be made leaves the folder in its place as it is."""
    group = group_folder(study)
    os.makedirs(os.path.join(group, "MNINonLinear"))
    missing = str(tmp_path / "missing")

    log = hcp_temporal_ica(
        study.sessions, tica_options(study, "run", hcp_tica_average_dataset=missing)
    )

    assert log.status == ("s1,s2", "HCP temporal ICA cannot be run", 1)
    assert f"source file does not exist [{missing}]" in log.text
    assert os.path.isdir(os.path.join(group, "MNINonLinear"))
    assert not os.path.islink(group)
    assert study.calls == []


def test_temporal_ica_does_not_replace_a_group_folder_with_files(study):
    make_average_dataset_output(study)
    group = group_folder(study)
    os.makedirs(os.path.join(group, "MNINonLinear"))
    keep = os.path.join(group, "MNINonLinear", "keep.txt")
    open(keep, "w").close()

    log = hcp_temporal_ica(study.sessions, tica_options(study, "run"))

    assert log.status == ("s1,s2", "HCP temporal ICA cannot be run", 1)
    assert f"{group} is a folder, cannot link" in log.text
    assert "Move it out of the way." in log.text
    assert study.calls == []
    assert os.path.exists(keep)


def test_temporal_ica_does_not_take_a_folder_it_cannot_read_for_empty(study):
    """
    os.walk passes over a folder it cannot read, so a group folder with files
    in one looked empty, and the dry run said it would be replaced.
    """
    make_average_dataset_output(study)
    group = group_folder(study)
    locked = os.path.join(group, "MNINonLinear", "locked")
    os.makedirs(locked)
    open(os.path.join(locked, "keep.txt"), "w").close()
    os.chmod(locked, 0)
    try:
        log = hcp_temporal_ica(study.sessions, tica_options(study, "test"))
    finally:
        os.chmod(locked, 0o755)

    assert log.status == ("s1,s2", "HCP temporal ICA cannot be run", 1)
    assert f"{group} is a folder, cannot link" in log.text
    assert "test, not removed" not in log.text
    assert os.path.exists(os.path.join(locked, "keep.txt"))


@pytest.mark.skipif(
    hasattr(os, "geteuid") and os.geteuid() == 0,
    reason="root removes a folder whatever its permissions",
)
def test_temporal_ica_reports_an_empty_group_folder_it_cannot_remove(study):
    """The run fails with the reason, and the folder is left as it is."""
    make_average_dataset_output(study)
    group = group_folder(study)
    os.makedirs(os.path.join(group, "MNINonLinear"))
    os.chmod(group, 0o555)
    try:
        log = hcp_temporal_ica(study.sessions, tica_options(study, "run"))
    finally:
        os.chmod(group, 0o755)

    assert log.status == ("s1,s2", "HCP temporal ICA cannot be run", 1)
    assert f"{group} could not be removed" in log.text
    assert os.path.isdir(os.path.join(group, "MNINonLinear"))
    assert not os.path.islink(group)
    assert study.calls == []


def test_temporal_ica_keeps_a_group_folder_that_holds_an_average_dataset(study, tmp_path):
    """
    A group folder that already holds an average dataset, made in it before
    hcp_make_average_dataset moved to average_dataset or linked by an earlier
    run, is used as it is: the group's results are in it.
    """
    in_place = make_average_dataset_output(study, group_folder(study))
    make_average_dataset_output(study)

    log = hcp_temporal_ica(study.sessions, tica_options(study, "run"))

    assert log.status == ("s1,s2", "done", 0)
    assert not os.path.islink(in_place)
    assert f"{in_place} holds an average dataset, used as it is" in log.text

    # nor is a link to a dataset named in an earlier run replaced
    os.rename(in_place, tmp_path / "earlier")
    os.symlink(tmp_path / "earlier", in_place)

    log = hcp_temporal_ica(study.sessions, tica_options(study, "run"))

    assert log.status == ("s1,s2", "done", 0)
    assert os.readlink(in_place) == str(tmp_path / "earlier")
    assert f"{in_place} holds an average dataset, used as it is" in log.text


def test_temporal_ica_longitudinal_keeps_a_group_folder_of_its_own(study):
    """
    The longitudinal run linked the average dataset's study folder, one level
    above the dataset, as the subject's group folder, so the subject's results
    went into the sessions folder. A longitudinal run is REUSE_TICA, which
    reads no average dataset: the subject's group folder is its own.
    """
    make_average_dataset_output(study)
    options = tica_options(
        study,
        "run",
        longitudinal=True,
        hcp_longitudinal_subject="subj-01",
        hcp_longitudinal_sessions="s1,s2",
        hcp_tica_extract_fmri_out="rfMRI_REST",
    )

    log = hcp_temporal_ica(study.sessions, options)

    assert log.status[2] == 0
    assert study.calls == ["tICAPipeline.sh"]
    group = study.root / "subjects" / "subj-01" / GROUP
    assert not os.path.islink(group)
    assert (group / "MNINonLinear").is_dir()


def test_temporal_ica_single_session_makes_its_group_folder(study):
    """
    A REUSE mode writes into <group>/MNINonLinear without making it, when the
    precomputed tICA has no volume template at the run's resolution.
    """
    sessions = gc.SessionList([study.sessions[0]])
    options = tica_options(
        study,
        "run",
        hcp_tica_icamode="REUSE_TICA",
        hcp_tica_precomputed_clean_folder="/precomputed/G",
        hcp_tica_precomputed_fmri_name="rfMRI_REST",
        hcp_tica_precomputed_group_name="G",
        hcp_tica_sicadim_override="10",
    )

    log = hcp_temporal_ica(sessions, options)

    assert log.status[2] == 0
    assert study.calls == ["tICAPipeline.sh"]
    group = os.path.join(study.sessionsfolder, "s1", "hcp", GROUP)
    assert os.path.isdir(os.path.join(group, "MNINonLinear"))


def test_temporal_ica_links_a_relative_average_dataset_that_resolves(study, monkeypatch):
    """
    A relative --hcp_tica_average_dataset was linked as given, and so read
    from the group folder's own folder: the link dangled and the run was
    reported done.
    """
    make_average_dataset_output(study, os.path.join(study.root, "my_average"))
    monkeypatch.chdir(study.root)

    log = hcp_temporal_ica(
        study.sessions, tica_options(study, "run", hcp_tica_average_dataset="my_average")
    )

    assert log.status[2] == 0
    assert os.path.samefile(group_folder(study), study.root / "my_average")


def test_temporal_ica_refuses_to_write_over_the_precomputed_tica(study, tmp_path):
    """
    The average dataset of a group is also the folder of its tICA results, so
    a REUSE run of another group naming both would write into, and remove
    files of, the tICA it reuses.
    """
    other = make_average_dataset_output(study, str(tmp_path / "other" / "average"))
    os.makedirs(tmp_path / "other" / GROUP)
    os.symlink(other, tmp_path / "other" / GROUP / GROUP)
    options = tica_options(
        study,
        "run",
        hcp_tica_average_dataset=other,
        hcp_tica_icamode="REUSE_TICA",
        hcp_tica_precomputed_clean_folder=str(tmp_path / "other" / GROUP / GROUP),
        hcp_tica_precomputed_fmri_name="rfMRI_REST",
        hcp_tica_precomputed_group_name=GROUP,
        hcp_tica_sicadim_override="10",
    )

    log = hcp_temporal_ica(study.sessions, options)

    assert log.status == ("s1,s2", "HCP temporal ICA cannot be run", 1)
    assert "the run would write over it" in log.text
    assert study.calls == []
    assert not os.path.lexists(group_folder(study))


def test_temporal_ica_refuses_its_own_group_folder_as_the_precomputed_tica(study):
    """
    The group folder becomes the average dataset by a link made as the run
    starts, so before it is there the two do not resolve to one folder.
    """
    make_average_dataset_output(study)
    options = tica_options(
        study,
        "run",
        hcp_tica_icamode="REUSE_TICA",
        hcp_tica_precomputed_clean_folder=group_folder(study),
        hcp_tica_precomputed_fmri_name="rfMRI_REST",
        hcp_tica_precomputed_group_name=GROUP,
        hcp_tica_sicadim_override="10",
    )

    log = hcp_temporal_ica(study.sessions, options)

    assert log.status == ("s1,s2", "HCP temporal ICA cannot be run", 1)
    assert f"The group folder {group_folder(study)} is the precomputed tICA" in log.text
    assert study.calls == []
    assert not os.path.lexists(group_folder(study))


def test_temporal_ica_refused_run_makes_no_average_dataset_link(study, tmp_path):
    """
    A later run uses a group folder in place as it is, so a link left by a
    refused run would decide it: the average dataset is linked only once every
    check has passed.
    """
    average = make_average_dataset_output(study, str(tmp_path / "my_average"))
    options = tica_options(study, "run", hcp_tica_average_dataset=average)
    options["hcp_matlab_mode"] = "matlab"

    log = hcp_temporal_ica(study.sessions, options)

    assert log.status == ("s1,s2", "HCP temporal ICA cannot be run", 1)
    assert "unknown setting for hcp_matlab_mode" in log.text
    assert study.calls == []
    assert not os.path.lexists(group_folder(study))


def test_temporal_ica_links_the_average_dataset_as_the_group(study, tmp_path):
    """
    The group folder <study_dir>/<group>/MNINonLinear was created before the
    average dataset was linked in its place, so the link failed silently and
    the dataset the user named was never used. A named dataset needs none of
    the study's own.
    """
    average = tmp_path / "my_average"
    make_average_dataset_output(study, str(average))
    options = tica_options(study, "run", hcp_tica_average_dataset=str(average))

    log = hcp_temporal_ica(study.sessions, options)

    group = os.path.join(study.sessionsfolder, GROUP, GROUP)
    assert os.path.islink(group)
    assert os.path.realpath(group) == str(average)
    assert study.calls == ["tICAPipeline.sh"]
    assert log.status[2] == 0
    for sid in ("s1", "s2"):
        link = os.path.join(study.sessionsfolder, GROUP, sid)
        assert os.path.realpath(link) == session_hcp(study, sid)


def test_temporal_ica_dry_run_names_the_average_dataset_link(study, tmp_path):
    average = tmp_path / "my_average"
    make_average_dataset_output(study, str(average))
    before = tree(study.root)

    log = hcp_temporal_ica(
        study.sessions,
        tica_options(study, "test", hcp_tica_average_dataset=str(average)),
    )

    group = os.path.join(study.sessionsfolder, GROUP, GROUP)
    assert f"test, not linked: {group} -> {average}" in log.text
    assert log.status == ("s1,s2", "HCP temporal ICA can be run", 0)
    assert tree(study.root) == before


def reuse_tica(**overrides):
    """The options of a REUSE_TICA run of a precomputed tICA of another study."""
    return dict(
        hcp_tica_icamode="REUSE_TICA",
        hcp_tica_precomputed_clean_folder="/precomputed/G",
        hcp_tica_precomputed_fmri_name="rfMRI_REST",
        hcp_tica_precomputed_group_name="G",
        hcp_tica_sicadim_override="10",
        **overrides,
    )


def longitudinal(**overrides):
    """The options of a longitudinal run of subject subj-01."""
    return dict(
        longitudinal=True,
        hcp_longitudinal_subject="subj-01",
        hcp_longitudinal_sessions="s1,s2",
        hcp_tica_extract_fmri_out="rfMRI_REST",
        **overrides,
    )


def test_temporal_ica_single_session_replaces_a_dangling_group_link(study):
    """
    A link left by a run that named a dataset since removed dangles, and
    making <group>/MNINonLinear through it failed with a traceback, reported
    as an unknown error, while the dry run said the run could be made.
    """
    sessions = gc.SessionList([study.sessions[0]])
    group = os.path.join(study.sessionsfolder, "s1", "hcp", GROUP)
    os.symlink("/nonexistent/removed_dataset", group)
    before = tree(study.root)

    log = hcp_temporal_ica(sessions, tica_options(study, "test", **reuse_tica()))

    assert log.status == ("s1", "HCP temporal ICA can be run", 0)
    assert f"test, not removed: {group} -> /nonexistent/removed_dataset" in log.text
    assert f"test, not created: {group}/MNINonLinear" in log.text
    assert tree(study.root) == before

    log = hcp_temporal_ica(sessions, tica_options(study, "run", **reuse_tica()))

    assert log.status == ("s1", "done", 0)
    assert study.calls == ["tICAPipeline.sh"]
    assert f"removed link: {group} -> /nonexistent/removed_dataset" in log.text
    assert not os.path.islink(group)
    assert os.path.isdir(os.path.join(group, "MNINonLinear"))


def test_temporal_ica_longitudinal_replaces_a_dangling_group_link(study):
    """The link earlier versions made dangles once its folder or the study moved."""
    subject = study.root / "subjects" / "subj-01"
    subject.mkdir(parents=True)
    group = subject / GROUP
    gone = os.path.join(study.sessionsfolder, "average_dataset", "gone")
    os.symlink(gone, group)

    log = hcp_temporal_ica(study.sessions, tica_options(study, "run", **longitudinal()))

    assert log.status == ("s1,s2", "done", 0)
    assert study.calls == ["tICAPipeline.sh"]
    assert f"removed link: {group} -> {gone}" in log.text
    assert not os.path.islink(group)
    assert (group / "MNINonLinear").is_dir()


def test_temporal_ica_longitudinal_replaces_the_link_to_the_shared_study(study, tmp_path):
    """
    Earlier versions linked the average dataset's study folder, which every
    subject shares, as the subject's group folder, and a later run kept
    writing the subject's results into it.
    """
    make_average_dataset_output(study)
    shared = os.path.join(study.sessionsfolder, "average_dataset", GROUP)
    subject = study.root / "subjects" / "subj-01"
    subject.mkdir(parents=True)
    group = subject / GROUP
    os.symlink(shared, group)
    before = tree(study.root)

    log = hcp_temporal_ica(study.sessions, tica_options(study, "test", **longitudinal()))

    assert log.status == ("s1,s2", "HCP temporal ICA can be run", 0)
    assert f"test, not removed: {group} -> {shared}" in log.text
    assert f"test, not created: {group}/MNINonLinear" in log.text
    assert tree(study.root) == before

    log = hcp_temporal_ica(study.sessions, tica_options(study, "run", **longitudinal()))

    assert log.status == ("s1,s2", "done", 0)
    assert f"removed link: {group} -> {shared}" in log.text
    assert not os.path.islink(group)
    assert (group / "MNINonLinear").is_dir()
    assert not os.path.exists(os.path.join(shared, "MNINonLinear"))

    # a link to any other folder is the user's, and is kept
    os.rename(group, tmp_path / "own")
    os.symlink(tmp_path / "own", group)

    log = hcp_temporal_ica(study.sessions, tica_options(study, "run", **longitudinal()))

    assert log.status == ("s1,s2", "done", 0)
    assert os.readlink(group) == str(tmp_path / "own")


def test_temporal_ica_refuses_a_named_dataset_one_level_too_high(study):
    """
    A named dataset was linked in without a check that it holds the file tICA
    reads, so a run naming the folder hcp_make_average_dataset runs in, one
    level above the dataset, as the docs used to say, was reported done and
    would fail at ComputeTICAFeatures, after days of processing.
    """
    made = make_average_dataset_output(study)
    named = os.path.dirname(made)
    wmparc = os.path.join(named, "MNINonLinear", f"{GROUP}_Averagewmparc.nii.gz")

    for run in ("test", "run"):
        log = hcp_temporal_ica(
            study.sessions, tica_options(study, run, hcp_tica_average_dataset=named)
        )

        assert log.status == ("s1,s2", "HCP temporal ICA cannot be run", 1)
        assert f"{wmparc} does not exist: --hcp_tica_average_dataset is the folder" in log.text
        assert f"--hcp_outgroupname={GROUP}" in log.text
        assert f"{made} holds it, it is probably the folder meant" in log.text
    assert study.calls == []
    assert not os.path.lexists(group_folder(study))


def test_temporal_ica_refuses_a_named_dataset_of_another_group(study, tmp_path):
    other = tmp_path / "other"
    (other / "MNINonLinear").mkdir(parents=True)
    open(other / "MNINonLinear" / "other_Averagewmparc.nii.gz", "w").close()

    log = hcp_temporal_ica(
        study.sessions, tica_options(study, "run", hcp_tica_average_dataset=str(other))
    )

    assert log.status == ("s1,s2", "HCP temporal ICA cannot be run", 1)
    assert "does not exist: --hcp_tica_average_dataset is the folder" in log.text
    assert "probably the folder meant" not in log.text
    assert study.calls == []


def test_temporal_ica_takes_any_dataset_for_steps_that_read_none(study, tmp_path):
    """
    Only ComputeTICAFeatures reads the average dataset, and REUSE_TICA skips
    it: a REUSE_TICA run, or one that starts after it, takes a named dataset
    of another group, and needs none of the study's own.
    """
    other = tmp_path / "other"
    (other / "MNINonLinear").mkdir(parents=True)

    log = hcp_temporal_ica(
        study.sessions,
        tica_options(study, "run", hcp_tica_average_dataset=str(other), **reuse_tica()),
    )

    assert log.status == ("s1,s2", "done", 0)
    assert os.readlink(group_folder(study)) == str(other)

    os.unlink(group_folder(study))
    log = hcp_temporal_ica(
        study.sessions,
        tica_options(
            study,
            "run",
            hcp_tica_starting_step="CleanData",
            hcp_tica_stop_after_step="CleanData",
        ),
    )

    assert log.status == ("s1,s2", "done", 0)
    assert study.calls == ["tICAPipeline.sh", "tICAPipeline.sh"]
    assert not os.path.islink(group_folder(study))
    assert os.path.isdir(os.path.join(group_folder(study), "MNINonLinear"))


def test_temporal_ica_takes_its_own_group_as_precomputed_for_steps_that_write_none(study):
    """
    In REUSE_TICA mode only indProjSICA, ConcatGroupSICA and ComputeGroupTICA
    write into the group folder, so a run of the later steps does not write
    over the tICA it reuses.
    """
    sessions = gc.SessionList([study.sessions[0]])
    own = os.path.join(study.sessionsfolder, "s1", "hcp", GROUP)
    steps = dict(hcp_tica_starting_step="CleanData", hcp_tica_stop_after_step="CleanData")
    options = tica_options(study, "run", **steps, **reuse_tica())
    options["hcp_tica_precomputed_clean_folder"] = own

    log = hcp_temporal_ica(sessions, options)

    assert log.status == ("s1", "done", 0)
    assert "the run would write over it" not in log.text

    options["hcp_tica_starting_step"] = "ComputeGroupTICA"
    log = hcp_temporal_ica(sessions, options)

    assert log.status == ("s1", "HCP temporal ICA cannot be run", 1)
    assert "the run would write over it" in log.text

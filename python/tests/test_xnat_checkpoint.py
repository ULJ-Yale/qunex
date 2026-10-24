# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""What an XNAT checkpoint restores into the build folder."""

import qx_utilities.general.xnat as gx


def test_a_checkpoint_does_not_restore_the_logs_of_earlier_runs(tmp_path, monkeypatch):
    """
    Only `processing/logs` was left out, so the run folders in `<study>/logs`,
    where runs log by default, were restored into the build -- and their
    `error_*` comlogs counted as failures of the run that restored them.
    """
    study = "/output/PROJ"
    monkeypatch.setenv("STUDY_FOLDER", study)
    monkeypatch.setenv("XNAT_DEFAULT_FILTERS", "no")
    monkeypatch.delenv("XNAT_CUSTOM_FILTERS", raising=False)
    monkeypatch.delenv("XNAT_CUSTOM_RSYNC", raising=False)
    ran = []
    monkeypatch.setattr(gx, "xnat_run_cmd", lambda cmd: ran.append(cmd) or "")

    checkpoint = tmp_path / "step_in:x.txt"
    checkpoint.write_text(
        "\n".join(
            [
                study + "/logs",
                study + "/logs/2026-10-23_run_recipe/comlogs/error_x.log",
                study + "/processing/logs/comlogs/error_y.log",
                study + "/sessions/S1/logs/comlogs/done_z.log",
                study + "/sessions/S1/session.txt",
                # the 'all' checkpoint joins an entry to the study without a "/"
                study + "logs/2026-10-23_run_recipe/runlogs/Log-x.log",
            ]
        )
    )

    gx.xnat_load_checkpoint(str(checkpoint))

    (cmd,) = ran
    assert [arg for arg in cmd if arg.startswith("--include=")] == [
        "--include=/sessions/S1/logs/comlogs/done_z.log",
        "--include=/sessions/S1/session.txt",
    ]

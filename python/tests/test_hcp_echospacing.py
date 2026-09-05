# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Resolving the BOLD echo spacing in ``hcp_fmri_volume``.

Every distortion correction method the command supports needs an echo spacing.
``hcp_bold_echospacing`` states it for the study and the session file's inline
``EchoSpacing`` states it per image, but neither is always set -- and the value
is usually still recoverable from the session file or the BOLD image's JSON
sidecar. These cover that fallback, and the reporting around it: the fallback
used to read the sidecar and then throw the value away, and a missing echo
spacing used to be reported twice, the second time as ``not defined correctly:
"None"``.
"""

import json
import os

from qx_utilities.general.log import ReportLog
from qx_utilities.hcp.hcp_fmri_volume import _check_echospacing, _infer_echospacing


def _bold_image(tmp_path, sidecar=None):
    """A BOLD image path, with a JSON sidecar beside it when one is given."""
    image = os.path.join(tmp_path, "sess-01_BOLD_1.nii.gz")
    open(image, "w").close()
    if sidecar is not None:
        with open(image.replace(".nii.gz", ".json"), "w") as f:
            json.dump(sidecar, f)
    return image


def test_echospacing_comes_from_the_session_file(tmp_path):
    log = ReportLog()
    echospacing = _infer_echospacing(
        {"EchoSpacing": "0.00058"}, _bold_image(tmp_path), log
    )

    assert echospacing == "0.00058"
    assert "EchoSpacing from the session file: 0.00058 s" in log.text


def test_echospacing_comes_from_the_sidecar(tmp_path):
    log = ReportLog()
    image = _bold_image(tmp_path, {"EffectiveEchoSpacing": 0.00058})
    echospacing = _infer_echospacing({}, image, log)

    assert echospacing == 0.00058
    assert "EffectiveEchoSpacing in sess-01_BOLD_1.json" in log.text


def test_sidecar_echospacing_falls_back_to_the_plain_field(tmp_path):
    image = _bold_image(tmp_path, {"EchoSpacing": 0.00058})

    assert _infer_echospacing({}, image, ReportLog()) == 0.00058


def test_the_session_file_wins_over_the_sidecar(tmp_path):
    image = _bold_image(tmp_path, {"EffectiveEchoSpacing": 0.00099})

    assert _infer_echospacing({"EchoSpacing": "0.00058"}, image, ReportLog()) == "0.00058"


def test_missing_echospacing_says_where_it_looked(tmp_path):
    log = ReportLog()
    image = _bold_image(tmp_path)

    assert _infer_echospacing({}, image, log) == ""
    assert "no EchoSpacing in the session file" in log.text
    assert "no JSON sidecar at %s" % image.replace(".nii.gz", ".json") in log.text


def test_an_unreadable_sidecar_is_reported_not_raised(tmp_path):
    log = ReportLog()
    image = os.path.join(tmp_path, "sess-01_BOLD_1.nii.gz")
    open(image, "w").close()
    with open(image.replace(".nii.gz", ".json"), "w") as f:
        f.write("{not json")

    assert _infer_echospacing({}, image, log) == ""
    assert "could not read the JSON sidecar" in log.text


def test_a_sidecar_without_echospacing_is_reported(tmp_path):
    log = ReportLog()

    assert _infer_echospacing({}, _bold_image(tmp_path, {"RepetitionTime": 0.735}), log) == ""
    assert "no EffectiveEchoSpacing or EchoSpacing in sess-01_BOLD_1.json" in log.text


def test_a_usable_echospacing_passes_the_check():
    log = ReportLog()

    assert _check_echospacing("0.00058", log) is True
    assert log.text == ""


def test_an_unusable_echospacing_is_reported():
    log = ReportLog()

    assert _check_echospacing("fast", log) is False
    assert 'hcp_bold_echospacing not defined correctly: "fast"!' in log.text


def test_a_missing_echospacing_is_not_reported_twice():
    # the caller resolving it already said it is missing; saying so again as
    # `not defined correctly: "None"` only added noise
    for missing in ["", None]:
        log = ReportLog()
        assert _check_echospacing(missing, log) is False
        assert log.text == ""

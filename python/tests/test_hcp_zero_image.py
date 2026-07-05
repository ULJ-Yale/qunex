# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Tests for resolve_session_relative_image used by hcp_fmri_volume to locate the
NHP zero-phase SE image and its FS brainmask in a session-flexible way.
"""

import os

from qx_utilities.hcp.process_hcp import resolve_session_relative_image


def _touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").close()


def test_resolve_absolute_path(tmp_path):
    base = str(tmp_path)
    img = os.path.join(base, "somewhere", "T2w.nii.gz")
    _touch(img)

    # an absolute path pointing at an existing file is used as is
    resolved, found = resolve_session_relative_image(img, base)
    assert found
    assert resolved == img


def test_resolve_relative_to_hcp_base(tmp_path):
    base = str(tmp_path)
    _touch(os.path.join(base, "custom.nii.gz"))

    # a relative value is resolved against the session's root hcp folder,
    # returned without the probed extension
    resolved, found = resolve_session_relative_image("custom", base)
    assert found
    assert resolved == os.path.join(base, "custom")


def test_resolve_relative_to_t2w_folder(tmp_path):
    base = str(tmp_path)
    _touch(os.path.join(base, "T2w", "T2w.nii.gz"))

    # the standard NHP case: 'T2w' resolves to the session's T2w folder
    resolved, found = resolve_session_relative_image("T2w", base)
    assert found
    assert resolved == os.path.join(base, "T2w", "T2w")


def test_resolve_prefers_hcp_base_over_t2w(tmp_path):
    base = str(tmp_path)
    _touch(os.path.join(base, "T2w_brainmask_fs.nii.gz"))
    _touch(os.path.join(base, "T2w", "T2w_brainmask_fs.nii.gz"))

    # the hcp base candidate takes precedence over the T2w fallback
    resolved, found = resolve_session_relative_image("T2w_brainmask_fs", base)
    assert found
    assert resolved == os.path.join(base, "T2w_brainmask_fs")


def test_resolve_not_found_returns_t2w_fallback(tmp_path):
    base = str(tmp_path)

    # nothing exists: report not found and return the T2w fallback candidate
    resolved, found = resolve_session_relative_image("missing", base)
    assert not found
    assert resolved == os.path.join(base, "T2w", "missing")


def test_resolve_matches_uncompressed_nifti(tmp_path):
    base = str(tmp_path)
    _touch(os.path.join(base, "T2w", "T2w.nii"))

    # .nii (uncompressed) is also probed
    resolved, found = resolve_session_relative_image("T2w", base)
    assert found
    assert resolved == os.path.join(base, "T2w", "T2w")

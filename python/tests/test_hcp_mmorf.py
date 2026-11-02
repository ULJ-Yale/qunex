# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
The HCP MMORF commands: hcp_pre_mmorf, hcp_mmorf and hcp_post_mmorf.

Nothing here runs a pipeline. The fixture lays out a fake HCP Pipelines folder
and a session that has been through the FreeSurfer chain, hcp_diffusion and
hcp_msmall, so what is tested is what QuNex decides: which flags reach the
pipeline, what it rejects, what a dry run says and what an overwrite removes.
"""

import os
import re
import subprocess
from pathlib import Path

import pytest
import yaml

import qx_utilities.hcp.mmorf_utils as mu
import qx_utilities.processing.core as pc
from qx_utilities.hcp.hcp_mmorf import hcp_mmorf
from qx_utilities.hcp.hcp_paths import get_hcp_paths
from qx_utilities.hcp.hcp_post_mmorf import hcp_post_mmorf
from qx_utilities.hcp.hcp_pre_mmorf import hcp_pre_mmorf

from .utils import build_hcp_session, default_options

REPO_ROOT = Path(__file__).resolve().parents[2]

COMMANDS = [hcp_pre_mmorf, hcp_mmorf, hcp_post_mmorf]
SCRIPTS = ["PreMMORFPipeline.sh", "MMORFPipeline.sh", "PostMMORFPipeline.sh"]
NAMES = ["HCP PreMMORF", "HCP MMORF", "HCP PostMMORF"]

COMMAND_SHOWN = "Running HCP Pipelines command via QuNex:"

TEMPLATES = [
    "MMORF_T1_0.7mm.nii.gz",
    "MMORF_T1_0.7mm_brain.nii.gz",
    "MMORF_T1_0.7mm_brain_mask.nii.gz",
    "MMORF_T2_0.7mm.nii.gz",
    "MMORF_DTI_0.7mm_tensor.nii.gz",
    "MMORF_DTI_0.7mm_brain_mask.nii.gz",
    "MMORF_T1_1mm.nii.gz",
]

# what the chain leaves for the later steps, by what writes it
PRE_OUTPUTS = ["T1w/Diffusion/data_tensor.nii.gz", "MMORFNonLinear/xfms/acpc2MMORFLinear.mat"]
WARP = "MMORFNonLinear/xfms/mov_to_ref_mm_warp.nii.gz"


def _touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").close()


def _tree(root):
    """Every file under `root`, with its size and mtime."""
    found = {}
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            stat = os.stat(path)
            found[path] = (stat.st_size, stat.st_mtime_ns)
    return found


def _lay_out_pipelines(root):
    templates = os.path.join(root, "global", "templates")
    for name in TEMPLATES:
        _touch(os.path.join(templates, name))
    for mesh in ("59", "79"):
        _touch(os.path.join(templates, "surface-only_cifti", f"CortexOnly.{mesh}k_fs_LR.dscalar.nii"))
        for h in ("L", "R"):
            for name in (
                f"{h}.sphere.{mesh}k_fs_LR.surf.gii",
                f"{h}.atlasroi.{mesh}k_fs_LR.shape.gii",
                f"colin.cerebral.{h}.flat.{mesh}k_fs_LR.surf.gii",
            ):
                _touch(os.path.join(templates, "standard_mesh_atlases", name))


def _lay_out_session(base, session):
    """Everything the chain reads from the commands that run before it."""
    for name in (
        "T1w_acpc_dc", "T1w_acpc_dc_restore", "T1w_acpc_dc_restore_brain",
        "T2w_acpc_dc", "T2w_acpc_dc_restore", "T2w_acpc_dc_restore_brain",
    ):
        _touch(os.path.join(base, "T1w", f"{name}.nii.gz"))
    for name in ("data.nii.gz", "bvecs", "nodif_brain_mask.nii.gz"):
        _touch(os.path.join(base, "T1w", "Diffusion", name))

    native = os.path.join(base, "MNINonLinear", "Native")
    _touch(os.path.join(native, f"{session}.thickness.native.dscalar.nii"))
    for h in ("L", "R"):
        for surface in ("white", "pial"):
            _touch(os.path.join(base, "T1w", "Native", f"{session}.{h}.{surface}.native.surf.gii"))
        for regname in ("MSMAll", "MSMSulc"):
            _touch(os.path.join(native, f"{session}.{h}.sphere.{regname}.native.surf.gii"))
        for kind in ("sphere", "flat", "midthickness"):
            _touch(os.path.join(base, "MNINonLinear", f"{session}.{h}.{kind}.164k_fs_LR.surf.gii"))
            for mesh in ("32", "59"):
                _touch(os.path.join(
                    base, "MNINonLinear", f"fsaverage_LR{mesh}k",
                    f"{session}.{h}.{kind}.{mesh}k_fs_LR.surf.gii",
                ))


@pytest.fixture
def mmorf(tmp_path, monkeypatch):
    """Build a session ready for the chain, and the options of one command."""
    pipelines = tmp_path / "hcppipedir"
    _lay_out_pipelines(str(pipelines))
    monkeypatch.setenv("HCPPIPEDIR", str(pipelines))
    monkeypatch.setenv("QUNEXPATH", str(tmp_path / "qunexpath"))

    def _build(bvals="5 5 1485 1510 2980 3010", suffix="", run="test", **overrides):
        sinfo, sessionsfolder = build_hcp_session(str(tmp_path / "study"))
        session = sinfo["id"] + suffix
        base = os.path.join(sinfo["hcp"], session)
        _lay_out_session(base, session)
        with open(os.path.join(base, "T1w", "Diffusion", "bvals"), "w") as f:
            f.write(bvals)
        options = default_options(
            run=run,
            sessionsfolder=sessionsfolder,
            comlogs=str(tmp_path / "comlogs"),
            hcp_suffix=suffix,
            **overrides,
        )
        return sinfo, options, base

    _build.pipelines = str(pipelines)
    _build.root = str(tmp_path)
    return _build


@pytest.fixture
def no_external(monkeypatch):
    """Make every external call a dry run could reach fatal."""

    def fail(*args, **kwargs):
        raise AssertionError("a --test run executed an external command")

    monkeypatch.setattr(pc, "run_external_for_file", fail)
    monkeypatch.setattr(subprocess, "run", fail)


@pytest.fixture
def external(monkeypatch):
    """Stand in for the pipeline in a real run, and record the calls."""
    calls = []

    def stub(checkfile, command, description, **kwargs):
        calls.append({"checkfile": checkfile, "command": command, **kwargs})
        return "", "done", 0

    monkeypatch.setattr(pc, "run_external_for_file", stub)
    return calls


def _chain_files(base, *names):
    for name in names:
        _touch(os.path.join(base, name))


def _make_older(base, name, than):
    stat = os.stat(os.path.join(base, than))
    os.utime(os.path.join(base, name), ns=(stat.st_atime_ns, stat.st_mtime_ns - 10**9))


# ------------------------------------------------------------- the option rule


def test_every_option_of_the_chain_has_no_qunex_default(mmorf):
    _, options, _ = mmorf()
    names = [e for e in options if e.startswith("hcp_mmorf_")]
    assert len(names) == 11
    assert all(options[e] is None for e in names)


def test_post_leaves_every_optional_flag_to_hcp(mmorf, no_external):
    sinfo, options, _ = mmorf()
    log = hcp_post_mmorf(sinfo, options)
    assert log.status[2] == 0, log.text
    for flag in ("hiresmesh", "lowresmesh", "diffusionmesh", "regname", "regnameorig", "inflatescale"):
        assert f"--{flag}=" not in log.text


@pytest.mark.parametrize(
    "option, flag",
    [
        ("hcp_lowresmesh", "lowresmesh"),
        ("hcp_inflatescale", "inflatescale"),
        ("hcp_mmorf_regname", "regname"),
        ("hcp_mmorf_diffusionmesh", "diffusionmesh"),
    ],
)
def test_post_takes_a_blank_value_as_not_set(mmorf, no_external, option, flag):
    # a per-session value, or a recipe variable that expanded to nothing
    sinfo, options, _ = mmorf()
    options[option] = ""
    log = hcp_post_mmorf(sinfo, options)
    assert log.status[2] == 0, log.text
    assert f"--{flag}=" not in log.text


def test_post_is_not_reading_the_registration_of_hcp_post_freesurfer(mmorf, no_external):
    sinfo, options, _ = mmorf(hcp_regname="FS")
    log = hcp_post_mmorf(sinfo, options)
    assert log.status[2] == 0, log.text
    assert "--regname=" not in log.text


@pytest.mark.parametrize("overrides", [{"hcp_hiresmesh": 164}, {"hcp_hiresmesh": "164"}, {"hcp_lowresmesh": "32"}])
def test_post_leaves_a_mesh_at_hcps_default_off_the_command_line(mmorf, no_external, overrides):
    sinfo, options, _ = mmorf(**overrides)
    log = hcp_post_mmorf(sinfo, options)
    assert log.status[2] == 0, log.text
    assert "--hiresmesh=" not in log.text
    assert "--lowresmesh=" not in log.text


def test_post_passes_a_high_resolution_mesh_that_is_not_hcps_default(mmorf, no_external):
    sinfo, options, base = mmorf(hcp_hiresmesh=59)
    for h in ("L", "R"):
        for kind in ("sphere", "flat"):
            _touch(os.path.join(base, "MNINonLinear", f"sess-01.{h}.{kind}.59k_fs_LR.surf.gii"))
    log = hcp_post_mmorf(sinfo, options)
    assert log.status[2] == 0, log.text
    assert '--hiresmesh="59"' in log.text


@pytest.mark.parametrize(
    "overrides, passed",
    [
        ({"hcp_lowresmesh": "59"}, '--lowresmesh="59"'),
        ({"hcp_lowresmesh": "32,59"}, '--lowresmesh="32@59"'),
        ({"hcp_lowresmesh": "32@59"}, '--lowresmesh="32@59"'),
        ({"hcp_mmorf_diffusionmesh": "79"}, '--diffusionmesh="79"'),
        ({"hcp_mmorf_regname": "MSMSulc"}, '--regname="MSMSulc"'),
        ({"hcp_mmorf_regnameorig": "MSMAll"}, '--regnameorig="MSMAll"'),
        ({"hcp_inflatescale": "2"}, '--inflatescale="2"'),
    ],
)
def test_post_passes_an_optional_flag_that_is_set(mmorf, no_external, overrides, passed):
    sinfo, options, _ = mmorf(**overrides)
    log = hcp_post_mmorf(sinfo, options)
    assert log.status[2] == 0, log.text
    assert passed in log.text


@pytest.mark.parametrize(
    "command, flag, template",
    [
        (hcp_pre_mmorf, "t1-brain-template", "MMORF_T1_0.7mm_brain.nii.gz"),
        (hcp_mmorf, "t1-template", "MMORF_T1_0.7mm.nii.gz"),
        (hcp_mmorf, "t2-template", "MMORF_T2_0.7mm.nii.gz"),
        (hcp_mmorf, "ref-mask", "MMORF_T1_0.7mm_brain_mask.nii.gz"),
        (hcp_mmorf, "diffusion-ref", "MMORF_DTI_0.7mm_tensor.nii.gz"),
        (hcp_mmorf, "dti-ref-mask", "MMORF_DTI_0.7mm_brain_mask.nii.gz"),
        (hcp_post_mmorf, "t1-template", "MMORF_T1_0.7mm.nii.gz"),
    ],
)
def test_a_mandatory_template_defaults_to_hcps(mmorf, no_external, command, flag, template):
    sinfo, options, _ = mmorf()
    log = command(sinfo, options)
    assert log.status[2] == 0, log.text
    expected = os.path.join(mmorf.pipelines, "global", "templates", template)
    assert f'--{flag}="{expected}"' in log.text


@pytest.mark.parametrize(
    "command, option, flag",
    [
        (hcp_pre_mmorf, "hcp_mmorf_t1_brain_template", "t1-brain-template"),
        (hcp_mmorf, "hcp_mmorf_t1_template", "t1-template"),
        (hcp_mmorf, "hcp_mmorf_t2_template", "t2-template"),
        (hcp_mmorf, "hcp_mmorf_ref_mask", "ref-mask"),
        (hcp_mmorf, "hcp_mmorf_diffusion_ref", "diffusion-ref"),
        (hcp_mmorf, "hcp_mmorf_dti_ref_mask", "dti-ref-mask"),
        (hcp_post_mmorf, "hcp_mmorf_t1_template", "t1-template"),
    ],
)
def test_a_set_option_replaces_the_automatic_template(mmorf, no_external, command, option, flag):
    mine = os.path.join(mmorf.root, "mine.nii.gz")
    _touch(mine)
    sinfo, options, _ = mmorf(**{option: mine})
    log = command(sinfo, options)
    assert log.status[2] == 0, log.text
    assert f'--{flag}="{mine}"' in log.text


@pytest.mark.parametrize("command", COMMANDS)
def test_session_flags_carry_the_suffix(mmorf, no_external, command):
    sinfo, options, _ = mmorf(suffix="_x")
    log = command(sinfo, options)
    assert log.status[2] == 0, log.text
    assert f'--study-folder="{sinfo["hcp"]}"' in log.text
    assert '--session="sess-01_x"' in log.text


def test_upstream_defaults_are_the_scripts():
    script = Path(os.environ.get("HCPPIPEDIR", "")) / "MMORF" / "PostMMORFPipeline.sh"
    if not script.exists():
        pytest.skip("needs HCP Pipelines with the MMORF chain")

    found = dict(re.findall(
        r"""^opts_AddOptional '--(\w+)' .* ['"]([^'"]*)['"]\s*$""", script.read_text(), re.M,
    ))
    for option, value in mu.UPSTREAM_POST_DEFAULTS.items():
        assert found[re.sub(r"^hcp_(mmorf_)?", "", option)] == value


# ------------------------------------------------------------------- threshold


@pytest.mark.parametrize(
    "bvals, threshold, kept",
    [
        ("5 995 1005", "1200", "3 of 3"),
        ("5 5 1485 1510 2980 3010", "1700", "4 of 6"),
        ("0 700 705 2000", "900", "3 of 4"),
        ("5 1500 3000\n\n", "1700", "2 of 3"),
        ("30 1000 1005", "1200", "3 of 3"),
        ("50 1000 1005", "1200", "3 of 3"),
    ],
)
def test_threshold_is_detected_from_the_bvals(mmorf, no_external, bvals, threshold, kept):
    sinfo, options, _ = mmorf(bvals=bvals)
    log = hcp_pre_mmorf(sinfo, options)
    assert log.status[2] == 0, log.text
    assert f'--lowest-shell-threshold="{threshold}"' in log.text
    assert f"keeping {kept} volumes" in log.text


def test_threshold_uses_the_b0_limit(mmorf, no_external):
    sinfo, options, _ = mmorf(bvals="60 1000 1005", hcp_dwi_b0maxbval="100")
    log = hcp_pre_mmorf(sinfo, options)
    assert '--lowest-shell-threshold="1200"' in log.text


@pytest.mark.parametrize(
    "bvals, message",
    [
        ("5 5 5", "no diffusion volumes above b0"),
        ("5 1000 1095 1190 1285", "could not detect the lowest shell"),
        ("5 abc", "could not work out the diffusion shells"),
        ("5\n1500\n3000\n", "has 3 lines"),
    ],
)
def test_threshold_that_can_not_be_detected_asks_for_the_option(mmorf, no_external, bvals, message):
    sinfo, options, _ = mmorf(bvals=bvals)
    log = hcp_pre_mmorf(sinfo, options)
    assert log.status[2] == 1
    assert message in log.text
    assert COMMAND_SHOWN not in log.text


def test_bvals_on_several_lines_are_rejected_with_a_threshold_set_by_hand(mmorf, no_external):
    sinfo, options, _ = mmorf(bvals="5\n1500\n3000\n", hcp_mmorf_lowest_shell_threshold="1700")
    log = hcp_pre_mmorf(sinfo, options)
    assert log.status[2] == 1
    assert "has 3 lines" in log.text
    assert COMMAND_SHOWN not in log.text


def test_threshold_set_by_hand_is_passed_as_it_is(mmorf, no_external):
    sinfo, options, _ = mmorf(hcp_mmorf_lowest_shell_threshold="1650")
    log = hcp_pre_mmorf(sinfo, options)
    assert log.status[2] == 0, log.text
    assert '--lowest-shell-threshold="1650"' in log.text
    assert "does not separate" not in log.text


@pytest.mark.parametrize("value", ["1200", "1500", "3100"])
def test_threshold_set_by_hand_that_does_not_separate_is_honoured_with_a_warning(mmorf, no_external, value):
    sinfo, options, _ = mmorf(hcp_mmorf_lowest_shell_threshold=value)
    log = hcp_pre_mmorf(sinfo, options)
    assert log.status[2] == 0, log.text
    assert f'--lowest-shell-threshold="{value}"' in log.text
    assert "does not separate the lowest shell" in log.text


@pytest.mark.parametrize("value", ["abc", "-5", "1e3"])
def test_threshold_that_is_not_a_number_is_rejected(mmorf, no_external, value):
    sinfo, options, _ = mmorf(hcp_mmorf_lowest_shell_threshold=value)
    log = hcp_pre_mmorf(sinfo, options)
    assert log.status[2] == 1
    assert "must be a number" in log.text
    assert COMMAND_SHOWN not in log.text


def test_missing_bvals_is_reported_as_an_input(mmorf, no_external):
    sinfo, options, base = mmorf()
    os.remove(os.path.join(base, "T1w", "Diffusion", "bvals"))
    log = hcp_pre_mmorf(sinfo, options)
    assert log.status[2] == 1
    assert "bvals not found, run hcp_diffusion first!" in log.text
    assert "Traceback" not in log.text


# -------------------------------------------------------- gradient nonlinearity


@pytest.mark.parametrize("present, flag", [(True, "TRUE"), (False, "FALSE")])
def test_gradnonlin_follows_grad_dev(mmorf, no_external, present, flag):
    sinfo, options, base = mmorf()
    if present:
        _touch(os.path.join(base, "T1w", "Diffusion", "grad_dev.nii.gz"))
    log = hcp_pre_mmorf(sinfo, options)
    assert log.status[2] == 0, log.text
    assert f'--gradnonlin="{flag}"' in log.text


def test_gradnonlin_on_without_the_file_fails(mmorf, no_external):
    sinfo, options, _ = mmorf(hcp_mmorf_gradnonlin="yes")
    log = hcp_pre_mmorf(sinfo, options)
    assert log.status[2] == 1
    assert "grad_dev.nii.gz not found" in log.text


def test_gradnonlin_on_with_the_file_passes(mmorf, no_external):
    sinfo, options, base = mmorf(hcp_mmorf_gradnonlin="yes")
    _touch(os.path.join(base, "T1w", "Diffusion", "grad_dev.nii.gz"))
    log = hcp_pre_mmorf(sinfo, options)
    assert '--gradnonlin="TRUE"' in log.text


def test_gradnonlin_off_with_the_file_is_honoured_with_a_warning(mmorf, no_external):
    sinfo, options, base = mmorf(hcp_mmorf_gradnonlin="no")
    _touch(os.path.join(base, "T1w", "Diffusion", "grad_dev.nii.gz"))
    log = hcp_pre_mmorf(sinfo, options)
    assert log.status[2] == 0, log.text
    assert '--gradnonlin="FALSE"' in log.text
    assert "is off although" in log.text


def test_gradnonlin_that_is_not_a_boolean_is_rejected(mmorf, no_external):
    sinfo, options, _ = mmorf(hcp_mmorf_gradnonlin="maybe")
    log = hcp_pre_mmorf(sinfo, options)
    assert log.status[2] == 1
    assert "must be yes or no" in log.text


# ------------------------------------------------------------------ rejections


@pytest.mark.parametrize("command", COMMANDS)
@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"hcp_species": "MacaqueRhesus"}, "support human data only"),
        ({"longitudinal": True}, "only read the cross-sectional T1w folder"),
        ({"hcp_dwi_name": "Diffusion2"}, "only read T1w/Diffusion"),
    ],
)
def test_chain_rejects_what_the_scripts_can_not_do(mmorf, no_external, command, overrides, message):
    sinfo, options, _ = mmorf(**overrides)
    log = command(sinfo, options)
    assert log.status[2] == 1
    assert "cannot be run" in log.status[1]
    assert message in log.text
    assert COMMAND_SHOWN not in log.text


@pytest.mark.parametrize("command", COMMANDS)
@pytest.mark.parametrize(
    "overrides", [{"hcp_species": "Human"}, {"hcp_species": "human"}, {"hcp_dwi_name": "Diffusion"}]
)
def test_chain_accepts_the_values_it_can_do(mmorf, no_external, command, overrides):
    sinfo, options, _ = mmorf(**overrides)
    log = command(sinfo, options)
    assert log.status[2] == 0, log.text


@pytest.mark.parametrize("command", COMMANDS)
@pytest.mark.parametrize(
    "image, hint",
    [
        ("T1w_acpc_dc_restore.nii.gz", "run hcp_pre_freesurfer first"),
        ("T2w_acpc_dc_restore.nii.gz", "MMORF requires a T2w image"),
    ],
)
def test_chain_needs_the_structural_images(mmorf, no_external, command, image, hint):
    sinfo, options, base = mmorf()
    os.remove(os.path.join(base, "T1w", image))
    log = command(sinfo, options)
    assert log.status[2] == 1
    assert f"{image} not found, {hint}!" in log.text
    assert COMMAND_SHOWN not in log.text


@pytest.mark.parametrize(
    "command, missing, hint",
    [
        (hcp_pre_mmorf, "T1w/T1w_acpc_dc_restore_brain.nii.gz", "run hcp_pre_freesurfer first"),
        (hcp_pre_mmorf, "T1w/Diffusion/data.nii.gz", "run hcp_diffusion first"),
        (hcp_pre_mmorf, "T1w/Diffusion/bvecs", "run hcp_diffusion first"),
        (hcp_pre_mmorf, "T1w/Diffusion/nodif_brain_mask.nii.gz", "run hcp_diffusion first"),
        (hcp_mmorf, "T1w/Diffusion/nodif_brain_mask.nii.gz", "run hcp_diffusion first"),
        (hcp_post_mmorf, "T1w/T1w_acpc_dc.nii.gz", "run hcp_post_freesurfer first"),
        (hcp_post_mmorf, "T1w/T1w_acpc_dc_restore_brain.nii.gz", "run hcp_post_freesurfer first"),
        (hcp_post_mmorf, "T1w/T2w_acpc_dc.nii.gz", "run hcp_post_freesurfer first"),
        (hcp_post_mmorf, "T1w/T2w_acpc_dc_restore_brain.nii.gz", "run hcp_post_freesurfer first"),
        (hcp_post_mmorf, "T1w/Native/sess-01.L.white.native.surf.gii", "run hcp_post_freesurfer first"),
        (hcp_post_mmorf, "T1w/Native/sess-01.R.pial.native.surf.gii", "run hcp_post_freesurfer first"),
        (hcp_post_mmorf, "MNINonLinear/Native/sess-01.thickness.native.dscalar.nii", "run hcp_post_freesurfer first"),
        (hcp_post_mmorf, "MNINonLinear/Native/sess-01.L.sphere.MSMAll.native.surf.gii", "set hcp_mmorf_regname"),
        (hcp_post_mmorf, "MNINonLinear/Native/sess-01.R.sphere.MSMSulc.native.surf.gii", "reg.reg_LR"),
        (hcp_post_mmorf, "MNINonLinear/sess-01.L.sphere.164k_fs_LR.surf.gii", "set hcp_hiresmesh"),
        (hcp_post_mmorf, "MNINonLinear/fsaverage_LR32k/sess-01.R.flat.32k_fs_LR.surf.gii", "set hcp_lowresmesh"),
    ],
)
def test_a_missing_input_names_what_to_do(mmorf, no_external, command, missing, hint):
    sinfo, options, base = mmorf()
    os.remove(os.path.join(base, missing))
    log = command(sinfo, options)
    assert log.status[2] == 1
    assert hint in log.text
    assert os.path.basename(missing) in log.text
    assert COMMAND_SHOWN not in log.text


@pytest.mark.parametrize(
    "command, template",
    [
        (hcp_pre_mmorf, "MMORF_T1_0.7mm_brain.nii.gz"),
        (hcp_mmorf, "MMORF_T1_0.7mm.nii.gz"),
        (hcp_mmorf, "MMORF_T2_0.7mm.nii.gz"),
        (hcp_mmorf, "MMORF_T1_0.7mm_brain_mask.nii.gz"),
        (hcp_mmorf, "MMORF_DTI_0.7mm_tensor.nii.gz"),
        (hcp_mmorf, "MMORF_DTI_0.7mm_brain_mask.nii.gz"),
        (hcp_post_mmorf, "MMORF_T1_0.7mm.nii.gz"),
        (hcp_post_mmorf, "MMORF_T1_1mm.nii.gz"),
    ],
)
def test_a_missing_template_is_reported(mmorf, no_external, command, template):
    sinfo, options, _ = mmorf()
    os.remove(os.path.join(mmorf.pipelines, "global", "templates", template))
    log = command(sinfo, options)
    assert log.status[2] == 1
    assert f"{template} not found" in log.text


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"hcp_mmorf_regname": "Custom"}, "sphere.Custom.native.surf.gii not found"),
        ({"hcp_mmorf_regnameorig": "FS"}, "sphere.FS.native.surf.gii not found"),
        ({"hcp_hiresmesh": "10"}, "sess-01.L.sphere.10k_fs_LR.surf.gii not found"),
        ({"hcp_lowresmesh": "32,10"}, "sess-01.L.sphere.10k_fs_LR.surf.gii not found"),
        ({"hcp_mmorf_diffusionmesh": "32"}, "is also a mesh hcp_post_freesurfer built"),
        ({"hcp_mmorf_diffusionmesh": "164"}, "is also a mesh hcp_post_freesurfer built"),
        ({"hcp_mmorf_diffusionmesh": "59", "hcp_lowresmesh": "32,59"}, "is also a mesh hcp_post_freesurfer built"),
        ({"hcp_mmorf_diffusionmesh": "59"}, "is also a mesh hcp_post_freesurfer built"),
        ({"hcp_mmorf_diffusionmesh": "abc"}, "must be a number"),
        ({"hcp_mmorf_diffusionmesh": "80"}, "no atlas for this hcp_mmorf_diffusionmesh"),
    ],
)
def test_post_rejects_what_the_session_can_not_do(mmorf, no_external, overrides, message):
    sinfo, options, _ = mmorf(**overrides)
    log = hcp_post_mmorf(sinfo, options)
    assert log.status[2] == 1
    assert message in log.text
    assert COMMAND_SHOWN not in log.text


def test_diffusion_mesh_is_compared_as_a_whole_mesh(mmorf, no_external):
    # 9 is in the text of 59 without being that mesh
    sinfo, options, _ = mmorf(hcp_mmorf_diffusionmesh="9", hcp_lowresmesh="59")
    log = hcp_post_mmorf(sinfo, options)
    assert "is also a mesh" not in log.text
    assert "no atlas for this hcp_mmorf_diffusionmesh" in log.text


def test_diffusion_mesh_needs_its_cortex_file(mmorf, no_external):
    sinfo, options, _ = mmorf()
    os.remove(os.path.join(mmorf.pipelines, "global", "templates", "surface-only_cifti", "CortexOnly.79k_fs_LR.dscalar.nii"))
    log = hcp_post_mmorf(sinfo, options)
    assert log.status[2] == 1
    assert "no atlas for this hcp_mmorf_diffusionmesh" in log.text


def test_one_report_names_every_problem(mmorf, no_external):
    sinfo, options, base = mmorf(hcp_species="MacaqueRhesus")
    os.remove(os.path.join(base, "T1w", "T2w_acpc_dc_restore.nii.gz"))
    os.remove(os.path.join(base, "T1w", "Diffusion", "bvecs"))
    log = hcp_pre_mmorf(sinfo, options)
    for message in ("support human data only", "MMORF requires a T2w image", "bvecs not found"):
        assert message in log.text


# ---------------------------------------------------------- the dry run contract


@pytest.mark.parametrize(
    "command, script, name", list(zip(COMMANDS, SCRIPTS, NAMES))
)
def test_a_dry_run_names_the_tool_and_changes_nothing(mmorf, no_external, command, script, name):
    sinfo, options, _ = mmorf()
    before = _tree(mmorf.root)
    log = command(sinfo, options)
    assert _tree(mmorf.root) == before
    assert log.status == ("sess-01", f"{name} can be run", 0)
    assert script in log.text
    assert COMMAND_SHOWN in log.text


def test_the_chain_dry_runs_in_order_on_a_session_it_has_not_run_on(mmorf, no_external):
    # what run_recipe --test does: each step wrote nothing for the next
    sinfo, options, _ = mmorf()
    for command, script in zip(COMMANDS, SCRIPTS):
        log = command(sinfo, options)
        assert log.status[2] == 0, log.text
        assert script in log.text


@pytest.mark.parametrize(
    "command, written, step",
    [
        (hcp_mmorf, PRE_OUTPUTS[0], "hcp_pre_mmorf"),
        (hcp_mmorf, PRE_OUTPUTS[1], "hcp_pre_mmorf"),
        (hcp_post_mmorf, PRE_OUTPUTS[0], "hcp_pre_mmorf"),
        (hcp_post_mmorf, PRE_OUTPUTS[1], "hcp_pre_mmorf"),
        (hcp_post_mmorf, WARP, "hcp_mmorf"),
    ],
)
def test_a_file_of_an_earlier_step_warns_in_a_dry_run_and_stops_a_real_one(
    mmorf, external, command, written, step
):
    sinfo, options, _ = mmorf()
    log = command(sinfo, options)
    assert log.status[2] == 0, log.text
    assert f"{os.path.basename(written)} not found, {step} would write it." in log.text

    sinfo, options, base = mmorf(run="run")
    _chain_files(base, *[e for e in PRE_OUTPUTS + [WARP] if e != written])
    log = command(sinfo, options)
    assert log.status[2] == 1
    assert f"{os.path.basename(written)} not found, run {step} first!" in log.text
    assert external == []


@pytest.mark.parametrize(
    "command, script, chain, test_file",
    [
        (hcp_mmorf, "MMORFPipeline.sh", PRE_OUTPUTS, "xfms/mov_to_ref_mm_bias_1.nii.gz"),
        (hcp_post_mmorf, "PostMMORFPipeline.sh", PRE_OUTPUTS + [WARP], "sess-01.thickness_MSMAll.79k_fs_LR.dscalar.nii"),
    ],
)
def test_a_real_run_with_the_earlier_steps_done_calls_the_pipeline(mmorf, external, command, script, chain, test_file):
    sinfo, options, base = mmorf(run="run")
    _chain_files(base, *chain)
    log = command(sinfo, options)
    assert log.status[2] == 0, log.text
    assert len(external) == 1
    assert external[0]["command"].split()[0].endswith(f"MMORF/{script}")
    assert f'--study-folder="{sinfo["hcp"]}"' in external[0]["command"]
    assert external[0]["checkfile"].endswith(test_file)
    assert external[0]["remove"] is False


def test_a_real_pre_run_calls_the_pipeline(mmorf, external):
    sinfo, options, _ = mmorf(run="run")
    log = hcp_pre_mmorf(sinfo, options)
    assert log.status[2] == 0, log.text
    assert len(external) == 1
    assert external[0]["command"].split()[0].endswith("MMORF/PreMMORFPipeline.sh")
    assert external[0]["checkfile"].endswith("xfms/T1w_acpc_dc_restore_to_MMORFLinear.nii.gz")


@pytest.mark.parametrize(
    "command, test_file",
    [
        (hcp_pre_mmorf, "MMORFNonLinear/xfms/T1w_acpc_dc_restore_to_MMORFLinear.nii.gz"),
        (hcp_mmorf, "MMORFNonLinear/xfms/mov_to_ref_mm_bias_1.nii.gz"),
        (hcp_post_mmorf, "MNINonLinear/fsaverage_LR79k/sess-01.thickness_MSMAll.79k_fs_LR.dscalar.nii"),
    ],
)
def test_a_finished_step_reports_so_and_removes_nothing(mmorf, no_external, command, test_file):
    sinfo, options, base = mmorf()
    _chain_files(base, test_file)
    before = _tree(mmorf.root)
    log = command(sinfo, options)
    assert _tree(mmorf.root) == before
    assert log.status[1].endswith("finished")
    assert log.status[2] == 0


# ------------------------------------------------------------------- overwrite


POST_TEST_FILE = "MNINonLinear/fsaverage_LR79k/sess-01.thickness_MSMAll.79k_fs_LR.dscalar.nii"


@pytest.mark.parametrize(
    "command, gone, kept",
    [
        (
            hcp_pre_mmorf,
            [WARP, PRE_OUTPUTS[1], POST_TEST_FILE, "MMORFNonLinear/Native/sess-01.native.wb.spec"],
            ["T1w/Diffusion/data.nii.gz"],
        ),
        (
            hcp_mmorf,
            [WARP, "MMORFNonLinear/xfms/mov_to_ref_mm_jac.nii.gz", "MMORFNonLinear/xfms/mov_to_ref_mm_bias_1.nii.gz", POST_TEST_FILE],
            PRE_OUTPUTS + ["T1w/Diffusion/data.nii.gz"],
        ),
        (hcp_post_mmorf, [POST_TEST_FILE], PRE_OUTPUTS + [WARP]),
    ],
)
def test_overwrite_removes_what_it_invalidates_and_nothing_else(mmorf, external, command, gone, kept):
    sinfo, options, base = mmorf(run="run")
    _chain_files(base, *PRE_OUTPUTS, WARP, *gone)
    log = command(sinfo, options, overwrite=True)
    assert log.status[2] == 0, log.text
    assert external[0]["overwrite"] is True
    for name in gone:
        assert not os.path.exists(os.path.join(base, name)), name
    for name in kept:
        assert os.path.exists(os.path.join(base, name)), name


@pytest.mark.parametrize("command", COMMANDS)
def test_overwrite_in_a_dry_run_removes_nothing_and_says_so(mmorf, no_external, command):
    sinfo, options, base = mmorf()
    _chain_files(base, *PRE_OUTPUTS, WARP, POST_TEST_FILE)
    before = _tree(mmorf.root)
    log = command(sinfo, options, overwrite=True)
    assert _tree(mmorf.root) == before
    assert log.status[2] == 0, log.text
    assert f"test, not removed: {os.path.join(base, POST_TEST_FILE)}" in log.text


@pytest.mark.parametrize(
    "command, overrides",
    [
        (hcp_pre_mmorf, {"hcp_mmorf_lowest_shell_threshold": "abc"}),
        (hcp_pre_mmorf, {"hcp_species": "MacaqueRhesus"}),
        (hcp_mmorf, {"hcp_mmorf_t2_template": "/not/there.nii.gz"}),
        (hcp_post_mmorf, {"hcp_mmorf_diffusionmesh": "32"}),
    ],
)
def test_overwrite_with_a_failed_check_removes_nothing(mmorf, external, command, overrides):
    sinfo, options, base = mmorf(run="run", **overrides)
    _chain_files(base, *PRE_OUTPUTS, WARP, POST_TEST_FILE)
    before = _tree(mmorf.root)
    log = command(sinfo, options, overwrite=True)
    assert _tree(mmorf.root) == before
    assert log.status[2] == 1
    assert external == []


@pytest.mark.parametrize("command", COMMANDS)
def test_a_real_run_without_overwrite_removes_nothing(mmorf, external, command):
    sinfo, options, base = mmorf(run="run")
    _chain_files(base, *PRE_OUTPUTS, WARP, POST_TEST_FILE)
    before = _tree(mmorf.root)
    log = command(sinfo, options)
    assert log.status[2] == 0, log.text
    assert _tree(mmorf.root) == before
    assert external[0]["overwrite"] is False


@pytest.mark.parametrize("command", COMMANDS)
def test_overwrite_removes_before_the_pipeline_runs(mmorf, monkeypatch, command):
    sinfo, options, base = mmorf(run="run")
    _chain_files(base, *PRE_OUTPUTS, WARP, POST_TEST_FILE)
    present = []

    def stub(*args, **kwargs):
        present.append(os.path.exists(os.path.join(base, POST_TEST_FILE)))
        return "", "done", 0

    monkeypatch.setattr(pc, "run_external_for_file", stub)
    command(sinfo, options, overwrite=True)
    assert present == [False]


def test_overwrite_removes_a_linked_folder_and_not_its_target(mmorf, external):
    sinfo, options, base = mmorf(run="run")
    target = os.path.join(mmorf.root, "elsewhere")
    _touch(os.path.join(target, "kept"))
    os.symlink(target, os.path.join(base, "MMORFNonLinear"))
    log = hcp_pre_mmorf(sinfo, options, overwrite=True)
    assert log.status[2] == 0, log.text
    assert not os.path.lexists(os.path.join(base, "MMORFNonLinear"))
    assert os.path.exists(os.path.join(target, "kept"))


@pytest.mark.parametrize("run", ["run", "test"])
def test_a_completion_file_older_than_the_warp_asks_for_an_overwrite(mmorf, external, run):
    sinfo, options, base = mmorf(run=run)
    _chain_files(base, *PRE_OUTPUTS, WARP, POST_TEST_FILE)
    _make_older(base, POST_TEST_FILE, WARP)
    before = _tree(mmorf.root)
    log = hcp_post_mmorf(sinfo, options)
    assert _tree(mmorf.root) == before
    assert log.status[2] == 1
    assert "is older than" in log.text
    assert "--overwrite=yes" in log.text
    assert external == []


def test_overwrite_reruns_a_completion_file_older_than_the_warp(mmorf, external):
    sinfo, options, base = mmorf(run="run")
    _chain_files(base, *PRE_OUTPUTS, WARP, POST_TEST_FILE)
    _make_older(base, POST_TEST_FILE, WARP)
    log = hcp_post_mmorf(sinfo, options, overwrite=True)
    assert log.status[2] == 0, log.text
    assert len(external) == 1
    assert not os.path.exists(os.path.join(base, POST_TEST_FILE))


def test_an_overwrite_that_misses_a_completion_file_does_not_leave_post_finished(mmorf, external):
    # hcp_post_mmorf was given a regname the earlier step was not told about
    written = "MNINonLinear/fsaverage_LR79k/sess-01.thickness_MSMSulc.79k_fs_LR.dscalar.nii"
    sinfo, options, base = mmorf(run="run")
    _chain_files(base, *PRE_OUTPUTS, WARP, written)
    hcp_pre_mmorf(sinfo, options, overwrite=True)
    assert os.path.exists(os.path.join(base, written))

    _chain_files(base, *PRE_OUTPUTS, WARP)
    _make_older(base, written, WARP)
    options["hcp_mmorf_regname"] = "MSMSulc"
    del external[:]
    log = hcp_post_mmorf(sinfo, options)
    assert log.status[2] == 1
    assert "is older than" in log.text
    assert external == []


@pytest.mark.parametrize("command", COMMANDS)
def test_a_pipeline_that_stops_is_reported_as_failed(mmorf, monkeypatch, command):
    sinfo, options, base = mmorf(run="run")
    _chain_files(base, *PRE_OUTPUTS, WARP)

    def stop(*args, **kwargs):
        raise pc.ExternalFailed("the script stopped")

    monkeypatch.setattr(pc, "run_external_for_file", stop)
    log = command(sinfo, options)
    assert log.status[2] == 1
    assert "the script stopped" in log.text


@pytest.mark.parametrize("command", COMMANDS)
def test_a_failure_the_run_returns_is_passed_on(mmorf, monkeypatch, command):
    sinfo, options, base = mmorf(run="run")
    _chain_files(base, *PRE_OUTPUTS, WARP)
    monkeypatch.setattr(pc, "run_external_for_file", lambda *args, **kwargs: ("", "did not finish", 1))
    log = command(sinfo, options)
    assert log.status[2] == 1


# ------------------------------------------------------------- the rest of it


@pytest.mark.parametrize(
    "overrides, suffix, mrcorr, name",
    [
        ({}, "", False, "fsaverage_LR79k/sess-01.thickness_MSMAll.79k_fs_LR.dscalar.nii"),
        ({}, "", True, "fsaverage_LR79k/sess-01.MRcorrThickness_MSMAll.79k_fs_LR.dscalar.nii"),
        ({}, "_x", False, "fsaverage_LR79k/sess-01_x.thickness_MSMAll.79k_fs_LR.dscalar.nii"),
        (
            {"hcp_mmorf_regname": "MSMSulc", "hcp_mmorf_diffusionmesh": "59"},
            "",
            False,
            "fsaverage_LR59k/sess-01.thickness_MSMSulc.59k_fs_LR.dscalar.nii",
        ),
    ],
)
def test_post_completion_file_is_the_last_one_written(mmorf, overrides, suffix, mrcorr, name):
    sinfo, options, base = mmorf(suffix=suffix, **overrides)
    if mrcorr:
        _touch(os.path.join(base, "MNINonLinear", "Native", "sess-01.MRcorrThickness.native.dscalar.nii"))
    hcp = get_hcp_paths(sinfo, options)
    assert mu.post_test_file(sinfo, options, hcp) == os.path.join(base, "MNINonLinear", name)


def test_mmorf_warns_when_it_would_fall_back_to_the_cpu(mmorf, no_external, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: None)
    sinfo, options, _ = mmorf()
    log = hcp_mmorf(sinfo, options)
    assert log.status[2] == 0, log.text
    assert "nvidia-smi not found" in log.text


def test_mmorf_says_nothing_when_it_finds_the_gpu(mmorf, no_external, monkeypatch):
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/nvidia-smi" if name == "nvidia-smi" else None)
    sinfo, options, _ = mmorf()
    log = hcp_mmorf(sinfo, options)
    assert "nvidia-smi not found" not in log.text


@pytest.mark.parametrize("name", ["hcp_pre_mmorf", "hcp_mmorf", "hcp_post_mmorf"])
def test_commands_are_registered(name):
    registry = yaml.safe_load((REPO_ROOT / "qx_commands.yaml").read_text())
    command = {c["name"]: c for c in registry["commands"]}[name]
    assert command["type"] == "processing.session"
    assert command["path"] == f"qx_utilities.hcp.{name}.{name}"

import os


def get_test_data_path(path):
    dir = os.path.dirname(__file__)
    return os.path.join(dir, "test_data", path)


def build_hcp_session(root, bolds=False, dwi=False, session_id="sess-01"):
    """
    Create a minimal session tree with an HCP folder for dry-run tests.

    Lays out the structural + diffusion scaffolding an HCP command inspects in
    ``--test`` mode and returns the ``(sinfo, sessionsfolder)`` pair.

    Parameters:
        root: base directory to build under (e.g. a pytest tmp_path).
        bolds: also add two BOLD entries to sinfo.
        dwi: also add an unprocessed AP/PA DWI pair and its sinfo entries.
        session_id: the session id to use.

    Returns:
        ``(sinfo, sessionsfolder)``.
    """
    sessionsfolder = os.path.join(root, "sessions")
    hcp = os.path.join(sessionsfolder, session_id, "hcp")
    base = os.path.join(hcp, session_id)
    for sub in ["T1w/Diffusion", "T1w/Results", "MNINonLinear/Results",
                "unprocessed/T1w", "unprocessed/T2w"]:
        os.makedirs(os.path.join(base, sub), exist_ok=True)
    for f in ["bvals", "bvecs", "data.nii.gz", "nodif_brain_mask.nii.gz"]:
        open(os.path.join(base, "T1w", "Diffusion", f), "w").close()

    sinfo = {"id": session_id, "hcp": hcp, "subject": "subj-01",
             "1": {"name": "T1w", "task": "T1w"},
             "2": {"name": "T2w", "task": "T2w"}}
    if bolds:
        sinfo["3"] = {"name": "bold", "task": "rest", "boldname": "BOLD_1",
                      "bold_number": "1", "filename": "BOLD_1"}
        sinfo["4"] = {"name": "bold", "task": "rest", "boldname": "BOLD_2",
                      "bold_number": "2", "filename": "BOLD_2"}
    if dwi:
        dwi_source = os.path.join(base, "unprocessed", "Diffusion")
        os.makedirs(dwi_source, exist_ok=True)
        next_key = len([k for k in sinfo if k.isdigit()]) + 1
        for pe in ["PA", "AP"]:
            name = "DWI_dir99_%s" % pe
            open(os.path.join(dwi_source, "%s.nii.gz" % name), "w").close()
            sinfo[str(next_key)] = {
                "name": "DWI", "task": name, "EchoSpacing": "0.00069",
            }
            next_key += 1
    return sinfo, sessionsfolder


def default_options(**overrides):
    """
    Build a full options dictionary the way the CLI would.

    The defaults come from ``general.process.arglist``, the same table the
    command line parser uses, so a dry run driven from a test sees the option
    surface a real invocation would -- recoded through each parameter's
    declared type and then imputed, both of which ``general.process`` does
    before it hands the options to a command. ``comlogs``, ``logfolder`` and
    ``command_ran`` are normally filled in by ``general.process`` at run time,
    so they are seeded here too.

    Parameters:
        overrides: option values to set on top of the defaults.

    Returns:
        The options dictionary.
    """
    from qx_utilities.general import commands_support, process

    typed = [entry for entry in process.arglist if len(entry) == 3]

    options = {name: default for name, default, _ in typed}
    options.update(overrides)

    # process.py recodes every value through its declared type as the last step
    # before the options are used; without this, defaults such as "" never
    # become None and commands see values the CLI would never hand them
    for name, _, recode in typed:
        options[name] = recode(options[name])

    options.setdefault("comlogs", "")
    options.setdefault("logfolder", "")
    options.setdefault("specfolder", "")
    options.setdefault("command_ran", "test_command")

    # and then fills the parameters that take their value from another one --
    # `nifti_tail` from `qx_nifti_tail` from `hcp_nifti_tail`, and the same for
    # the CIFTI tail. Without this they stay None, which is a value the CLI
    # would never hand a command, and the first thing that resolves a BOLD file
    # name fails on it deep inside path building
    return commands_support.impute_parameters(options, options["command_ran"])

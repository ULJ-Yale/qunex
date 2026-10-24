# SPDX-FileCopyrightText: 2022 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import importlib.machinery
import importlib.util
import os
import stat


def get_test_data_path(path):
    dir = os.path.dirname(__file__)
    return os.path.join(dir, "test_data", path)


def load_gmri(name="gmri_under_test"):
    """
    The ``gmri`` dispatcher, loaded as a module of its own.

    ``python/qx_utilities/gmri`` is a script without a ``.py`` extension, so
    it is loaded by path. Each call loads a fresh module; the modules it
    imports are the ones every test shares, so a test patches those.

    Parameters:
        name: the name of the module, one per test module.

    Returns:
        the module.
    """
    path = os.path.join(os.path.dirname(__file__), "..", "qx_utilities", "gmri")
    loader = importlib.machinery.SourceFileLoader(name, path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def load_container(path=None):
    """
    The container launcher, ``bin/qunex_container``, loaded as a module.

    The launcher is a script without a ``.py`` extension, and it can not
    import QuNex -- it runs on the host, outside the container -- so it is
    loaded by path, with the spliced copies of ``general/batch_io.py`` and
    ``general/folders.py`` it carries. Each call loads a fresh module, so a
    test patches only its own.

    Parameters:
        path: the launcher to load, by default the one of this tree.

    Returns:
        the module.
    """
    if path is None:
        path = os.path.join(
            os.path.dirname(__file__), "..", "..", "bin", "qunex_container"
        )
    loader = importlib.machinery.SourceFileLoader(
        "qunex_container_under_test", str(path)
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def layout(root):
    """
    A study a run names, and a folder beside it the run is started from.

    The study, ``<root>/study``, carries its marker, one session, ``S01``, and
    a batch file, ``processing/batch.txt``, listing it. The other folder,
    ``<root>/elsewhere``, is empty.

    Parameters:
        root: the folder to build them in, a ``pathlib.Path``.

    Returns:
        ``(study, elsewhere)``, as ``pathlib.Path``.
    """
    study = root / "study"
    (study / "sessions" / "S01").mkdir(parents=True)
    (study / "processing").mkdir()
    (study / ".qunexstudy").write_text("")
    (study / "processing" / "batch.txt").write_text(
        "_x: 1\n---\nid: S01\nsubject: S01\nhcp: hcp\n01: T1w\n"
    )
    elsewhere = root / "elsewhere"
    elsewhere.mkdir()
    return study, elsewhere


def write_script(path, body, mode=0o755):
    """
    Write a script a test runs, or puts on the PATH in place of a program.

    Parameters:
        path: where to write it, a ``pathlib.Path``.
        body: its text.
        mode: its permissions; its owner can always read it.

    Returns:
        the path, as a string.
    """
    path.write_text(body)
    path.chmod(mode | stat.S_IRUSR)
    return str(path)


class Submission:
    """
    A job ``general.scheduler.schedule`` submitted, kept instead of run.

    ``schedule`` pipes the job script into ``sbatch`` or ``qsub`` through
    ``subprocess.Popen``. :meth:`install` puts this class in that call's place
    in the scheduler module alone, so a test reads what would have been
    submitted, and nothing else the test runs is taken for a submission.

    Attributes:
        program: what the script was handed to, ``sbatch`` or ``qsub``.
        script: the job script.
        jobid: the job id it answers with, as sbatch does.
    """

    def __init__(self, program, jobid):
        self.program = program
        self.script = ""
        self.jobid = jobid
        # the pipes `schedule` writes the script to and reads the answer from
        self.stdin = self.stdout = self.stderr = self

    def write(self, data):
        self.script += data.decode()

    def close(self):
        pass

    def read(self):
        return b"Submitted batch job %d" % self.jobid

    @classmethod
    def install(cls, monkeypatch):
        """
        Keep every job the scheduler module submits, for the rest of the test.

        Returns:
            the list each submission is appended to, in order.
        """
        import subprocess
        import types

        import qx_utilities.general.scheduler as gs

        submitted = []

        def popen(program, **kwargs):
            submitted.append(cls(program, len(submitted) + 1))
            return submitted[-1]

        view = types.SimpleNamespace(**vars(subprocess))
        view.Popen = popen
        monkeypatch.setattr(gs, "subprocess", view)
        return submitted


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
    from qx_utilities.general import batch_io, commands_support, folders, process

    typed = [entry for entry in process.arglist if len(entry) == 3]

    options = {name: default for name, default, _ in typed}
    options.update(overrides)

    # the two folders, absolute as `process.merge_options` settles them: the
    # study from the current folder, and a sessions folder from the study when
    # one is given. An empty one, or one of spaces, is one nobody named
    for key in ("studyfolder", "sessionsfolder"):
        if isinstance(options.get(key), str) and not options[key].strip():
            options[key] = ""
    study, sessions = options.get("studyfolder"), options.get("sessionsfolder")
    if study:
        options["studyfolder"] = batch_io.run_path(study)

    if sessions:
        options["sessionsfolder"] = batch_io.run_path(
            sessions, options["studyfolder"] if study else None
        )
    elif study:
        # a study folder given without a sessions folder brings its own
        options["sessionsfolder"] = folders.sessions_folder(options["studyfolder"])

    # process.py recodes every value through its declared type as the last step
    # before the options are used; without this, defaults such as "" never
    # become None and commands see values the CLI would never hand them
    for name, _, recode in typed:
        options[name] = recode(options[name])

    # and settles the study folder: the one given, else the folder the
    # sessions folder is in, else -- neither named -- the study marked above
    # the current folder. A command reads it, and never derives it
    if study or sessions:
        options["studyfolder"] = folders.study_folder(
            options["studyfolder"], options["sessionsfolder"]
        )
    else:
        options["studyfolder"] = folders.find_study(
            options["sessionsfolder"]
        ) or folders.study_folder(None, options["sessionsfolder"])

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

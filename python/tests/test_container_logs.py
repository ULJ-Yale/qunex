# SPDX-FileCopyrightText: 2026 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Where ``qunex_container`` keeps the logs of a run: in the folder QuNex places
the run in (``general/folders.py``'s ``run_folders``, which the launcher
carries a copy of), decided on the host before the container starts and handed
to the command in it once, with the launcher's own files -- the job scripts,
the scripts it submits and the jobs' output -- in its ``batchlogs``. A call that
runs nothing makes no folder.

The container never starts here: the launcher's ``subprocess`` is replaced, so
nothing is run or submitted, and the job scripts it wrote are read back.

The launcher reads on the host what QuNex reads to place a run: the settings
files and run_recipe's recipe file, which it can not read without PyYAML and
says so, and the recipe's ``{{$VAR}}`` labels, from its own environment and
from what ``--bash_post`` exports. It refuses the settings QuNex refuses,
before it runs anything. ``tests/test_log_placement.py`` holds it to placing
every run where ``gmri`` does.
"""

import os
import re
import subprocess
import sys
import types
from pathlib import Path

import pytest
import yaml

import qx_utilities.general.batch_io as bio
import qx_utilities.general.exceptions as ge
import qx_utilities.general.log.settings as ls
from tests.utils import load_container

TS = "2026-10-22_10.00.00.000000"

# the recipe of the Quick Start, as `Overview-QuickStart.md` gives it
QUICK_START = """\
global_parameters:
    studyfolder     : "{{$STUDY_FOLDER}}"
    sessions        : "HCPA001"
    batchfile       : "{{$STUDY_FOLDER}}/processing/batch.txt"

recipes:
    quick_start:
        commands:
            - create_study
            - import_dicom:
                inbox       : "{{$RAW_DATA}}"
                archive     : "leave"
            - create_session_info:
                mapping : "{{$RAW_DATA}}/HCPA001_mapping.txt"
            - setup_hcp
            - create_batch:
                targetfile  : "{{$STUDY_FOLDER}}/processing/batch.txt"
                paramfile   : "{{$RAW_DATA}}/HCPA001_parameters.txt"
            - hcp_pre_freesurfer
"""


def make_study(root, header=""):
    """A study with two sessions, and a batch file listing them."""
    for session in ("S01", "S02"):
        (root / "sessions" / session).mkdir(parents=True)
    (root / "processing").mkdir()
    (root / ".qunexstudy").write_text("")
    (root / "processing" / "batch.txt").write_text(
        header + "---\nid: S01\nsubject: S01\n---\nid: S02\nsubject: S02\n"
    )
    return root


class Launch:
    """What a call of the launcher did: ran, submitted, and how it ended."""

    def __init__(self):
        self.ran, self.submitted, self.code = [], [], 0


@pytest.fixture
def launch(tmp_path, monkeypatch):
    """
    Runs the launcher from `tmp_path`, with a home folder of its own and the
    container never started. Returns a callable taking the launcher's command
    line, without `--container`, and returning a `Launch`.
    """
    (tmp_path / "home").mkdir()
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.chdir(tmp_path)

    def run(*args, container="x.sif", qc=None):
        qc = qc or load_container()
        done = Launch()

        class Submission:
            """`sbatch` or `qsub`, keeping the job script piped to it."""

            def __init__(self, program, **kwargs):
                self.stdin, self.script = self, ""
                done.submitted.append(self)

            def write(self, data):
                self.script += data.decode()

            def close(self):
                pass

        view = types.SimpleNamespace(**vars(subprocess))
        view.run = lambda command, **kwargs: done.ran.append(command)
        view.Popen = Submission
        monkeypatch.setattr(qc, "subprocess", view)
        monkeypatch.setattr(qc, "time", types.SimpleNamespace(sleep=lambda s: None))
        try:
            qc.main([*args, "--container=%s" % container])
        except SystemExit as e:
            done.code = e.code
        done.submitted = [submission.script for submission in done.submitted]
        return done

    return run


def handed(script):
    """The log folders the command in the container is given."""
    return re.findall(r'--logfolder="([^"]*)"', script)


def job_scripts(folder):
    """The scripts the jobs run in the container, in job order."""
    return sorted(
        (Path(folder) / "batchlogs").glob("qunex_container_command_*.sh"),
        key=lambda path: int(path.stem.rsplit("_", 1)[1]),
    )


# ---------------------------------------------------------- one folder a run


def test_every_container_job_logs_in_one_folder_with_output_of_its_own(
    tmp_path, launch
):
    """
    All the jobs of a submission shared one output and one error file, which
    each job wrote over, and their job scripts sat in the folder itself, or
    in ~/qunex when the launcher could not tell the study.
    """
    study = make_study(tmp_path / "study")

    done = launch(
        "dwi_dtifit",
        "--studyfolder=%s" % study,
        "--batchfile=%s" % (study / "processing" / "batch.txt"),
        "--scheduler=SLURM,time=1:00:00",
    )

    (folder,) = (study / "logs").iterdir()
    stamp = folder.name[: -len("_dwi_dtifit")]
    batchlogs = folder / "batchlogs"
    assert sorted(path.name for path in folder.iterdir()) == ["batchlogs"]
    assert sorted(path.name for path in batchlogs.iterdir()) == [
        "SLURM_dwi_dtifit_job00.%s.sh" % stamp,
        "SLURM_dwi_dtifit_job01.%s.sh" % stamp,
        "qunex_container_command_%s_0.sh" % stamp,
        "qunex_container_command_%s_1.sh" % stamp,
    ]

    for number, job in enumerate(done.submitted):
        output = str(batchlogs / ("SLURM_dwi_dtifit_job%02d.%s.log" % (number, stamp)))
        assert re.findall(r"#SBATCH -([oe]) (\S+)", job) == [
            ("o", output),
            ("e", output),
        ]
        kept = (
            batchlogs / ("SLURM_dwi_dtifit_job%02d.%s.sh" % (number, stamp))
        ).read_text()
        assert kept.replace("\n", "") == job.replace("\n", ""), "the script submitted"

    for script in job_scripts(folder):
        assert handed(script.read_text()) == [str(folder)], "handed once, absolute"
    assert not (tmp_path / "home" / "qunex").exists()


@pytest.mark.parametrize("pyyaml", [True, False], ids=["pyyaml", "no pyyaml"])
def test_scheduled_jobs_are_not_handed_the_status_record(tmp_path, launch, pyyaml):
    """
    Each job was handed the --logstatus the launcher was given, so the jobs of
    one call wrote the same record and the last to finish overwrote the
    others. The launcher writes it, saying which job each session went to.
    """
    study = make_study(tmp_path / "study")
    qc = load_container()
    if not pyyaml:
        qc.yaml = None

    launch(
        "dwi_dtifit",
        "--studyfolder=%s" % study,
        "--batchfile=%s" % (study / "processing" / "batch.txt"),
        "--scheduler=SLURM,time=1:00:00",
        "--logstatus=status.yaml",
        qc=qc,
    )

    (folder,) = (study / "logs").iterdir()
    for script in job_scripts(folder):
        assert "--logstatus" not in script.read_text()
    record = yaml.safe_load((tmp_path / "status.yaml").read_text())
    assert record["command"] == "dwi_dtifit" and record["failed"] is None
    assert record["sessions"] == [
        {"id": "S01", "summary": "submitted (job 00)", "failed": None},
        {"id": "S02", "summary": "submitted (job 01)", "failed": None},
    ]


def test_a_job_run_on_the_host_writes_its_own_status_record(tmp_path, launch):
    """Run, not submitted, the one job says what it did itself."""
    study = make_study(tmp_path / "study")

    launch("dwi_dtifit", "--studyfolder=%s" % study, "--logstatus=status.yaml")

    (folder,) = (study / "logs").iterdir()
    (script,) = job_scripts(folder)
    assert '--logstatus="%s"' % (tmp_path / "status.yaml") in script.read_text()
    assert not (tmp_path / "status.yaml").exists()


@pytest.fixture
def rebuilt(tmp_path):
    """The launcher with the splice of this tree's modules, as the build makes it."""
    import qx_container_build as build

    path = tmp_path / "qunex_container"
    path.write_text(
        build.render(
            build.CONTAINER.read_text(), build.spliced_modules(), build.read_version()
        )
    )
    return load_container(path)


def test_a_deprecated_command_is_placed_by_the_name_it_has_now(
    tmp_path, launch, rebuilt
):
    """
    The run was filed under the name as typed, which gmri maps first, and a
    deprecated create_study took a relative --logfolder from the study it
    names rather than from the current folder.
    """
    study = make_study(tmp_path / "study")

    launch("fc_ComputeSeedMaps", "--studyfolder=%s" % study, qc=rebuilt)
    launch(
        "createStudy", "--studyfolder=%s" % study, "--logfolder=mine", qc=rebuilt
    )

    (folder,) = (study / "logs").iterdir()
    assert folder.name.endswith("_fc_compute_seedmaps")
    assert (tmp_path / "mine" / "batchlogs").is_dir()
    assert not (study / "mine").exists()


def test_a_job_that_runs_no_sessions_is_not_numbered(tmp_path, launch):
    """As QuNex names a job it submits without sessions: the run alone."""
    study = make_study(tmp_path / "study")
    recipe = tmp_path / "r.yaml"
    recipe.write_text("recipes:\n    r:\n        commands: [create_study]\n")

    done = launch(
        "run_recipe",
        "--studyfolder=%s" % study,
        "--recipe_file=%s" % recipe,
        "--recipe=r",
        "--scheduler=PBS,walltime=1:00:00",
    )

    (folder,) = (study / "logs").iterdir()
    stamp = folder.name[: -len("_run_recipe_r")]
    output = str(folder / "batchlogs" / ("PBS_run_recipe_r.%s.log" % stamp))
    (job,) = done.submitted
    assert "#PBS -o %s\n#PBS -e %s\n#PBS -j oe\n" % (output, output) in job, (
        "one file, both streams, as PBS joins them"
    )
    assert (folder / "batchlogs" / ("PBS_run_recipe_r.%s.sh" % stamp)).exists()


def test_a_job_array_writes_an_output_for_each_of_its_tasks(tmp_path, launch):
    study = make_study(tmp_path / "study")

    done = launch(
        "hcp_freesurfer",
        "--studyfolder=%s" % study,
        "--sessions=S01,S02",
        "--parjobs=1",
        "--scheduler=SLURM,time=1:00:00,array",
    )

    (folder,) = (study / "logs").iterdir()
    stamp = folder.name[: -len("_hcp_freesurfer")]
    (job,) = done.submitted
    assert "#SBATCH --array=0-1%1\n" in job, "it read 0-1%%1, which is no array"
    output = folder / "batchlogs" / ("SLURM_hcp_freesurfer_job%%a.%s.log" % stamp)
    assert "#SBATCH -o %s\n" % output in job
    assert (folder / "batchlogs" / ("SLURM_hcp_freesurfer.%s.sh" % stamp)).exists()


def test_the_output_console_out_names_is_where_the_jobs_write(tmp_path, launch):
    """
    A file named without a folder was refused as being in a folder that does
    not exist; it is in the current one, and handed to the scheduler absolute.
    """
    study = make_study(tmp_path / "study")

    done = launch(
        "hcp_freesurfer",
        "--studyfolder=%s" % study,
        "--sessions=S01",
        "--scheduler=SLURM,time=1:00:00",
        "--console_out=both:out.log",
    )

    (job,) = done.submitted
    assert "#SBATCH -o %s\n" % (tmp_path / "out.log") in job
    (folder,) = (study / "logs").iterdir()
    assert (
        len(list((folder / "batchlogs").glob("SLURM_hcp_freesurfer_job00.*.sh"))) == 1
    )


def test_a_relative_logfolder_is_in_the_named_study_and_handed_in_once(
    tmp_path, launch, capsys
):
    """It was handed twice: as it was typed, and as the launcher read it."""
    study = make_study(tmp_path / "study")

    done = launch("dwi_dtifit", "--studyfolder=study", "--logfolder=mylogs")

    (script,) = job_scripts(study / "mylogs")
    assert handed(script.read_text()) == [str(study / "mylogs")]
    assert "--logfolder=mylogs" not in script.read_text()
    assert not (tmp_path / "mylogs").exists()
    assert len(done.ran) == 1
    assert "\n---> Logs: %s\n" % (study / "mylogs") in capsys.readouterr().out


def test_a_study_named_only_in_the_batch_file_header_holds_the_logs(tmp_path, launch):
    """The launcher used to see only the command line, and logged in ~/qunex."""
    study = make_study(
        tmp_path / "study", header="_studyfolder: %s\n" % (tmp_path / "study")
    )

    launch("dwi_dtifit", "--batchfile=%s" % (study / "processing" / "batch.txt"))

    (folder,) = (study / "logs").iterdir()
    assert folder.name.endswith("_dwi_dtifit")
    assert not (tmp_path / "home" / "qunex").exists()


def test_a_container_run_of_a_script_is_filed_under_the_script(tmp_path, launch):
    """Its folder was named after the first parameter, `<stamp>_--studyfolder="..."`."""
    study = make_study(tmp_path / "study")
    (tmp_path / "my_pipeline.sh").write_text("echo scripted\n")

    launch("--script=my_pipeline.sh", "--studyfolder=%s" % study)

    (folder,) = (study / "logs").iterdir()
    assert folder.name.endswith("_my_pipeline")
    (script,) = job_scripts(folder)
    assert "\nbash %s\n" % (tmp_path / "my_pipeline.sh") in script.read_text(), (
        "run by its absolute path, taken from where the launcher runs"
    )


def test_a_docker_job_runs_a_script_as_it_is_written(tmp_path, launch):
    """
    Docker runs the script's text inside the job script, which was written a
    line and an empty line at a time: a here document gained blank lines.
    """
    study = make_study(tmp_path / "study")
    text = "cat > out.txt <<END\nline one\nline two\nEND"
    (tmp_path / "here.sh").write_text(text)

    launch("--script=here.sh", "--studyfolder=%s" % study, container="qunex/suite:1")

    (folder,) = (study / "logs").iterdir()
    (script,) = job_scripts(folder)
    assert script.read_text().endswith("\n" + text + "\n")


def test_the_logs_line_comes_before_what_the_container_prints(tmp_path):
    """
    Printed and not flushed, it waited in the launcher's buffer while the
    container wrote, and came after the command's own output in a file.
    """
    study = make_study(tmp_path / "study")
    stubs = tmp_path / "stubs"
    stubs.mkdir()
    (stubs / "singularity").write_text("#!/bin/sh\necho INNER\n")
    (stubs / "singularity").chmod(0o755)
    (tmp_path / "home").mkdir()
    launcher = Path(__file__).resolve().parents[2] / "bin" / "qunex_container"
    out = tmp_path / "out.txt"

    with open(out, "w") as f:
        subprocess.run(
            [sys.executable, str(launcher), "general_find_peaks"]
            + ["--studyfolder=%s" % study, "--container=x.sif"],
            cwd=tmp_path,
            env={
                **os.environ,
                "HOME": str(tmp_path / "home"),
                "PATH": "%s:%s" % (stubs, os.environ["PATH"]),
            },
            stdout=f,
            stderr=subprocess.STDOUT,
            timeout=60,
        )

    text = out.read_text()
    assert "---> Logs: " in text and "INNER" in text, text
    assert text.index("---> Logs: ") < text.index("INNER"), text


@pytest.mark.parametrize(
    "extra",
    [
        ["--parinfo", "--scheduler=SLURM,time=1:00:00"],
        ["--env_status"],
        ["--interactive"],
    ],
    ids=["parinfo", "env_status", "interactive"],
)
def test_a_call_that_runs_nothing_creates_no_folder(tmp_path, launch, extra):
    study = make_study(tmp_path / "study")

    done = launch(
        "dwi_dtifit",
        "--studyfolder=%s" % study,
        "--batchfile=%s" % (study / "processing" / "batch.txt"),
        *extra,
    )

    assert done.code in (0, None)
    assert not (study / "logs").exists()
    assert sorted((tmp_path / "home").iterdir()) == [], "nor ~/qunex, nor ~/qunex_logs"


def test_the_quick_start_recipe_logs_in_its_study(
    tmp_path, launch, monkeypatch, capsys
):
    """
    The study the recipe names is a label that only --bash_post sets: the
    launcher reads the export, and the run logs in the study the Quick Start
    says it does, which does not exist until the recipe's first step makes it.
    """
    for name in ("STUDY_FOLDER", "RAW_DATA"):
        monkeypatch.delenv(name, raising=False)
    study, data = tmp_path / "qunex" / "quickstart", tmp_path / "qunex" / "data"
    data.mkdir(parents=True)
    (data / "recipe.yaml").write_text(QUICK_START)
    bash_post = "export STUDY_FOLDER=%s;export RAW_DATA=%s" % (study, data)

    done = launch(
        "run_recipe",
        "--recipe_file=%s" % (data / "recipe.yaml"),
        "--recipe=quick_start",
        "--bash_post=%s" % bash_post,
    )

    (folder,) = (study / "logs").iterdir()
    assert folder.name.endswith("_run_recipe_quick_start")
    (script,) = job_scripts(folder)
    lines = script.read_text().splitlines()
    assert handed(lines[-1]) == [str(folder)]
    assert lines.index(bash_post) == 2, "after the environment and the folder"
    assert len(done.ran) == 1
    assert "WARNING" not in capsys.readouterr().out


def test_logging_none_still_keeps_the_job_script(tmp_path, launch):
    """The command logs nothing, but the job still needs its script."""
    study = make_study(tmp_path / "study")

    launch("dwi_dtifit", "--studyfolder=%s" % study, "--sessions=S01", "--logging=none")

    (folder,) = (study / "logs").iterdir()
    (script,) = job_scripts(folder)
    assert sorted(path.relative_to(folder) for path in folder.rglob("*")) == [
        Path("batchlogs"),
        script.relative_to(folder),
    ]
    assert '--logging="none"' in script.read_text()


def test_a_recipe_file_the_host_can_not_read_stops_the_launcher(
    tmp_path, launch, capsys
):
    """run_recipe would stop on it in the container, after the folder was made."""
    (tmp_path / "r.yaml").write_text("recipes: [unclosed\n")
    before = sorted(tmp_path.rglob("*"))

    done = launch("run_recipe", "--recipe_file=r.yaml", "--recipe=r")

    assert done.code == 1 and done.ran == []
    assert sorted(tmp_path.rglob("*")) == before, "nothing written anywhere"
    out = capsys.readouterr().out
    assert "ERROR: Could not parse recipe file\n%s\n" % (tmp_path / "r.yaml") in out


def test_settings_qunex_refuses_stop_the_launcher_before_it_writes_anything(
    tmp_path, launch, capsys
):
    """The run would have failed in the container, after the folder was made."""
    study = make_study(tmp_path / "study")
    (tmp_path / "home" / ".qunex_settings.yaml").write_text(
        "logging:\n    layout: flat\n"
    )
    before = sorted(tmp_path.rglob("*"))

    done = launch("dwi_dtifit", "--studyfolder=%s" % study, "--sessions=S01")

    assert done.code == 1
    assert done.ran == [] and done.submitted == []
    assert sorted(tmp_path.rglob("*")) == before, "nothing written anywhere"
    out = capsys.readouterr().out
    assert "ERROR: Invalid logging setting" in out
    assert "logging.layout must be one of [default, legacy, nested], got: 'flat'" in out


# ------------------------------------------------- what the host reads to place


@pytest.fixture
def host(tmp_path, monkeypatch):
    """The launcher, run in `tmp_path/cwd` with a home folder of its own."""
    for folder in ("home", "cwd"):
        (tmp_path / folder).mkdir()
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.chdir(tmp_path / "cwd")
    return load_container()


def write_recipe(path, **global_parameters):
    """A recipe file holding the one recipe, `r`, with the global parameters given."""
    path.write_text(
        yaml.safe_dump(
            {
                "global_parameters": global_parameters,
                "recipes": {"r": {"commands": ["create_study"]}},
            }
        )
    )
    return str(path)


# what --bash_post exports as the launcher reads it, with HOME set to /home/u
EXPORTS = [
    (  # the Quick Start's
        "export STUDY_FOLDER=/home/u/qunex/quickstart;export RAW_DATA=/home/u/qunex/data",
        {"STUDY_FOLDER": "/home/u/qunex/quickstart", "RAW_DATA": "/home/u/qunex/data"},
    ),
    (  # the acceptance tests'
        "export STUDY_FOLDER=/a/b; export QX_AT_FOLDER=/c;export QX_RAWDATA_FOLDER=/d",
        {"STUDY_FOLDER": "/a/b", "QX_AT_FOLDER": "/c", "QX_RAWDATA_FOLDER": "/d"},
    ),
    ('cd /tmp && export A="/p q/r"; export B=$A/s', {"A": "/p q/r", "B": "/p q/r/s"}),
    ("export A=/a B=$A/b", {"A": "/a"}),
    ("export H=${HOME}/h I=$NOBODY/i", {"H": "/home/u/h"}),
    ("S=/data/study; export S", {"S": "/data/study"}),
    ("C=1 ; export D=2 E=$C", {"D": "2", "E": "1"}),
    ("export -n F=1; export G='/g'", {"G": "/g"}),
    ("export A=1\nB=2", {"A": "1"}),
    ("export A B=1", {"B": "1"}),
    ("echo export A=1", {}),
    ("export J=1 || export K=2", {"J": "1"}),
    ("export L=1 | cat; export M=2 &", {}),
    ("source /nowhere.sh; export C=$(pwd); export D=`pwd`; E=1", {}),
    ("export T=1; export T=$(pwd); export U=$T", {}),
    ("export A='unbalanced", {}),
    # a later statement changes what is exported, or takes it back
    ("export A=1; A=2", {"A": "2"}),
    ("A=1 B=$A; export B", {"B": "1"}),
    ("export A=1; unset A", {}),
    ("export A=1; unset -f A", {"A": "1"}),
    ("export A=1; export -n A", {}),
    ("export A=1; export -n A=3; export B=$A", {"B": "3"}),
    ("export A=1 -n", {"A": "1"}),
    ("true & export B=2", {"B": "2"}),
    # a comment as bash reads one: a `#` inside a word, or quoted, is no comment
    ("export A=1 # B=2; export C=3\nexport D=4", {"A": "1", "D": "4"}),
    ("A=1 #c\nexport A", {"A": "1"}),
    ("export A=/data/study#1 B=$HOME#2", {"A": "/data/study#1", "B": "/home/u#2"}),
    (
        'export A=\'#x\' B="x # y"; echo "# no"; export C=3',
        {"A": "#x", "B": "x # y", "C": "3"},
    ),
    # a `~` that begins a value is the home folder; what else bash expands, the
    # host can not tell
    ("export A=~/s B=~", {"A": "/home/u/s", "B": "/home/u"}),
    ("export A=${X:-/d} B=/tmp/$$ C=$1/s D=${HOME#/} E=~root F=/x:~/y", {}),
    ("A=1; export A+=2 B=(x y)", {}),
    # quoted or escaped, a `$` or a `~` is taken as it is written
    ("export A='$B' B=\\$A C=\"\\$A\"", {"A": "$B", "B": "$A", "C": "$A"}),
    ("export A=\"~/k\" B='~' C=\\~/m", {"A": "~/k", "B": "~", "C": "~/m"}),
    ("export A='it'\\''s'", {"A": "it's"}),
    # a `&` sends the whole `&&`/`||` list to the background, a line break
    # after `&&`, `||` or `|` goes on with it, and what a statement after `||`
    # sets may or may not be set
    ("export C=~ || true & echo x", {}),
    ("export A=1 && true &", {}),
    ("export A=1 ||\nexport B=2", {"A": "1"}),
    ("export A=1 || # c\nexport B=2 &", {}),
    ("export B=/1; false || export B=/2", {}),
    # an array is never exported, nor read
    ("B=(1 2) HOME=$1; export A=$HOME/z", {}),
    ("export A=(1 2) C=1; export A=/x C", {}),
]


@pytest.mark.parametrize("bash_post, expected", EXPORTS)
def test_bash_post_exports_are_read_as_bash_exports_them(
    tmp_path, host, bash_post, expected
):
    """
    Read before the container starts, so only what the host can tell: a
    value a command or an expansion other than `$NAME` makes, one that refers
    to what the host does not know, and an export that does not reach the
    shell that runs the command -- in a pipeline, in the background, after a
    `||` -- are not read. And an export's words are expanded before it runs,
    so `export A=/a B=$A/b` does not give B the A it sets. What is read is
    what bash exports: a value read wrong would place the run in another
    folder than the one the command in the container works in.
    """
    env = {"HOME": "/home/u", "PATH": os.environ["PATH"]}

    read = host.bash_post_exports(bash_post, env)

    assert read == expected
    shell = subprocess.run(
        ["bash", "-c", bash_post + "\nenv"],
        env=env,
        cwd=tmp_path,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
    )
    exported = dict(
        line.split("=", 1) for line in shell.stdout.splitlines() if "=" in line
    )
    assert {name: exported.get(name) for name in read} == read


@pytest.mark.parametrize("bash_post, expected", EXPORTS)
def test_qunex_reads_the_exports_as_the_launcher_does(host, bash_post, expected):
    """
    `gmri` reads a scheduled run's --bash with the parser the launcher reads
    --bash_post with: the one `general/batch_io.py` holds, and the launcher
    carries spliced.
    """
    env = {"HOME": "/home/u", "PATH": os.environ["PATH"]}

    assert bio.bash_post_exports(bash_post, env) == expected
    assert host.bash_post_exports(bash_post, env) == expected


def test_bash_post_exports_refer_to_the_environment_unless_given_another(host):
    assert host.bash_post_exports("export Q=$HOME") == {"Q": os.environ["HOME"]}
    for nothing in (None, True, "", "   "):
        assert host.bash_post_exports(nothing) == {}


def test_a_label_the_host_can_not_resolve_is_said_and_skipped(
    tmp_path, monkeypatch, host, capsys
):
    monkeypatch.delenv("QX_NOT_SET_ANYWHERE", raising=False)
    args = {
        "recipe_file": write_recipe(
            tmp_path / "r.yaml", studyfolder="{{$QX_NOT_SET_ANYWHERE}}"
        ),
        "recipe": "r",
    }

    placed = host.host_placement("run_recipe", args, {}, TS)

    assert placed.logfolder == str(
        tmp_path / "home" / "qunex_logs" / (TS + "_run_recipe_r")
    ), "placed by what else the run states"
    out = capsys.readouterr().out
    assert out.count("WARNING") == 1
    assert "{{$QX_NOT_SET_ANYWHERE}}" in out
    assert "--bash_post (export NAME=value)" in out and "--studyfolder" in out


def test_without_pyyaml_the_launcher_says_what_it_can_not_apply(
    tmp_path, monkeypatch, host, capsys
):
    """
    A host python without PyYAML can not read the settings files or a recipe
    file. The run is placed without them, and each file that states something
    that would place it is named, once.
    """
    legacy = make_study(tmp_path / "legacy")
    (legacy / "qunex_settings.yaml").write_text("logging:\n    layout: legacy\n")
    args = {
        "studyfolder": str(legacy),
        "recipe_file": write_recipe(tmp_path / "r.yaml", logfolder="rlogs"),
        "recipe": "r",
    }
    monkeypatch.setattr(host, "yaml", None)

    placed = host.host_placement("run_recipe", args, {}, TS)

    assert placed.logfolder == str(legacy / "logs" / (TS + "_run_recipe_r"))
    out = capsys.readouterr().out
    assert out.count("has no PyYAML") == 2, out
    assert str(legacy / "qunex_settings.yaml") in out and args["recipe_file"] in out

    (legacy / "qunex_settings.yaml").write_text("logging:\n    comlog: false\n")
    host.host_placement("c", {"studyfolder": str(legacy)}, {}, TS)
    assert "PyYAML" not in capsys.readouterr().out, (
        "a file that states nothing about where a run logs is not missed"
    )


@pytest.mark.parametrize(
    "shape",
    [
        "two user files",
        "a layout it does not take",
        "logging not a mapping",
        "no mapping",
        "no yaml",
    ],
)
def test_the_launcher_refuses_the_settings_qunex_refuses(tmp_path, host, shape):
    """
    With the same error and the same hints, before anything is submitted:
    the run would otherwise fail in the container, after its folder was made.
    """
    study = make_study(tmp_path / "study")
    files = {
        "two user files": [
            "home/.qunex_settings.yaml",
            "home/qunex/qunex_settings.yaml",
        ],
    }.get(shape, ["study/qunex_settings.yaml"])
    text = {
        "a layout it does not take": "logging:\n    layout: flat\n",
        "logging not a mapping": "logging: true\n",
        "no mapping": "- logging\n",
        "no yaml": "logging: [unclosed\n",
    }.get(shape, "logging:\n    layout: nested\n")
    for name in files:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / name).write_text(text)

    with pytest.raises(ge.CommandError) as qunex:
        ls.resolve_logging("c", {}, studyfolder=str(study))
    with pytest.raises(host.CommandError) as launcher:
        host.host_settings(str(study))

    assert launcher.value.error == qunex.value.error
    assert launcher.value.hints == qunex.value.hints

#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``workflow/get_bold_data.py``

Maps NIL preprocessed data to the session's images folder.
"""

# Created by Grega Repovs on 2016-12-17.
# Code split from dofcMRIp_core gCodeP/preprocess codebase.
# Copyright (c) Grega Repovs. All rights reserved.

import os
import time
import traceback
from datetime import datetime

import qx_utilities.processing.core as pc
import qx_utilities.general.img as gi
from qx_utilities.general.log import ReportLog
from qx_utilities.processing.workflow import dryrun


def get_bold_data(sinfo, options, overwrite=False, thread=0):
    """
    ``get_bold_data [... processing options]``

    Map NIL preprocessed data into the session's images folder.

    ..  qx_command:
        type: processing.session

    Parameters:
        --batchfile (str, default ''):
            The batch.txt file with all the session information.

        --sessions (str, default ''):
            A list of sessions to process.

        --sessionsfolder (str, default '.'):
            The path to the study/sessions folder.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no).

        --logfolder (str, default ''):
            The path to the folder where runlogs and comlogs are to be stored,
            if other than default.
    """
    log = ReportLog()

    log.rule()
    log.info(f"Session id: {sinfo['id']} \n[started on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}]")
    log.info("Copying imaging data ...")

    log.info("Structural data ...")
    pc.do_options_check(options, sinfo, "get_bold_data")
    f = pc.get_file_names(sinfo, options)

    with pc.combined_comlog(log, options, "get_bold_data", thread=sinfo["id"]):
        copy = True
        if os.path.exists(f["t1"]):
            copy = False

        try:
            if overwrite or copy:
                if f["t1_source"] is None:
                    raise pc.NoSourceFolder(
                        "ERROR: Data source folder is not set. Please check your paths!"
                    )
                log.detail(f"copying {f['t1_source']}")
                if options["image_target"] == "4dfp":
                    if gi.get_img_format(f["t1_source"]) == ".4dfp.img":
                        dryrun.link_or_copy(log, options, f["t1_source"], f["t1"])
                        dryrun.link_or_copy(
                            log,
                            options,
                            f["t1_source"].replace(".img", ".ifh"),
                            f["t1"].replace(".img", ".ifh"),
                        )
                    else:
                        tmpfile = f["t1"].replace(
                            ".4dfp.img", gi.get_img_format(f["t1_source"])
                        )
                        dryrun.link_or_copy(log, options, f["t1_source"], tmpfile)
                        dryrun.run_external(
                            log,
                            options,
                            f["t1"],
                            "g_FlipFormat %s %s"
                            % (tmpfile, f["t1"].replace(".img", ".ifh")),
                            "... converting %s to 4dfp" % (os.path.basename(tmpfile)),
                            overwrite=overwrite,
                        )
                        dryrun.remove(log, options, tmpfile)
                if options["image_target"] == "nifti":
                    if gi.get_img_format(f["t1_source"]) == ".4dfp.img":
                        tmpimg = f["t1"] + ".4dfp.img"
                        tmpifh = f["t1"] + ".4dfp.ifh"
                        dryrun.link_or_copy(log, options, f["t1_source"], tmpimg)
                        dryrun.link_or_copy(
                            log, options, f["t1_source"].replace(".img", ".ifh"), tmpifh
                        )
                        dryrun.run_external(
                            log,
                            options,
                            f["t1"],
                            "g_FlipFormat %s %s"
                            % (tmpifh, f["t1"].replace(".img", ".ifh")),
                            "... converting %s to NIfTI" % (os.path.basename(tmpimg)),
                            overwrite=overwrite,
                        )
                        dryrun.remove(log, options, tmpimg)
                        dryrun.remove(log, options, tmpifh)
                    else:
                        if gi.get_img_format(f["t1_source"]) == ".nii.gz":
                            tmpfile = f["t1"] + ".gz"
                            dryrun.link_or_copy(log, options, f["t1_source"], tmpfile)
                            dryrun.run_external(
                                log,
                                options,
                                f["t1"],
                                "gunzip -f %s" % (tmpfile),
                                "... gunzipping %s" % (os.path.basename(tmpfile)),
                                overwrite=overwrite,
                            )
                            if os.path.exists(tmpfile):
                                dryrun.remove(log, options, tmpfile)
                        else:
                            dryrun.link_or_copy(log, options, f["t1_source"], f["t1"])

            else:
                log.detail(f"{f['t1']} present")
        except Exception:
            log.error("getting the data failed! Please check paths and files!", depth=1)

        # the same bold selection every other command in this file uses. The
        # hand-rolled loop this replaces matched `task` alone, split `--bolds`
        # on "|" only, and had no case for its own default of "all" -- which
        # matched no task and so processed nothing at all
        bolds, _, _ = pc.use_or_skip_bold(sinfo, options, _log=log)

        for boldinfo in bolds:
            boldname = boldinfo["name"]

            log.raw("\n\nWorking on: " + boldname + " ...")

            try:
                # --- filenames
                f = pc.get_file_names(sinfo, options)
                f.update(pc.get_bold_file_names(sinfo, boldname, options))
                _ = pc.get_session_folders(sinfo, options)

                # the bold's own data, not the status of whichever structural
                # conversion happened to run last: that name is unbound
                # whenever none did -- which is every run where the T1 is
                # already in place, and every dry run -- and reading it raised
                # a NameError the handler below reported as an unknown error,
                # once per bold
                if os.path.exists(f["bold_vol"]):
                    log.step("Data ready!")
                else:
                    log.error("Data missing, please check source!")

            except (pc.ExternalFailed, pc.NoSourceFolder) as errormessage:
                log.raw(str(errormessage))
            except Exception:
                log.error(f"Unknown error occured: \n...................................\n{traceback.format_exc()}...................................\n")
                time.sleep(3)

    log.blank()
    log.info(f"Imaging data copy completed on {datetime.now().strftime('%A, %d. %B %Y %H:%M:%S')}")
    log.rule()

    # the per-bold errors above are what the failure count is derived from
    return log.finish("Imaging data copy completed", name=sinfo["id"])

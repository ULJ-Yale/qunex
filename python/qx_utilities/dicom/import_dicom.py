#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``import_dicom.py``

The ``import_dicom`` command: discovers incoming DICOM packets, sorts them
into per session folders, converts them to NIfTI and archives the processed
packets.
"""

# Copyright (c) Grega Repovs. All rights reserved.

import os

import qx_utilities.dicom.sort_report as gdr
import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl
from qx_utilities.dicom.dicom2niix import dicom2niix
from qx_utilities.dicom.import_utils import (
    _archive_packet,
    _import_discover,
    _import_final_report,
    _import_normalize_args,
    _import_parse_logfile,
    _import_report_packets,
    _import_select_to_process,
    _resolve_packet_sources,
)
from qx_utilities.dicom.sort_dicom import _scan_and_sort_session
from qx_utilities.general.parsing import true_or_false


def import_dicom(
    sessionsfolder=None,
    sessions=None,
    masterinbox=None,
    check="any",
    pattern=None,
    nameformat=None,
    tool="auto",
    parelements=1,
    logfile=None,
    archive="leave",
    add_image_type=0,
    add_json_info="all",
    unzip="yes",
    gzip="folder",
    verbose="yes",
    overwrite="no",
    min_files=4,
    tr_abs_ms=100.0,
    tr_rel_pct=5.0,
    existing_structure=False,
    test=False,
    _log=None,
):
    r"""
    ``import_dicom [sessionsfolder=.] [sessions=""] [masterinbox=<sessionsfolder>/inbox/MR] [check=any] [pattern="(?P<packet_name>.*?)(?:\.zip$|\.tar$|.tgz$|\.tar\..*$|$)"] [nameformat='(?P<subject_id>.*)'] [tool=auto] [parelements=1] [logfile=""] [archive=leave] [add_image_type=0] [add_json_info=all] [unzip="yes"] [gzip="folder"] [verbose=yes] [overwrite="no"] [min_files=4] [tr_abs_ms=100] [tr_rel_pct=5]``

    Process sessions's DICOM or PAR/REC files and generate NIfTI files.

    ..  qx_command:
        type: utility

    Parameters:
        --sessionsfolder (str, default '.'):
            The base study sessions folder (e.g. WM44/sessions) where the inbox
            and individual session folders are. If not specified, the current
            working folder will be taken as the location of the sessionsfolder.

        --sessions (str, default ''):
            A comma delimited string that lists the sessions to process. If
            master inbox folder is used, the parameter is optional and it can
            include regex patterns. In this case only those sessions identified
            by the pattern that also match with any of the patterns in the
            sessions list will be processed. If `masterinbox` is set to none,
            the list specifies the session folders to process, and it can
            include glob patterns.

        --masterinbox (str, default '<sessionsfolder>/inbox/MR'):
            The master inbox folder with packages to process. By default
            masterinbox is in sessions folder: <sessionsfolder>/inbox/MR. If
            the packages are elsewhere, the location can be specified here. If
            set to "none", the data is assumed to already exist in the
            individual sessions' inbox folder:
            <studyfolder>/<sessionsfolder>/<session id>/inbox.

        --check (str, default 'any'):
            The type of check to perform when packages or session folders are
            identified.

            The possible values are:
            - 'no'  ... report and continue w/o additional checks
            - 'any' ... continue if any packages are ready to process report error otherwise.

        --pattern (str, default '(?P<packet_name>.*?)(?:\\.zip$|\\.tar$|\\.tgz$|\\.tar\\..*$|$)'):
            The regex pattern to use to find the packages and to extract the
            packet name.

        --nameformat (str, default '(?P<subject_id>.*)'):
            The regex pattern to use to extract subject id and (optionally) the
            session name from the session or packet name.

        --tool (str, default 'auto'):
            What tool to use for the conversion.

            It can be one of:
            - 'auto' (determine best tool based on heuristics)
            - 'dcm2niix'
            - 'dcm2nii'
            - 'dicm2nii'.

        --parelements (int, default 1):
            The number of parallel processes to use when running converting
            DICOM images to NIfTI files. If specified as 'all', all avaliable
            resources will be utilized.

        --logfile (str, default ''):
            A string specifying the location of the log file and the columns in
            which packetname, subject id and session name information are
            stored. The string should specify: ``"path:<path to the log file>|
            packet_name:<name of the packet extracted by the
            pattern>|subject_id:<the column with subjectid
            information>[|session_name:<the column with sesion id
            information>]"``.

        --archive (str, default 'leave'):
            What to do with a processed package.

            Options are:

            - 'move'   ... move the package to the default archive folder
            - 'copy'   ... copy the package to the default archive folder
            - 'leave'  ... keep the package in the session or master inbox
              folder
            - 'delete' ... delete the package after it has been processed.

            In case of processing data from a sessions folder, the
            `archive` parameter is only valid for compressed
            packages.

        --add_image_type (int, default 0):
            Adds image type information to the sequence name (Siemens scanners).
            The value should specify how many of image type labels from the end
            of the image type list to add.

        --add_json_info (str, default 'all'):
            What sequence information to extract from JSON sidecar files and add
            to session.txt file. Specify a comma separated list of fields or
            'all'. See list in session.txt file description below.

        --unzip (str, default 'yes'):
            Whether to unzip individual DICOM files that are gzipped. Valid
            options are 'yes', 'no'.

        --gzip (str, default 'folder'):
            Whether to gzip individual DICOM files after they were processed
            ('file'), gzip a DICOM sequence or acquisition as an tar.gz archive
            ('folder'), or leave them ungzipped ('no'). Valid options are
            'folder', 'file', 'no'.

        --verbose (str, default 'yes'):
            Whether to provide detailed report also of packets that could not be
            identified and/or are not matched with log file.

        --overwrite (str, default 'no'):
            Whether to overwrite existing data (yes) or not (no). Note that
            previous data is deleted before the run, so in the case of a failed
            command run, previous results are lost.

        --min_files (int, default 4):
            The minimum number of imaging files a sequence has to hold for the
            incomplete volume (orphan) detection to run. Shorter sequences
            (localizers, single volume references) are reported but never
            pruned. Set it higher to be more conservative.

        --tr_abs_ms (float, default 100):
            The absolute tolerance in milliseconds when comparing the observed
            volume repetition time with the TR reported in the DICOM header. A
            sequence is only flagged for a TR mismatch when it deviates by more
            than both `tr_abs_ms` and `tr_rel_pct`.

        --tr_rel_pct (float, default 5):
            The relative tolerance in percent for the same TR comparison. See
            `tr_abs_ms`.

        --existing_structure (bool, default False):
            Deprecated and ignored, a warning is printed when it is set. The
            single pass importer reads every file in the package and sorts it
            by its series number, whether or not the package is already
            organized into per sequence subfolders, so there is nothing left
            for this flag to switch on.

    Notes:
        The command is used to automatically process packets with individual
        session's DICOM or PAR/REC files all the way to, and including,
        generation of NIfTI files. Packet can be either a zip file, a tar
        archive or a folder that contains DICOM or PAR/REC files.

        The command can import packets either from a dedicated masterinbox
        folder and create the necessary session folders within
        `--sessionsfolder`, or it can process the data already present in
        the session specific folders.

        Unlike earlier versions, the importer processes each packet in a single
        pass: every file is read only once and written directly into the
        session's `dicom` folder, without an intermediate copy into an `inbox`
        folder. During this pass it also inspects the DICOM files and sets aside:

        - files that contain no image data (only metadata), which are moved to
          `dicom/non-image`, and
        - files with orphaned slices that do not complete a full volume (e.g.
          from a prematurely stopped acquisition), which are moved to
          `dicom/orphans`.

        This inspection is scanner-aware and safe: for acquisitions where
        incomplete volumes cannot occur or slice completeness cannot be robustly
        determined (e.g. Siemens mosaic images, enhanced multi-frame files, or
        sequences with missing geometry information) the files are reported but
        never removed. A per-session DICOM integrity report is written to
        `dicom/<session id>_import_report.md`. The thresholds the inspection
        uses can be adjusted with the `min_files`, `tr_abs_ms` and `tr_rel_pct`
        parameters; the defaults are sensible for standard MR protocols and
        rarely need to be changed.

        The next sections will describe the two use cases in more detail.

        Processing data from a dedicated inbox folder:
            This is the default operation. In this mode of operation:

            - The candidate packages are identified by a `pattern` parameter,
              which also specifies, how to extract a packet name.
            - The packets found are optionally filtered using the `sessions`
              parameter.
            - Subject id and (optionally) session name are either extracted
              from the packet name using the `nameformat` parameter or looked
              up in a log file.
            - A report of packets identified is generated.
            - Session folders are created as needed.
            - In a single read pass the DICOM data is sorted directly into
              per-sequence `dicom` subfolders, with non-image files and orphaned
              slices set aside as described above, and a DICOM integrity report
              is written.
            - Images are converted to nifti format
            - `session.txt` files are generated
            - Original packets are archived as specified by the `archive`
              parameter.

            In this mode of operation the `masterinbox` parameter passed to
            `import_dicom` has to provide a path to the folder with the
            incoming packets. The default location is
            `<study>/<sessionsfolder>/inbox/MR`, which is used automatically if
            `masterinbox` is not specified. Data from each session has to be
            present in the `masterinbox` directory either as a separate folder
            with the raw DICOM files or as a compressed package with that
            session's data. `import_dicom` supports the following packages:
            `.zip`, `.tar`, `.tar.gz`, `.tar.bz2`, `.tarz` and `.tar.bzip2`.

            The `pattern` parameter is used to specify, which files and/or
            folders are to be identified as potential packets to be processed.
            Specifically, the `pattern` parameter is a string that specifies a
            `regular expression <http://www.rexegg.com/regex-quickstart.html>`_
            against which the files and folders in the `masterinbox` are
            matched. In addition, the regular expression has to return a named
            group, 'packet_name' that is used in further processing.

            The default `pattern` parameter is
            `"(?P<packet_name>.*?)(?:\\.zip$|\\.tar$|\\.tar\\..*$|$)"`. This
            pattern will identify the initial part of the packet file- or
            foldername, (without any extension that identifies a compressed
            package) as the packet name.

            Specifically:

            - OP386
            - OP386.zip
            - OP386.tar.gz

            will all be identified as packet names 'OP386'.

            Next the packet name has to be processed to identify the subject id
            and (optionally) the session name. This can be done in one of two
            ways. If the necessary information is present in the packet name
            itself, it can be extracted as specified in by the `nameformat`
            parameter. If not, it can be specified using a `logfile` parameter.

            Extracting subject id from packet name:
                To extract subject id from a packet name, the `nameformat`
                parameter has to specify a `regular
                expression <http://www.rexegg.com/regex-quickstart.html>`_ that
                will extract the subject id and (optionally) the session name
                from the packet name as named groups, `subject_id` and
                `session_name`, respectively. The default `nameformat`
                parameter is `"(?P<subject_id>.*)"`. It assumes that the packet
                name is equal to the subject id and only a single session was
                recorded. Here are a few additional examples of how subject id
                and session names can be extracted using the `nameformat`
                parameter:

                +-----------------------+--------------------------------------------------+------------+--------------+---------------+
                | packet name           | `nameformat` parameter                           | subject id | session name | session id    |
                +=======================+==================================================+============+==============+===============+
                | AP346_MR_1            | `"(?P<subject_id>.*?)_(?P<session_name>.*)"`     | AP346      | MR_1         | AP346_MR_1    |
                +-----------------------+--------------------------------------------------+------------+--------------+---------------+
                | Siemens_Baseline-S002 | `".*?_(?P<session_name>.*?)-(?P<subject_id>.*)"` | S002       | Baseline     | S002_Baseline |
                +-----------------------+--------------------------------------------------+------------+--------------+---------------+
                | Yale-EQ469-Placebo    | `".*?-(?P<subject_id>.*?)-(?P<session_name>.*)"` | EQ469      | Placebo      | EQ469_Placebo |
                +-----------------------+--------------------------------------------------+------------+--------------+---------------+
                | Oxford.MR492.T3-Trio  | `".*?\\.(?P<subject_id>.*?)\\..*"`               | MR492      | -            | MR492         |
                +-----------------------+--------------------------------------------------+------------+--------------+---------------+


                Shown are the extracted packet name, the `nameformat` regular
                expression, the resulting extracted subject id and session name
                (when present), and the final generated session id.

            Looking up subject id in a log file:
                If subject id and (optionally) session name is not present or
                cannot be robustly extracted from the package name, it is
                possible to make use of a file that provides the mapping
                between package names, subject ids and session names. A log
                file has to be either a comma separated value (`.csv`) file or
                a tab separated text file in which each row provides
                information about a single scanning session. An example log
                file (e.g. `scanning_sessions.csv`) can be::

                    scanning code,subject,session,date of scan, ...
                    AP1789,S001,baseline,2019-03-21, ...
                    AP1790,S001,incentive,2019-03-21, ...
                    WID1832,S002,baselime,2019-04-12, ...
                    WID1913,S002,incentive,2019-04-12, ...

                To use a log file, a `logfile` parameter has to be provided.
                The content of the `logfile` has to be a string of the
                following format::

                    path:<path to the log file>|packet_name:<the column number with the packet name>|subject_id:<a column number with the subject id>|session_name:<a column number with the session name>

                In case of the above information, the `logfile` parameter would be::

                    --logfile="path:/studies/myStudy/info/scanning_sessions.csv|packet_name:1|subject_id:2|session_name:3"

                And the resulting mapping would be:

                +-------------+------------+--------------+----------------+
                | packet name | subject id | session name | session id     |
                +=============+============+==============+================+
                | AP1789      | S001       | baseline     | S001_baseline  |
                +-------------+------------+--------------+----------------+
                | AP1790      | S001       | incentive    | S001_incentive |
                +-------------+------------+--------------+----------------+
                | WID1832     | S002       | baseline     | S002_baseline  |
                +-------------+------------+--------------+----------------+
                | WID1913     | S002       | incentive    | S002_incentive |
                +-------------+------------+--------------+----------------+

                Shown are the extracted packet name, the extracted subject id
                and session name, and the final generated session id.

                Do note that at least `packet_name` and `subject_id` have to be
                provided in the `logfile` parameter and in the log file itself.
                If `session_name` is not provided, it is assumed that only a
                single session was recorded for each subject and session id
                equals subject id.

            Further processing:
                As can be seen from the examples, after the subject id and
                (optionally) the session name are extracted, the session id is
                generated using the formula `<subject_id>[_<session_name>]`,
                where `_<session_name>` is appended only if extracted from
                either the packet name or the log file. The generated session
                id would then be used to name the sessions' folders in the
                `/studies/myStudy/sessions`.

                The progress of processing now depends on the `check` parameter.
                If the `check` parameter is set to `any` it will proceed if any
                packets to process were found, and it will report an error
                otherwise. If `check` is set to `no`, no additional check will
                be performed. If any packets were found to be processed, they
                will be processed. If none were found, the command will exit
                without reporting an error.

                If packets were found to process and a go ahead was given,
                import_dicom reads each packet in a single pass, sorting the
                files directly into the session's `dicom` folder. Depending on
                the `archive` parameter, the packet is then either moved
                ('move') or copied ('copy') to the
                `<study>/sessions/archive/MR` folder, left as is ('leave'), or
                deleted ('delete'). If the archive folder does not yet exist,
                it is created.

                If a session folder already contains `dicom` or `nii` results,
                then the related packet will not be processed so that the
                existing data is not changed. In this case the user has to
                either remove or rename the existing folder(s), or set
                `overwrite` to 'yes', to process those packet(s) as well.

            Filtering sessions:
                If not all packets in the `masterinbox` folder are to be
                processed, it is possible to explicitly define which packets
                can be processed by specifying the `sessions` parameter. The
                parameter is a comma separated string of packet names that can
                be processed. Each entry in the list can be a regular extension
                pattern, in which case all the packet names that match any of
                the patterns will be processed. Following the last example
                above, specifying::

                    --sessions=".*_baseline"

                Would only process the baseline sessions and prepare data in
                these session-specific folders:

                - /studies/myStudy/sessions/S001_baseline
                - /studies/myStudy/sessions/S002_baseline

        Processing data from a session folder:
            If the raw DICOM files or compressed packages with the raw DICOM
            files are already present in the respective
            `<study>/sessions/<session id>/inbox` folders, then the
            `masterinbox` parameter has to be explicitly set to 'none', and the
            session folders to be processed have to be listed in the `sessions`
            parameter. In this case the `session` parameter is a comma
            separated string, where each entry in the list can be a glob
            pattern matching with multiple session folders.

            Please note that the `sessions` parameter is only used to identify
            possible folders. If a session folder is not present, even though
            explicitly listed, `import_dicom` won't report an error.

            In this mode of operation the session id is taken to be the folder
            name. However, if subject id is not equal to the session id, the
            `nameformat` parameter has to be specified to correctly extract the
            subject id from the session name. Specifically, `nameformat`
            parameter has to specify a `regular
            expression <http://www.rexegg.com/regex-quickstart.html>`_ string
            that returns a 'subject_id' named group. By default, the
            `nameformat` parameter is `"(?P<subject_id>.*)"`, which identifies
            the whole session name as the subject id. Here are a few examples
            of how to change the `nameformat` parameter to extract the subject
            id correctly:

            +------------------+----------------------------+-------------+
            | session id       | `nameformat` string        | subject id  |
            +==================+============================+=============+
            | P1102_000_01     | `"(?P<subject_id>.*?)_.*"` | P1102       |
            +------------------+----------------------------+-------------+
            | S5238_Placebo    | `"(?P<subject_id>.*?)_.*"` | S5238       |
            +------------------+----------------------------+-------------+
            | NDAR_INV2CTC8934 | `".*?_(?P<subject_id>.*)"` | INV2CTC8934 |
            +------------------+----------------------------+-------------+

            After the sessions are identified and subject id extracted,
            depending on the `check` parameter, the processing continues but an
            error is reported if no sessions are identified (`check="any"`), or
            the processing continues and no error is reported even if no
            sessions to be processed are found (`check="no"`).

            The folders found are expected to have the data stored in the inbox
            folder either as individual raw DICOM files—that can be nested in
            additional subfolders—or as a compressed package(s). The files are
            read directly from the inbox folder in a single pass; if compressed
            package(s) are present they are read in place and submitted to the
            setting in the `archive` parameter.

            If any results—e.g. files in `dicom` or `nii` folders—already
            exists, the processing of the folder will be skipped.

            For similar use cases refer to the Examples section.

        Processing steps:
            `import_dicom` reads each packet in a single pass, sorting the DICOM
            files directly into per-sequence `dicom` subfolders and setting
            aside non-image and orphaned-slice files as described above. It then
            calls the `dicom2niix` command, which converts the DICOM files to
            NIfTI format, stores them in the `nii` folder, and creates a
            `session.txt` file (and a `DICOM-Report.txt`) with details of the
            session. A per-session DICOM integrity report is also written to the
            `dicom` folder.

    Examples:
        Data from a dedicated inbox folder:
            First the examples for processing packages from `masterinbox` folder.

            In the first example, we are assuming that the packages we want to
            process are in the default folder
            (`<path_to_studyfolder>/sessions/inbox/MR`), the file or folder names
            contain only the packet names to be used, and the subject id is equal
            to the packet name. All packets found are to be processed:

            ::

                qunex import_dicom \\
                    --sessionsfolder="<path_to_studyfolder>/sessions" \\
                    --check="any"

            If only package names starting with 'AP' or 'HQ' are to be processed
            then the `sessions` parameter has to be added:

            ::

                qunex import_dicom \\
                    --sessionsfolder="<path_to_studyfolder>/sessions" \\
                    --sessions="AP.*,HQ.*" \\
                    --check="any"

            If the packages are named e.g. 'Yale-AP4983.zip' with the extension
            optional, then to extract the packet name and map it directly to
            subject id, the following `pattern` parameter needs to be added:

            ::

                qunex import_dicom \\
                    --sessionsfolder="<path_to_studyfolder>/sessions" \\
                    --pattern=".*?-(?P<packet_name>.*?)($|\\..*$)" \\
                    --sessions="AP.*,HQ.*" \\
                    --check="any"

            If the session name can also be extracted and the files are in the
            format e.g. 'Yale-AP4876_Baseline.zip', then a `nameformat` parameter
            needs to be added:

            ::

                qunex import_dicom \\
                    --sessionsfolder="<path_to_studyfolder>/sessions" \\
                    --pattern=".*?-(?P<packet_name>.*?)($|\\..*$)" \\
                    --sessions="AP.*,HQ.*" \\
                    --nameformat="(?P<subject_id>.*?)_(?P<session_name>.*)" \\
                    --check="any"

            In this case, 'AP4876_Baseline' will be first extracted as a packet name
            and then parsed into 'AP4876' subject id and 'Baseline' session name.

            If the files are named e.g. 'Yale-AP4983.zip' and a log file exists in
            which the AP* or HQ* are mapped to a corresponding subject id and
            session names, then the command is changed to:

            ::

                qunex import_dicom \\
                    --sessionsfolder="<path_to_studyfolder>/sessions" \\
                    --pattern=".*?-(?P<packet_name>.*?)($|\\..*$)" \\
                    --sessions="AP.*,HQ.*" \\
                    --logfile="path:/studies/myStudy/info/scanning_sessions.csv|packet_name:1|subject_id:2|session_name:3" \\
                    --check="any"

        Data already present:
            For the examples of processing data already present in the individual
            session id folder, let's assume that we have the following files
            present, with no other files in the sessions folders:

            - /studies/myStudy/sessions/S001_baseline/inbox/AYXQ.tar.gz
            - /studies/myStudy/sessions/S001_incentive/inbox/TWGS.tar.gz
            - /studies/myStudy/sessions/S002_baseline/inbox/OHTZ.zip
            - /studies/myStudy/sessions/S002_incentive/inbox/QRTD.zip

            Then these are a set of possible commands:

            ::

                qunex import_dicom \\
                    --sessionsfolder="/studies/myStudy/sessions" \\
                    --masterinbox="none" \\
                    --sessions="S*"

            In the above case all the folders will be processed, the packages will
            be read in place and (by default) left as is. To instead delete the
            packages after successful processing::

                qunex import_dicom \\
                    --sessionsfolder="/studies/myStudy/sessions" \\
                    --masterinbox="none" \\
                    --sessions="*baseline" \\
                    --archive="delete"

            In the above case only the `S001_baseline` and `S002_baseline` sessions
            will be processed and the respective compressed packages will be
            deleted after the successful processing.
    """

    log = gl.log_or_console(_log)

    # `raw` with an explicit trailing newline, not `info`, wherever the next
    # line comes from a helper that still `print()`s: a record renders as
    # "\n<line>" and a print emits "<line>\n", so a record followed by a print
    # runs the two together. Reads as `info` again once the helpers convert.
    log.raw("\nRunning import_dicom\n====================\n")

    if true_or_false(existing_structure):
        log.warning(
            "the existing_structure parameter is deprecated and ignored. The "
            "importer reads and sorts every file in the package by its series "
            "number, so preorganized packages need no special handling."
        )

    try:
        min_images = int(min_files)
        tr_abs_ms = float(tr_abs_ms)
        tr_rel_pct = float(tr_rel_pct)
    except (TypeError, ValueError):
        raise ge.CommandError("import_dicom", "Misspecified inspection thresholds", "min_files has to be an integer, tr_abs_ms and tr_rel_pct numbers! [%s, %s, %s]" % (min_files, tr_abs_ms, tr_rel_pct), "Please check command instructions!")

    (sessionsfolder, masterinbox, pattern, nameformat, add_image_type, sessions_list, verbose_b, overwrite_b) = _import_normalize_args(
        sessionsfolder, sessions, masterinbox, pattern, nameformat, tool, add_image_type, verbose, overwrite
    )
    sessions_info = _import_parse_logfile(logfile)

    packets, report_set = _import_discover(sessionsfolder, sessions_list, masterinbox, pattern, nameformat, sessions_info)
    _import_report_packets(packets, report_set, overwrite_b)

    to_process = _import_select_to_process(packets, masterinbox, sessionsfolder, check, overwrite_b, test)
    if to_process is None:
        return

    afolder = os.path.join(sessionsfolder, "archive", "MR")
    if not os.path.exists(afolder):
        os.makedirs(afolder)
        log.step("Created Archive folder for processed packages.")

    report = {"failed": [], "ok": []}
    log.step("Starting to process %d packets ..." % (len(to_process)))

    for afile, session in to_process:
        note = []
        try:
            sfolder = os.path.join(sessionsfolder, session["sessionid"])
            dicom_dir = os.path.join(sfolder, "dicom")
            log.raw("\n\n---=== PROCESSING %s ===---\n" % (session["sessionid"]))

            sources = _resolve_packet_sources(afile, session, masterinbox, sfolder)

            # single read-once/write-once pass: scan, sort, set aside non-image/orphan files, report
            pkg = _scan_and_sort_session(
                sources,
                dicom_dir,
                session["sessionid"],
                tr_abs_ms=tr_abs_ms,
                tr_rel_pct=tr_rel_pct,
                min_images=min_images,
                verbose=verbose_b,
            )
            gdr.write_report(pkg, os.path.join(dicom_dir, "%s_import_report.md" % (session["sessionid"])))
            log.blank()
            log.info(gdr.render_console_summary(pkg))
            log.step("Package verdict: %s" % (pkg.verdict))

            # convert to NIfTI (still writes session.txt and DICOM-Report.txt).
            # dicom2niix does not take a log, so its output is live on the
            # console and in the comlog but is not part of this report
            log.blank()
            dicom2niix(
                folder=sfolder,
                clean="no",
                unzip=unzip,
                gzip=gzip,
                sessionid=session["sessionid"],
                tool=tool,
                parelements=parelements,
                add_image_type=add_image_type,
                add_json_info=add_json_info,
                verbose=True,
            )

            if archive != "leave":
                s = "Processing packages: " + archive
                # `_archive_packet` prints -- see the note on the opening line
                log.raw("\n%s\n%s\n" % (s, "=" * len(s)))
            note += _archive_packet(sources, afolder, archive, masterinbox, verbose_b)

            report["ok"].append((afile, dict(session), note))

        except ge.CommandFailed as e:
            report["failed"].append((afile, dict(session), ["%s: %s" % (e.function, e.error)]))

    _import_final_report(report)

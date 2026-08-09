#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``legacy/import_dicom_old.py``

The superseded ``import_dicom_old`` command.

Kept as a one release fallback for the rewritten ``import_dicom``.
"""

# Copyright (c) Grega Repovs. All rights reserved.

import csv
import glob
import io
import os
import re
import shutil
import sys
import tarfile
import tempfile
import zipfile
import gzip as gz

import qx_utilities.general.exceptions as ge
from qx_utilities.dicom.dicom2niix import dicom2niix
from qx_utilities.dicom.dicom_utils import _safe_rmtree, match_all
from qx_utilities.dicom.legacy.sort_clean_legacy import (
    _clean_dicom_legacy,
    _sort_dicom_legacy,
)
from qx_utilities.general.parsing import true_or_false


def import_dicom_old(
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
    existing_structure=False,
    clean_dicom_folders=False,
    test=False,
):
    r"""
    ``import_dicom_old [sessionsfolder=.] [sessions=""] [masterinbox=<sessionsfolder>/inbox/MR] [check=any] [pattern="(?P<packet_name>.*?)(?:\.zip$|\.tar$|.tgz$|\.tar\..*$|$)"] [nameformat='(?P<subject_id>.*)'] [tool=auto] [parelements=1] [logfile=""] [archive=leave] [add_image_type=0] [add_json_info=""] [unzip="yes"] [gzip="folder"] [verbose=yes] [overwrite="no"] [existing_structure=False] [clean_dicom_folders=False]``

    Deprecated. Process sessions's DICOM or PAR/REC files and generate NIfTI
    files using the pre-1.5.0 two-pass implementation.

    ..  qx_command:
        type: utility

    Warning:
        This command is deprecated and is superseded by `import_dicom`, which
        reads and writes each file only once, inspects the DICOM files while it
        sorts them, sets aside non-image and orphaned files, and writes a
        per-session integrity report. `import_dicom_old` is the frozen
        pre-1.5.0 implementation, kept only as a fallback in case the new
        importer misbehaves on a specific dataset. It receives no further
        development and will be removed in a future release. If you have to use
        it, please report the reason on the QuNex forum
        (https://forum.qunex.yale.edu) so that the new importer can be fixed.

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

        --pattern (str, default '(?P<session_id>.*?)(?:\\.zip$|\\.tar$|\\.tgz$|\\.tar\\..*$|$)'):
            The regex pattern to use to find the packages and to extract the
            session id.

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
            packetname:<name of the packet extracted by the
            pattern>|subjectid:<the column with subjectid
            information>[|sessionid:<the column with sesion id
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

        --existing_structure (bool, default False):
            If the images are preorganized in folders, set this to True so QuNex
            will not try to reorganize them.

        --clean_dicom (bool, default False):
            If set to True, after sorting dicom files into sequence folders, the
            dicom files will be inspected and any dicom files that do not
            contain image data, or that do not constitute a full volume (e.g.,
            in the case of interrupted scans) will be set aside before
            conversion to NIfTI.

    Notes:
        The command is used to automatically process packets with individual
        session's DICOM or PAR/REC files all the way to, and including,
        generation of NIfTI files. Packet can be either a zip file, a tar
        archive or a folder that contains DICOM or PAR/REC files.

        The command can import packets either from a dedicated masterinbox
        folder and create the necessary session folders within
        `--sessionsfolder`, or it can process the data already present in
        the session specific folders.

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
            - Session folders are created and packet data is moved or copied to
              the session's `inbox` folder.
            - Dicom data is sorted into folders holding information from a
              single scan
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
                import_dicom will then copy, unzip or untar all the files in
                each packet into an inbox folder created within the session
                folder. Once all the files are extracted or copied, depending
                on the `archive` parameter, the packet is then either moved
                ('move') or copied ('copy') to the
                `<study>/sessions/archive/MR` folder, left as is ('leave'), or
                deleted ('delete'). If the archive folder does not yet exist,
                it is created. The default `archive` setting is 'move'.

                If a session folder and an inbox folder within it already
                exists, then the related packet will not be processed so that
                the existing data is not changed. In this case the user has to
                either remove or rename the existing folder(s) and rerun the
                command to process those packet(s) as well.

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
            depending on the `check` parameter, the user is prompted to confirm
            processing (`check="yes"`), the processing continues, but an error
            is reported if no sessions are identified (`check="any"`), or the
            processing continues and no error is reported even if no sessions
            to be processed are found (`check="no"`).

            The folders found are expected to have the data stored in the inbox
            folder either as individual raw DICOM files—that can be nested in
            additional subfolders—or as a compressed package(s). If the latter
            is the case, the files will be extracted to the inbox folder, and
            the package(s) will submit to the setting in the `archive`
            parameter.

            If any results—e.g. files in `dicom` or `nii` folders—already
            exists, the processing of the folder will be skipped.

            For similar use cases refer to the Examples section.

        Processing steps:
            `import_dicom` will first extract and organize the data as described above. As a next step, it will call `sort_dicom` command to organize the raw DICOM files into separate folders for each images. Next it will call `dicom2niix` command that will convert the DICOM files to NIfTI format, store them in `nii` folder and create a `session.txt` file with details of the session.

    Examples:
        Data from a dedicated inbox folder:
            First the examples for processing packages from `masterinbox` folder.

            In the first example, we are assuming that the packages we want to
            process are in the default folder
            (`<path_to_studyfolder>/sessions/inbox/MR`), the file or folder names
            contain only the packet names to be used, and the subject id is equal
            to the packet name. All packets found are to be processed, after the
            user gives a go-ahead to an interactive prompt:

            ::

                qunex import_dicom_old \\
                    --sessionsfolder="<path_to_studyfolder>/sessions"

            If the processing should continue automatically if packages to process
            were found, then the command should be:

            ::

                qunex import_dicom_old \\
                    --sessionsfolder="<path_to_studyfolder>/sessions" \\
                    --check="any"

            If only package names starting with 'AP' or 'HQ' are to be processed
            then the `sessions` parameter has to be added:

            ::

                qunex import_dicom_old \\
                    --sessionsfolder="<path_to_studyfolder>/sessions" \\
                    --sessions="AP.*,HQ.*" \\
                    --check="any"

            If the packages are named e.g. 'Yale-AP4983.zip' with the extension
            optional, then to extract the packet name and map it directly to
            subject id, the following `pattern` parameter needs to be added:

            ::

                qunex import_dicom_old \\
                    --sessionsfolder="<path_to_studyfolder>/sessions" \\
                    --pattern=".*?-(?P<packet_name>.*?)($|\\..*$)" \\
                    --sessions="AP.*,HQ.*" \\
                    --check="any"

            If the session name can also be extracted and the files are in the
            format e.g. 'Yale-AP4876_Baseline.zip', then a `nameformat` parameter
            needs to be added:

            ::

                qunex import_dicom_old \\
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

                qunex import_dicom_old \\
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

                qunex import_dicom_old \\
                    --sessionsfolder="/studies/myStudy/sessions" \\
                    --masterinbox="none" \\
                    --sessions="S*"

            In the above case all the folders will be processed, the packages will
            be extracted and (by default) moved to
            `/studies/myStudy/sessions/archive/MR`::

                qunex import_dicom_old \\
                    --sessionsfolder="/studies/myStudy/sessions" \\
                    --masterinbox="none" \\
                    --sessions="*baseline" \\
                    --archive="delete"

            In the above case only the `S001_baseline` and `S002_baseline` sessions
            will be processed and the respective compressed packages will be
            deleted after the successful processing.
    """

    clean_dicom_folders = true_or_false(clean_dicom_folders)
    existing_structure = true_or_false(existing_structure)

    isgz = re.compile(r"(^.*)\.gz$")
    iszip = re.compile(r"(^.*)\.zip$")
    istar = re.compile(
        r"(^.*)(\.tar$|\.tar.gz$|\.tar.bz2$|\.tarz$|\.tar.bzip2$|\.tgz$)"
    )

    def _process_file(fobj, fname, fnum, dnum, target):
        if not isinstance(fobj, io.IOBase):
            if os.path.isfile(fobj):
                fobj = open(fobj, "rb")
            else:
                return (fnum, dnum)

        if isgz.match(fname):
            fobj = gz.GzipFile(fileobj=fobj)
            fname = isgz.match(fname).group(1)
        elif istar.match(fname):
            return _extract_tar(fobj, fname, fnum, dnum, target)
        elif iszip.match(fname):
            return _extract_zip(fobj, fname, fnum, dnum, target)

        if fnum % 1000 == 0:
            dnum += 1
            if not os.path.exists(os.path.join(target, str(dnum))):
                os.makedirs(os.path.join(target, str(dnum)))
        fnum += 1

        tfile = f"{dnum}-{os.path.basename(fname)}"

        # --- check if par/rec/log
        if tfile.split(".")[-1].lower() in ["par", "rec", "log"]:
            for ext in ["rec", "par"]:
                if tfile.split(".")[-1] == ext:
                    tfile = tfile[:-3] + ext.upper()

        with open(os.path.join(target, str(dnum), tfile), "wb") as fout:
            shutil.copyfileobj(fobj, fout)

        fobj.close()
        return (fnum, dnum)

    def _extract_zip(packet, packetname, fnum=0, dnum=0, target=None):
        # -- open packet
        try:
            z = zipfile.ZipFile(packet, "r")
        except Exception:
            e = sys.exc_info()[0]
            raise ge.CommandFailed(
                "import_dicom",
                "Zip file could not be processed",
                "Opening zip [%s] returned an error [%s]!" % (packetname, e),
                "Please check your data!",
            )

        # -- get list of files in packet
        file_list = z.infolist()

        # -- process list
        for source_file in file_list:
            if source_file.file_size > 0:
                print("...  extracting:", source_file.filename, source_file.file_size)
                fnum, dnum = _process_file(
                    z.open(source_file), source_file.filename, fnum, dnum, target
                )

        # -- close and return with latest numbers
        print("     -> done!")
        z.close()
        return (fnum, dnum)

    def _extract_tar(packet, packetname, fnum=0, dnum=0, target=None):
        # -- open packet
        try:
            if isinstance(packet, io.IOBase):
                tar = tarfile.open(fileobj=packet, mode="r")
            else:
                tar = tarfile.open(packet, "r")
        except Exception:
            e = sys.exc_info()[0]
            raise ge.CommandFailed(
                "import_dicom",
                "Tar file could not be processed",
                "Opening tar [%s] returned an error [%s]!" % (packetname, e),
                "Please check your data!",
            )

        # -- process files
        for tarinfo in tar:
            if tarinfo.isfile():
                print("...  extracting:", tarinfo.name, tarinfo.size)
                fnum, dnum = _process_file(
                    tar.extractfile(tarinfo), tarinfo.name, fnum, dnum, target
                )

        # -- close and return with latest numbers
        print("     -> done!")
        tar.close()
        return (fnum, dnum)

    def _process_folder(folder, fnum=0, dnum=0, target=None):
        # -- get list of files
        files_iter = glob.iglob(os.path.join(folder, "**", "*"), recursive=True)
        for source_file in files_iter:
            fnum, dnum = _process_file(
                source_file, os.path.basename(source_file), fnum, dnum, target
            )

        return (fnum, dnum)

    print("Running import_dicom_old\n========================")
    print(
        "WARNING: import_dicom_old is deprecated and will be removed in a future\n"
        "         release. It is the frozen pre-1.5.0 importer, kept only as a\n"
        "         fallback. Please use import_dicom and report the reason you had\n"
        "         to fall back on https://forum.qunex.yale.edu.\n"
    )

    # check settings
    if tool not in ["auto", "dcm2niix", "dcm2nii", "dicm2nii"]:
        raise ge.CommandError(
            "import_dicom",
            "Incorrect tool specified",
            "The tool specified for conversion to nifti (%s) is not valid!" % (tool),
            "Please use one of dcm2niix, dcm2nii, dicm2nii or auto!",
        )

    verbose = verbose.lower() == "yes"

    overwrite = overwrite if isinstance(overwrite, bool) else overwrite.lower() == "yes"

    if sessionsfolder is None:
        sessionsfolder = "."

    if masterinbox is None:
        masterinbox = os.path.join(sessionsfolder, "inbox", "MR")

    if masterinbox.lower() == "none":
        masterinbox = None
        if sessions is None or sessions == "":
            raise ge.CommandError(
                "import_dicom",
                "Sessions parameter not specified",
                "If `masterinbox` is set to 'none' the `sessions` has to list sessions to process!",
                "Please check your command!",
            )

    if pattern is None:
        pattern = r"(?P<packet_name>.*?)(?:\.zip$|\.tar$|\.tgz$|\.tar\..*$|$)"

    if nameformat is None:
        nameformat = r"(?P<subject_id>.*)"

    try:
        if add_image_type is None or add_image_type == "":
            add_image_type = 0
        else:
            add_image_type = int(add_image_type)
    except Exception:
        raise ge.CommandError(
            "import_dicom",
            "Misspecified add_image_type",
            "The add_image_type argument value could not be converted to integer! [%s]"
            % (add_image_type),
            "Please check command instructions!",
        )

    if sessions:
        sessions = re.split(r", *", sessions)

    # ---- check acquisition log if present:
    sessions_info = None

    if logfile is not None and logfile != "":
        log = dict([[f.strip() for f in e.split(":")] for e in logfile.split("|")])

        if not all([e in log for e in ["path", "subject_id", "packet_name"]]):
            raise ge.CommandFailed(
                "import_dicom",
                "Missing information in logfile",
                "Please provide all information in the logfile specification! [%s]"
                % (logfile),
            )

        try:
            for key in [
                e
                for e in log.keys()
                if e in ["packet_name", "subject_id", "session_name"]
            ]:
                log[key] = int(log[key]) - 1
        except Exception:
            raise ge.CommandFailed(
                "import_dicom",
                "Invalid logfile specification",
                "Please create a valid logfile specification! [%s]" % (logfile),
            )

        sessionname = "session_name" in log

        if not os.path.exists(log["path"]):
            raise ge.CommandFailed(
                "import_dicom",
                "Logfile does not exist",
                "The specified logfile does not exist:",
                log["path"],
                "Please check your paths!",
            )

        print("---> Reading acquisition log [%s]." % (log["path"]))
        sessions_info = {}
        with open(log["path"]) as f:
            if log["path"].split(".")[-1] == "csv":
                reader = csv.reader(f, delimiter=",")
            else:
                reader = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
            for line in reader:
                try:
                    if sessionname:
                        sessions_info[line[log["packetname"]]] = {
                            "subjectid": line[log["subject_id"]],
                            "sessionname": line[log["session_name"]],
                            "sessionid": "%s_%s"
                            % (line[log["subject_id"]], line[log["session_name"]]),
                            "packetname": line[log["packet_name"]],
                        }
                    else:
                        sessions_info[line[log["packetname"]]] = {
                            "subjectid": line[log["subject_id"]],
                            "sessionname": None,
                            "sessionid": line[log["subject_id"]],
                            "packetname": line[log["packet_name"]],
                        }
                except Exception:
                    pass

    # ---- set up lists
    packets = {"ok": [], "nolog": [], "bad": [], "exist": [], "skip": [], "invalid": []}
    emptysession = {
        "subjectid": None,
        "sessionname": None,
        "sessionid": None,
        "packetname": None,
    }

    # ---- get list of files / folders in masterinbox
    if masterinbox:
        report_set = [
            ("ok", "---> Found the following packets to process:"),
            (
                "nolog",
                "---> These packets do not match with the log and they won't be processed",
            ),
            (
                "bad",
                "---> For these packets a packet name could not be identified and they won't be processed:",
            ),
            (
                "invalid",
                "---> For these packets the packet name could not parsed and they won't be processed:",
            ),
            (
                "exist",
                "---> The session and inbox folder for these packages already exist:",
            ),
            (
                "skip",
                "---> These packages do not match list of sessions and will be skipped:",
            ),
        ]

        if not os.path.exists(masterinbox):
            raise ge.CommandFailed(
                "import_dicom",
                "Master inbox does not exist",
                f"A folder {masterinbox} does not exist.",
                "Please check your path!",
            )

        if not os.path.isdir(masterinbox):
            raise ge.CommandFailed(
                "import_dicom",
                "Master inbox is not a folder",
                f"{masterinbox} is not a folder.",
                "Please check your path!",
            )

        print(
            "---> Checking for packets in %s \n     ... using regular expression '%s'\n     ... extracting subject id using regular expression '%s'"
            % (os.path.abspath(masterinbox), pattern, nameformat)
        )

        files = glob.glob(os.path.join(masterinbox, "*"))
        try:
            getop = re.compile(pattern)
        except Exception:
            raise ge.CommandFailed(
                "import_dicom",
                "Invalid pattern",
                "Coud not parse the provided regular expression pattern: '%s'"
                % (pattern),
                "Please check and correct it!",
            )
        try:
            getid = re.compile(nameformat)
        except Exception:
            raise ge.CommandFailed(
                "import_dicom",
                "Invalid nameformat",
                "Coud not parse the provided regular expression pattern: '%s'"
                % (nameformat),
                "Please check and correct it!",
            )

        for afile in files:
            m = getop.search(os.path.basename(afile))
            if m:
                if "packet_name" in m.groupdict() and m.group("packet_name"):
                    pname = m.group("packet_name")
                    session = dict(emptysession)
                    session["packetname"] = pname

                    if sessions_info:
                        if pname in sessions_info:
                            session = dict(sessions_info[pname])
                        else:
                            packets["nolog"].append((afile, dict(session)))
                            continue
                    else:
                        session = dict(emptysession)
                        session["packetname"] = pname

                        ms = getid.search(pname)

                        if (
                            ms
                            and "subject_id" in ms.groupdict()
                            and ms.group("subject_id")
                        ):
                            _ = ms.group("subject_id")
                            if "session_name" in ms.groupdict() and ms.group(
                                "session_name"
                            ):
                                session.update(
                                    {
                                        "subjectid": ms.group("subject_id"),
                                        "sessionname": ms.group("session_name"),
                                        "sessionid": "%s_%s"
                                        % (
                                            ms.group("subject_id"),
                                            ms.group("session_name"),
                                        ),
                                    }
                                )
                            else:
                                session.update(
                                    {
                                        "subjectid": ms.group("subject_id"),
                                        "sessionname": None,
                                        "sessionid": ms.group("subject_id"),
                                    }
                                )

                        else:
                            packets["invalid"].append((afile, session))
                            continue

                    sfolder = os.path.join(sessionsfolder, session["sessionid"])

                    if sessions:
                        if not any(
                            [match_all(e, session["sessionid"]) for e in sessions]
                        ):
                            packets["skip"].append((afile, session))
                            continue

                    if os.path.exists(os.path.join(sfolder, "inbox")):
                        packets["exist"].append((afile, session))
                        continue

                    packets["ok"].append((afile, session))

                else:
                    packets["bad"].append(afile, dict(emptysession))

    # ---- get list of session folders to process
    else:
        if not sessions:
            raise ge.CommandFailed(
                "import_dicom",
                "Input data not specified",
                "Neither masterinbox nor sessions to process were specified.",
                "Please check your command call!",
            )

        report_set = [
            ("ok", "---> Found the following folders to process:"),
            (
                "invalid",
                "---> For these folders the folder name could not parsed and they won't be processed:",
            ),
            ("exist", "---> These folders have existing results:"),
        ]

        print(
            "---> Checking for folders to process in '%s'"
            % (os.path.abspath(sessionsfolder))
        )

        getid = re.compile(nameformat)

        sfolders = []
        for sessionid in sessions:
            sfolders += glob.glob(os.path.join(sessionsfolder, sessionid))
        sfolders = list(set(sfolders))

        for sfolder in sfolders:
            session = dict(emptysession)
            pname = os.path.basename(sfolder)
            session["packetname"] = pname
            _ = pname.split("_")

            archives = []
            for tarchive in ["*.zip", "*.tar", "*.tar.*", "*.tgz"]:
                archives += glob.glob(os.path.join(sfolder, "inbox", tarchive))
            session["archives"] = list(archives)

            ms = getid.search(pname)
            if ms and "subject_id" in ms.groupdict() and ms.group("subject_id"):
                _ = ms.group("subject_id")
                if "session_name" in ms.groupdict() and ms.group("session_name"):
                    session.update(
                        {
                            "subjectid": ms.group("subject_id"),
                            "sessionname": ms.group("session_name"),
                            "sessionid": pname,
                        }
                    )
                else:
                    session.update(
                        {
                            "subjectid": ms.group("subject_id"),
                            "sessionname": None,
                            "sessionid": pname,
                        }
                    )

            else:
                packets["invalid"].append((sfolder, session))
                continue

            if glob.glob(os.path.join(sfolder, "dicom")) or glob.glob(
                os.path.join(sfolder, "nii")
            ):
                packets["exist"].append((sfolder, session))
                continue

            packets["ok"].append((sfolder, session))

    # ---> Report
    for tag, message in report_set:
        if packets[tag]:
            print(f"\n{message}")
            for afile, session in packets[tag]:
                if session["sessionname"]:
                    print(
                        "     subject: %s, session: %s ... %s <= %s <- %s"
                        % (
                            session["subjectid"],
                            session["sessionname"],
                            session["sessionid"],
                            session["packetname"],
                            os.path.basename(afile),
                        )
                    )
                elif session["subjectid"]:
                    print(
                        "     subject: %s ... %s <= %s <- %s"
                        % (
                            session["subjectid"],
                            session["sessionid"],
                            session["packetname"],
                            os.path.basename(afile),
                        )
                    )
                elif session["sessionid"]:
                    print(
                        "     %s <= %s <- %s"
                        % (
                            session["sessionid"],
                            session["packetname"],
                            os.path.basename(afile),
                        )
                    )
                elif session["packetname"]:
                    print(
                        "     %s <= %s <- %s"
                        % ("????", session["packetname"], os.path.basename(afile))
                    )
                else:
                    print(
                        "     %s <= %s <- %s"
                        % ("????", "????", os.path.basename(afile))
                    )

            if tag == "exist":
                if overwrite:
                    print(
                        " ... Since overwrite is set the folders will be removed and replaced"
                    )
                else:
                    print(
                        " ... To process them, remove or rename the existing subject folders or set `overwrite` to 'yes'"
                    )

    n_to_process = len(packets["ok"])
    if overwrite:
        n_to_process += len(packets["exist"])

    # just testing
    if n_to_process and test:
        print("\n---> To process them, remove the --test option!")
        return
    elif not n_to_process:
        if check.lower() == "any":
            if masterinbox:
                raise ge.CommandFailed(
                    "import_dicom",
                    "No packets found to process",
                    "No packets were found to be processed in the master inbox [%s]!"
                    % (os.path.abspath(masterinbox)),
                    "Please check your data!",
                )
            else:
                raise ge.CommandFailed(
                    "import_dicom",
                    "No sessions found to process",
                    "No sessions were found to be processed in session folder [%s]!"
                    % (os.path.abspath(sessionsfolder)),
                    "Please check your data!",
                )
        else:
            if masterinbox:
                raise ge.CommandNull(
                    "import_dicom",
                    "No packets found to process",
                    "No packets were found to be processed in the master inbox [%s]!"
                    % (os.path.abspath(masterinbox)),
                )
            else:
                raise ge.CommandNull(
                    "import_dicom",
                    "No sessions found to process",
                    "No sessions were found to be processed in session folder [%s]!"
                    % (os.path.abspath(sessionsfolder)),
                )

    # ---- Ok, now loop through the packets
    afolder = os.path.join(sessionsfolder, "archive", "MR")
    if not os.path.exists(afolder):
        os.makedirs(afolder)
        print("---> Created Archive folder for processed packages.")

    report = {"failed": [], "ok": []}

    # ---> clean existing data if needed
    if overwrite:
        if packets["exist"]:
            print("---> Cleaning existing data in folders:")
            for afile, session in packets["exist"]:
                sfolder = os.path.join(sessionsfolder, session["sessionid"])
                print(" ... %s" % (sfolder))
                if masterinbox:
                    ifolder = os.path.join(sfolder, "inbox")
                    if os.path.exists(ifolder):
                        _safe_rmtree(ifolder)
                nfolder = os.path.join(sfolder, "nii")
                dfolder = os.path.join(sfolder, "dicom")
                for rmfolder in [nfolder, dfolder]:
                    if os.path.exists(rmfolder):
                        _safe_rmtree(rmfolder)

        packets["ok"] += packets["exist"]

    # ---> process packets
    print("---> Starting to process %d packets ..." % (len(packets["ok"])))

    for afile, session in packets["ok"]:
        note = []
        try:
            sfolder = os.path.join(sessionsfolder, session["sessionid"])
            ifolder = os.path.join(sfolder, "inbox")
            dfolder = os.path.join(sfolder, "dicom")

            # --- Big info
            print("\n\n---=== PROCESSING %s ===---\n" % (session["sessionid"]))

            if masterinbox and not os.path.exists(ifolder):
                os.makedirs(ifolder)
                files = [afile]
            else:
                if "archives" in session and session["archives"]:
                    files = session["archives"]
                else:
                    files = [ifolder]

            if not existing_structure:
                dnum = 0
                fnum = 0

                for p in files:
                    # --- unzip or copy the package
                    if iszip.match(p):
                        ptype = "zip"
                        fnum, dnum = _extract_zip(
                            p, os.path.basename(p), fnum, dnum, ifolder
                        )

                    elif istar.match(p):
                        ptype = "tar"
                        fnum, dnum = _extract_tar(
                            p, os.path.basename(p), fnum, dnum, ifolder
                        )

                    else:
                        ptype = "folder"
                        if masterinbox and ifolder != p:
                            fnum, dnum = _process_folder(p, fnum, dnum, ifolder)

                            # if os.path.exists(ifolder):
                            #     shutil.rmtree(ifolder)
                            # print("...  copying %s dicom files" % (os.path.basename(p)))
                            # shutil.copytree(p, ifolder)
            else:
                source_folder = afile
                # --- unpack zip first
                if iszip.match(afile):
                    print(f"---> found a zip archive at {afile}")
                    temp_dir = tempfile.mkdtemp(prefix="import_dicom_")
                    with zipfile.ZipFile(afile, "r") as z:
                        z.extractall(temp_dir)
                    source_folder = temp_dir

                elif istar.match(afile):
                    temp_dir = tempfile.mkdtemp(prefix="import_dicom_")
                    print(f"---> found a tar archive at {afile}")
                    with tarfile.open(afile, "r:*") as t:
                        t.extractall(temp_dir)
                    source_folder = temp_dir

                # first‐level subfolders only
                fnum = 0
                for root, dirs, files in os.walk(source_folder):
                    for sub in dirs:
                        subpath = os.path.join(root, sub)
                        if not os.path.isdir(subpath):
                            continue
                        # find any .dcm files
                        dcms = glob.glob(os.path.join(subpath, "*.dcm"))
                        if not dcms:
                            continue
                        # one group found → bump fnum, make dest, copy & rename
                        fnum += 1
                        dest = os.path.join(ifolder, str(fnum))
                        os.makedirs(dest, exist_ok=True)
                        print(f"---> found {len(dcms)} dicom files in {subpath}")
                        print(f"     ... copying to {dest}")
                        for dcm in dcms:
                            name = os.path.basename(dcm)
                            shutil.copy2(dcm, os.path.join(dest, f"{fnum}-{name}"))

            # ---> run sort dicom
            print()
            _sort_dicom_legacy(folder=sfolder)

            # ---> run clean dicom
            if clean_dicom_folders:
                print()
                _clean_dicom_legacy(folder=sfolder, verbose=verbose)

            # ---> run dicom to nii
            print()
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

            # ---> archive
            if archive != "leave":
                s = "Processing packages: " + archive
                print()
                print(s)
                print("".join(["=" for e in range(len(s))]))

            for p in files:
                if masterinbox or re.search(
                    r"\.zip$|\.tar$|\.tar.gz$|\.tar.bz2$|\.tarz$|\.tar.bzip2$|\.tgz$", p
                ):
                    archivetarget = os.path.join(afolder, os.path.basename(p))

                    # --- move package to archive
                    if archive == "move":
                        if os.path.exists(archivetarget):
                            print(
                                "...  WARNING: %s already exists in archive and it will not be moved!"
                                % (os.path.basename(p))
                            )
                            note.append(
                                "WARNING: %s already exists in archive and it was not moved!"
                                % (os.path.basename(p))
                            )
                        else:
                            print("...  moving %s to archive" % (os.path.basename(p)))
                            shutil.move(p, archivetarget)
                            print("     -> done!")

                    # --- copy package to archive
                    elif archive == "copy":
                        if os.path.exists(archivetarget):
                            print(
                                "...  WARNING: %s already exists in archive and it will not be copied!"
                                % (os.path.basename(p))
                            )
                            note.append(
                                "WARNING: %s already exists in archive and it was not copied!"
                                % (os.path.basename(p))
                            )
                        else:
                            print("...  copying %s to archive" % (os.path.basename(p)))
                            if ptype == "folder":
                                shutil.copytree(p, archivetarget)
                            else:
                                shutil.copy2(p, afolder)
                            print("     -> done!")

                    # --- delete original package
                    elif archive == "delete":
                        print("...  deleting packet [%s]" % (os.path.basename(p)))
                        if ptype == "folder":
                            _safe_rmtree(p)
                        else:
                            os.remove(p)

            report["ok"].append((afile, dict(session), note))

        except ge.CommandFailed as e:
            report["failed"].append(
                (afile, dict(session), ["%s: %s" % (e.function, e.error)])
            )

    print("\nFinal report\n============")

    if report["ok"]:
        print("\nSuccessfully processed:")
        for afile, session, notes in report["ok"]:
            print("... %s [%s]" % (session["sessionid"], afile))
            for note in notes:
                print("    %s" % (note))

    if report["failed"]:
        print("\nFailed to process:")
        for afile, session, notes in report["failed"]:
            print("... %s [%s]" % (session["sessionid"], afile))
            for note in notes:
                print("    %s" % (note))
        raise ge.CommandFailed(
            "import_dicom", "Some packages failed to process", "Please check report!"
        )

    return

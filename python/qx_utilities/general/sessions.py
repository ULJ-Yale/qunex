# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
# SPDX-License-Identifier: GPL-3.0-or-later

"""
sessions.py

Functions for managing and joining QuNex sessions.
"""

import os
import re
import shutil
from typing import List, Tuple, Dict, Set
import qx_utilities.general.exceptions as ge
import qx_utilities.general.log as gl

# A sequence line starts with its number and a colon. QuNex's writers pad the
# number before the colon (dicom2niix "%-4s:", create_session_info "{:<4}:"), so
# a sequence under four digits arrives as "71  :".
_SEQ_LINE = re.compile(r"^(\d+)\s*:")


def merge_session(
    studyfolder: str,
    source: str,
    target: str,
    overwrite: str = "no",
    raw_data: str = "copy",
    original_sessions: str = "leave",
    _log=None,
) -> bool:
    r"""
    ``merge_session --studyfolder=<path> --source=<sessions> --target=<session> [--overwrite=<mode>] [--raw_data=<mode>] [--original_sessions=<action>]``

    Join multiple sessions into a single session.

    Description:
        Merges data from multiple source sessions into a target session. This
        is useful when the data for one subject was acquired, or imported, as
        several sessions, for instance when a scanning session was interrupted
        and continued, or when one visit was split over two exports, and the
        data needs to be processed and analysed as one session.

        For each source session, in the order given, the command:

        - copies the NIfTI files from `nii/` into the target `nii/` folder,
          renaming them to new, non-overlapping sequence numbers,
        - adds the sequence lines from `session.txt` and `session_hcp.txt` to
          the target files of the same name, renumbered to match the renamed
          NIfTI files, with bold/boldref indices and se()/fm() grouping tags
          renumbered so that they do not clash with other sessions,
        - copies or moves the raw data folders (`dicom/`, `bids/`, `inbox/`,
          `hcpls/`) into a subfolder of the matching target folder, unless
          `--raw_data=leave`,
        - collects the additional metadata (e.g. `institution`, `device`).

        The target `session.txt` and `session_hcp.txt` are then written with
        the target session and subject IDs and with paths pointing into the
        target session folder. Finally, the source sessions are left, removed
        or moved, as set by `--original_sessions`.

        Only raw data and session information files are merged. Derivatives
        (`images/`, `hcp/`) are not, and the processing steps that produce them
        need to be run on the merged session.

    ..  qx_command:
        type: utility

    Parameters:
        --studyfolder (str):
            Path to the study folder. Session IDs given in `--source` and
            `--target` are looked for in `<studyfolder>/sessions/`, relative
            paths are resolved against the study folder, and so is a relative
            `move:<path>` in `--original_sessions`.

        --source (str):
            A comma-separated list of the sessions to join, each given as a
            session ID, a relative path or an absolute path.

            Each is resolved as follows:

            - a session ID (e.g. 'session1'), resolved as
              `<studyfolder>/sessions/<id>`,
            - a relative path (e.g. 'other/session1'), resolved against the
              study folder,
            - an absolute path (e.g. '/data/study/sessions/session1').

            The sessions are merged in the order specified, and their sequence
            numbers and indices are assigned in that order. A source session
            that has neither `session.txt` nor `session_hcp.txt` is skipped, and
            none of its data is merged.

        --target (str):
            The target session, given as a session ID, a relative path or an
            absolute path, resolved as for `--source`. The folder is created if
            it does not exist. Its name is used as the session ID in the target
            session files, and the subject ID is derived from it (see Notes).

        --overwrite (str, default 'no'):
            What to do when the target folder already exists and is not empty:
            'no', 'clean' or 'merge'.

            - 'no': stop with an error,
            - 'clean': remove the existing target folder, including any
              derivatives, and create the merged session in its place,
            - 'merge': add the source sessions to the existing target session,
              which is then treated as one of the merged sessions (see
              "Merging into an existing session" in Notes). The command stops
              with an error if the target contains derivatives (`images/` or
              `hcp/`).

            The value also decides what happens when `--original_sessions`
            moves a session onto an existing one (see below).

        --raw_data (str, default 'copy'):
            What to do with the raw data folders (`dicom/`, `bids/`, `inbox/`
            and `hcpls/`) of each source session: 'copy', 'move' or 'leave'.

            - 'copy': copy them into the target session,
            - 'move': move them into the target session,
            - 'leave': leave them in the source sessions only.

            The NIfTI files in `nii/` are always copied, whatever the value,
            since the merged session cannot be used without them. Note that
            with 'leave' the raw data exists only in the source sessions, so
            combining it with `--original_sessions=remove` deletes it.

        --original_sessions (str, default 'leave'):
            What to do with the source sessions once the merge has succeeded:
            'leave', 'remove' or 'move:<path>'.

            - 'leave': leave them unchanged,
            - 'remove': delete them,
            - 'move:<path>': move them into the folder `<path>`, e.g.
              'move:/data/backup_sessions' or 'move:archive/merged_sessions'. A
              relative path is resolved against the study folder, and the folder
              is created if it does not exist. If a session of the same name
              already exists there, it is replaced when `--overwrite` is
              'clean' or 'merge'. When `--overwrite=no`, that session is not
              moved and a warning is reported.

            Nothing is removed or moved if the merge fails.

    Output files:
        The command creates, or adds to, the target session folder::

            <target session id>/
                nii/                     # NIfTI files, renamed to the new
                    <new seq num>.nii.gz # sequence numbers
                    <new seq num>.json
                dicom/                   # raw DICOM data, one subfolder per
                    <source subfolder>/  # source session, content unchanged
                bids/                    # if present in the sources
                    <source subfolder>/
                inbox/                   # if present in the sources
                    <source subfolder>/
                hcpls/                   # if present in the sources
                    <source subfolder>/
                session.txt              # combined session information
                session_hcp.txt          # combined HCP session information,
                                         # only if a source (or the target)
                                         # had one

        The raw data subfolders are created only when `--raw_data` is 'copy' or
        'move'. Their content is not renamed, so the sequence numbers inside
        them are the original ones. Each subfolder is named after its source
        session: if the source session ID has the form `<target id>_<suffix>`,
        the subfolder is `<suffix>`; otherwise it is the full source session
        ID. For example, merging `OP1242_1` and `OP1242_2` into `OP1242` gives
        `dicom/1/` and `dicom/2/`.

    Notes:
        Sequence renumbering:
            Each source session gets a block of sequence numbers of its own:

            1. Find the largest sequence number across all source sessions.
            2. Take the smallest power of 10 that is larger than it, and at
               least 1000, as the base increment.
            3. Add base × N to every sequence number of the N-th source session
               (N = 1, 2, 3, ...).

            Example: if the sources have sequences numbered 1010-2010 and
            1010-3010, the largest is 3010 and the base increment is 10000. The
            first source's sequences become 11010-12010 and the second
            source's become 21010-23010.

            The renumbering is applied to the NIfTI file names (`.nii.gz`,
            `.json` and any other file in `nii/` whose name starts with the
            sequence number) and to the sequence lines in `session.txt` and
            `session_hcp.txt`, so the two always agree. Sequence lines are
            recognised with or without padding before the colon, as written by
            `import_dicom` and `create_session_info` (e.g. `71  : T1w`).

        BOLD/BOLDREF indexing:
            In `session_hcp.txt` each bold and boldref sequence carries an index
            (bold1, bold2, boldref1, ...). The indices of each source session
            continue from the highest index used so far, so if the first source
            has bold1-bold2, the second source's bold1-bold2 become bold3-bold4.
            Gaps within a session's own numbering are preserved.

        Grouping tags:
            The se(N) and fm(N) tags group the spin-echo and gradient-echo field
            maps with the images they belong to. Groups stay together within each
            source session and are renumbered across sessions, so that no two
            sessions share a group. For example, if both sources have se(1) and
            se(2), the first source keeps se(1) and se(2), and the second source's
            become se(3) and se(4).

        Session information files:
            `session.txt` and `session_hcp.txt` are merged separately, each
            from the files of the same name in the source sessions.
            `session_hcp.txt` is created only when at least one source session
            (or, with `--overwrite=merge`, the target) has one. If the sources
            have only `session.txt`, run `create_session_info` on the merged
            session to create `session_hcp.txt`.

            Metadata lines other than the IDs and paths (e.g. `institution`,
            `device`) are collected from all source sessions. When sources
            disagree on a value, both values are kept and a warning is reported.

            When raw data is copied or moved, a `session_<N>: <subfolder>` line
            is added for each merged session, recording which raw data
            subfolder holds its data.

        Merging into an existing session:
            With `--overwrite=merge`, an existing target session is treated as
            one of the merged sessions:

            - If the target is a single session, it is first renumbered as
              session 1 (its NIfTI files and sequence lines get the base
              increment, and its raw data folders are moved into a subfolder
              named like a source's). The sources then follow as sessions 2, 3,
              and so on.
            - If the target is itself the result of an earlier merge, its
              numbering is kept and the sources are added after its last session
              block. Such a target is recognised by a large gap in its sequence
              numbers: the largest gap between consecutive sequence numbers is
              at least 50000 and at least 50 times the median gap.

            The target's own sequence lines and metadata are kept in the file
            they came from.

        Session and subject IDs:
            The target session ID is the name of the target folder. If it
            contains an underscore (e.g. 'A_B'), the subject ID is the part
            before the first underscore ('A'). Otherwise the subject ID is the
            same as the session ID.

        Derivatives:
            Derivatives (`images/` and `hcp/` folders) are never merged. If a
            source session contains them, a warning is reported and they remain
            in the source folder. Note that removing or moving the source
            sessions with `--original_sessions` takes their derivatives with
            them.

    Examples:
        Join two sessions into a new session `A` in the study's sessions
        folder, copying the raw data and leaving the source sessions as they
        are::

            qunex merge_session \
                --studyfolder=/data/my_study \
                --source="A_001,A_002" \
                --target=A

        Join three sessions, replacing an earlier version of the target, and
        remove the source sessions once the merge has succeeded::

            qunex merge_session \
                --studyfolder=/data/my_study \
                --source="A_001,A_002,A_003" \
                --target=A \
                --overwrite=clean \
                --original_sessions=remove

        Add a further session to an existing merged session, moving its raw
        data, and move the source session to an archive folder in the study::

            qunex merge_session \
                --studyfolder=/data/my_study \
                --source=A_004 \
                --target=A \
                --overwrite=merge \
                --raw_data=move \
                --original_sessions="move:archive/merged_sessions"

        Use paths instead of session IDs::

            qunex merge_session \
                --studyfolder=/data/my_study \
                --source="/data/import/s1,other_sessions/s2" \
                --target=/data/my_study/sessions/merged
    """

    log = gl.log_or_console(_log)

    # Validate parameters
    if overwrite not in ["no", "clean", "merge"]:
        raise ge.CommandError(
            "merge_session",
            f"overwrite must be 'no', 'clean', or 'merge', got '{overwrite}'",
        )

    if raw_data not in ["copy", "move", "leave"]:
        raise ge.CommandError(
            "merge_session",
            f"raw_data must be 'copy', 'move', or 'leave', got '{raw_data}'",
        )

    # Validate original_sessions parameter
    if not (
        original_sessions == "leave"
        or original_sessions == "remove"
        or original_sessions.startswith("move:")
    ):
        raise ge.CommandError(
            "merge_session",
            f"original_sessions must be 'leave', 'remove', or 'move:<path>', got '{original_sessions}'",
        )

    # Parse move destination if specified
    move_destination = None
    if original_sessions.startswith("move:"):
        move_destination = original_sessions[5:]  # Strip 'move:' prefix
        if not move_destination:
            raise ge.CommandError(
                "merge_session", "move destination path must be specified after 'move:'"
            )
        # Convert to absolute path if relative
        if not os.path.isabs(move_destination):
            move_destination = os.path.join(studyfolder, move_destination)

    # Validate study folder
    if not studyfolder:
        raise ge.CommandError("merge_session", "studyfolder parameter is required")

    study_folder = os.path.abspath(studyfolder)
    if not os.path.exists(study_folder):
        raise ge.CommandFailed(
            "merge_session", f"Study folder does not exist: {study_folder}"
        )

    sessions_folder = os.path.join(study_folder, "sessions")

    # Parse source sessions
    source_session_specs = [s.strip() for s in source.split(",")]
    if not source_session_specs:
        raise ge.CommandError("merge_session", "No source sessions provided")

    # Helper function to resolve paths
    def resolve_path(spec: str, base_folder: str, sessions_folder: str) -> str:
        """Resolve a session specification to an absolute path.

        Args:
            spec: Session ID, relative path, or absolute path
            base_folder: Study folder for relative paths
            sessions_folder: Default sessions folder for session IDs

        Returns:
            Absolute path to the session
        """
        # Check if absolute path
        if os.path.isabs(spec):
            return spec
        # Check if it contains path separators (relative path)
        elif "/" in spec or "\\" in spec:
            return os.path.join(base_folder, spec)
        # Otherwise treat as session ID in sessions folder
        else:
            return os.path.join(sessions_folder, spec)

    # Resolve and verify all source sessions exist
    source_paths = []
    for session_spec in source_session_specs:
        session_path = resolve_path(session_spec, study_folder, sessions_folder)
        if not os.path.exists(session_path):
            raise ge.CommandFailed(
                "merge_session", f"Source session not found: {session_path}"
            )
        source_paths.append(session_path)

    # Determine target path
    target_path = resolve_path(target, study_folder, sessions_folder)
    target_session_id = os.path.basename(target_path)

    # Derive subject ID from session ID
    if "_" in target_session_id:
        subject_id = target_session_id.split("_")[0]
    else:
        subject_id = target_session_id

    # Check target existence and handle overwrite
    target_exists = os.path.exists(target_path)
    target_has_content = False

    if target_exists:
        # Check if target has any content
        target_has_content = any(os.listdir(target_path))

        if target_has_content:
            # Check for derivatives
            has_derivatives = os.path.exists(
                os.path.join(target_path, "images")
            ) or os.path.exists(os.path.join(target_path, "hcp"))

            if overwrite == "no":
                raise ge.CommandFailed(
                    "merge_session",
                    f"Target session '{target_path}' exists and has content",
                    "Use overwrite='clean' or 'merge' to proceed",
                )
            elif overwrite == "merge" and has_derivatives:
                raise ge.CommandFailed(
                    "merge_session",
                    f"Target session '{target_path}' contains derivatives (images/ or hcp/)",
                    "Cannot merge safely. Use overwrite='clean' to replace or choose different target",
                )
            elif overwrite == "clean":
                log.warning(f"Removing existing content from {target_path}")
                shutil.rmtree(target_path)
                target_exists = False
                target_has_content = False

    # Check source sessions for derivatives
    for idx, session_path in enumerate(source_paths):
        has_images = os.path.exists(os.path.join(session_path, "images"))
        has_hcp = os.path.exists(os.path.join(session_path, "hcp"))

        if has_images or has_hcp:
            log.warning(
                f"Source session '{source_session_specs[idx]}' contains derivatives "
                f"({'images/' if has_images else ''}{'hcp/' if has_hcp else ''}) "
                f"which will NOT be merged. Derivatives remain in source folder."
            )

    # Create target directory structure if needed
    if not target_exists:
        os.makedirs(target_path, exist_ok=True)
        os.makedirs(os.path.join(target_path, "dicom"), exist_ok=True)
        os.makedirs(os.path.join(target_path, "nii"), exist_ok=True)

    # Analyze existing target sequences if merging. Each target file is kept
    # for its own merged counterpart; numbering is driven by the hcp sequences
    # when present, by session.txt otherwise.
    target_sequences = []
    target_hcp_sequences = []
    target_txt_sequences = []
    target_hcp_metadata = None
    target_txt_metadata = None
    target_max_seq = 0
    target_max_bold = 0
    target_max_se = 0
    target_max_fm = 0
    target_is_joined = False

    if overwrite == "merge" and target_has_content:
        target_hcp_file = os.path.join(target_path, "session_hcp.txt")
        if os.path.exists(target_hcp_file):
            target_hcp_sequences = _parse_session_file(target_hcp_file)
            target_hcp_metadata = _parse_session_metadata(target_hcp_file)

        target_txt_file = os.path.join(target_path, "session.txt")
        if os.path.exists(target_txt_file):
            target_txt_sequences = _parse_session_file(target_txt_file)
            target_txt_metadata = _parse_session_metadata(target_txt_file)

        target_sequences = target_hcp_sequences or target_txt_sequences
        if target_sequences:
            target_max_seq = _find_max_sequence_number(target_sequences)
            target_max_bold = _find_max_bold_index(target_sequences)
            target_max_se = _find_max_group_tag(target_sequences, "se")
            target_max_fm = _find_max_group_tag(target_sequences, "fm")
            target_is_joined = _detect_joined_session(target_sequences)

    # Analyze source sessions
    all_source_sequences = []
    source_session_data = []

    for session_path in source_paths:
        session_data = {"path": session_path}

        # Parse session_hcp.txt if it exists
        session_hcp_file = os.path.join(session_path, "session_hcp.txt")
        if os.path.exists(session_hcp_file):
            with open(session_hcp_file, "r") as f:
                content = f.read()
            sequences = _parse_session_file(session_hcp_file)
            metadata = _parse_session_metadata(session_hcp_file)
            session_data["hcp_file"] = session_hcp_file
            session_data["hcp_content"] = content
            session_data["hcp_sequences"] = sequences
            session_data["hcp_metadata"] = metadata
            all_source_sequences.extend(sequences)

        # Parse session.txt if it exists
        session_txt_file = os.path.join(session_path, "session.txt")
        if os.path.exists(session_txt_file):
            with open(session_txt_file, "r") as f:
                content = f.read()
            sequences = _parse_session_file(session_txt_file)
            metadata = _parse_session_metadata(session_txt_file)
            session_data["txt_file"] = session_txt_file
            session_data["txt_content"] = content
            session_data["txt_sequences"] = sequences
            session_data["txt_metadata"] = metadata
            # Only extend if we didn't already get sequences from hcp file
            if "hcp_sequences" not in session_data:
                all_source_sequences.extend(sequences)

        if "hcp_file" in session_data or "txt_file" in session_data:
            source_session_data.append(session_data)

    # Find maximum sequence number across all sources
    source_max_seq = _find_max_sequence_number(all_source_sequences)

    # Determine base increment
    if overwrite == "merge" and target_is_joined:
        # Target already contains joined sessions, use the same base increment
        base_increment = _detect_base_increment(target_sequences)
        if base_increment == 0:
            # Fallback if detection fails
            base_increment = _determine_base_increment(target_max_seq)
    else:
        # Determine based on combined max
        combined_max = max(target_max_seq, source_max_seq)
        base_increment = _determine_base_increment(combined_max)

    # If target is a single session being merged into, renumber it first
    if overwrite == "merge" and target_has_content and not target_is_joined:
        log.step(
            f"Renumbering existing target session to use base increment {base_increment}"
        )
        target_offset = base_increment  # Target becomes session 1 (prefix 1)

        # Move raw data folders to nested structure if raw_data != 'leave'
        if raw_data != "leave":
            # Determine subfolder name for target
            # If target ID is like "A_B", use "B" as subfolder
            # Otherwise use the full target session ID
            if "_" in target_session_id:
                parts = target_session_id.split("_", 1)
                nest_folder = parts[1]
            else:
                nest_folder = target_session_id

            # Move raw data folders (dicom, bids, inbox, hcpls)
            for folder_name in ["dicom", "bids", "inbox", "hcpls"]:
                folder_path = os.path.join(target_path, folder_name)
                if os.path.exists(folder_path):
                    # Create temporary location
                    temp_path = os.path.join(target_path, f"_temp_{folder_name}")
                    os.rename(folder_path, temp_path)
                    os.makedirs(folder_path, exist_ok=True)
                    # Move to nested location
                    nested_path = os.path.join(folder_path, nest_folder)
                    os.rename(temp_path, nested_path)

        # Renumber nii files
        target_nii = os.path.join(target_path, "nii")
        if os.path.exists(target_nii):
            for item in sorted(
                os.listdir(target_nii), reverse=True
            ):  # Reverse to avoid conflicts
                source_file = os.path.join(target_nii, item)
                if os.path.isfile(source_file):
                    match = re.match(r"^(\d+)", item)
                    if match:
                        old_seq_num = int(match.group(1))
                        new_seq_num = old_seq_num + target_offset
                        new_name = item.replace(str(old_seq_num), str(new_seq_num), 1)
                        new_file = os.path.join(target_nii, new_name)
                        os.rename(source_file, new_file)

        # Update target sequences of both files to reflect new numbering
        for seq in target_hcp_sequences + target_txt_sequences:
            old_num = seq["number"]
            new_num = old_num + target_offset
            seq["number"] = new_num
            # Update the line with new sequence number
            seq["line"] = _SEQ_LINE.sub(f"{new_num}:", seq["line"])

        # Update max values
        target_max_seq = _find_max_sequence_number(target_sequences)

    # Track session metadata for session_N entries. A target that is itself a
    # merge already carries session_N entries; new ones are numbered after them.
    session_metadata = []
    prior_sessions = max(
        sum(
            1
            for key, _ in (md["additional"] if md else [])
            if re.fullmatch(r"session_\d+", key)
        )
        for md in (target_hcp_metadata, target_txt_metadata)
    )

    # Add target session metadata if merging into a single session; a joined
    # target already lists its sessions
    if overwrite == "merge" and target_has_content and not target_is_joined:
        # Determine target's nest folder name
        if "_" in target_session_id:
            parts = target_session_id.split("_", 1)
            target_nest = parts[1]
        else:
            target_nest = target_session_id
        session_metadata.append(("session_1", target_nest))

    # Process each source session
    current_bold_index = target_max_bold
    current_se_index = target_max_se
    current_fm_index = target_max_fm

    combined_hcp_lines = []
    combined_txt_lines = []
    combined_hcp_metadata = {"additional": []}
    combined_txt_metadata = {"additional": []}
    if target_hcp_metadata:
        _merge_metadata(combined_hcp_metadata, target_hcp_metadata, _log=log)
    if target_txt_metadata:
        _merge_metadata(combined_txt_metadata, target_txt_metadata, _log=log)

    for idx, session_data in enumerate(source_session_data):
        session_path = session_data["path"]
        session_id = os.path.basename(session_path)

        # Use hcp sequences for determining mappings if available, otherwise txt sequences
        sequences = session_data.get(
            "hcp_sequences", session_data.get("txt_sequences", [])
        )

        # Calculate offset for this session
        if overwrite == "merge" and target_is_joined:
            # Target is joined, find next available prefix
            # Get the next prefix number (not the offset)
            next_prefix = (
                _find_next_prefix_offset(target_sequences, base_increment)
                // base_increment
            )
            # Each source session gets sequential prefixes: next_prefix, next_prefix+1, next_prefix+2, ...
            offset = (next_prefix + idx) * base_increment
        elif overwrite == "merge" and target_has_content:
            # Target exists but is a single session, treat it as session 1
            # and add new sessions as 2, 3, etc.
            offset = (idx + 2) * base_increment
        else:
            # Fresh join: treat all sources as new sessions, number them 1, 2, 3, etc.
            offset = (idx + 1) * base_increment

        # Find bold/boldref sequences and determine renumbering
        bold_mapping = {}
        se_mapping = {}
        fm_mapping = {}

        # Extract current bold indices from this session
        session_bold_indices = _extract_bold_indices(sequences)
        if session_bold_indices:
            # Find the minimum bold index in this session
            min_bold_idx = min(session_bold_indices)
            # Calculate offset: where min should map to
            bold_offset = current_bold_index + 1 - min_bold_idx

            # Create mapping by adding offset to each index
            for old_idx in sorted(session_bold_indices):
                new_idx = old_idx + bold_offset
                bold_mapping[old_idx] = new_idx
                # Update current_bold_index to track the maximum we've used
                current_bold_index = max(current_bold_index, new_idx)

        # Extract and map se() tags
        session_se_indices = _extract_group_tags(sequences, "se")
        for old_idx in sorted(session_se_indices):
            current_se_index += 1
            se_mapping[old_idx] = current_se_index

        # Extract and map fm() tags
        session_fm_indices = _extract_group_tags(sequences, "fm")
        for old_idx in sorted(session_fm_indices):
            current_fm_index += 1
            fm_mapping[old_idx] = current_fm_index

        # Handle raw data (dicom, bids, inbox, hcpls) based on raw_data parameter
        if raw_data != "leave":
            _ = shutil.move if raw_data == "move" else shutil.copytree
            _ = shutil.move if raw_data == "move" else shutil.copy2

            # Determine target subfolder name for nesting
            # If source ID is like "A_B" and target ID is "A", use "B" as subfolder
            # Otherwise use the full source session ID
            if "_" in session_id:
                parts = session_id.split("_", 1)
                if parts[0] == target_session_id:
                    nest_folder = parts[1]
                else:
                    nest_folder = session_id
            else:
                nest_folder = session_id

            # Calculate session number for metadata
            session_num = prior_sessions + len(session_metadata) + 1
            session_metadata.append((f"session_{session_num}", nest_folder))

            # Handle raw data folders
            for folder_name in ["dicom", "bids", "inbox", "hcpls"]:
                source_folder = os.path.join(session_path, folder_name)
                if os.path.exists(source_folder):
                    target_folder = os.path.join(target_path, folder_name)
                    os.makedirs(target_folder, exist_ok=True)

                    # Nest under session subfolder
                    target_session_folder = os.path.join(target_folder, nest_folder)
                    if os.path.exists(target_session_folder):
                        log.warning(f"{target_session_folder} already exists, skipping")
                    else:
                        if raw_data == "move":
                            shutil.move(source_folder, target_session_folder)
                        else:
                            shutil.copytree(source_folder, target_session_folder)

        # Copy and rename nii files
        source_nii = os.path.join(session_path, "nii")
        target_nii = os.path.join(target_path, "nii")

        if os.path.exists(source_nii):
            for item in os.listdir(source_nii):
                source_file = os.path.join(source_nii, item)
                if os.path.isfile(source_file):
                    # Extract sequence number from filename
                    match = re.match(r"^(\d+)", item)
                    if match:
                        old_seq_num = int(match.group(1))
                        new_seq_num = old_seq_num + offset
                        new_name = item.replace(str(old_seq_num), str(new_seq_num), 1)
                        target_file = os.path.join(target_nii, new_name)

                        if os.path.exists(target_file):
                            log.warning(f"{target_file} already exists, skipping")
                        else:
                            shutil.copy2(source_file, target_file)

        # Process session_hcp.txt content if it exists
        if "hcp_content" in session_data:
            processed_hcp_lines = _process_session_file_content(
                session_data["hcp_content"],
                offset,
                bold_mapping,
                se_mapping,
                fm_mapping,
                is_hcp=True,
            )
            combined_hcp_lines.extend(processed_hcp_lines)

            # Collect metadata from hcp file
            _merge_metadata(
                combined_hcp_metadata, session_data["hcp_metadata"], _log=log
            )

        # Process session.txt content if it exists
        if "txt_content" in session_data:
            processed_txt_lines = _process_session_file_content(
                session_data["txt_content"],
                offset,
                bold_mapping,
                se_mapping,
                fm_mapping,
                is_hcp=False,
            )
            combined_txt_lines.extend(processed_txt_lines)

            # Collect metadata from txt file
            _merge_metadata(
                combined_txt_metadata, session_data["txt_metadata"], _log=log
            )

    # Write combined session files. session_hcp.txt only when a source, or
    # the target being merged into, had one.
    write_hcp = target_hcp_metadata is not None or any(
        "hcp_file" in session_data for session_data in source_session_data
    )
    _write_session_files(
        target_path,
        target_session_id,
        subject_id,
        [seq["line"] for seq in target_hcp_sequences] + combined_hcp_lines,
        [seq["line"] for seq in target_txt_sequences] + combined_txt_lines,
        combined_hcp_metadata,
        combined_txt_metadata,
        write_hcp,
        session_metadata,
        _log=log,
    )

    log.step(
        f"Successfully joined {len(source_session_specs)} sessions into {target_path}"
    )

    # Handle original sessions if merge was successful
    if original_sessions == "remove":
        # Remove original source sessions
        for session_path in source_paths:
            if os.path.exists(session_path):
                log.step(f"Removing original session: {session_path}")
                shutil.rmtree(session_path)
    elif original_sessions.startswith("move:"):
        # Move original source sessions to specified location
        with log.section(f"Moving original sessions to {move_destination}"):
            # Handle move destination based on overwrite parameter
            if os.path.exists(move_destination):
                if os.path.isfile(move_destination):
                    if overwrite != "no":
                        log.step("Removing the existing file at the move destination")
                        os.remove(move_destination)
                    else:
                        # overwrite='no' - warn and skip moving
                        log.warning(
                            "Move destination is a file, not a directory: "
                            f"{move_destination}"
                        )
                        log.detail("Sessions not moved. Please, resolve manually.")
                        return True
            else:
                # Destination doesn't exist - create it
                log.step("Creating the move destination folder")
                os.makedirs(move_destination, exist_ok=True)

            # Move sessions to destination
            for session_path in source_paths:
                if os.path.exists(session_path):
                    session_name = os.path.basename(session_path)
                    dest_path = os.path.join(move_destination, session_name)

                    # If destination session exists and overwrite is not 'no', remove it first
                    if os.path.exists(dest_path):
                        if overwrite != "no":
                            log.step(f"Removing existing session at {dest_path}")
                            shutil.rmtree(dest_path)
                        elif os.path.isdir(dest_path):
                            target_content = os.listdir(dest_path)
                            if target_content:
                                log.warning(
                                    "Session already exists at move destination: "
                                    f"{dest_path}"
                                )
                                log.detail(
                                    f"Session '{session_name}' not moved. "
                                    "Please, resolve manually."
                                )
                                continue
                        else:
                            log.warning(
                                f"A file exists at move destination: {dest_path}"
                            )
                            log.detail(
                                f"Session '{session_name}' not moved. "
                                "Please, resolve manually."
                            )
                            continue

                    log.step(f"Moving original session {session_name}")
                    shutil.move(session_path, move_destination)

    return True


def merge_sessions_list(
    studyfolder: str,
    session_list: str,
    source_folder: str,
    target_folder: str,
    overwrite: str = "no",
    raw_data: str = "copy",
    original_sessions: str = "leave",
    _log=None,
) -> bool:
    r"""
    ``merge_sessions_list --studyfolder=<path> --session_list=<file> --source_folder=<path> --target_folder=<path> [--overwrite=<mode>] [--raw_data=<mode>] [--original_sessions=<action>]``

    Join multiple sets of sessions, as listed in a file.

    Description:
        Reads a list file in which each line names a target session and the
        source sessions to join into it, and runs `merge_session` for each
        line. This is the way to merge sessions for a whole study in one step,
        for instance after importing data in which several subjects were
        scanned in more than one session.

        All source sessions are read from one folder (`--source_folder`) and all
        target sessions are created in one folder (`--target_folder`). The two
        can be the same folder, or different ones, e.g. importing into
        `sessions/` and merging into `subjects/`.

        The lines are processed in order. If joining one target fails, the
        error is reported and the remaining lines are still processed. A summary
        at the end lists the targets that were joined and those that failed,
        and the command fails if any of them did. Every merge follows the rules
        described in `merge_session`, including sequence renumbering and which
        session information files are created.

    ..  qx_command:
        type: utility

    Parameters:
        --studyfolder (str):
            Path to the study folder. The source and target sessions are given
            by the folders below, so the study folder is used only to resolve
            a relative `move:<path>` in `--original_sessions` and to report the
            target paths.

        --session_list (str):
            Path to a text file listing the merges, one per line, in the
            format::

                <target_id>: <source_id>, <source_id>, ...

            `<target_id>` is the name of the merged session to create and the
            `<source_id>` values are the sessions to join into it, in the order
            in which they are to be merged. Lines starting with `#` are
            comments, and empty lines are ignored. A line without a colon, or
            with an empty target or no sources, is skipped with a warning. If
            no valid line remains, a warning is reported and nothing is done.

        --source_folder (str):
            Path to the folder containing the source sessions. Each
            `<source_id>` is resolved as `<source_folder>/<source_id>`. The
            folder must exist.

        --target_folder (str):
            Path to the folder in which the target sessions are created. Each
            `<target_id>` is resolved as `<target_folder>/<target_id>`. The
            folder is created if it does not exist.

        --overwrite (str, default 'no'):
            What to do when a target session already exists and is not empty:
            'no' (fail for that target), 'clean' (replace it) or 'merge' (add
            the sources to it). See `merge_session` for details.

        --raw_data (str, default 'copy'):
            What to do with the raw data folders (`dicom/`, `bids/`, `inbox/`,
            `hcpls/`) of the source sessions: 'copy', 'move' or 'leave'. NIfTI
            files are always copied. See `merge_session` for details.

        --original_sessions (str, default 'leave'):
            What to do with the source sessions of a target once it has been
            joined successfully: 'leave', 'remove' or 'move:<path>'.

            - 'leave': leave them unchanged,
            - 'remove': delete them,
            - 'move:<path>': move them into the folder `<path>`, e.g.
              'move:/data/backup_sessions' or 'move:archive/merged_sessions'. A
              relative path is resolved against the study folder.

            The sources of a target that failed are left unchanged. See
            `merge_session` for how existing sessions at the move destination
            are handled.

    Output files:
        One merged session folder per line of the list file, in
        `<target_folder>/<target_id>`, with the content described in
        `merge_session`.

    Examples:
        A list file, e.g. `/data/my_study/processing/merge_sessions.txt`::

            # subject A was scanned in three sessions
            A: A_1, A_2, A_3

            # subject B in two
            B: B_1, B_2

        Merge the sessions in the study's sessions folder into a separate
        `subjects` folder, copying the raw data and leaving the source sessions
        as they are::

            qunex merge_sessions_list \
                --studyfolder=/data/my_study \
                --session_list=/data/my_study/processing/merge_sessions.txt \
                --source_folder=/data/my_study/sessions \
                --target_folder=/data/my_study/subjects

        Merge within the sessions folder, replacing earlier merges, and remove
        the source sessions once each merge has succeeded::

            qunex merge_sessions_list \
                --studyfolder=/data/my_study \
                --session_list=/data/my_study/processing/merge_sessions.txt \
                --source_folder=/data/my_study/sessions \
                --target_folder=/data/my_study/sessions \
                --overwrite=clean \
                --original_sessions=remove

        Move the raw data into the merged sessions and the source sessions to
        an archive folder in the study::

            qunex merge_sessions_list \
                --studyfolder=/data/my_study \
                --session_list=/data/my_study/processing/merge_sessions.txt \
                --source_folder=/data/my_study/sessions \
                --target_folder=/data/my_study/subjects \
                --overwrite=clean \
                --raw_data=move \
                --original_sessions="move:archive/pre_merge_sessions"
    """

    log = gl.log_or_console(_log)

    # Validate parameters
    if not os.path.exists(session_list):
        raise ge.CommandFailed(
            "merge_sessions_list", f"Session list file does not exist: {session_list}"
        )

    if not os.path.exists(studyfolder):
        raise ge.CommandFailed(
            "merge_sessions_list", f"Study folder does not exist: {studyfolder}"
        )

    if not os.path.exists(source_folder):
        raise ge.CommandFailed(
            "merge_sessions_list", f"Source folder does not exist: {source_folder}"
        )

    # Create target folder if it doesn't exist
    if not os.path.exists(target_folder):
        os.makedirs(target_folder, exist_ok=True)
        log.step(f"Created target folder: {target_folder}")

    # Parse session list file
    join_specs = []
    with open(session_list, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Parse line: target_id: source_id1, source_id2, ...
            if ":" not in line:
                log.warning(f"Skipping malformed line {line_num}: {line}")
                continue

            target_id, sources_str = line.split(":", 1)
            target_id = target_id.strip()

            # Parse comma-separated source IDs
            source_ids = [s.strip() for s in sources_str.split(",")]
            source_ids = [s for s in source_ids if s]  # Remove empty strings

            if not target_id:
                log.warning(f"Skipping line {line_num} with empty target ID")
                continue

            if not source_ids:
                log.warning(f"Skipping line {line_num} with no source IDs")
                continue

            join_specs.append(
                {"target_id": target_id, "source_ids": source_ids, "line_num": line_num}
            )

    if not join_specs:
        log.warning("No valid join specifications found in session list")
        return False

    # Report header. `raw` because a title over its own rule is not a record
    # shape; it carries no trailing newline, since every record that follows
    # opens with one.
    log.raw("\nmerge_sessions_list\n==================")
    log.step(
        f"Running {len(join_specs)} join operations from source folder: "
        f"{os.path.basename(source_folder)} to target folder: "
        f"{os.path.basename(target_folder)}"
    )
    log.detail(f"Raw data: {raw_data}")
    log.detail(f"Original sessions: {original_sessions}")

    # Process each join specification
    successful = 0
    failed = 0
    successful_ids = []
    failed_ids = []

    for spec in join_specs:
        target_id = spec["target_id"]
        source_ids = spec["source_ids"]
        line_num = spec["line_num"]

        # Build source paths
        source_paths = [os.path.join(source_folder, sid) for sid in source_ids]
        source_str = ",".join(source_paths)

        # Build target path
        target_path = os.path.join(target_folder, target_id)

        # Compute relative target path
        target_rel = os.path.relpath(target_path, studyfolder)
        log.blank()
        # the nesting is what `merge_session`'s `_indent` used to spell
        with log.section(f"Joining to {target_rel}"):
            log.detail(f"Sources: {', '.join(source_ids)}")
            log.detail(f"Target: {target_id}")

            try:
                merge_session(
                    studyfolder=studyfolder,
                    source=source_str,
                    target=target_path,
                    overwrite=overwrite,
                    raw_data=raw_data,
                    original_sessions=original_sessions,
                    _log=log,
                )
                successful += 1
                successful_ids.append(target_id)
            except Exception as e:
                failed += 1
                failed_ids.append(target_id)
                log.error(f"Failed joining {target_id}: {str(e)}")
                # Continue processing remaining specifications

    # Report summary
    log.blank()
    with log.section("Summary"):
        if successful_ids:
            log.detail(
                f"Successfully joined {len(successful_ids)}/{len(join_specs)} "
                f"sessions: {', '.join(successful_ids)}"
            )
        if failed_ids:
            log.detail(
                f"Failed joining {len(failed_ids)}/{len(join_specs)} "
                f"sessions: {', '.join(failed_ids)}"
            )
        if not successful_ids and not failed_ids:
            log.detail("No operations completed")

    # A failing join is recorded where it happens and raised here, after the
    # loop, so one failing session does not abort its siblings. The success
    # line the command used to print is `run_with_log`'s to write.
    if failed:
        log.error("Not all sessions joined successfully.")
        raise ge.CommandFailed(
            "merge_sessions_list",
            "Not all sessions joined successfully",
            f"{failed} of {len(join_specs)} join operations failed: "
            f"{', '.join(failed_ids)}",
        )

    return True


def _merge_metadata(combined: Dict, new_metadata: Dict, _log=None) -> None:
    """Merge new metadata into combined metadata, detecting conflicts.

    Args:
        combined: dict with 'additional' as list of (key, value) tuples
        new_metadata: dict with 'additional' as list of (key, value) tuples
    """
    log = gl.log_or_console(_log)

    # Track existing keys for conflict detection
    existing_keys = {}
    for key, value in combined.get("additional", []):
        if key in existing_keys:
            if value not in existing_keys[key]:
                existing_keys[key].append(value)
        else:
            existing_keys[key] = [value]

    # Merge new metadata
    for key, value in new_metadata.get("additional", []):
        if key in existing_keys:
            if value not in existing_keys[key]:
                log.warning(
                    f"Metadata conflict for '{key}': "
                    f"existing='{existing_keys[key]}', new='{value}'. "
                    f"Keeping both values."
                )
                combined["additional"].append((key, value))
                existing_keys[key].append(value)
        else:
            combined["additional"].append((key, value))
            existing_keys[key] = [value]


def _parse_session_file(filepath: str) -> List[Dict]:
    """Parse session file and extract sequence information."""
    sequences = []

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Check if line is a sequence definition (starts with number followed by colon)
            match = _SEQ_LINE.match(line)
            if match:
                seq_num = int(match.group(1))
                sequences.append({"number": seq_num, "line": line})

    return sequences


def _parse_session_metadata(filepath: str) -> Dict:
    """Parse metadata from session file.

    Returns dict with:
        'session': session id (or None)
        'id': session id for session.txt files (or None)
        'subject': subject id
        'paths': dict of path metadata (dicom, raw_data, data, hcp)
        'additional': list of tuples (key, value) preserving order
        'original_lines': original metadata lines preserving formatting
        'is_hcp': True if this is from session_hcp.txt
    """
    metadata = {
        "session": None,
        "id": None,
        "subject": None,
        "paths": {},
        "additional": [],
        "original_lines": [],
        "is_hcp": "session_hcp.txt" in filepath,
    }

    path_keys = {"dicom", "raw_data", "data", "hcp"}
    id_keys = {"session", "subject", "id"}

    with open(filepath, "r") as f:
        for line in f:
            stripped = line.rstrip()
            if not stripped or stripped.startswith("#"):
                continue
            if ":" in stripped and not stripped[0].isdigit():
                # Metadata line
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    value = parts[1].strip()

                    if key in id_keys:
                        metadata[key] = value
                    elif key in path_keys:
                        metadata["paths"][key] = value
                    else:
                        # Store as tuple to preserve order
                        metadata["additional"].append((key, value))

                    # Store original line for formatting preservation
                    metadata["original_lines"].append(stripped)

    return metadata


def _find_max_sequence_number(sequences: List[Dict]) -> int:
    """Find maximum sequence number."""
    if not sequences:
        return 0
    return max(seq["number"] for seq in sequences)


def _find_max_bold_index(sequences: List[Dict]) -> int:
    """Find maximum bold/boldref index in sequences."""
    max_idx = 0

    for seq in sequences:
        line = seq["line"]
        # Look for bold[N] or boldref[N]
        matches = re.findall(r":bold(?:ref)?(\d+):", line)
        for match in matches:
            max_idx = max(max_idx, int(match))

    return max_idx


def _find_max_group_tag(sequences: List[Dict], tag: str) -> int:
    """Find maximum value for a grouping tag (se or fm)."""
    max_idx = 0

    pattern = re.compile(rf"{tag}\((\d+)\)")

    for seq in sequences:
        line = seq["line"]
        matches = pattern.findall(line)
        for match in matches:
            max_idx = max(max_idx, int(match))

    return max_idx


def _detect_joined_session(sequences: List[Dict]) -> bool:
    """
    Detect if session already contains joined sessions.

    A joined session has sequences clustered into distinct groups with large gaps.
    For example: 101011-116011, then 201011-217011 (gap of ~85000).
    A single session has small sequential gaps: 1011, 2011, 3011, ... 16011.

    Strategy: Look for gaps significantly larger than the typical sequence spacing.
    """
    if not sequences or len(sequences) < 2:
        return False

    seq_numbers = sorted([seq["number"] for seq in sequences])

    # Calculate all gaps between consecutive sequences
    gaps = []
    for i in range(len(seq_numbers) - 1):
        gap = seq_numbers[i + 1] - seq_numbers[i]
        gaps.append(gap)

    if not gaps:
        return False

    # Calculate statistics
    max_gap = max(gaps)
    median_gap = sorted(gaps)[len(gaps) // 2]

    # If the maximum gap is significantly larger than the median gap,
    # we likely have multiple merged sessions with a large gap between them.
    # Use a threshold: max_gap should be at least 50x the median gap and at least 50000
    if max_gap >= 50 * median_gap and max_gap >= 50000:
        return True

    return False


def _detect_base_increment(sequences: List[Dict]) -> int:
    """
    Detect the base increment used in an already-joined session.

    Analyzes the sequence numbers to determine the increment between
    merged sessions. For example, if sequences are numbered 101011, 102011, ...
    and 201011, 202011, ..., the base increment is 100000.

    Returns:
        Detected base increment, or 0 if cannot be determined
    """
    if not sequences or len(sequences) < 2:
        return 0

    seq_numbers = sorted([seq["number"] for seq in sequences])

    # Try different potential base increments (powers of 10), from largest to smallest
    # We want to find the largest base that creates meaningful groups
    potential_increments = [10000000, 1000000, 100000, 10000, 1000]

    best_base = 0
    min_groups = float("inf")

    for base in potential_increments:
        # Calculate prefixes using this base
        prefixes = {}
        for num in seq_numbers:
            prefix = num // base
            if prefix not in prefixes:
                prefixes[prefix] = []
            prefixes[prefix].append(num)

        # Check if this base creates distinct groups
        # Each group should have sequences that differ by small amounts (< base)
        if len(prefixes) > 1:
            # Verify that sequences within each group are close together
            valid = True
            for prefix, nums in prefixes.items():
                # All numbers in this group should be within base of each other
                if max(nums) - min(nums) >= base:
                    valid = False
                    break

            if valid and len(prefixes) < min_groups:
                # Prefer the base that creates fewer, more meaningful groups
                # (e.g., 2 groups for base=100000 is better than 4 groups for base=10000)
                min_groups = len(prefixes)
                best_base = base

    return best_base


def _determine_base_increment(max_seq: int) -> int:
    """Determine appropriate base increment for sequence renumbering."""
    if max_seq == 0:
        return 1000

    # Find next power of 10 above max_seq
    power = 1000
    while power <= max_seq:
        power *= 10

    return power


def _find_next_prefix_offset(target_sequences: List[Dict], base_increment: int) -> int:
    """Find next available prefix when adding to already-joined session.

    For example, if target has sequences 101011, 201011 with base_increment=100000,
    this returns 300000 (the offset for the next session to start at 301011).
    """
    if not target_sequences:
        return 0

    # Extract prefixes
    prefixes = set()
    for seq in target_sequences:
        num = seq["number"]
        # Calculate prefix based on base_increment
        prefix = num // base_increment
        prefixes.add(prefix)

    # Find max prefix and return offset for next prefix
    if prefixes:
        next_prefix = max(prefixes) + 1
        return next_prefix * base_increment
    return 0


def _extract_bold_indices(sequences: List[Dict]) -> Set[int]:
    """Extract all bold/boldref indices from sequences."""
    indices = set()

    for seq in sequences:
        line = seq["line"]
        matches = re.findall(r":bold(?:ref)?(\d+):", line)
        for match in matches:
            indices.add(int(match))

    return indices


def _extract_group_tags(sequences: List[Dict], tag: str) -> Set[int]:
    """Extract all values for a specific grouping tag (se or fm)."""
    indices = set()
    pattern = re.compile(rf"{tag}\((\d+)\)")

    for seq in sequences:
        line = seq["line"]
        matches = pattern.findall(line)
        for match in matches:
            indices.add(int(match))

    return indices


def _reformat_sequence_line(line: str, is_hcp: bool = True) -> str:
    """
    Reformat a sequence line to ensure proper column alignment.

    For session_hcp.txt (is_hcp=True):
    - Simple: <number>:<tag>:<name>: <properties>
    - Compound (bold/boldref/DWI): <number>:<tag>:<subtype>:<name>: <properties>

    For session.txt (is_hcp=False):
    - Format: <number>: <name> : <properties>

    Examples:
        HCP Simple:   "13011:SE-FM-AP:SE_AP_EPI_2.4mm: TR(4.64333): se(3)"
                      "13011:SE-FM-AP        :SE_AP_EPI_2.4mm: TR(4.64333): se(3)"

        HCP Compound: "15011:boldref4:task:REFBOLD_SWM_MB4_S1.9_2.4mm_AP: TR(3.49986): se(3): phenc(AP)"
                      "15011:boldref4:task   :REFBOLD_SWM_MB4_S1.9_2.4mm_AP: TR(3.49986): se(3): phenc(AP)"

        TXT:          "215011: REFBOLD_RS_MB4_S1.9_2.4mm_AP : TR(3.49986)"
                      "215011: REFBOLD_RS_MB4_S1.9_2.4mm_AP  : TR(3.49986)"
    """
    # Parse the sequence line
    parts = line.split(":")

    if len(parts) < 2:
        return line  # Can't reformat, return as-is

    seq_num = parts[0]

    if not is_hcp:
        # session.txt format: <number>: <name> : <properties>
        # Just align the name field
        if len(parts) < 2:
            return line

        name = parts[1].strip()
        rest = ":".join(parts[2:]).strip() if len(parts) > 2 else ""

        # Standard width for name in session.txt
        name_width = 33
        formatted_name = name.ljust(name_width)

        if rest:
            return f"{seq_num}: {formatted_name} : {rest}"
        else:
            return f"{seq_num}: {formatted_name}"
    else:
        # session_hcp.txt format
        if len(parts) < 3:
            return line  # Can't reformat, return as-is

        # Check if this is a compound tag (bold*, boldref*, DWI*)
        # Compound tags have format: <primary_tag>:<subtype>:<name>:...
        # Simple tags have format: <tag>:<name>:...
        is_compound = False
        if parts[1].startswith("bold") or parts[1].startswith("DWI"):
            is_compound = True

        # Standard width for tag section (primary tag + subtype if present)
        tag_section_width = 18

        if is_compound:
            # Compound tag: number:primary_tag:subtype:name:properties
            if len(parts) < 4:
                return line  # Malformed compound tag

            primary_tag = parts[1]
            subtype = parts[2]
            name = parts[3]
            rest = ":".join(parts[4:]) if len(parts) > 4 else ""

            # Format compound tag section with padding
            compound_tag = f"{primary_tag}:{subtype}"
            formatted_tag = compound_tag.ljust(tag_section_width)

            # Reconstruct the line
            if rest:
                return f"{seq_num}:{formatted_tag}:{name}:{rest}"
            else:
                return f"{seq_num}:{formatted_tag}:{name}"
        else:
            # Simple tag: number:tag:name:properties
            tag = parts[1]
            name = parts[2]
            rest = ":".join(parts[3:]) if len(parts) > 3 else ""

            # Format simple tag with padding to match compound tag width
            formatted_tag = tag.ljust(tag_section_width)

            # Reconstruct the line
            if rest:
                return f"{seq_num}:{formatted_tag}:{name}:{rest}"
            else:
                return f"{seq_num}:{formatted_tag}:{name}"


def _process_session_file_content(
    content: str,
    offset: int,
    bold_mapping: Dict[int, int],
    se_mapping: Dict[int, int],
    fm_mapping: Dict[int, int],
    is_hcp: bool = True,
) -> List[str]:
    """
    Process session file content, renumbering sequences and tags.

    Args:
        is_hcp: If True, format as session_hcp.txt; if False, format as session.txt

    Returns list of sequence lines (not metadata).
    """
    processed_lines = []

    for line in content.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Skip metadata lines
        if ":" in line and not line[0].isdigit():
            continue

        # Process sequence lines
        match = _SEQ_LINE.match(line)
        if match:
            old_seq_num = int(match.group(1))
            new_seq_num = old_seq_num + offset

            # Replace sequence number at start
            new_line = _SEQ_LINE.sub(f"{new_seq_num}:", line)

            # Replace bold/boldref indices - process in REVERSE order to avoid cascading replacements
            # (e.g., if 1→5 and 5→9, processing 1 first would create :bold5: which would then be replaced to :bold9:)
            for old_idx in sorted(bold_mapping.keys(), reverse=True):
                new_idx = bold_mapping[old_idx]
                # Match :boldN: or :boldrefN: exactly
                new_line = re.sub(rf":bold{old_idx}:", f":bold{new_idx}:", new_line)
                new_line = re.sub(
                    rf":boldref{old_idx}:", f":boldref{new_idx}:", new_line
                )

            # Replace se() tags - process in reverse order
            for old_idx in sorted(se_mapping.keys(), reverse=True):
                new_idx = se_mapping[old_idx]
                new_line = re.sub(rf"se\({old_idx}\)", f"se({new_idx})", new_line)

            # Replace fm() tags - process in reverse order
            for old_idx in sorted(fm_mapping.keys(), reverse=True):
                new_idx = fm_mapping[old_idx]
                new_line = re.sub(rf"fm\({old_idx}\)", f"fm({new_idx})", new_line)

            # Reformat the line for proper alignment
            new_line = _reformat_sequence_line(new_line, is_hcp=is_hcp)

            processed_lines.append(new_line)

    return processed_lines


def _write_session_files(
    target_path: str,
    session_id: str,
    subject_id: str,
    hcp_sequence_lines: List[str],
    txt_sequence_lines: List[str],
    hcp_metadata: Dict,
    txt_metadata: Dict,
    write_hcp: bool,
    session_metadata: List[Tuple[str, str]],
    _log=None,
) -> None:
    """Write combined session.txt and session_hcp.txt files with proper formatting.

    Args:
        write_hcp: Write session_hcp.txt; true when a source or the target had one
        session_metadata: List of tuples (session_N, source_id) to add as metadata
    """

    log = gl.log_or_console(_log)

    # Add session_N metadata to both hcp and txt metadata
    for key, value in session_metadata:
        hcp_metadata["additional"].append((key, value))
        txt_metadata["additional"].append((key, value))

    # Prepare paths
    dicom_path = os.path.join(target_path, "dicom")
    nii_path = os.path.join(target_path, "nii")
    data_path = os.path.join(target_path, "4dfp")
    hcp_path = os.path.join(target_path, "hcp")

    # Calculate maximum key width for proper alignment
    def calculate_max_key_width(metadata: Dict, standard_keys: List[str]) -> int:
        """Calculate the maximum key length for alignment."""
        max_width = max(len(k) for k in standard_keys) if standard_keys else 0
        # Check additional metadata keys
        for key, _ in metadata.get("additional", []):
            max_width = max(max_width, len(key))
        return max_width

    # Calculate key width for HCP file
    hcp_standard_keys = ["session", "subject", "dicom", "raw_data", "data", "hcp"]
    hcp_key_width = calculate_max_key_width(hcp_metadata, hcp_standard_keys)

    # Calculate key width for TXT file
    txt_standard_keys = ["id", "subject", "dicom", "raw_data", "data", "hcp"]
    txt_key_width = calculate_max_key_width(txt_metadata, txt_standard_keys)

    # Helper to format metadata with proper alignment
    def format_metadata_line(key: str, value: str, key_width: int) -> str:
        return f"{key}:{' ' * (key_width - len(key))} {value}"

    # Section 1 for session_hcp.txt: uses 'session' field
    section1_hcp = [
        format_metadata_line("session", session_id, hcp_key_width),
        format_metadata_line("subject", subject_id, hcp_key_width),
    ]

    # Section 1 for session.txt: uses 'id' field
    section1_txt = [
        format_metadata_line("id", session_id, txt_key_width),
        format_metadata_line("subject", subject_id, txt_key_width),
    ]

    # Section 2 for HCP: Paths
    section2_hcp = [
        format_metadata_line("dicom", dicom_path, hcp_key_width),
        format_metadata_line("raw_data", nii_path, hcp_key_width),
        format_metadata_line("data", data_path, hcp_key_width),
        format_metadata_line("hcp", hcp_path, hcp_key_width),
    ]

    # Section 2 for TXT: Paths
    section2_txt = [
        format_metadata_line("dicom", dicom_path, txt_key_width),
        format_metadata_line("raw_data", nii_path, txt_key_width),
        format_metadata_line("data", data_path, txt_key_width),
        format_metadata_line("hcp", hcp_path, txt_key_width),
    ]

    if write_hcp:
        # Section 3: Additional metadata for HCP file (preserve order)
        section3_hcp = []
        for key, value in hcp_metadata.get("additional", []):
            section3_hcp.append(format_metadata_line(key, value, hcp_key_width))

        session_hcp_path = os.path.join(target_path, "session_hcp.txt")
        with open(session_hcp_path, "w") as f:
            # Write sections with blank lines between
            f.write("\n".join(section1_hcp) + "\n")
            f.write("\n")
            f.write("\n".join(section2_hcp) + "\n")
            if section3_hcp:
                f.write("\n")
                f.write("\n".join(section3_hcp) + "\n")
            if hcp_sequence_lines:
                f.write("\n")
                f.write("\n".join(hcp_sequence_lines) + "\n")

        log.step(f"Created {session_hcp_path}")

    # Write session.txt if we have txt sequences or metadata
    if txt_sequence_lines or txt_metadata.get("additional"):
        # Section 3: Additional metadata for TXT file (preserve order)
        section3_txt = []
        for key, value in txt_metadata.get("additional", []):
            section3_txt.append(format_metadata_line(key, value, txt_key_width))

        session_txt_path = os.path.join(target_path, "session.txt")
        with open(session_txt_path, "w") as f:
            # Write sections with blank lines between
            f.write("\n".join(section1_txt) + "\n")
            f.write("\n")
            f.write("\n".join(section2_txt) + "\n")
            if section3_txt:
                f.write("\n")
                f.write("\n".join(section3_txt) + "\n")
            if txt_sequence_lines:
                f.write("\n")
                f.write("\n".join(txt_sequence_lines) + "\n")

        log.step(f"Created {session_txt_path}")
    elif not hcp_sequence_lines:
        # If we have no sequences at all, still create session.txt
        session_txt_path = os.path.join(target_path, "session.txt")
        with open(session_txt_path, "w") as f:
            f.write("\n".join(section1_txt) + "\n")
            f.write("\n")
            f.write("\n".join(section2_txt) + "\n")

        log.step(f"Created {session_txt_path}")

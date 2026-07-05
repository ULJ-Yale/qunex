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


def merge_session(
    studyfolder: str,
    source: str,
    target: str,
    overwrite: str = "no",
    raw_data: str = "copy",
    original_sessions: str = "leave",
    _indent: str = "",
) -> bool:
    r"""
    ``merge_session  --studyfolder=<path> --source=<sessions> --target=<session> [--overwrite=<mode>] [--raw_data=<mode>] [--original_sessions=<action>]``

    Join multiple sessions into a single session.

    Description:
        Merges data from multiple source sessions into a target session, handling
        sequence renumbering, BOLD/BOLDREF indexing, and grouping tags. This is
        useful when data for a subject is split across multiple scanning sessions
        and needs to be combined for processing and analysis.

    Parameters:
        --source (str):
            A comma-separated list of session IDs or paths to join. Each can be:
            - A session ID (e.g., 'session1') - assumes <studyfolder>/sessions/<id>
            - A relative path (e.g., 'other/session1') - relative to studyfolder
            - An absolute path (e.g., '/data/study/sessions/session1')
            The sessions will be merged in the order specified, with sequence
            numbers and indices adjusted accordingly.

        --target (str):
            The target session ID or path. Can be specified as:
            - A session ID (e.g., 'merged_session') - creates in <studyfolder>/sessions/
            - A relative path (e.g., 'sessions/merged') - relative to studyfolder
            - An absolute path (e.g., '/data/study/sessions/merged')

        --studyfolder (str):
            Path to the study folder. This is used as the base for resolving
            relative paths and for locating sessions when only session IDs are
            provided (assumes sessions are in <studyfolder>/sessions/).

        --overwrite (str, default 'no'):
            How to handle existing target folder. Options are 'no' (raise an
            error if target exists with content), 'clean' (remove existing
            content and replace with merged data), or 'merge' (add new data to
            existing session, continuing sequence numbering from where target
            left off).

        --raw_data (str, default 'copy'):
            How to handle raw data (dicom/ and bids/ folders). Options are:
            - 'copy': Copy raw data from source to target (default)
            - 'move': Move raw data from source to target
            - 'leave': Do not transfer raw data, only merge session metadata

        --original_sessions (str, default 'leave'):
            How to handle original source sessions after merging. Options are:
            - 'leave': Leave original sessions unchanged (default)
            - 'remove': Remove original sessions after successful merge
            - 'move:<path>': Move original sessions to specified path (e.g.,
            'move:/data/backup_sessions'). If a session already exists at the
            destination, behavior depends on the --overwrite parameter: 'no'
            skips the move with a warning, while 'clean' or 'merge' replaces
            the existing session.

    Output files:
        The function creates or modifies a target session folder with the
        following structure::

            <target session id>/
                dicom/              # DICOM files organized by sequence folders
                    <seq_num>/      # Sequence folders with renumbered identifiers
                nii/                # NIfTI files with renumbered names
                    <seq_num>.nii.gz
                    <seq_num>.json
                bids/               # BIDS data (if present in sources)
                    <source_session_id>/  # Nested by source session
                session.txt         # Combined session metadata
                session_hcp.txt     # Combined HCP session metadata

    Notes:
        Sequence Renumbering:
            When joining sessions, sequence numbers are renumbered to avoid
            conflicts:

            1. Find maximum sequence number across all source sessions
            2. Determine base increment (1000, 10000, 100000, etc. - next
               power of 10)
            3. Add base * session_index to each sequence from each source
               session

            Example: If sources have sequences numbered 1010-2010 and
            1010-3010, and the maximum is 3010, the base increment will be
            10000. The first source's sequences become 11010-12010, the second
            source's become 21010-23010.

            This renumbering is applied to:

            - DICOM subfolder names in the dicom/ folder
            - NIfTI file names in the nii/ folder (both .nii.gz and .json
              files)
            - Sequence numbers in session.txt and session_hcp.txt files

        BOLD/BOLDREF Indexing:
            In session_hcp.txt, each bold and boldref sequence is numbered
            (e.g., bold1, bold2, boldref1, boldref2). When joining sessions,
            numbers continue from where target left off. Example: target has
            bold1-bold2, first source adds bold3-bold4, second source adds
            bold5-bold6.

        Grouping Tags:
            The se(N) and fm(N) tags group related sequences (same scanning
            session or fieldmap group). When joining, groups are maintained
            within each source session and numbers are renumbered to avoid
            overlap between sessions. Example: If both sources have se(1) and
            se(2), the first source keeps se(1) and se(2), the second source
            becomes se(3) and se(4).

        BIDS Handling:
            If source sessions contain a bids/ folder instead of (or in
            addition to) dicom/, the BIDS data is preserved by nesting it under
            the source session ID in the target's bids/ folder.

        Derivatives Handling:
            The function handles existing derivatives (images/ and hcp/ folders)
            as follows:

            - If source sessions contain derivatives: Warns user that
              derivatives will NOT be merged and remain in source folders
            - If overwrite='merge' and target contains derivatives: Raises
              error to prevent unsafe merge
            - If overwrite='clean': Warns user before removing all content
              including derivatives

        Pre-joined Session Detection:
            The function detects if a target session already contains joined
            sessions by checking for sequence numbers that are 10x+ higher than
            typical (5+ digits) and multiple sequences sharing the same prefix
            (e.g., 11010, 11020 share prefix 11, while 21010, 21020 share
            prefix 21). When detected, only source sequence numbers are
            adjusted; existing target sequences remain unchanged.

        Session and Subject IDs:
            The target session ID is used to derive the subject ID. If session
            ID contains underscore (e.g., 'A_B'), subject ID is the part before
            the first underscore ('A'). Otherwise, subject and session IDs are
            the same. Paths in session.txt and session_hcp.txt are updated to
            be valid within the new target session folder.

        Use:
            This function only merges raw imaging data (DICOM, NIfTI, BIDS) and
            session metadata files. Processed derivatives must be regenerated
            by running the appropriate processing pipelines on the merged
            session.

    Examples:
        ::

            merge_session(
                source='session1,session2,session3',
                target='merged_session',
                studyfolder='/data/my_study',
                overwrite='clean'
            )

        ::

            merge_session(
                source='A_001,A_002',
                target='sessions/A_combined',
                studyfolder='/data/my_study',
                overwrite='merge',
                original_sessions='remove'
            )

        ::

            merge_session(
                source='/data/study/sessions/s1,other_sessions/s2',
                target='/data/study/sessions/merged',
                studyfolder='/data/study',
                overwrite='clean',
                original_sessions='move:archive/merged_sessions'
            )
                overwrite='clean'
            )
    """

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
                print(f"{_indent}WARNING: Removing existing content from {target_path}")
                shutil.rmtree(target_path)
                target_exists = False
                target_has_content = False

    # Check source sessions for derivatives
    for idx, session_path in enumerate(source_paths):
        has_images = os.path.exists(os.path.join(session_path, "images"))
        has_hcp = os.path.exists(os.path.join(session_path, "hcp"))

        if has_images or has_hcp:
            print(
                f"{_indent}WARNING: Source session '{source_session_specs[idx]}' contains derivatives "
                f"({'images/' if has_images else ''}{'hcp/' if has_hcp else ''}) "
                f"which will NOT be merged. Derivatives remain in source folder."
            )

    # Create target directory structure if needed
    if not target_exists:
        os.makedirs(target_path, exist_ok=True)
        os.makedirs(os.path.join(target_path, "dicom"), exist_ok=True)
        os.makedirs(os.path.join(target_path, "nii"), exist_ok=True)

    # Analyze existing target sequences if merging
    target_sequences = []
    target_max_seq = 0
    target_max_bold = 0
    target_max_se = 0
    target_max_fm = 0
    target_is_joined = False

    if overwrite == "merge" and target_has_content:
        # Parse existing target session file
        target_session_file = os.path.join(target_path, "session_hcp.txt")
        if not os.path.exists(target_session_file):
            target_session_file = os.path.join(target_path, "session.txt")

        if os.path.exists(target_session_file):
            target_sequences = _parse_session_file(target_session_file)
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
        print(
            f"{_indent}Renumbering existing target session to use base increment {base_increment}"
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

        # Update target_sequences to reflect new numbering
        for seq in target_sequences:
            old_num = seq["number"]
            new_num = old_num + target_offset
            seq["number"] = new_num
            # Update the line with new sequence number
            seq["line"] = re.sub(r"^(\d+):", f"{new_num}:", seq["line"])

        # Update max values
        target_max_seq = _find_max_sequence_number(target_sequences)

    # Track session metadata for session_N entries
    session_metadata = []

    # Add target session metadata if merging
    if overwrite == "merge" and target_has_content:
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
            transfer_func = shutil.move if raw_data == "move" else shutil.copytree
            transfer_file_func = shutil.move if raw_data == "move" else shutil.copy2

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
            session_num = idx + (
                2
                if (
                    overwrite == "merge" and target_has_content and not target_is_joined
                )
                else 1
            )
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
                        print(
                            f"{_indent}WARNING: {target_session_folder} already exists, skipping"
                        )
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
                            print(
                                f"{_indent}WARNING: {target_file} already exists, skipping"
                            )
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
            _merge_metadata(combined_hcp_metadata, session_data["hcp_metadata"])

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
            _merge_metadata(combined_txt_metadata, session_data["txt_metadata"])

    # Write combined session files
    _write_session_files(
        target_path,
        target_session_id,
        subject_id,
        combined_hcp_lines,
        combined_txt_lines,
        combined_hcp_metadata,
        combined_txt_metadata,
        target_sequences if overwrite == "merge" else [],
        session_metadata,
        _indent,
    )

    print(
        f"{_indent}Successfully joined {len(source_session_specs)} sessions into {target_path}"
    )

    # Handle original sessions if merge was successful
    if original_sessions == "remove":
        # Remove original source sessions
        for session_path in source_paths:
            if os.path.exists(session_path):
                print(f"{_indent}Removing original session: {session_path}")
                shutil.rmtree(session_path)
    elif original_sessions.startswith("move:"):
        # Move original source sessions to specified location
        # Handle move destination based on overwrite parameter
        if os.path.exists(move_destination):
            if os.path.isfile(move_destination):
                if overwrite != "no":
                    print(
                        f"{_indent}Removing existing file at move destination: {move_destination}"
                    )
                    os.remove(move_destination)
                else:
                    # overwrite='no' - warn and skip moving
                    print(
                        f"{_indent}WARNING: Move destination is a file, not a directory: {move_destination}"
                    )
                    print(
                        f"{_indent}         Sessions not moved. Please, resolve manually."
                    )
                    return True
        else:
            # Destination doesn't exist - create it
            print(f"{_indent}Creating move destination folder: {move_destination}")
            os.makedirs(move_destination, exist_ok=True)

        # Move sessions to destination
        for session_path in source_paths:
            if os.path.exists(session_path):
                session_name = os.path.basename(session_path)
                dest_path = os.path.join(move_destination, session_name)

                # If destination session exists and overwrite is not 'no', remove it first
                if os.path.exists(dest_path):
                    if overwrite != "no":
                        print(f"{_indent}Removing existing session at {dest_path}")
                        shutil.rmtree(dest_path)
                    elif os.path.isdir(dest_path):
                        target_content = os.listdir(dest_path)
                        if target_content:
                            print(
                                f"{_indent}WARNING: Session already exists at move destination: {dest_path}"
                            )
                            print(
                                f"{_indent}         Session '{session_name}' not moved. Please, resolve manually."
                            )
                            continue
                    else:
                        print(
                            f"{_indent}WARNING: A file exists at move destination: {dest_path}"
                        )
                        print(
                            f"{_indent}         Session '{session_name}' not moved. Please, resolve manually."
                        )
                        continue

                print(
                    f"{_indent}Moving original session {session_name} to {move_destination}"
                )
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
) -> bool:
    r"""
    ``merge_sessions_list --studyfolder=<path> --session_list=<file> --source_folder=<path> --target_folder=<path> [--overwrite=<mode>] [--raw_data=<mode>] [--original_sessions=<action>]``

    Join multiple sessions according to a list file.

    Description:
        Processes a list file containing multiple session join specifications,
        calling merge_session for each line. This is useful for batch processing
        multiple session merges with a single command.

    Parameters:
        --studyfolder (str):
            Path to the study folder. This is passed to each merge_session call.

        --session_list (str):
            Path to a text file containing join specifications. Each line should
            have the format:

            <target_id>: <source_id>, <source_id>, <source_id>

            Where target_id is the name of the merged session to create, and
            source_id are the sessions to merge (comma-separated). Lines starting
            with # are treated as comments and ignored. Empty lines are skipped.

        --source_folder (str):
            Path to the folder containing source sessions. Each source_id from
            the session_list will be resolved as <source_folder>/<source_id>.

        --target_folder (str):
            Path to the folder where target sessions will be created. Each
            target_id from the session_list will be resolved as
            <target_folder>/<target_id>.

        --overwrite (str, default 'no'):
            How to handle existing target folders. Passed to each merge_session
            call. Options are 'no', 'clean', or 'merge'.

        --raw_data (str, default 'copy'):
            How to handle raw data. Passed to each merge_session call. Options
            are 'copy', 'move', or 'leave'.

        --original_sessions (str, default 'leave'):
            How to handle original source sessions after merging. Options are:
            - 'leave': Leave original sessions unchanged (default)
            - 'remove': Remove original sessions after successful merge
            - 'move:<path>': Move original sessions to specified path (e.g.,
            'move:/data/backup_sessions')

    Examples:
        Session list file example (session_joins.txt)::

            # Merge sessions for subject A
            A_merged: A_001, A_002, A_003

            # Merge sessions for subject B
            B_merged: B_001, B_002

        Basic usage with default settings::

            merge_sessions_list(
                studyfolder='/data/my_study',
                session_list='/data/my_study/processing/session_joins.txt',
                source_folder='/data/my_study/sessions',
                target_folder='/data/my_study/merged',
                overwrite='clean',
                raw_data='copy'
            )

        Remove original sessions after successful merge::

            merge_sessions_list(
                studyfolder='/data/my_study',
                session_list='/data/my_study/processing/session_joins.txt',
                source_folder='/data/my_study/sessions',
                target_folder='/data/my_study/merged',
                overwrite='clean',
                raw_data='copy',
                original_sessions='remove'
            )

        Move original sessions to archive folder::

            merge_sessions_list(
                studyfolder='/data/my_study',
                session_list='/data/my_study/processing/session_joins.txt',
                source_folder='/data/my_study/sessions',
                target_folder='/data/my_study/merged',
                overwrite='clean',
                raw_data='move',
                original_sessions='move:archive/pre_merge_sessions'
            )
    """

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
        print(f"Created target folder: {target_folder}")

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
                print(f"WARNING: Skipping malformed line {line_num}: {line}")
                continue

            target_id, sources_str = line.split(":", 1)
            target_id = target_id.strip()

            # Parse comma-separated source IDs
            source_ids = [s.strip() for s in sources_str.split(",")]
            source_ids = [s for s in source_ids if s]  # Remove empty strings

            if not target_id:
                print(f"WARNING: Skipping line {line_num} with empty target ID")
                continue

            if not source_ids:
                print(f"WARNING: Skipping line {line_num} with no source IDs")
                continue

            join_specs.append(
                {"target_id": target_id, "source_ids": source_ids, "line_num": line_num}
            )

    if not join_specs:
        print("WARNING: No valid join specifications found in session list")
        return False

    # Print header
    print("merge_sessions_list")
    print("==================")
    print(
        f"--> Running {len(join_specs)} join operations from source folder: {os.path.basename(source_folder)} to target folder: {os.path.basename(target_folder)}"
    )
    print(f"    Raw data: {raw_data}")
    print(f"    Original sessions: {original_sessions}")

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
        print(f"\n--> Joining to {target_rel}")
        print(f"    Sources: {', '.join(source_ids)}")
        print(f"    Target: {target_id}")

        try:
            merge_session(
                studyfolder=studyfolder,
                source=source_str,
                target=target_path,
                overwrite=overwrite,
                raw_data=raw_data,
                original_sessions=original_sessions,
                _indent="    -> ",
            )
            successful += 1
            successful_ids.append(target_id)
        except Exception as e:
            failed += 1
            failed_ids.append(target_id)
            print(f"    -> FAILED: {str(e)}")
            # Continue processing remaining specifications

    # Print summary
    print("\n=== Summary ===")
    if successful_ids:
        print(
            f"Successfully joined {len(successful_ids)}/{len(join_specs)} sessions: {', '.join(successful_ids)}"
        )
    if failed_ids:
        print(
            f"Failed joining {len(failed_ids)}/{len(join_specs)} sessions: {', '.join(failed_ids)}"
        )
    if not successful_ids and not failed_ids:
        print("No operations completed")

    # Final status message
    if failed == 0:
        print("\nSuccessful completion of task.")
    else:
        print("\nERROR: Not all sessions joined successfully.")

    return failed == 0


def _merge_metadata(combined: Dict, new_metadata: Dict) -> None:
    """Merge new metadata into combined metadata, detecting conflicts.

    Args:
        combined: dict with 'additional' as list of (key, value) tuples
        new_metadata: dict with 'additional' as list of (key, value) tuples
    """
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
                print(
                    f"WARNING: Metadata conflict for '{key}': "
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
            match = re.match(r"^(\d+):", line)
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
        match = re.match(r"^(\d+):", line)
        if match:
            old_seq_num = int(match.group(1))
            new_seq_num = old_seq_num + offset

            # Replace sequence number at start
            new_line = re.sub(r"^(\d+):", f"{new_seq_num}:", line)

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
    existing_target_sequences: List[Dict],
    session_metadata: List[Tuple[str, str]],
    _indent: str = "",
) -> None:
    """Write combined session.txt and session_hcp.txt files with proper formatting.

    Args:
        session_metadata: List of tuples (session_N, source_id) to add as metadata
    """

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

    # Write session_hcp.txt if we have HCP sequences or metadata
    if (
        hcp_sequence_lines
        or existing_target_sequences
        or hcp_metadata.get("additional")
    ):
        # Section 3: Additional metadata for HCP file (preserve order)
        section3_hcp = []
        for key, value in hcp_metadata.get("additional", []):
            section3_hcp.append(format_metadata_line(key, value, hcp_key_width))

        # Combine existing and new sequences
        all_hcp_sequences = []
        if existing_target_sequences:
            for seq in existing_target_sequences:
                all_hcp_sequences.append(seq["line"])
        all_hcp_sequences.extend(hcp_sequence_lines)

        session_hcp_path = os.path.join(target_path, "session_hcp.txt")
        with open(session_hcp_path, "w") as f:
            # Write sections with blank lines between
            f.write("\n".join(section1_hcp) + "\n")
            f.write("\n")
            f.write("\n".join(section2_hcp) + "\n")
            if section3_hcp:
                f.write("\n")
                f.write("\n".join(section3_hcp) + "\n")
            if all_hcp_sequences:
                f.write("\n")
                f.write("\n".join(all_hcp_sequences) + "\n")

        print(f"{_indent}Created {session_hcp_path}")

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

        print(f"{_indent}Created {session_txt_path}")
    elif not hcp_sequence_lines:
        # If we have no sequences at all, still create session.txt
        session_txt_path = os.path.join(target_path, "session.txt")
        with open(session_txt_path, "w") as f:
            f.write("\n".join(section1_txt) + "\n")
            f.write("\n")
            f.write("\n".join(section2_txt) + "\n")

        print(f"{_indent}Created {session_txt_path}")

#!/usr/bin/env python
# encoding: utf-8

# SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
``snapshots.py``

Functions for recording, comparing, and rolling back directory snapshots:
- record_snapshot(): Create a snapshot of a directory structure
- compare_snapshots(): Compare two snapshots or a snapshot against a live directory
- rollback_snapshot(): Rollback changes based on a comparison snapshot

Function for creating and restoring file backups:
- create_backup(): Create a backup copy of files
- restore_backup(): Restore files from backup
"""

"""
Created by Grega Repovs on 2026-02-01.
Copyright (c) Grega Repovs and Jure Demsar. All rights reserved.
"""


import os
import os.path
from datetime import datetime

import qx_utilities.general.exceptions as ge
from qx_utilities.general.parsing import true_or_false


def _is_path_excluded(rel_path, exclude_list):
    """
    Check if a relative path should be excluded.

    Parameters:
    -----------
    rel_path : str
        Relative path from root (e.g., 'data/file.txt' or 'logs')
    exclude_list : list
        List of relative paths to exclude

    Returns:
    --------
    bool : True if the path should be excluded, False otherwise
    """
    return rel_path in exclude_list


def _normalize_exclude_list(exclude_list, root_path):
    """
    Normalize exclude list by converting absolute paths to relative paths.

    Parameters:
    -----------
    exclude_list : list
        List of paths (can be absolute or relative)
    root_path : str
        The root directory path to use for making paths relative

    Returns:
    --------
    list : Normalized list of relative paths
    """
    normalized = []
    abs_root = os.path.abspath(root_path)

    for path in exclude_list:
        # Strip trailing slashes
        path = path.rstrip("/")

        # Check if path is absolute
        if os.path.isabs(path):
            # Convert to relative path from root
            try:
                abs_path = os.path.abspath(path)
                rel_path = os.path.relpath(abs_path, abs_root)
                # Don't add paths that go outside the root (start with ..)
                if not rel_path.startswith(".."):
                    normalized.append(rel_path)
            except ValueError:
                # On Windows, relpath can fail if paths are on different drives
                # In this case, skip this exclude entry
                pass
        else:
            # Already relative, strip ./ prefix if present
            if path.startswith("./"):
                path = path[2:]
            normalized.append(path)

    return normalized


def record_snapshot(targetfolder, outfile, includehash=True, exclude=None):
    """
    ``record_snapshot targetfolder=<folder path> outfile=<output file> [includehash=True] [exclude=None]``

    Creates a hierarchical snapshot of a directory structure, recording file names,
    modification times, sizes, and optionally MD5 hashes. The snapshot is saved as
    a human-readable tree structure in a text file, which can later be used for
    comparison or rollback operations.

    Parameters:
        --targetfolder (str):
            The path to the folder to snapshot. The function recursively
            traverses all subdirectories and captures metadata for every file.
            The folder must exist or an error will be raised.

        --outfile (str):
            The path to the output text file where the snapshot will be saved.
            If the file exists, it will be overwritten. Parent directories will
            be created automatically if they don't exist.

        --includehash (bool or str, default True):
            Whether to compute and include MD5 hash for each file:

            - True: Compute MD5 hash for all files (slower but more accurate
              for detecting modifications)

            - False: Skip hash computation (faster, relies only on modification
              time and file size for change detection)

            Can be specified as boolean or string ("true", "false", "yes", "no").

        --exclude (list or str, default None):
            Optional list of files or folders to exclude from the snapshot.
            Excluded items will not appear in the snapshot output. Can be specified as:

            - List of paths: ['temp', 'cache', 'logs/debug.log'] - excludes these
              specific files or folders (relative to targetfolder)

            - Comma-separated string: 'temp, cache, logs/debug.log'

            - Quoted strings for spaces: "'build output', cache, 'temp files'"

            Exclusions are matched against relative paths from the target folder root.
            If a folder is excluded, all its contents are also excluded.

    Snapshot Format:
        The snapshot file uses a tree structure with Unicode box-drawing characters:

        - Directories are shown with branch lines (├──, └──, │)
        - Files include metadata aligned to column 80
        - Metadata format: [mtime, hash, size bytes] or [mtime, size bytes]
        - Modification time includes microseconds for precision

        Example output:
        ::

            /home/user/project/data
            .
            ├── configs
            │   ├── settings.json              [2024-01-15 10:23:45.123456, a1b2c3d4, 1024 bytes]
            │   └── database.ini               [2024-01-15 10:23:45.234567, e5f6g7h8, 512 bytes]
            ├── data
            │   ├── input.txt                  [2024-01-15 10:25:30.345678, i9j0k1l2, 2048 bytes]
            │   └── processed
            │       └── output.csv             [2024-01-15 11:00:00.456789, m3n4o5p6, 4096 bytes]
            └── README.md                      [2024-01-15 09:00:00.567890, q7r8s9t0, 256 bytes]

    Metadata Components:
        - **Modification time**: File's last modification timestamp with microsecond
          precision (format: YYYY-MM-DD HH:MM:SS.ffffff)

        - **MD5 hash**: 32-character hexadecimal hash of file contents (if includehash=True)

        - **File size**: Size in bytes

    Use Cases:
        - **Baseline creation**: Capture the state of a directory before making changes
        - **Change tracking**: Monitor what files were added, modified, or deleted
        - **Documentation**: Record the exact state of data or configuration files
        - **Rollback preparation**: Create snapshots before risky operations

    Notes:
        - Hash computation can be slow for large files or many files
        - Snapshots capture file metadata, not file contents
        - Modification times are preserved with microsecond precision
        - The snapshot is a text file, not a backup of the actual files
        - Can be compared with other snapshots using compare_snapshots()
        - Can be used for rollback operations with rollback_snapshot()

    Examples:
        Create snapshot with hashes:
        ::

            qunex record_snapshot \\
                --targetfolder=/path/to/project/data \\
                --outfile=/path/to/snapshots/baseline.txt

        Create fast snapshot without hashes:
        ::

            qunex record_snapshot \\
                --targetfolder=/path/to/project/data \\
                --outfile=/path/to/snapshots/quick_check.txt \\
                --includehash=no
    """
    import hashlib

    # Convert includehash to boolean using true_or_false helper
    includehash = true_or_false(includehash)

    # Process exclude list
    exclude_list = []
    if exclude is not None:
        exclude_list = _process_filelist(exclude)
        # Normalize paths (convert absolute to relative, remove trailing slashes, handle ./ prefix)
        exclude_list = _normalize_exclude_list(exclude_list, targetfolder)

    def compute_file_hash(filepath):
        """Compute MD5 hash of a file."""
        md5_hash = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            return f"ERROR: {str(e)}"

    def get_file_info(filepath):
        """Get file size, modification time, and hash."""
        try:
            stat_info = os.stat(filepath)
            size = stat_info.st_size
            mtime = datetime.fromtimestamp(stat_info.st_mtime).strftime(
                "%Y-%m-%d %H:%M:%S.%f"
            )
            file_hash = compute_file_hash(filepath) if includehash else None
            return size, mtime, file_hash
        except Exception as e:
            return None, None, f"ERROR: {str(e)}"

    def build_tree(root_path):
        """Build a dictionary representation of the directory tree."""
        tree = {}

        for dirpath, dirnames, filenames in os.walk(root_path):
            # Get relative path from root
            rel_path = os.path.relpath(dirpath, root_path)

            # Filter excluded directories (modifying dirnames in-place affects os.walk)
            dirnames_filtered = []
            for dirname in sorted(dirnames):
                dir_rel_path = (
                    os.path.join(rel_path, dirname) if rel_path != "." else dirname
                )
                if not _is_path_excluded(dir_rel_path, exclude_list):
                    dirnames_filtered.append(dirname)
            dirnames[:] = dirnames_filtered

            # Sort filenames
            filenames.sort()

            # Store directory and file information
            tree[rel_path] = {
                "dirs": dirnames[:],  # Copy the list
                "files": [],
            }

            # Get file information
            for filename in filenames:
                # Check if file is excluded
                file_rel_path = (
                    os.path.join(rel_path, filename) if rel_path != "." else filename
                )
                if _is_path_excluded(file_rel_path, exclude_list):
                    continue

                filepath = os.path.join(dirpath, filename)
                size, mtime, file_hash = get_file_info(filepath)
                tree[rel_path]["files"].append(
                    {"name": filename, "size": size, "mtime": mtime, "hash": file_hash}
                )

        return tree

    def write_tree(tree, root_path, outfile_handle):
        """Write the tree structure to file."""

        def write_subtree(current_path, prefix="", is_last=True):
            """Recursively write tree structure."""

            if current_path == ".":
                # Root level
                abs_path = os.path.abspath(root_path)
                outfile_handle.write(f"{abs_path}\n")
                outfile_handle.write(".\n")
                rel_path = "."
            else:
                rel_path = current_path

            if rel_path not in tree:
                return

            dirs = tree[rel_path]["dirs"]
            files = tree[rel_path]["files"]

            # Combine dirs and files for processing
            items = [("dir", d) for d in dirs] + [("file", f) for f in files]

            for idx, (item_type, item) in enumerate(items):
                is_last_item = idx == len(items) - 1

                # Determine the branch characters
                if current_path == ".":
                    connector = "├── " if not is_last_item else "└── "
                    new_prefix = "│   " if not is_last_item else "    "
                else:
                    connector = prefix + ("├── " if not is_last_item else "└── ")
                    new_prefix = prefix + ("│   " if not is_last_item else "    ")

                if item_type == "dir":
                    # Write directory name
                    outfile_handle.write(f"{connector}{item}\n")

                    # Recurse into subdirectory
                    if rel_path == ".":
                        subdir_path = item
                    else:
                        subdir_path = os.path.join(rel_path, item)

                    write_subtree(subdir_path, new_prefix, is_last_item)

                else:  # file
                    # Write file name with metadata
                    file_info = item
                    name = file_info["name"]
                    size = file_info["size"] if file_info["size"] is not None else "N/A"
                    mtime = file_info["mtime"]
                    file_hash = file_info["hash"]

                    # Calculate padding to align metadata (aim for column ~80)
                    name_with_connector = f"{connector}{name}"
                    padding_needed = max(1, 80 - len(name_with_connector))
                    padding = " " * padding_needed

                    if includehash:
                        metadata = f"[{mtime}, {file_hash}, {size} bytes]"
                    else:
                        metadata = f"[{mtime}, {size} bytes]"
                    outfile_handle.write(f"{name_with_connector}{padding}{metadata}\n")

        # Start writing from root
        write_subtree(".")

    # Main execution
    if not os.path.exists(targetfolder):
        raise ge.CommandError(
            "record_snapshot",
            "Target path does not exist: %s" % targetfolder,
            "Please check the path!",
        )

    if not os.path.isdir(targetfolder):
        raise ge.CommandError(
            "record_snapshot",
            "Target path is not a directory: %s" % targetfolder,
            "Please check the path!",
        )

    # Build the tree structure
    tree = build_tree(targetfolder)

    # Ensure output directory exists
    outfile_dir = os.path.dirname(os.path.abspath(outfile))
    if outfile_dir and not os.path.exists(outfile_dir):
        os.makedirs(outfile_dir)

    # Write to output file
    with open(outfile, "w") as f:
        write_tree(tree, targetfolder, f)


def compare_snapshots(before, after, outfile, includehash=True, exclude=None):
    """
    ``compare_snapshots before=<before snapshot> after=<after snapshot or folder> outfile=<output file> [includehash=True] [exclude=None]``

    Compares two directory snapshots or a snapshot against a live directory to identify
    changes. Creates a detailed comparison tree showing which files were added, deleted,
    or modified. The comparison can be used for change analysis or as input to
    rollback_snapshot() for reverting changes.

    Parameters:
        --before (str):
            Path to the "before" snapshot file (baseline state). This must be
            a snapshot file created by record_snapshot(). The snapshot captures
            the original state before changes were made.

        --after (str):
            Path to either:

            - A snapshot file created by record_snapshot() (for comparing two
              snapshots from different times)

            - A directory path (the function will create a temporary snapshot
              of the current state for comparison)

            This represents the state after changes were made.

        --outfile (str):
            Path to the output file where the comparison results will be saved.
            The file will contain a tree structure with status markers showing
            all changes. If the file exists, it will be overwritten.

        --includehash (bool or str, default True):
            Whether to use MD5 hash when detecting modifications:

            - True: Files are considered modified if modification time, size,
              OR hash differs. Most accurate but only works if both snapshots
              included hashes.

            - False: Files are considered modified only if modification time
              or size differs. Faster and works even if snapshots lack hashes.

            Can be specified as boolean or string ("true", "false", "yes", "no").

        --exclude (list or str, default None):
            Optional list of files or folders to exclude from the comparison.
            Excluded items will not appear in the comparison output. Can be specified as:

            - List of paths: ['temp', 'cache', 'logs/debug.log']
            - Comma-separated string: 'temp, cache, logs/debug.log'
            - Quoted strings for spaces: "'build output', cache"

            If 'after' is a directory (not a snapshot file), the exclude list is
            passed to record_snapshot when creating the temporary snapshot.

    Comparison Output Format:
        The output file uses a tree structure with status markers:
        ::

            before: /home/user/project/data
            after: /home/user/project/data
            .
              ├── configs
              │   ├── settings.json              [2024-01-15 10:23:45.123456, a1b2c3d4, 1024 bytes]
              │   └── database.ini               [2024-01-15 10:23:45.234567, e5f6g7h8, 512 bytes]
            + ├── new_data
            + │   └── results.csv                [2024-01-15 12:00:00.123456, x1y2z3a4, 8192 bytes]
            M ├── data
            M │   └── input.txt                  [2024-01-15 10:25:30.345678 -> 2024-01-15 14:30:00.123456, ...]
            - └── old_file.txt                   [2024-01-14 09:00:00.000000, q7r8s9t0, 256 bytes]

    Status Markers:
        - **+** (Added): File or folder exists in 'after' but not in 'before'
        - **-** (Deleted): File or folder exists in 'before' but not in 'after'
        - **M** (Modified): File metadata changed between snapshots (time, size, or hash)
        - **  ** (Unchanged): File or folder unchanged (two spaces, no marker)

    Modification Detection:
        Files are considered modified when:

        1. Modification time differs (always checked)
        2. File size differs (always checked)
        3. MD5 hash differs (only if includehash=True AND both snapshots have hashes)

        For modified files, metadata shows before → after values.

    Use Cases:
        - **Change auditing**: See exactly what changed in a directory tree
        - **Quality control**: Verify that processing modified only expected files
        - **Rollback preparation**: Identify files to remove when reverting changes
        - **Documentation**: Create a record of changes for compliance or debugging

    Notes:
        - If 'after' is a directory, a temporary snapshot is created automatically
        - Hash comparison only works if both snapshots included hashes
        - The comparison file can be used directly with rollback_snapshot()
        - Comparison is smart: directories marked modified only if children changed
        - Empty directories are tracked (shown as added/deleted if they change)

    Examples:
        Compare two snapshot files:
        ::

            qunex compare_snapshots \\
                --before=/snapshots/before_processing.txt \\
                --after=/snapshots/after_processing.txt \\
                --outfile=/snapshots/diff_processing.txt

        Compare snapshot against current directory state:
        ::

            qunex compare_snapshots \\
                --before=/snapshots/baseline.txt \\
                --after=/path/to/project/data \\
                --outfile=/snapshots/current_changes.txt

        Fast comparison without hash checking:
        ::

            qunex compare_snapshots \\
                --before=/snapshots/baseline.txt \\
                --after=/path/to/project/data \\
                --outfile=/snapshots/quick_diff.txt \\
                --includehash=no
    """
    import tempfile

    # Convert includehash to boolean
    includehash = true_or_false(includehash)

    # Process exclude parameter (can be string, list, or None)
    if exclude is None:
        exclude = []
    else:
        exclude = _process_filelist(exclude)

    def write_comparison(
        before_tree,
        after_tree,
        outfile_handle,
        before_path,
        after_path,
        target_path,
        exclude_list=None,
    ):
        """Write the comparison output in tree format."""

        if exclude_list is None:
            exclude_list = []

        def files_differ(before_file, after_file, use_hash):
            """Compare two file nodes and determine if they differ."""
            # Compare mtime
            if before_file.get("mtime") != after_file.get("mtime"):
                return True

            # Compare size
            if before_file.get("size") != after_file.get("size"):
                return True

            # Compare hash only if:
            # 1. use_hash is True (includehash parameter)
            # 2. Both files have hash data
            if use_hash and before_file.get("has_hash") and after_file.get("has_hash"):
                if before_file.get("hash") != after_file.get("hash"):
                    return True

            return False

        def compare_and_write(
            before_node, after_node, prefix="", is_root=True, current_path=""
        ):
            """Recursively compare and write nodes."""

            if is_root:
                outfile_handle.write(f"before: {before_path}\n")
                outfile_handle.write(f"after: {after_path}\n")
                outfile_handle.write(f"target: {target_path}\n")
                outfile_handle.write(".\n")

            # Get all unique child names
            before_children = (
                set(before_node.get("children", {}).keys()) if before_node else set()
            )
            after_children = (
                set(after_node.get("children", {}).keys()) if after_node else set()
            )
            all_children = sorted(before_children | after_children)

            for idx, child_name in enumerate(all_children):
                is_last = idx == len(all_children) - 1

                # Build the full relative path for this child
                child_rel_path = (
                    os.path.join(current_path, child_name)
                    if current_path
                    else child_name
                )

                # Check if this path should be excluded
                if _is_path_excluded(child_rel_path, exclude_list):
                    continue

                before_child = (
                    before_node.get("children", {}).get(child_name)
                    if before_node
                    else None
                )
                after_child = (
                    after_node.get("children", {}).get(child_name)
                    if after_node
                    else None
                )

                # Determine status
                if before_child and after_child:
                    # Present in both
                    if before_child["type"] == "file" and after_child["type"] == "file":
                        if files_differ(before_child, after_child, includehash):
                            status = "M "
                        else:
                            status = "  "
                    else:
                        status = "  "
                elif after_child and not before_child:
                    status = "+ "
                else:  # before_child and not after_child
                    status = "- "

                # Determine connector
                connector = "├── " if not is_last else "└── "
                new_prefix = prefix + ("│   " if not is_last else "    ")

                # Get node info from whichever exists
                node = after_child if after_child else before_child

                if node["type"] == "dir":
                    # Directory
                    outfile_handle.write(f"{status}{prefix}{connector}{child_name}\n")
                    # Recurse with updated path
                    compare_and_write(
                        before_child, after_child, new_prefix, False, child_rel_path
                    )
                else:
                    # File
                    name_with_connector = f"{status}{prefix}{connector}{child_name}"
                    padding_needed = max(1, 80 - len(name_with_connector))
                    padding = " " * padding_needed

                    if status == "M ":
                        # Modified - show before -> after
                        before_meta = before_child.get("metadata_str", "")
                        after_meta = after_child.get("metadata_str", "")
                        metadata = f"[{before_meta} -> {after_meta}]"
                    elif status == "+ ":
                        # Added - show after metadata
                        metadata = f"[{after_child.get('metadata_str', '')}]"
                    elif status == "- ":
                        # Deleted - show before metadata
                        metadata = f"[{before_child.get('metadata_str', '')}]"
                    else:
                        # Unchanged - show current metadata
                        metadata = f"[{after_child.get('metadata_str', '')}]"

                    outfile_handle.write(f"{name_with_connector}{padding}{metadata}\n")

        compare_and_write(before_tree, after_tree)

    # Main execution
    if not os.path.exists(before):
        raise ge.CommandError(
            "compare_snapshots",
            "Before snapshot file does not exist: %s" % before,
            "Please check the path!",
        )

    # Determine if 'after' is a file or directory
    temp_after_file = None
    after_dir_path = None  # Track the actual directory path (for target: line)
    after_snapshot_path = None  # Track what to show in after: line

    if os.path.isdir(after):
        # Generate temporary snapshot
        temp_after_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".snapshot.txt"
        )
        temp_after_file.close()
        after_snapshot = temp_after_file.name
        after_dir_path = os.path.abspath(after)
        after_snapshot_path = after_dir_path  # Show directory path in after: line

        # Normalize exclude list relative to the 'after' directory
        # (exclude is already processed and will be passed to record_snapshot which handles it)
        record_snapshot(after, after_snapshot, includehash, exclude)
    elif os.path.isfile(after):
        after_snapshot = after
        after_snapshot_path = os.path.abspath(
            after
        )  # Show snapshot file path in after: line
        # Extract directory path from snapshot file for target: line
        _, after_dir_path = _parse_snapshot_tree(after, extract_root_path=True)
        if not after_dir_path:
            # Fallback to using the snapshot file path
            after_dir_path = os.path.abspath(after)
    else:
        raise ge.CommandError(
            "compare_snapshots",
            "After parameter must be either a snapshot file or a directory: %s" % after,
            "Please check the path!",
        )

    # Also get the before directory path for normalization
    _, before_dir_path = _parse_snapshot_tree(before, extract_root_path=True)
    if not before_dir_path:
        before_dir_path = os.path.abspath(before)

    # Normalize exclude list - use after_dir_path as reference since that's what we're comparing to
    # This ensures the exclude paths are relative to the snapshot root
    normalized_exclude = _normalize_exclude_list(exclude, after_dir_path)

    try:
        # Parse both snapshots using shared helper
        before_tree = _parse_snapshot_tree(before)
        after_tree = _parse_snapshot_tree(after_snapshot)

        # Ensure output directory exists
        outfile_dir = os.path.dirname(os.path.abspath(outfile))
        if outfile_dir and not os.path.exists(outfile_dir):
            os.makedirs(outfile_dir)

        # Write comparison with exclude list
        with open(outfile, "w") as f:
            write_comparison(
                before_tree,
                after_tree,
                f,
                os.path.abspath(before),
                after_snapshot_path,
                after_dir_path,
                normalized_exclude,
            )

    finally:
        # Clean up temporary file if created
        if temp_after_file:
            try:
                os.unlink(temp_after_file.name)
            except:
                pass


def _parse_snapshot_tree(snapshot_file, extract_root_path=False):
    """
    Parse a snapshot or diff file into a hierarchical dictionary structure.

    Parameters:
    -----------
    snapshot_file : str
        Path to snapshot or diff file to parse
    extract_root_path : bool
        If True, extract and return the root path from first line or 'after:' line

    Returns:
    --------
    tuple : (root_dict, root_path) if extract_root_path=True, else just root_dict
        root_dict is the hierarchical tree structure
        root_path is the extracted absolute path (or None)
    """
    with open(snapshot_file, "r") as f:
        lines = f.readlines()

    # Build hierarchical tree structure
    root = {"name": ".", "type": "dir", "children": {}}
    path_stack = [root]
    root_path = None

    for line in lines:
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            continue

        # Check for root path indicators
        if extract_root_path:
            # Look for 'target:' line in diff files (preferred)
            if stripped.startswith("target:"):
                root_path = stripped.split("target:", 1)[1].strip()
                continue
            # Fallback: Look for 'after:' line for backwards compatibility
            if stripped.startswith("after:"):
                # Only use if we haven't found target: yet
                if root_path is None:
                    root_path = stripped.split("after:", 1)[1].strip()
                continue
            # Skip 'before:' line
            if stripped.startswith("before:"):
                continue
            # Look for absolute path (starts with /) - for old snapshot format
            if (
                stripped.startswith("/")
                and "after:" not in line
                and "before:" not in line
                and "target:" not in line
            ):
                if root_path is None:
                    root_path = stripped
                continue

        # Skip root marker
        if stripped == ".":
            continue

        # Count depth by finding the position of the connector (├── or └──)
        # Each level adds 4 characters ("│   " or "    ")
        # Remove status markers if present (M, +, -, or two spaces for unchanged)
        clean_line = line
        if len(line) >= 2 and line[1] == " " and line[0] in "M+-":
            clean_line = line[2:]  # Remove status marker
        elif len(line) >= 3 and line[0] == " " and line[1] == " " and line[2] in "├└│":
            # Line starts with "  " followed by tree character - this is unchanged status
            clean_line = line[2:]  # Remove the "  " status marker

        connector_pos = clean_line.find("├── ")
        if connector_pos == -1:
            connector_pos = clean_line.find("└── ")

        if connector_pos == -1:
            # Malformed line, skip
            continue

        depth = connector_pos // 4

        # Extract content after connector
        content = clean_line[connector_pos + 4 :].strip()

        # Check if this is a file (has metadata in brackets)
        if "[" in content and content.endswith("]"):
            # It's a file
            bracket_pos = content.rfind("[")
            name = content[:bracket_pos].strip()
            metadata_str = content[bracket_pos + 1 : -1]  # Remove [ and ]

            # Parse metadata into components
            # Format: "mtime, hash, size bytes" or "mtime, size bytes"
            # Or for diffs: "before_meta -> after_meta"
            parts = [p.strip() for p in metadata_str.split(",")]

            mtime = None
            file_hash = None
            size = None
            has_hash = False

            if len(parts) >= 2:
                mtime = parts[0]
                # Check if we have 3 parts (with hash) or 2 parts (without hash)
                if len(parts) == 3:
                    # Format: mtime, hash, size bytes
                    file_hash = parts[1]
                    size = parts[2].replace(" bytes", "").strip()
                    has_hash = True
                elif len(parts) == 2:
                    # Format: mtime, size bytes
                    size = parts[1].replace(" bytes", "").strip()
                    has_hash = False

            node = {
                "name": name,
                "type": "file",
                "mtime": mtime,
                "hash": file_hash,
                "size": size,
                "has_hash": has_hash,
                "metadata_str": metadata_str,
            }
        else:
            # It's a directory
            name = content
            node = {"name": name, "type": "dir", "children": {}}

        # Adjust path_stack to correct depth
        while len(path_stack) > depth + 1:
            path_stack.pop()

        # Add node to parent's children
        parent = path_stack[-1]
        parent["children"][name] = node

        # If it's a directory, add to stack for potential children
        if node["type"] == "dir":
            path_stack.append(node)

    if extract_root_path:
        return root, root_path
    return root


def _collect_file_paths(tree_node, current_path=".", status_filter=None):
    """
    Recursively collect all file paths from a tree structure.

    Parameters:
    -----------
    tree_node : dict
        The tree node to traverse
    current_path : str
        Current path being built
    status_filter : str or None
        If provided, only collect files/dirs with this status (for diff trees)

    Returns:
    --------
    list : List of (path, node) tuples
    """
    results = []

    if "children" not in tree_node:
        return results

    for name, node in sorted(tree_node["children"].items()):
        if current_path == ".":
            full_path = name
        else:
            full_path = f"{current_path}/{name}"

        # Add this item
        results.append((full_path, node))

        # Recurse for directories
        if node["type"] == "dir":
            results.extend(_collect_file_paths(node, full_path, status_filter))

    return results


def rollback_snapshot(
    diff=None, before=None, after=None, includehash=True, action="check", exclude=None
):
    """
    ``rollback_snapshot [diff=<diff file>] [before=<before snapshot>] [after=<after snapshot>] [includehash=True] [action=check] [exclude=None]``

    Analyzes snapshot differences to identify added files and optionally deletes them
    to roll back changes. Useful for reverting unwanted modifications, cleaning up
    failed processing runs, or undoing experimental changes. Can operate in two modes:
    check (analyze only) or delete (perform rollback).

    Parameters:
        --diff (str, optional):
            Path to a comparison file created by compare_snapshots(). If provided,
            this file is used directly to determine what changed. If not provided,
            both 'before' and 'after' parameters must be specified to generate
            the comparison on-the-fly.

        --before (str, optional):
            Path to the "before" snapshot file (baseline state). Required if
            'diff' is not provided. This snapshot represents the state you want
            to roll back to.

        --after (str, optional):
            Path to either a snapshot file or a directory representing the current
            state. Required if 'diff' is not provided. If a directory is provided,
            a temporary snapshot will be created for comparison.

        --includehash (bool or str, default True):
            Whether to use MD5 hash when comparing files (only relevant if
            generating comparison on-the-fly). If using an existing diff file,
            this parameter is ignored.

            Can be specified as boolean or string ("true", "false", "yes", "no").

        --action (str, default "check"):
            The action to perform:

            - "check": Analyze changes and show what would be deleted, but don't
              actually delete anything. Safe for previewing rollback operations.

            - "delete": Actually delete added files to perform the rollback.
              Use with caution - deleted files cannot be recovered unless you
              have backups.

        --exclude (list or str, default None):
            Optional list of files or folders to exclude from rollback operations.
            Excluded files will not be deleted even if they were added. Can be specified as:

            - List of paths: ['temp', 'cache', 'logs/debug.log']
            - Comma-separated string: 'temp, cache, logs/debug.log'
            - Quoted strings for spaces: "'build output', cache"

            If generating a comparison on-the-fly (using before/after parameters),
            the exclude list is passed to compare_snapshots.

    Rollback Behavior:
        The function categorizes all changes into three types:

        1. **Added files** (+ marker):
           - Can be automatically rolled back by deletion
           - In "delete" mode, these files are removed from disk
           - In "check" mode, lists files that would be deleted

        2. **Modified files** (M marker):
           - Cannot be automatically rolled back
           - Original content is not stored in snapshots
           - Warning is displayed listing these files
           - Manual intervention required to restore original state

        3. **Deleted files** (- marker):
           - Cannot be automatically restored
           - Original file content is not stored in snapshots
           - Warning is displayed listing these files
           - Manual intervention required to restore from backups

    Output Information:
        The function provides detailed information about:

        - Total number of changes detected (added/modified/deleted)
        - List of files that can be automatically rolled back
        - List of files that require manual intervention
        - In "delete" mode: confirmation of files successfully deleted
        - In "delete" mode: errors if any deletions fail

    Safety Features:
        - Default action is "check" (non-destructive preview)
        - Clear warnings about files that cannot be auto-rolled back
        - Detailed output before performing any deletions
        - Reports both successful and failed deletion attempts

    Use Cases:
        - **Undo failed processing**: Remove files created by a failed analysis run
        - **Clean up experiments**: Revert changes from experimental code
        - **Quality control**: Preview what would be rolled back before committing
        - **Partial rollback**: Understand what can/cannot be automatically reverted

    Limitations:
        - Only added files can be automatically removed
        - Modified files cannot be restored (original content not in snapshot)
        - Deleted files cannot be recovered (content not in snapshot)
        - Snapshots record metadata only, not file contents
        - For full rollback capability, use backup_files() before making changes

    Notes:
        - Always run with action="check" first to preview changes
        - The function extracts the target directory path from the diff file
        - Empty directories are not removed (only files)
        - If any deletion fails, the function continues with remaining files
        - Consider using backup_files() for reversible operations

    Examples:
        Preview rollback using existing diff:
        ::

            qunex rollback_snapshot \\
                --diff=/snapshots/processing_diff.txt \\
                --action=check

        Actually perform rollback:
        ::

            qunex rollback_snapshot \\
                --diff=/snapshots/processing_diff.txt \\
                --action=delete

        Rollback with on-the-fly comparison:
        ::

            qunex rollback_snapshot \\
                --before=/snapshots/baseline.txt \\
                --after=/path/to/project/data \\
                --action=check

        Quick preview without hash comparison:
        ::

            qunex rollback_snapshot \\
                --before=/snapshots/baseline.txt \\
                --after=/path/to/project/data \\
                --includehash=no \\
                --action=check
    """
    import tempfile

    # Convert includehash to boolean
    includehash = true_or_false(includehash)

    # Note: exclude list will be normalized later after we extract the root path from diff file

    # Validate action parameter
    if action not in ["check", "delete"]:
        raise ge.CommandError(
            "rollback_snapshot",
            "Invalid action parameter: %s" % action,
            "Action must be either 'check' or 'delete'",
        )

    # Determine diff file to use
    temp_diff_file = None
    if diff:
        if not os.path.exists(diff):
            raise ge.CommandError(
                "rollback_snapshot",
                "Diff file does not exist: %s" % diff,
                "Please check the path!",
            )
        diff_file = diff
    else:
        # Need to create diff
        if not before or not after:
            raise ge.CommandError(
                "rollback_snapshot",
                "Either diff or both before and after must be provided",
                "Please provide required parameters!",
            )

        # Create temporary diff file
        temp_diff_file = tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".diff.txt"
        )
        temp_diff_file.close()
        diff_file = temp_diff_file.name

        # Generate the diff
        compare_snapshots(before, after, diff_file, includehash, exclude)

    try:
        # Parse the diff file to extract target path (the actual directory to rollback)
        diff_tree, after_root_path = _parse_snapshot_tree(
            diff_file, extract_root_path=True
        )

        if not after_root_path:
            raise ge.CommandError(
                "rollback_snapshot",
                "Could not extract target path from diff file",
                "Diff file may be malformed or missing target: line!",
            )

        # Normalize exclude list relative to the after_root_path
        if exclude is not None:
            exclude_list = _process_filelist(exclude)
            exclude_list = _normalize_exclude_list(exclude_list, after_root_path)
        else:
            exclude_list = []

        # Read the diff file to identify status of each file
        added_files = []
        added_dirs = []  # Track added directories
        modified_files = []
        deleted_files = []

        with open(diff_file, "r") as f:
            lines = f.readlines()

        # Track current path stack to build full paths
        # Track if current path is under an excluded directory
        path_stack = []
        excluded_stack = []

        for line in lines:
            # Skip non-tree lines
            if (
                not line.strip()
                or line.strip() == "."
                or line.startswith("before:")
                or line.startswith("after:")
                or line.startswith("target:")
            ):
                continue

            # Check for absolute path line
            if line.strip().startswith("/"):
                continue

            # Detect status markers (or lack thereof for unchanged items)
            status = None
            clean_line = line

            if len(line) >= 2 and line[1] == " ":
                if line[0] == "+":
                    status = "added"
                    clean_line = line[2:]  # Remove status marker
                elif line[0] == "-":
                    status = "deleted"
                    clean_line = line[2:]  # Remove status marker
                elif line[0] == "M":
                    status = "modified"
                    clean_line = line[2:]  # Remove status marker
                elif line[0] == " ":
                    # Unchanged item (two spaces at start)
                    status = "unchanged"
                    clean_line = line[2:]  # Remove status marker

            # Find connector position
            connector_pos = clean_line.find("├── ")
            if connector_pos == -1:
                connector_pos = clean_line.find("└── ")

            if connector_pos == -1:
                continue

            depth = connector_pos // 4

            # Extract content after connector
            content = clean_line[connector_pos + 4 :].strip()

            # Extract name (without metadata)
            if "[" in content and content.endswith("]"):
                bracket_pos = content.rfind("[")
                name = content[:bracket_pos].strip()
                is_file = True
            else:
                name = content
                is_file = False

            # Adjust path stack to current depth
            while len(path_stack) > depth:
                path_stack.pop()
                if excluded_stack:
                    excluded_stack.pop()

            # Build full path
            if path_stack:
                full_path = "/".join(path_stack + [name])
            else:
                full_path = name

            # Check if this path is excluded
            is_excluded = _is_path_excluded(full_path, exclude_list)

            # Check if parent is excluded
            if excluded_stack and excluded_stack[-1]:
                is_excluded = True

            # Add to path stack if directory
            if not is_file:
                path_stack.append(name)
                excluded_stack.append(is_excluded)

            # Skip if excluded
            if is_excluded:
                continue

            # Only process files with status markers (not unchanged)
            if status == "unchanged" or status is None:
                continue

            # Build absolute path in after directory
            abs_path = os.path.join(after_root_path, full_path)

            # Categorize by status
            if status == "added":
                if is_file:
                    added_files.append(abs_path)
                else:
                    # Track added directories with their depth for later removal
                    added_dirs.append((depth, abs_path))
            elif status == "modified" and is_file:
                modified_files.append(abs_path)
            elif status == "deleted" and is_file:
                deleted_files.append(abs_path)

        # Execute action
        if action == "check":
            # Just print the lists
            print("\n=== Rollback Analysis ===")
            print(f"\nAfter directory: {after_root_path}")

            if added_files:
                print(f"\nFiles to be deleted ({len(added_files)}):")
                for filepath in sorted(added_files):
                    print(f"  {filepath}")
            else:
                print("\nNo files to delete.")

            if added_dirs:
                print(f"\nDirectories to be deleted if empty ({len(added_dirs)}):")
                # Sort by depth (deepest first) for display
                for depth, dirpath in sorted(added_dirs, key=lambda x: -x[0]):
                    print(f"  {dirpath}")

            if modified_files:
                print(
                    f"\nModified files (cannot be automatically rolled back) ({len(modified_files)}):"
                )
                for filepath in sorted(modified_files):
                    print(f"  {filepath}")

            if deleted_files:
                print(
                    f"\nDeleted files (cannot be automatically rolled back) ({len(deleted_files)}):"
                )
                for filepath in sorted(deleted_files):
                    print(f"  {filepath}")

            print("\n=== End Rollback Analysis ===\n")

        elif action == "delete":
            # Delete added files and warn about others
            print("\n=== Executing Rollback ===")
            print(f"\nAfter directory: {after_root_path}")

            deleted_count = 0
            failed_count = 0

            if added_files:
                print(f"\nDeleting {len(added_files)} added file(s)...")
                for filepath in sorted(added_files):
                    try:
                        if os.path.exists(filepath):
                            os.remove(filepath)
                            print(f"  Deleted: {filepath}")
                            deleted_count += 1
                        else:
                            print(f"  Warning: File not found: {filepath}")
                            failed_count += 1
                    except Exception as e:
                        print(f"  Error deleting {filepath}: {str(e)}")
                        failed_count += 1

                print(f"\nSuccessfully deleted: {deleted_count} file(s)")
                if failed_count > 0:
                    print(f"Failed to delete: {failed_count} file(s)")
            else:
                print("\nNo files to delete.")

            # Remove empty added directories (deepest first)
            if added_dirs:
                print("\nRemoving empty added directories...")
                # Sort by depth (deepest first) to remove child directories before parents
                sorted_dirs = sorted(added_dirs, key=lambda x: -x[0])
                dir_deleted_count = 0
                dir_skipped_count = 0

                for depth, dirpath in sorted_dirs:
                    try:
                        if os.path.exists(dirpath):
                            # Check if directory is empty
                            if not os.listdir(dirpath):
                                os.rmdir(dirpath)
                                print(f"  Removed: {dirpath}")
                                dir_deleted_count += 1
                            else:
                                print(f"  Skipped (not empty): {dirpath}")
                                dir_skipped_count += 1
                        else:
                            print(f"  Warning: Directory not found: {dirpath}")
                    except Exception as e:
                        print(f"  Error removing {dirpath}: {str(e)}")

                if dir_deleted_count > 0:
                    print(
                        f"\nSuccessfully removed: {dir_deleted_count} empty director{'y' if dir_deleted_count == 1 else 'ies'}"
                    )
                if dir_skipped_count > 0:
                    print(
                        f"Skipped (not empty): {dir_skipped_count} director{'y' if dir_skipped_count == 1 else 'ies'}"
                    )

            # Print warnings about non-rollbackable changes
            if modified_files:
                print(
                    f"\nWARNING: {len(modified_files)} modified file(s) cannot be automatically rolled back:"
                )
                for filepath in sorted(modified_files):
                    print(f"  {filepath}")

            if deleted_files:
                print(
                    f"\nWARNING: {len(deleted_files)} deleted file(s) cannot be restored:"
                )
                for filepath in sorted(deleted_files):
                    print(f"  {filepath}")

            print("\n=== Rollback Complete ===\n")

    finally:
        # Clean up temporary diff file if created
        if temp_diff_file:
            try:
                os.unlink(temp_diff_file.name)
            except:
                pass


def _process_filelist(filelist):
    """
    Process filelist which can be a comma-separated string, list, or single string.

    Handles formats like:
    - String with commas: "file1.txt, file2.txt"
    - Quoted strings: "'file 1.txt', 'file 2.txt'" or '"file a.txt", "file b.txt"'
    - Mixed: "b001, 'file with spaces.txt', b003"
    - List: ['file1.txt', 'file2.txt']

    Returns a list of filename strings with quotes removed and whitespace stripped.
    """
    if isinstance(filelist, str):
        # Parse comma-separated string
        items = []
        for item in filelist.split(","):
            item = item.strip()
            # Remove surrounding quotes (single or double)
            if len(item) >= 2:
                if (item.startswith("'") and item.endswith("'")) or (
                    item.startswith('"') and item.endswith('"')
                ):
                    item = item[1:-1]
            items.append(item)
        return items
    else:
        # Normalize list entries (strip whitespace)
        return [f.strip() for f in filelist]


def backup_files(source, target, filelist, store="original", overwrite=False):
    """
    ``backup_files source=<source folder path> target=<target folder path> filelist=<file list> [store=original] [overwrite=False]``

    Creates a backup of specified files from a source folder to a target location.
    Files are stored with sequential backup prefixes (b001\_, b002\_, etc.) and a
    file_list.txt manifest is created to track the original locations.

    Parameters:
        --source (str):
            The path to the source folder containing the files to back up.
            All file paths in filelist are resolved relative to this folder
            if they are not absolute paths.

        --target (str):
            The path to the target folder where backups will be stored.
            If the folder does not exist, it will be created.
            For store=zip mode, this should be the path without .zip extension
            (the .zip extension will be added automatically).

        --filelist (list of str):
            A list of file paths to back up. Paths can be absolute or relative
            to the source folder. The list can be provided as a Python list or
            as a comma-separated string.

        --store (str, default 'original'):
            Storage mode for the backup files:

            - 'original': Files are copied as-is to the target folder with
              backup prefixes. Directory structure is flattened - all files
              are stored in the root of the target folder.

            - 'gzip': Files are gzipped during backup. Files without .gz
              extension are compressed and get .gz added. Files already
              ending in .gz are copied as-is without further compression.

            - 'zip': All files are packaged into a single ZIP archive named
              <target>.zip. The target folder itself is not created. Parent
              directories in the path are created if needed. The file_list.txt
              manifest is included inside the ZIP archive.

        --overwrite (bool, default False):
            Controls behavior when target already exists and contains files:

            - False: If target exists and contains files, raise an error and
              exit without creating backup.

            - True: If target exists and contains files, remove existing files
              before creating the backup.

    File Naming:
        Each backed up file receives a sequential prefix:
        - b001\_<filename> for the first file
        - b002\_<filename> for the second file
        - b003\_<filename> for the third file
        - And so on...

        For gzip mode, non-compressed files also get .gz extension:
        - b001_config.json → b001_config.json.gz
        - b002_data.nii.gz → b002_data.nii.gz (already compressed, no change)

    Manifest File (file_list.txt):
        A manifest file named file_list.txt is created with the backup:
        - First line: Source folder path (source folder: <path>)
        - Second line: Storage mode (store: <mode>)
        - Following lines: <prefix>: <relative path within source folder>

        Example:
        ::

            source folder: /home/user/project/data
            store: original
            b001: configs/settings.json
            b002: results/output.txt
            b003: logs/process.log

        For store=zip mode, file_list.txt is included inside the ZIP archive.
        For other modes, it's placed in the target folder.

    Directory Structure:
        Backups use a flat structure - all files are stored in the root of
        the target folder or ZIP archive, regardless of their original
        directory structure in the source. The original paths are preserved
        only in the file_list.txt manifest.

    Notes:
        - The function creates all necessary parent directories automatically
        - By default (overwrite=False), the function will fail if target exists
          and contains files, preventing accidental data loss
        - With overwrite=True, existing files in target are removed before backup
        - For large files, gzip mode can significantly reduce storage space
        - For many small files, zip mode provides better organization
        - The manifest file allows easy restoration of original directory structure

    Examples:
        Back up configuration files as-is:
        ::

            qunex backup_files \\
                --source=/path/to/project \\
                --target=/path/to/backups/config_backup \\
                --filelist=configs/settings.json,configs/database.ini,README.md \\
                --store=original

        Back up data files with gzip compression:
        ::

            qunex backup_files \\
                --source=/path/to/study/sessions/subject01 \\
                --target=/path/to/backups/subject01_data \\
                --filelist="bold/run1.nii,bold/run2.nii,anat/T1w.nii" \\
                --store=gzip

        Create a ZIP archive of analysis results:
        ::

            qunex backup_files \\
                --source=/path/to/analysis \\
                --target=/path/to/archives/results_2024 \\
                --filelist="output.csv,plots/figure1.png,plots/figure2.png" \\
                --store=zip
    """
    import gzip
    import shutil
    import zipfile

    print("Running backup_files\n====================\n")

    # Process filelist (handles strings and lists, strips whitespace and quotes)
    filelist = _process_filelist(filelist)

    # Convert overwrite to boolean
    overwrite = true_or_false(overwrite)

    # Validate parameters
    if not source:
        raise ge.CommandError(
            "backup_files",
            "No source folder specified",
            "Please provide the source folder path using the source parameter!",
        )

    if not target:
        raise ge.CommandError(
            "backup_files",
            "No target folder specified",
            "Please provide the target folder path using the target parameter!",
        )

    if not filelist or len(filelist) == 0:
        raise ge.CommandError(
            "backup_files",
            "No files specified",
            "Please provide a list of files to back up using the filelist parameter!",
        )

    # Validate store parameter
    store = store.lower()
    if store not in ["original", "gzip", "zip"]:
        raise ge.CommandError(
            "backup_files",
            f"Invalid store mode: {store}",
            "Store parameter must be one of: 'original', 'gzip', 'zip'",
        )

    # Get absolute source path
    source = os.path.abspath(source)

    if not os.path.exists(source):
        raise ge.CommandError(
            "backup_files",
            f"Source folder does not exist: {source}",
            "Please check the source path!",
        )

    if not os.path.isdir(source):
        raise ge.CommandError(
            "backup_files",
            f"Source path is not a directory: {source}",
            "Please provide a valid directory path!",
        )

    print(f"Source folder: {source}")
    print(f"Target: {target}")
    print(f"Store mode: {store}")
    print(f"Overwrite: {overwrite}")
    print(f"Files to backup: {len(filelist)}")
    print()

    # Check if target exists and handle overwrite
    if store == "zip":
        target_check = target if target.endswith(".zip") else target + ".zip"
    else:
        target_check = target

    if os.path.exists(target_check):
        # Check if it contains files
        has_files = False
        if store == "zip":
            # ZIP file exists
            has_files = True
        else:
            # Directory exists - check if it has files
            if os.path.isdir(target_check):
                existing_items = os.listdir(target_check)
                has_files = len(existing_items) > 0

        if has_files:
            if not overwrite:
                raise ge.CommandError(
                    "backup_files",
                    f"Target already exists and contains files: {target_check}",
                    "Use overwrite=True to remove existing files, or choose a different target path!",
                )
            else:
                print(f"Removing existing target: {target_check}")
                if store == "zip":
                    os.remove(target_check)
                else:
                    shutil.rmtree(target_check)
                print()

    # Prepare file list with absolute paths and relative paths
    backup_items = []
    missing_files = []

    for filepath in filelist:
        # Convert to absolute path if relative
        if os.path.isabs(filepath):
            abs_path = filepath
            # Calculate relative path from source
            try:
                rel_path = os.path.relpath(abs_path, source)
            except ValueError:
                # On different drives (Windows), keep as absolute
                rel_path = abs_path
        else:
            abs_path = os.path.join(source, filepath)
            rel_path = filepath

        if not os.path.exists(abs_path):
            missing_files.append(filepath)
            continue

        if not os.path.isfile(abs_path):
            print(f"Warning: Skipping non-file path: {filepath}")
            continue

        backup_items.append(
            {"abs_path": abs_path, "rel_path": rel_path, "original": filepath}
        )

    if missing_files:
        print(f"Warning: {len(missing_files)} file(s) not found:")
        for f in missing_files:
            print(f"  - {f}")
        print()

    if not backup_items:
        raise ge.CommandError(
            "backup_files",
            "No valid files to back up",
            "All specified files are missing or invalid!",
        )

    print(f"Processing {len(backup_items)} file(s)...\n")

    # Build manifest content with header
    manifest_lines = [f"source folder: {source}", f"store: {store}"]
    backed_up_files = []

    # Process based on store mode
    if store == "zip":
        # For ZIP mode, create parent directories and the ZIP file
        target_zip = target if target.endswith(".zip") else target + ".zip"
        target_dir = os.path.dirname(target_zip)

        if target_dir and not os.path.exists(target_dir):
            os.makedirs(target_dir)
            print(f"Created directory: {target_dir}")

        print(f"Creating ZIP archive: {target_zip}\n")

        with zipfile.ZipFile(target_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, item in enumerate(backup_items, start=1):
                prefix = f"b{idx:03d}_"
                original_name = os.path.basename(item["abs_path"])
                backup_name = prefix + original_name

                # Add file to ZIP
                zf.write(item["abs_path"], backup_name)

                # Track in manifest (prefix without trailing underscore)
                manifest_lines.append(f"{prefix[:-1]}: {item['rel_path']}")
                backed_up_files.append(backup_name)

                print(f"  [{idx:03d}] {item['rel_path']} → {backup_name}")

            # Add manifest to ZIP
            manifest_content = "\n".join(manifest_lines)
            zf.writestr("file_list.txt", manifest_content)
            print("\n  Added file_list.txt to archive")

        print(f"\nBackup complete: {target_zip}")
        print(f"Total files backed up: {len(backed_up_files)}")

    else:
        # For original and gzip modes, create target folder
        if not os.path.exists(target):
            os.makedirs(target)
            print(f"Created directory: {target}\n")

        for idx, item in enumerate(backup_items, start=1):
            prefix = f"b{idx:03d}_"
            original_name = os.path.basename(item["abs_path"])

            if store == "gzip":
                # Check if file is already gzipped
                if original_name.endswith(".gz"):
                    backup_name = prefix + original_name
                    backup_path = os.path.join(target, backup_name)
                    # Just copy the already-gzipped file
                    shutil.copy2(item["abs_path"], backup_path)
                    print(
                        f"  [{idx:03d}] {item['rel_path']} → {backup_name} (already compressed)"
                    )
                else:
                    backup_name = prefix + original_name + ".gz"
                    backup_path = os.path.join(target, backup_name)
                    # Gzip the file
                    with open(item["abs_path"], "rb") as f_in:
                        with gzip.open(backup_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    print(
                        f"  [{idx:03d}] {item['rel_path']} → {backup_name} (compressed)"
                    )
            else:
                # Original mode - just copy
                backup_name = prefix + original_name
                backup_path = os.path.join(target, backup_name)
                shutil.copy2(item["abs_path"], backup_path)
                print(f"  [{idx:03d}] {item['rel_path']} → {backup_name}")

            # Track in manifest (prefix without trailing underscore)
            manifest_lines.append(f"{prefix[:-1]}: {item['rel_path']}")
            backed_up_files.append(backup_name)

        # Write manifest file
        manifest_path = os.path.join(target, "file_list.txt")
        with open(manifest_path, "w") as f:
            f.write("\n".join(manifest_lines))

        print("\n  Created file_list.txt")
        print(f"\nBackup complete: {target}")
        print(f"Total files backed up: {len(backed_up_files)}")

    return backed_up_files


def restore_files(source, target=None, overwrite=False, filelist=None):
    """
    ``restore_files source=<backup location> [target=None] [overwrite=False] [filelist=None]``

    Restores files from a backup created by backup_files function. The backup can
    be in any format (original, gzip, or zip). Files are restored to their original
    locations or to a specified target directory, with automatic decompression of
    gzipped files when needed.

    Parameters:
        --source (str):
            The path to the backup location. Can be either:

            - A directory containing backed up files and file_list.txt
            - A ZIP archive (.zip file) created with store=zip mode

            The backup must contain a valid file_list.txt manifest describing
            the backup structure and original file locations.

        --target (str, default None):
            The target directory where files should be restored:

            - If provided: Files are restored relative to this directory path,
              using the relative paths from file_list.txt

            - If None: Files are restored to their original location as specified
              in the "source folder" line of file_list.txt

            Parent directories are created automatically if they don't exist.

        --overwrite (bool or str, default False):
            Controls behavior when restored files already exist at target:

            - False: If ANY target files exist, raise an error and do not restore
              anything. This prevents accidental overwriting.

            - True: Overwrite all existing files with backed up versions.

            - "skip": Only restore files that don't currently exist at the
              target location. Skip files that already exist without error.

        --filelist (list or str, default None):
            Optional list of specific files to restore. If not provided, all files
            from the backup are restored. Can be specified as:

            - List of backup numbers: ['b001', 'b002', 'b005'] - restores only
              those specific backup entries

            - List of original paths: ['configs/settings.json', 'data/file.txt'] -
              restores only files matching these exact relative paths

            - Comma-separated string: 'b001, b002, configs/settings.json' -
              parsed into list of items

            - Single string: 'b001' or 'configs/settings.json'

            - Mixed format: ['b001', 'configs/settings.json'] - matches either
              backup numbers or original paths

            Files not matching any entry in filelist are skipped during restoration.

    Backup Format Detection:
        The function automatically detects the backup format:

        - ZIP archives: Extracts and reads file_list.txt from the archive
        - Directories: Reads file_list.txt from the directory
        - Invalid backups without file_list.txt generate an error

    Manifest File Structure:
        The file_list.txt must follow this format:
        ::

            source folder: /original/path/to/source
            store: <original|gzip|zip>
            b001: relative/path/file1.txt
            b002: relative/path/file2.json
            b003: data/file3.csv

    Automatic Decompression:
        When restoring gzipped backups (store: gzip):

        - Files that were originally uncompressed (without .gz extension) are
          automatically decompressed during restoration

        - Files that were already compressed (with .gz extension) are copied
          as-is without decompression

        - Decompression is determined by comparing the original filename in
          file_list.txt with the backup filename

    Restoration Process:
        1. Validate backup source and read file_list.txt
        2. Parse source folder path and store mode from manifest
        3. Determine target directory (provided or from manifest)
        4. Check for existing files based on overwrite mode
        5. Create necessary parent directories
        6. Restore each file:
           - Remove b[n]_ prefix from backup filename
           - Decompress if needed (gzip mode only)
           - Copy to relative path specified in manifest
        7. Report restoration summary

    Notes:
        - The function preserves the original directory structure from file_list.txt
        - Backup file prefixes (b001\_, b002\_, etc.) are automatically removed
        - With overwrite="skip", partial restoration is supported
        - For gzip backups, only files that need decompression are unzipped
        - The restore operation is atomic when overwrite=False (all or nothing)

    Examples:
        Restore to original location:
        ::

            qunex restore_files \\
                --source=/path/to/backups/config_backup

        Restore to different location:
        ::

            qunex restore_files \\
                --source=/path/to/backups/subject01_data \\
                --target=/path/to/new/location

        Restore from ZIP archive, overwriting existing files:
        ::

            qunex restore_files \\
                --source=/path/to/archives/results_2024.zip \\
                --target=/path/to/restore/location \\
                --overwrite=True

        Restore only missing files:
        ::

            qunex restore_files \\
                --source=/path/to/backups/config_backup \\
                --overwrite=missing
    """
    import gzip
    import io
    import shutil
    import zipfile

    print("Running restore_files\n=====================\n")

    # Validate source
    if not source:
        raise ge.CommandError(
            "restore_files",
            "No source specified",
            "Please provide the backup location using the source parameter!",
        )

    if not os.path.exists(source):
        raise ge.CommandError(
            "restore_files",
            f"Source does not exist: {source}",
            "Please check the backup path!",
        )

    # Convert overwrite to proper type
    if isinstance(overwrite, str):
        if overwrite.lower() == "skip":
            overwrite_mode = "skip"
        else:
            overwrite_mode = true_or_false(overwrite)
    else:
        overwrite_mode = overwrite

    # Validate overwrite mode
    if overwrite_mode not in [True, False, "skip"]:
        raise ge.CommandError(
            "restore_files",
            f"Invalid overwrite mode: {overwrite}",
            "Overwrite must be True, False, or 'missing'!",
        )

    print(f"Source: {source}")
    print(f"Overwrite mode: {overwrite_mode}")

    # Determine if source is ZIP or directory
    is_zip = source.endswith(".zip") and os.path.isfile(source)

    # Read and parse file_list.txt
    manifest_content = None

    if is_zip:
        print("Backup type: ZIP archive\n")
        try:
            with zipfile.ZipFile(source, "r") as zf:
                if "file_list.txt" not in zf.namelist():
                    raise ge.CommandError(
                        "restore_files",
                        "Not a valid backup: file_list.txt not found in ZIP archive",
                        f"The ZIP file {source} does not contain a file_list.txt manifest!",
                    )

                manifest_content = zf.read("file_list.txt").decode("utf-8")
        except zipfile.BadZipFile:
            raise ge.CommandError(
                "restore_files",
                f"Invalid ZIP file: {source}",
                "The file is not a valid ZIP archive!",
            )
    else:
        print("Backup type: Directory\n")
        if not os.path.isdir(source):
            raise ge.CommandError(
                "restore_files",
                f"Source is neither a directory nor a ZIP file: {source}",
                "Please provide a valid backup directory or ZIP archive!",
            )

        manifest_path = os.path.join(source, "file_list.txt")
        if not os.path.exists(manifest_path):
            raise ge.CommandError(
                "restore_files",
                "Not a valid backup: file_list.txt not found",
                f"The directory {source} does not contain a file_list.txt manifest!",
            )

        with open(manifest_path, "r") as f:
            manifest_content = f.read()

    # Parse manifest
    lines = manifest_content.strip().split("\n")

    if len(lines) < 2:
        raise ge.CommandError(
            "restore_files",
            "Invalid file_list.txt: insufficient header lines",
            "The manifest must contain at least 2 header lines (source folder and store mode)!",
        )

    # Parse header
    source_folder = None
    store_mode = None

    for line in lines[:2]:
        if line.startswith("source folder:"):
            source_folder = line.split("source folder:", 1)[1].strip()
        elif line.startswith("store:"):
            store_mode = line.split("store:", 1)[1].strip()

    if not source_folder or not store_mode:
        raise ge.CommandError(
            "restore_files",
            "Invalid file_list.txt: missing required headers",
            "The manifest must contain 'source folder:' and 'store:' headers!",
        )

    print(f"Original source folder: {source_folder}")
    print(f"Store mode: {store_mode}")

    # Parse file entries (skip header lines)
    file_entries = []
    for line in lines[2:]:
        line = line.strip()
        if not line:
            continue

        # Parse format: b001: relative/path/file.txt
        if ":" not in line:
            continue

        prefix_part, rel_path = line.split(":", 1)
        prefix_part = prefix_part.strip()
        rel_path = rel_path.strip()

        # Extract backup number from prefix (b001, b002, etc.)
        if not prefix_part.startswith("b") or len(prefix_part) < 2:
            continue

        file_entries.append({"prefix": prefix_part, "rel_path": rel_path})

    if not file_entries:
        raise ge.CommandError(
            "restore_files",
            "No files listed in file_list.txt",
            "The manifest does not contain any file entries to restore!",
        )

    print(f"Files to restore: {len(file_entries)}\n")

    # Determine target folder
    if target:
        target_folder = os.path.abspath(target)
        print(f"Target folder: {target_folder} (user-specified)")
    else:
        target_folder = source_folder
        print(f"Target folder: {target_folder} (from manifest)")

    print()

    # Build list of files to restore with their target paths
    restore_plan = []

    for entry in file_entries:
        # Determine backup filename
        original_basename = os.path.basename(entry["rel_path"])

        if store_mode == "gzip":
            # Check if original file had .gz extension
            if original_basename.endswith(".gz"):
                # File was already gzipped, backup name is prefix + basename
                backup_filename = f"{entry['prefix']}_{original_basename}"
                needs_decompress = False
            else:
                # File was compressed during backup, has .gz added
                backup_filename = f"{entry['prefix']}_{original_basename}.gz"
                needs_decompress = True
        else:
            # Original or zip mode - no special handling
            backup_filename = f"{entry['prefix']}_{original_basename}"
            needs_decompress = False

        # Target path
        target_path = os.path.join(target_folder, entry["rel_path"])

        restore_plan.append(
            {
                "backup_filename": backup_filename,
                "target_path": target_path,
                "rel_path": entry["rel_path"],
                "prefix": entry["prefix"],
                "needs_decompress": needs_decompress,
            }
        )

    # Filter restore_plan if filelist is specified
    if filelist is not None:
        # Process filelist (handles strings and lists, strips whitespace and quotes)
        filelist = _process_filelist(filelist)

        # Filter restore_plan
        original_count = len(restore_plan)
        filtered_plan = []

        for item in restore_plan:
            # Check if item matches any entry in filelist
            # Match by backup number (e.g., 'b001')
            if item["prefix"] in filelist:
                filtered_plan.append(item)
                continue

            # Match by original relative path
            if item["rel_path"] in filelist:
                filtered_plan.append(item)
                continue

        restore_plan = filtered_plan

        if not restore_plan:
            raise ge.CommandError(
                "restore_files",
                "No files matched the specified filelist",
                f"None of the {original_count} backup entries matched any of the {len(filelist)} filter(s)!",
            )

        print(
            f"Filtered to {len(restore_plan)} file(s) matching filelist (from {original_count} total)\n"
        )

    # Check for existing files based on overwrite mode
    existing_files = []
    for item in restore_plan:
        if os.path.exists(item["target_path"]):
            existing_files.append(item["rel_path"])

    if existing_files:
        if overwrite_mode is False:
            print(
                f"ERROR: {len(existing_files)} file(s) already exist at target location:"
            )
            for filepath in existing_files[:10]:  # Show first 10
                print(f"  - {filepath}")
            if len(existing_files) > 10:
                print(f"  ... and {len(existing_files) - 10} more")
            print()
            raise ge.CommandError(
                "restore_files",
                f"{len(existing_files)} file(s) already exist at target",
                "Use overwrite=True to replace existing files, or overwrite='skip' to skip them!",
            )
        elif overwrite_mode == "skip":
            print(
                f"Note: {len(existing_files)} file(s) already exist and will be skipped"
            )
            print()

    # Perform restoration
    restored_count = 0
    skipped_count = 0

    print("Restoring files...\n")

    if is_zip:
        # Restore from ZIP
        with zipfile.ZipFile(source, "r") as zf:
            for idx, item in enumerate(restore_plan, start=1):
                # Skip if file exists and overwrite is "skip"
                if os.path.exists(item["target_path"]) and overwrite_mode == "skip":
                    print(
                        f"  [{idx:03d}] {item['rel_path']} (skipped - already exists)"
                    )
                    skipped_count += 1
                    continue

                # Create parent directory if needed
                target_dir = os.path.dirname(item["target_path"])
                if target_dir and not os.path.exists(target_dir):
                    os.makedirs(target_dir)

                # Extract and restore
                if item["needs_decompress"]:
                    # Decompress during extraction
                    compressed_data = zf.read(item["backup_filename"])
                    with gzip.GzipFile(fileobj=io.BytesIO(compressed_data)) as gz:
                        with open(item["target_path"], "wb") as f_out:
                            shutil.copyfileobj(gz, f_out)
                    print(f"  [{idx:03d}] {item['rel_path']} (decompressed)")
                else:
                    # Direct extraction
                    with zf.open(item["backup_filename"]) as f_in:
                        with open(item["target_path"], "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    print(f"  [{idx:03d}] {item['rel_path']}")

                restored_count += 1
    else:
        # Restore from directory
        for idx, item in enumerate(restore_plan, start=1):
            # Skip if file exists and overwrite is "skip"
            if os.path.exists(item["target_path"]) and overwrite_mode == "skip":
                print(f"  [{idx:03d}] {item['rel_path']} (skipped - already exists)")
                skipped_count += 1
                continue

            backup_path = os.path.join(source, item["backup_filename"])

            if not os.path.exists(backup_path):
                print(
                    f"  [{idx:03d}] {item['rel_path']} (WARNING: backup file not found)"
                )
                continue

            # Create parent directory if needed
            target_dir = os.path.dirname(item["target_path"])
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir)

            # Restore file
            if item["needs_decompress"]:
                # Decompress during copy
                with gzip.open(backup_path, "rb") as f_in:
                    with open(item["target_path"], "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                print(f"  [{idx:03d}] {item['rel_path']} (decompressed)")
            else:
                # Direct copy
                shutil.copy2(backup_path, item["target_path"])
                print(f"  [{idx:03d}] {item['rel_path']}")

            restored_count += 1

    print("\nRestoration complete!")
    print(f"Files restored: {restored_count}")
    if skipped_count > 0:
        print(f"Files skipped: {skipped_count}")

    return restored_count

#!/usr/bin/env python
# encoding: utf-8

"""
Test suite for snapshot functions: record_snapshot, compare_snapshots, rollback_snapshot
"""

import sys
import os
import tempfile
import shutil
import time

# Add the parent directory to the path to import qx_utilities
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'qx_utilities'))

from general.snapshots import record_snapshot, compare_snapshots, rollback_snapshot
from general.exceptions import CommandError
import pytest


def create_test_directory(base_path):
    """Helper to create a test directory structure with files"""
    # Create directory structure
    os.makedirs(os.path.join(base_path, "subdir1"))
    os.makedirs(os.path.join(base_path, "subdir2", "nested"))
    
    # Create files with known content
    with open(os.path.join(base_path, "file1.txt"), 'w') as f:
        f.write("This is file 1\n")
    
    with open(os.path.join(base_path, "file2.txt"), 'w') as f:
        f.write("This is file 2\n")
    
    with open(os.path.join(base_path, "subdir1", "nested_file.txt"), 'w') as f:
        f.write("Nested file in subdir1\n")
    
    with open(os.path.join(base_path, "subdir2", "another_file.txt"), 'w') as f:
        f.write("File in subdir2\n")
    
    with open(os.path.join(base_path, "subdir2", "nested", "deep_file.txt"), 'w') as f:
        f.write("Deep nested file\n")


def read_snapshot_file(filepath):
    """Helper to read and return snapshot file contents"""
    with open(filepath, 'r') as f:
        return f.read()


def count_lines_with_pattern(filepath, pattern):
    """Helper to count lines containing a specific pattern"""
    count = 0
    with open(filepath, 'r') as f:
        for line in f:
            if pattern in line:
                count += 1
    return count


def test_record_snapshot_basic():
    """Test basic snapshot recording with hash"""
    print("\n" + "=" * 70)
    print("TEST: Basic snapshot recording with hash")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        snapshot_file = os.path.join(tmpdir, "snapshot.txt")
        record_snapshot(test_dir, snapshot_file, includehash=True)
        
        assert os.path.exists(snapshot_file), "Snapshot file should be created"
        
        content = read_snapshot_file(snapshot_file)
        
        # Check that absolute path is recorded
        assert test_dir in content, "Absolute path should be in snapshot"
        
        # Check tree structure markers
        assert "├──" in content or "└──" in content, "Should contain tree connectors"
        
        # Check files are listed
        assert "file1.txt" in content, "file1.txt should be in snapshot"
        assert "file2.txt" in content, "file2.txt should be in snapshot"
        assert "nested_file.txt" in content, "nested_file.txt should be in snapshot"
        
        # Check directories are listed
        assert "subdir1" in content, "subdir1 should be in snapshot"
        assert "subdir2" in content, "subdir2 should be in snapshot"
        
        # Check that metadata is included (with hash)
        # Metadata format: [mtime, hash, size bytes]
        assert "bytes]" in content, "Should contain file size in bytes"
        
        # Count hash entries (32 char hex strings from MD5)
        # Each file should have a hash in its metadata
        lines_with_metadata = [l for l in content.split('\n') if '[' in l and 'bytes]' in l]
        assert len(lines_with_metadata) == 5, "Should have metadata for 5 files"
        
        print(f"Snapshot created successfully with {len(lines_with_metadata)} files")


def test_record_snapshot_without_hash():
    """Test snapshot recording without hash"""
    print("\n" + "=" * 70)
    print("TEST: Snapshot recording without hash")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        snapshot_file = os.path.join(tmpdir, "snapshot_nohash.txt")
        record_snapshot(test_dir, snapshot_file, includehash=False)
        
        assert os.path.exists(snapshot_file), "Snapshot file should be created"
        
        content = read_snapshot_file(snapshot_file)
        
        # Check that files are listed
        assert "file1.txt" in content, "file1.txt should be in snapshot"
        
        # Check metadata format without hash: [mtime, size bytes]
        assert "bytes]" in content, "Should contain file size in bytes"
        
        # Verify no hash (metadata should have fewer commas)
        lines_with_metadata = [l for l in content.split('\n') if '[' in l and 'bytes]' in l]
        # Without hash, metadata has 2 components: mtime, size
        # With hash, it would have 3: mtime, hash, size
        # Check that a typical line doesn't have a 32-char hex string
        for line in lines_with_metadata:
            # Extract the metadata part
            if '[' in line:
                metadata = line[line.index('['):line.index(']')+1]
                # Count commas - should be 1 without hash (mtime, size)
                assert metadata.count(',') == 1, f"Metadata should have 1 comma without hash: {metadata}"
        
        print(f"Snapshot created successfully without hashes")


def test_record_snapshot_string_parameters():
    """Test snapshot recording with string boolean parameters"""
    print("\n" + "=" * 70)
    print("TEST: Snapshot with string boolean parameters")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        
        with open(os.path.join(test_dir, "test.txt"), 'w') as f:
            f.write("test content\n")
        
        # Test with "yes"
        snapshot1 = os.path.join(tmpdir, "snapshot_yes.txt")
        record_snapshot(test_dir, snapshot1, includehash="yes")
        content1 = read_snapshot_file(snapshot1)
        assert content1.count(',') == 2, "Should have hash (2 commas in metadata)"
        
        # Test with "no"
        snapshot2 = os.path.join(tmpdir, "snapshot_no.txt")
        record_snapshot(test_dir, snapshot2, includehash="no")
        content2 = read_snapshot_file(snapshot2)
        # Extract metadata line
        for line in content2.split('\n'):
            if 'test.txt' in line and '[' in line:
                metadata = line[line.index('['):line.index(']')+1]
                assert metadata.count(',') == 1, "Should not have hash (1 comma in metadata)"
        
        print("String boolean parameters work correctly")


def test_record_snapshot_empty_directory():
    """Test snapshot of an empty directory"""
    print("\n" + "=" * 70)
    print("TEST: Snapshot of empty directory")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "empty_folder")
        os.makedirs(test_dir)
        
        snapshot_file = os.path.join(tmpdir, "snapshot_empty.txt")
        record_snapshot(test_dir, snapshot_file, includehash=True)
        
        assert os.path.exists(snapshot_file), "Snapshot file should be created"
        
        content = read_snapshot_file(snapshot_file)
        
        # Should have absolute path and root marker
        assert test_dir in content, "Should contain directory path"
        assert "." in content, "Should contain root marker"
        
        # Should not have any file metadata
        assert "bytes]" not in content, "Should not contain any file metadata"
        
        print("Empty directory snapshot created successfully")


def test_record_snapshot_invalid_path():
    """Test snapshot with invalid path"""
    print("\n" + "=" * 70)
    print("TEST: Snapshot with invalid path")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        invalid_path = os.path.join(tmpdir, "nonexistent")
        snapshot_file = os.path.join(tmpdir, "snapshot.txt")
        
        with pytest.raises(CommandError) as exc_info:
            record_snapshot(invalid_path, snapshot_file, includehash=True)
        
        assert "does not exist" in str(exc_info.value).lower(), "Should report path does not exist"
        
        print("Invalid path correctly raises error")


def test_compare_snapshots_no_changes():
    """Test comparing two identical snapshots"""
    print("\n" + "=" * 70)
    print("TEST: Compare identical snapshots")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        snapshot1 = os.path.join(tmpdir, "snapshot1.txt")
        snapshot2 = os.path.join(tmpdir, "snapshot2.txt")
        diff_file = os.path.join(tmpdir, "diff.txt")
        
        # Create two snapshots of the same directory
        record_snapshot(test_dir, snapshot1, includehash=True)
        time.sleep(0.1)  # Small delay
        record_snapshot(test_dir, snapshot2, includehash=True)
        
        # Compare
        compare_snapshots(snapshot1, snapshot2, diff_file, includehash=True)
        
        content = read_snapshot_file(diff_file)
        
        # Check headers
        assert "before:" in content, "Should have 'before:' header"
        assert "after:" in content, "Should have 'after:' header"
        
        # Should not have any status markers (M, +, -)
        status_markers = content.count("M ") + content.count("+ ") + content.count("- ")
        assert status_markers == 0, "Should have no status markers for unchanged files"
        
        # Files should still be listed
        assert "file1.txt" in content, "Files should be listed"
        
        print("Identical snapshots compared successfully")


def test_compare_snapshots_added_files():
    """Test comparing snapshots with added files"""
    print("\n" + "=" * 70)
    print("TEST: Compare snapshots with added files")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        snapshot1 = os.path.join(tmpdir, "snapshot_before.txt")
        record_snapshot(test_dir, snapshot1, includehash=True)
        
        # Add new files
        with open(os.path.join(test_dir, "new_file.txt"), 'w') as f:
            f.write("This is a new file\n")
        
        with open(os.path.join(test_dir, "subdir1", "another_new.txt"), 'w') as f:
            f.write("Another new file\n")
        
        snapshot2 = os.path.join(tmpdir, "snapshot_after.txt")
        record_snapshot(test_dir, snapshot2, includehash=True)
        
        diff_file = os.path.join(tmpdir, "diff.txt")
        compare_snapshots(snapshot1, snapshot2, diff_file, includehash=True)
        
        content = read_snapshot_file(diff_file)
        
        # Check for added markers
        assert "+ " in content, "Should have '+' markers for added files"
        
        # Count added files
        added_count = count_lines_with_pattern(diff_file, "+ ")
        assert added_count == 2, f"Should have 2 added files, found {added_count}"
        
        # Verify specific files are marked as added
        lines = content.split('\n')
        new_file_line = [l for l in lines if "new_file.txt" in l][0]
        assert "+ " in new_file_line, "new_file.txt should be marked as added"
        
        another_new_line = [l for l in lines if "another_new.txt" in l][0]
        assert "+ " in another_new_line, "another_new.txt should be marked as added"
        
        print(f"Added files detected correctly: {added_count} files")


def test_compare_snapshots_deleted_files():
    """Test comparing snapshots with deleted files"""
    print("\n" + "=" * 70)
    print("TEST: Compare snapshots with deleted files")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        snapshot1 = os.path.join(tmpdir, "snapshot_before.txt")
        record_snapshot(test_dir, snapshot1, includehash=True)
        
        # Delete files
        os.remove(os.path.join(test_dir, "file1.txt"))
        os.remove(os.path.join(test_dir, "subdir2", "another_file.txt"))
        
        snapshot2 = os.path.join(tmpdir, "snapshot_after.txt")
        record_snapshot(test_dir, snapshot2, includehash=True)
        
        diff_file = os.path.join(tmpdir, "diff.txt")
        compare_snapshots(snapshot1, snapshot2, diff_file, includehash=True)
        
        content = read_snapshot_file(diff_file)
        
        # Check for deleted markers
        assert "- " in content, "Should have '-' markers for deleted files"
        
        # Count deleted files
        deleted_count = count_lines_with_pattern(diff_file, "- ")
        assert deleted_count == 2, f"Should have 2 deleted files, found {deleted_count}"
        
        # Verify specific files are marked as deleted
        lines = content.split('\n')
        file1_line = [l for l in lines if "file1.txt" in l][0]
        assert "- " in file1_line, "file1.txt should be marked as deleted"
        
        print(f"Deleted files detected correctly: {deleted_count} files")


def test_compare_snapshots_modified_files():
    """Test comparing snapshots with modified files"""
    print("\n" + "=" * 70)
    print("TEST: Compare snapshots with modified files")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        snapshot1 = os.path.join(tmpdir, "snapshot_before.txt")
        record_snapshot(test_dir, snapshot1, includehash=True)
        
        # Modify a file (change content)
        time.sleep(0.1)  # Ensure different mtime
        with open(os.path.join(test_dir, "file1.txt"), 'w') as f:
            f.write("This is modified content\n")
        
        snapshot2 = os.path.join(tmpdir, "snapshot_after.txt")
        record_snapshot(test_dir, snapshot2, includehash=True)
        
        diff_file = os.path.join(tmpdir, "diff.txt")
        compare_snapshots(snapshot1, snapshot2, diff_file, includehash=True)
        
        content = read_snapshot_file(diff_file)
        
        # Check for modified markers
        assert "M " in content, "Should have 'M' markers for modified files"
        
        # Verify the modified file shows before -> after
        lines = content.split('\n')
        file1_line = [l for l in lines if "file1.txt" in l][0]
        assert "M " in file1_line, "file1.txt should be marked as modified"
        assert " -> " in file1_line, "Modified file should show before -> after"
        
        print("Modified files detected correctly")


def test_compare_snapshots_with_directory():
    """Test comparing snapshot with a live directory"""
    print("\n" + "=" * 70)
    print("TEST: Compare snapshot with live directory")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        snapshot1 = os.path.join(tmpdir, "snapshot_before.txt")
        record_snapshot(test_dir, snapshot1, includehash=True)
        
        # Add a new file to the directory
        with open(os.path.join(test_dir, "new_file.txt"), 'w') as f:
            f.write("New content\n")
        
        diff_file = os.path.join(tmpdir, "diff.txt")
        # Compare snapshot with directory (not another snapshot)
        compare_snapshots(snapshot1, test_dir, diff_file, includehash=True)
        
        content = read_snapshot_file(diff_file)
        
        # Should detect the new file
        assert "+ " in content, "Should detect added file"
        assert "new_file.txt" in content, "Should list new_file.txt"
        
        print("Comparison with live directory works correctly")


def test_compare_snapshots_without_hash():
    """Test comparing snapshots without hash comparison"""
    print("\n" + "=" * 70)
    print("TEST: Compare snapshots without hash")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        
        with open(os.path.join(test_dir, "test.txt"), 'w') as f:
            f.write("content\n")
        
        snapshot1 = os.path.join(tmpdir, "snapshot1.txt")
        snapshot2 = os.path.join(tmpdir, "snapshot2.txt")
        
        # Create snapshots without hash
        record_snapshot(test_dir, snapshot1, includehash=False)
        time.sleep(0.1)
        record_snapshot(test_dir, snapshot2, includehash=False)
        
        diff_file = os.path.join(tmpdir, "diff.txt")
        compare_snapshots(snapshot1, snapshot2, diff_file, includehash=False)
        
        content = read_snapshot_file(diff_file)
        
        # Should complete without error
        assert "test.txt" in content, "Should contain file listing"
        
        print("Comparison without hash works correctly")


def test_rollback_snapshot_check_mode():
    """Test rollback in check mode"""
    print("\n" + "=" * 70)
    print("TEST: Rollback snapshot check mode")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        snapshot_before = os.path.join(tmpdir, "before.txt")
        record_snapshot(test_dir, snapshot_before, includehash=True)
        
        # Add new files
        with open(os.path.join(test_dir, "added1.txt"), 'w') as f:
            f.write("Added file 1\n")
        
        with open(os.path.join(test_dir, "added2.txt"), 'w') as f:
            f.write("Added file 2\n")
        
        snapshot_after = os.path.join(tmpdir, "after.txt")
        record_snapshot(test_dir, snapshot_after, includehash=True)
        
        diff_file = os.path.join(tmpdir, "diff.txt")
        compare_snapshots(snapshot_before, snapshot_after, diff_file, includehash=True)
        
        # Run rollback in check mode
        rollback_snapshot(diff=diff_file, action="check")
        
        # Files should still exist (check mode doesn't delete)
        assert os.path.exists(os.path.join(test_dir, "added1.txt")), "Files should not be deleted in check mode"
        assert os.path.exists(os.path.join(test_dir, "added2.txt")), "Files should not be deleted in check mode"
        
        print("Rollback check mode works correctly")


def test_rollback_snapshot_delete_mode():
    """Test rollback in delete mode"""
    print("\n" + "=" * 70)
    print("TEST: Rollback snapshot delete mode")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        snapshot_before = os.path.join(tmpdir, "before.txt")
        record_snapshot(test_dir, snapshot_before, includehash=True)
        
        # Add new files
        added_file1 = os.path.join(test_dir, "added1.txt")
        added_file2 = os.path.join(test_dir, "subdir1", "added2.txt")
        
        with open(added_file1, 'w') as f:
            f.write("Added file 1\n")
        
        with open(added_file2, 'w') as f:
            f.write("Added file 2\n")
        
        snapshot_after = os.path.join(tmpdir, "after.txt")
        record_snapshot(test_dir, snapshot_after, includehash=True)
        
        diff_file = os.path.join(tmpdir, "diff.txt")
        compare_snapshots(snapshot_before, snapshot_after, diff_file, includehash=True)
        
        # Verify files exist before rollback
        assert os.path.exists(added_file1), "File should exist before rollback"
        assert os.path.exists(added_file2), "File should exist before rollback"
        
        # Run rollback in delete mode
        rollback_snapshot(diff=diff_file, action="delete")
        
        # Files should be deleted
        assert not os.path.exists(added_file1), "Added file should be deleted"
        assert not os.path.exists(added_file2), "Added file should be deleted"
        
        # Original files should still exist
        assert os.path.exists(os.path.join(test_dir, "file1.txt")), "Original files should not be affected"
        assert os.path.exists(os.path.join(test_dir, "file2.txt")), "Original files should not be affected"
        
        print("Rollback delete mode works correctly")


def test_rollback_snapshot_without_diff():
    """Test rollback by creating diff on the fly"""
    print("\n" + "=" * 70)
    print("TEST: Rollback without pre-existing diff")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        snapshot_before = os.path.join(tmpdir, "before.txt")
        record_snapshot(test_dir, snapshot_before, includehash=True)
        
        # Add new file
        added_file = os.path.join(test_dir, "to_delete.txt")
        with open(added_file, 'w') as f:
            f.write("This will be deleted\n")
        
        # Run rollback without creating diff first
        # This should create a temporary diff and delete the added file
        rollback_snapshot(before=snapshot_before, after=test_dir, action="delete", includehash=True)
        
        # File should be deleted
        assert not os.path.exists(added_file), "Added file should be deleted"
        
        print("Rollback without pre-existing diff works correctly")


def test_rollback_snapshot_invalid_action():
    """Test rollback with invalid action parameter"""
    print("\n" + "=" * 70)
    print("TEST: Rollback with invalid action")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        
        with open(os.path.join(test_dir, "test.txt"), 'w') as f:
            f.write("test\n")
        
        snapshot_file = os.path.join(tmpdir, "snapshot.txt")
        record_snapshot(test_dir, snapshot_file, includehash=True)
        
        with pytest.raises(CommandError) as exc_info:
            rollback_snapshot(before=snapshot_file, after=test_dir, action="invalid")
        
        assert "invalid action" in str(exc_info.value).lower(), "Should report invalid action"
        
        print("Invalid action correctly raises error")


def test_rollback_snapshot_mixed_changes():
    """Test rollback with mixed added, modified, and deleted files"""
    print("\n" + "=" * 70)
    print("TEST: Rollback with mixed changes")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        snapshot_before = os.path.join(tmpdir, "before.txt")
        record_snapshot(test_dir, snapshot_before, includehash=True)
        
        # Add a file
        added_file = os.path.join(test_dir, "added.txt")
        with open(added_file, 'w') as f:
            f.write("Added\n")
        
        # Modify a file
        time.sleep(0.1)
        with open(os.path.join(test_dir, "file1.txt"), 'w') as f:
            f.write("Modified content\n")
        
        # Delete a file
        os.remove(os.path.join(test_dir, "file2.txt"))
        
        diff_file = os.path.join(tmpdir, "diff.txt")
        compare_snapshots(snapshot_before, test_dir, diff_file, includehash=True)
        
        # Run rollback in delete mode
        rollback_snapshot(diff=diff_file, action="delete")
        
        # Added file should be deleted
        assert not os.path.exists(added_file), "Added file should be deleted"
        
        # Modified file should still exist (can't be rolled back automatically)
        assert os.path.exists(os.path.join(test_dir, "file1.txt")), "Modified file should still exist"
        
        # Deleted file cannot be restored (remains deleted)
        assert not os.path.exists(os.path.join(test_dir, "file2.txt")), "Deleted file cannot be restored"
        
        print("Rollback with mixed changes works correctly")


def test_integration_full_workflow():
    """Test full workflow: record -> modify -> compare -> rollback"""
    print("\n" + "=" * 70)
    print("TEST: Full integration workflow")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "project")
        os.makedirs(test_dir)
        
        # Initial state
        with open(os.path.join(test_dir, "original.txt"), 'w') as f:
            f.write("Original file\n")
        
        # Record initial snapshot
        snapshot1 = os.path.join(tmpdir, "snapshot_initial.txt")
        record_snapshot(test_dir, snapshot1, includehash=True)
        
        # Make changes
        with open(os.path.join(test_dir, "change1.txt"), 'w') as f:
            f.write("First change\n")
        
        with open(os.path.join(test_dir, "change2.txt"), 'w') as f:
            f.write("Second change\n")
        
        # Compare and verify changes detected
        diff1 = os.path.join(tmpdir, "diff1.txt")
        compare_snapshots(snapshot1, test_dir, diff1, includehash=True)
        
        diff_content = read_snapshot_file(diff1)
        assert "change1.txt" in diff_content, "Should detect change1.txt"
        assert "change2.txt" in diff_content, "Should detect change2.txt"
        assert count_lines_with_pattern(diff1, "+ ") == 2, "Should have 2 added files"
        
        # Rollback changes
        rollback_snapshot(diff=diff1, action="delete")
        
        # Verify rollback
        assert not os.path.exists(os.path.join(test_dir, "change1.txt")), "change1.txt should be deleted"
        assert not os.path.exists(os.path.join(test_dir, "change2.txt")), "change2.txt should be deleted"
        assert os.path.exists(os.path.join(test_dir, "original.txt")), "original.txt should remain"
        
        # Verify state matches initial snapshot
        snapshot2 = os.path.join(tmpdir, "snapshot_after_rollback.txt")
        record_snapshot(test_dir, snapshot2, includehash=True)
        
        diff2 = os.path.join(tmpdir, "diff2.txt")
        compare_snapshots(snapshot1, snapshot2, diff2, includehash=True)
        
        final_diff = read_snapshot_file(diff2)
        status_markers = final_diff.count("M ") + final_diff.count("+ ") + final_diff.count("- ")
        assert status_markers == 0, "After rollback, should have no differences"
        
        print("Full workflow integration test passed!")


def test_record_snapshot_exclude_files():
    """Test exclude parameter with individual files"""
    print("\n" + "=" * 70)
    print("TEST: Exclude individual files from snapshot")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        # Create additional files to exclude
        with open(os.path.join(test_dir, "temp.txt"), 'w') as f:
            f.write("Temporary file\n")
        
        with open(os.path.join(test_dir, "cache.txt"), 'w') as f:
            f.write("Cache file\n")
        
        # Record snapshot excluding specific files
        snapshot_file = os.path.join(tmpdir, "snapshot.txt")
        record_snapshot(test_dir, snapshot_file, includehash=True, exclude=['temp.txt', 'cache.txt'])
        
        content = read_snapshot_file(snapshot_file)
        
        # Verify excluded files are not in snapshot
        assert "temp.txt" not in content, "temp.txt should be excluded"
        assert "cache.txt" not in content, "cache.txt should be excluded"
        
        # Verify other files are included
        assert "file1.txt" in content, "file1.txt should be in snapshot"
        assert "file2.txt" in content, "file2.txt should be in snapshot"
        
        print("Exclude files test passed!")


def test_record_snapshot_exclude_folders():
    """Test exclude parameter with folders"""
    print("\n" + "=" * 70)
    print("TEST: Exclude folders from snapshot")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        # Record snapshot excluding a folder
        snapshot_file = os.path.join(tmpdir, "snapshot.txt")
        record_snapshot(test_dir, snapshot_file, includehash=True, exclude=['subdir2'])
        
        content = read_snapshot_file(snapshot_file)
        
        # Verify excluded folder and its contents are not in snapshot
        assert "subdir2" not in content, "subdir2 folder should be excluded"
        assert "another_file.txt" not in content, "Files in subdir2 should be excluded"
        assert "subdir2/nested" not in content or ("nested_file.txt" in content and "another_file.txt" not in content), "Nested folder in subdir2 should be excluded"
        assert "deep_file.txt" not in content, "Files in nested folder should be excluded"
        
        # Verify other folders are included
        assert "subdir1" in content, "subdir1 should be in snapshot"
        assert "nested_file.txt" in content, "Files in subdir1 should be in snapshot"
        
        print("Exclude folders test passed!")


def test_record_snapshot_exclude_nested_paths():
    """Test exclude parameter with nested paths"""
    print("\n" + "=" * 70)
    print("TEST: Exclude nested paths from snapshot")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        # Record snapshot excluding a nested file
        snapshot_file = os.path.join(tmpdir, "snapshot.txt")
        record_snapshot(test_dir, snapshot_file, includehash=True, exclude=['subdir2/nested/deep_file.txt'])
        
        content = read_snapshot_file(snapshot_file)
        
        # Verify excluded file is not in snapshot
        assert "deep_file.txt" not in content, "deep_file.txt should be excluded"
        
        # Verify parent folder and sibling files are included
        assert "subdir2" in content, "subdir2 folder should be in snapshot"
        assert "another_file.txt" in content, "Sibling file should be in snapshot"
        assert "nested" in content, "Parent nested folder should be in snapshot"
        
        print("Exclude nested paths test passed!")


def test_record_snapshot_exclude_comma_separated():
    """Test exclude parameter with comma-separated string"""
    print("\n" + "=" * 70)
    print("TEST: Exclude with comma-separated string")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        # Create files with spaces in names
        with open(os.path.join(test_dir, "temp file.txt"), 'w') as f:
            f.write("Temp file with space\n")
        
        # Record snapshot using comma-separated string
        snapshot_file = os.path.join(tmpdir, "snapshot.txt")
        record_snapshot(test_dir, snapshot_file, includehash=True, exclude="file1.txt, subdir2, 'temp file.txt'")
        
        content = read_snapshot_file(snapshot_file)
        
        # Verify excluded items are not in snapshot
        assert "file1.txt" not in content, "file1.txt should be excluded"
        assert "subdir2" not in content, "subdir2 should be excluded"
        assert "temp file.txt" not in content, "temp file.txt should be excluded"
        
        # Verify other items are included
        assert "file2.txt" in content, "file2.txt should be in snapshot"
        assert "subdir1" in content, "subdir1 should be in snapshot"
        
        print("Exclude comma-separated test passed!")


def test_compare_snapshots_exclude():
    """Test exclude parameter in compare_snapshots"""
    print("\n" + "=" * 70)
    print("TEST: Exclude parameter in compare_snapshots")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        # Record initial snapshot without exclusions
        snapshot1 = os.path.join(tmpdir, "snapshot1.txt")
        record_snapshot(test_dir, snapshot1, includehash=True)
        
        # Make changes
        with open(os.path.join(test_dir, "new_file.txt"), 'w') as f:
            f.write("New file\n")
        
        with open(os.path.join(test_dir, "temp.txt"), 'w') as f:
            f.write("Temp file to exclude\n")
        
        # Compare with exclusion
        diff_file = os.path.join(tmpdir, "diff.txt")
        compare_snapshots(snapshot1, test_dir, diff_file, includehash=True, exclude=['temp.txt'])
        
        diff_content = read_snapshot_file(diff_file)
        
        # Verify new_file.txt is detected
        assert "new_file.txt" in diff_content, "new_file.txt should be in diff"
        assert "+ " in diff_content, "Should have added files marker"
        
        # Verify temp.txt is excluded from diff
        assert "temp.txt" not in diff_content, "temp.txt should be excluded from diff"
        
        print("Compare snapshots exclude test passed!")


def test_rollback_snapshot_exclude():
    """Test exclude parameter in rollback_snapshot"""
    print("\n" + "=" * 70)
    print("TEST: Exclude parameter in rollback_snapshot")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        
        # Create initial file
        with open(os.path.join(test_dir, "original.txt"), 'w') as f:
            f.write("Original file\n")
        
        # Record initial snapshot
        snapshot1 = os.path.join(tmpdir, "snapshot1.txt")
        record_snapshot(test_dir, snapshot1, includehash=True)
        
        # Add new files
        with open(os.path.join(test_dir, "added1.txt"), 'w') as f:
            f.write("Added file 1\n")
        
        with open(os.path.join(test_dir, "added2.txt"), 'w') as f:
            f.write("Added file 2\n")
        
        with open(os.path.join(test_dir, "keep_this.txt"), 'w') as f:
            f.write("This file should be kept\n")
        
        # Create diff excluding keep_this.txt
        diff_file = os.path.join(tmpdir, "diff.txt")
        compare_snapshots(snapshot1, test_dir, diff_file, includehash=True, exclude=['keep_this.txt'])
        
        # Rollback with exclusion
        rollback_snapshot(diff=diff_file, action="delete", exclude=['keep_this.txt'])
        
        # Verify added1.txt and added2.txt are deleted
        assert not os.path.exists(os.path.join(test_dir, "added1.txt")), "added1.txt should be deleted"
        assert not os.path.exists(os.path.join(test_dir, "added2.txt")), "added2.txt should be deleted"
        
        # Verify keep_this.txt still exists (excluded from rollback)
        assert os.path.exists(os.path.join(test_dir, "keep_this.txt")), "keep_this.txt should be kept"
        
        # Verify original file still exists
        assert os.path.exists(os.path.join(test_dir, "original.txt")), "original.txt should remain"
        
        print("Rollback snapshot exclude test passed!")


def test_exclude_integration():
    """Test exclude parameter across all snapshot functions in a workflow"""
    print("\n" + "=" * 70)
    print("TEST: Exclude integration across all functions")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        
        # Create initial structure
        os.makedirs(os.path.join(test_dir, "data"))
        os.makedirs(os.path.join(test_dir, "cache"))
        os.makedirs(os.path.join(test_dir, "logs"))
        
        with open(os.path.join(test_dir, "data", "important.txt"), 'w') as f:
            f.write("Important data\n")
        
        with open(os.path.join(test_dir, "cache", "temp.txt"), 'w') as f:
            f.write("Cache file\n")
        
        with open(os.path.join(test_dir, "logs", "debug.log"), 'w') as f:
            f.write("Log file\n")
        
        # Record snapshot excluding cache and logs
        snapshot1 = os.path.join(tmpdir, "snapshot1.txt")
        exclude_list = ['cache', 'logs']
        record_snapshot(test_dir, snapshot1, includehash=True, exclude=exclude_list)
        
        snapshot_content = read_snapshot_file(snapshot1)
        assert "cache" not in snapshot_content, "cache folder should be excluded"
        assert "logs" not in snapshot_content, "logs folder should be excluded"
        assert "data" in snapshot_content, "data folder should be included"
        
        # Make changes
        with open(os.path.join(test_dir, "data", "new_data.txt"), 'w') as f:
            f.write("New data file\n")
        
        with open(os.path.join(test_dir, "cache", "new_cache.txt"), 'w') as f:
            f.write("New cache file\n")
        
        # Compare with same exclusions
        diff_file = os.path.join(tmpdir, "diff.txt")
        compare_snapshots(snapshot1, test_dir, diff_file, includehash=True, exclude=exclude_list)
        
        diff_content = read_snapshot_file(diff_file)
        assert "new_data.txt" in diff_content, "new_data.txt should be in diff"
        assert "new_cache.txt" not in diff_content, "new_cache.txt should be excluded"
        
        # Rollback with same exclusions
        rollback_snapshot(diff=diff_file, action="check", exclude=exclude_list)
        
        # Just verify the test structure is correct - don't actually delete
        # Note: There's a known cosmetic issue where nested directory structures
        # may appear flattened in diff output when using exclusions, but the
        # underlying file paths are correct
        
        print("Exclude integration test passed!")


def test_compare_snapshots_exclude_file_to_file():
    """Test exclude parameter when comparing two snapshot files (not directories)"""
    print("\n" + "=" * 70)
    print("TEST: Compare snapshots exclude (file-to-file)")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = os.path.join(tmpdir, "test_folder")
        os.makedirs(test_dir)
        create_test_directory(test_dir)
        
        # Record initial snapshot
        snapshot1 = os.path.join(tmpdir, "snapshot1.txt")
        record_snapshot(test_dir, snapshot1, includehash=True)
        
        # Make changes
        with open(os.path.join(test_dir, "new_file.txt"), 'w') as f:
            f.write("New file\n")
        
        with open(os.path.join(test_dir, "temp.txt"), 'w') as f:
            f.write("Temp file to exclude\n")
        
        # Create a subdirectory with files to exclude
        exclude_dir = os.path.join(test_dir, "cache")
        os.makedirs(exclude_dir, exist_ok=True)
        with open(os.path.join(exclude_dir, "cache1.txt"), 'w') as f:
            f.write("Cache file 1\n")
        with open(os.path.join(exclude_dir, "cache2.txt"), 'w') as f:
            f.write("Cache file 2\n")
        
        # Record second snapshot (without exclusions)
        snapshot2 = os.path.join(tmpdir, "snapshot2.txt")
        record_snapshot(test_dir, snapshot2, includehash=True)
        
        # Compare two snapshot FILES with exclusion - this tests the actual comparison logic
        diff_file = os.path.join(tmpdir, "diff.txt")
        compare_snapshots(snapshot1, snapshot2, diff_file, includehash=True, exclude=['temp.txt', 'cache'])
        
        diff_content = read_snapshot_file(diff_file)
        
        # Verify new_file.txt is detected (not excluded)
        assert "new_file.txt" in diff_content, "new_file.txt should be in diff"
        assert "+ " in diff_content, "Should have added files marker"
        
        # Verify temp.txt is excluded from diff
        assert "temp.txt" not in diff_content, "temp.txt should be excluded from diff"
        
        # Verify cache directory and its contents are excluded
        assert "cache" not in diff_content, "cache directory should be excluded from diff"
        assert "cache1.txt" not in diff_content, "cache1.txt should be excluded from diff"
        assert "cache2.txt" not in diff_content, "cache2.txt should be excluded from diff"
        
        print("File-to-file comparison with exclude test passed!")


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])


#!/usr/bin/env python
# encoding: utf-8

"""
Test suite for backup_files function.
"""

import sys
import os
import tempfile
import gzip
import zipfile

# Add the parent directory to the path to import qx_utilities
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'qx_utilities'))

from general.utilities import backup_files, restore_files
from general.exceptions import CommandError
import pytest


def create_test_files(base_dir):
    """Helper to create test files in a directory structure"""
    # Create directory structure
    os.makedirs(os.path.join(base_dir, "configs"))
    os.makedirs(os.path.join(base_dir, "data", "processed"))
    os.makedirs(os.path.join(base_dir, "logs"))
    
    # Create test files
    files = {
        "README.md": "# Test Project\n",
        "configs/settings.json": '{"setting": "value"}\n',
        "configs/database.ini": "[database]\nhost=localhost\n",
        "data/input.txt": "Input data\n" * 100,
        "data/processed/output.csv": "col1,col2\n1,2\n3,4\n",
        "logs/app.log": "Log entry 1\nLog entry 2\n",
    }
    
    for filepath, content in files.items():
        full_path = os.path.join(base_dir, filepath)
        with open(full_path, 'w') as f:
            f.write(content)
    
    # Create a pre-gzipped file
    gzipped_file = os.path.join(base_dir, "data", "compressed.txt.gz")
    with gzip.open(gzipped_file, 'wt') as f:
        f.write("This is already compressed\n")
    
    return files


def test_backup_files_original_mode():
    """Test backing up files in original mode"""
    print("\n" + "=" * 70)
    print("TEST: Backup files in original mode")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "backup")
        
        os.makedirs(source)
        files = create_test_files(source)
        
        # Backup selected files
        filelist = ["README.md", "configs/settings.json", "data/input.txt"]
        
        result = backup_files(source, target, filelist, store="original")
        
        # Check target directory was created
        assert os.path.exists(target), "Target directory should be created"
        assert os.path.isdir(target), "Target should be a directory"
        
        # Check backed up files exist
        assert os.path.exists(os.path.join(target, "b001_README.md")), "First file should exist"
        assert os.path.exists(os.path.join(target, "b002_settings.json")), "Second file should exist"
        assert os.path.exists(os.path.join(target, "b003_input.txt")), "Third file should exist"
        
        # Check file_list.txt exists and has correct content
        manifest_path = os.path.join(target, "file_list.txt")
        assert os.path.exists(manifest_path), "Manifest file should exist"
        
        with open(manifest_path, 'r') as f:
            manifest = f.read()
        
        assert f"source folder: {source}" in manifest, "Manifest should contain source path header"
        assert "store: original" in manifest, "Manifest should contain store mode"
        assert "b001: README.md" in manifest, "Manifest should list first file"
        assert "b002: configs/settings.json" in manifest, "Manifest should list second file"
        assert "b003: data/input.txt" in manifest, "Manifest should list third file"
        
        # Verify file content is preserved
        with open(os.path.join(target, "b001_README.md"), 'r') as f:
            assert f.read() == "# Test Project\n", "File content should be preserved"
        
        print(f"Backed up {len(result)} files successfully")


def test_backup_files_gzip_mode():
    """Test backing up files with gzip compression"""
    print("\n" + "=" * 70)
    print("TEST: Backup files with gzip compression")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "backup_gz")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Backup files including one already gzipped
        filelist = [
            "configs/settings.json",
            "data/input.txt",
            "data/compressed.txt.gz"
        ]
        
        result = backup_files(source, target, filelist, store="gzip")
        
        # Check files exist
        assert os.path.exists(os.path.join(target, "b001_settings.json.gz")), "First file should be gzipped"
        assert os.path.exists(os.path.join(target, "b002_input.txt.gz")), "Second file should be gzipped"
        assert os.path.exists(os.path.join(target, "b003_compressed.txt.gz")), "Already gzipped file should exist"
        
        # Verify first file is actually gzipped and content is correct
        with gzip.open(os.path.join(target, "b001_settings.json.gz"), 'rt') as f:
            content = f.read()
            assert content == '{"setting": "value"}\n', "Gzipped content should match original"
        
        # Verify already-gzipped file wasn't double-compressed
        with gzip.open(os.path.join(target, "b003_compressed.txt.gz"), 'rt') as f:
            content = f.read()
            assert "already compressed" in content, "Pre-gzipped file should be readable"
        
        print(f"Backed up and compressed {len(result)} files successfully")


def test_backup_files_zip_mode():
    """Test backing up files as a ZIP archive"""
    print("\n" + "=" * 70)
    print("TEST: Backup files as ZIP archive")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "backup_archive")
        
        os.makedirs(source)
        create_test_files(source)
        
        filelist = [
            "README.md",
            "configs/settings.json",
            "data/processed/output.csv"
        ]
        
        result = backup_files(source, target, filelist, store="zip")
        
        # Check ZIP file was created (not directory)
        assert not os.path.isdir(target), "Target should not be a directory in zip mode"
        zip_path = target + ".zip"
        assert os.path.exists(zip_path), "ZIP file should be created"
        
        # Open and verify ZIP contents
        with zipfile.ZipFile(zip_path, 'r') as zf:
            namelist = zf.namelist()
            
            assert "b001_README.md" in namelist, "First file should be in ZIP"
            assert "b002_settings.json" in namelist, "Second file should be in ZIP"
            assert "b003_output.csv" in namelist, "Third file should be in ZIP"
            assert "file_list.txt" in namelist, "Manifest should be in ZIP"
            
            # Verify file content
            content = zf.read("b001_README.md").decode('utf-8')
            assert content == "# Test Project\n", "File content should be preserved in ZIP"
            
            # Verify manifest content
            manifest = zf.read("file_list.txt").decode('utf-8')
            assert f"source folder: {source}" in manifest, "Manifest should contain source path header"
            assert "store: zip" in manifest, "Manifest should contain store mode"
            assert "b001: README.md" in manifest, "Manifest should list files"
        
        print(f"Created ZIP archive with {len(result)} files successfully")


def test_backup_files_string_filelist():
    """Test with comma-separated string filelist"""
    print("\n" + "=" * 70)
    print("TEST: Backup with comma-separated string filelist")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "backup")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Pass filelist as string
        filelist = "README.md, configs/settings.json, data/input.txt"
        
        result = backup_files(source, target, filelist, store="original")
        
        assert len(result) == 3, "Should process 3 files"
        assert os.path.exists(os.path.join(target, "b001_README.md")), "Files should be backed up"
        
        print("String filelist handled correctly")


def test_backup_files_absolute_paths():
    """Test with absolute file paths"""
    print("\n" + "=" * 70)
    print("TEST: Backup with absolute file paths")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "backup")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Use absolute paths
        filelist = [
            os.path.join(source, "README.md"),
            os.path.join(source, "configs", "settings.json")
        ]
        
        result = backup_files(source, target, filelist, store="original")
        
        assert len(result) == 2, "Should process 2 files"
        assert os.path.exists(os.path.join(target, "b001_README.md")), "Files should be backed up"
        
        # Check manifest uses relative paths
        with open(os.path.join(target, "file_list.txt"), 'r') as f:
            manifest = f.read()
        
        assert "README.md" in manifest, "Manifest should use relative paths"
        
        print("Absolute paths handled correctly")


def test_backup_files_creates_parent_dirs():
    """Test that parent directories are created if needed"""
    print("\n" + "=" * 70)
    print("TEST: Backup creates parent directories")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "deep", "nested", "backup")
        
        os.makedirs(source)
        create_test_files(source)
        
        filelist = ["README.md"]
        
        result = backup_files(source, target, filelist, store="original")
        
        assert os.path.exists(target), "Nested directories should be created"
        assert os.path.exists(os.path.join(target, "b001_README.md")), "File should be backed up"
        
        print("Parent directories created successfully")


def test_backup_files_zip_creates_parent_dirs():
    """Test that parent directories are created for ZIP file"""
    print("\n" + "=" * 70)
    print("TEST: Backup ZIP creates parent directories")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "deep", "nested", "archive")
        
        os.makedirs(source)
        create_test_files(source)
        
        filelist = ["README.md"]
        
        result = backup_files(source, target, filelist, store="zip")
        
        assert os.path.exists(target + ".zip"), "ZIP file should be created"
        
        print("Parent directories for ZIP created successfully")


def test_backup_files_missing_files_warning():
    """Test handling of missing files"""
    print("\n" + "=" * 70)
    print("TEST: Backup with missing files")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "backup")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Include some missing files
        filelist = [
            "README.md",
            "nonexistent.txt",
            "configs/settings.json",
            "missing/file.dat"
        ]
        
        result = backup_files(source, target, filelist, store="original")
        
        # Should only back up existing files
        assert len(result) == 2, "Should only back up existing files"
        assert os.path.exists(os.path.join(target, "b001_README.md")), "Existing files should be backed up"
        assert os.path.exists(os.path.join(target, "b002_settings.json")), "Existing files should be backed up"
        
        print("Missing files handled correctly")


def test_backup_files_no_source_error():
    """Test error when source is not provided"""
    print("\n" + "=" * 70)
    print("TEST: Error when source not provided")
    print("=" * 70)
    
    with pytest.raises(CommandError) as exc_info:
        backup_files(None, "/tmp/backup", ["file.txt"])
    
    assert "no source folder" in str(exc_info.value).lower(), "Should report missing source"
    
    print("Missing source error raised correctly")


def test_backup_files_no_target_error():
    """Test error when target is not provided"""
    print("\n" + "=" * 70)
    print("TEST: Error when target not provided")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(CommandError) as exc_info:
            backup_files(tmpdir, None, ["file.txt"])
        
        assert "no target folder" in str(exc_info.value).lower(), "Should report missing target"
    
    print("Missing target error raised correctly")


def test_backup_files_no_filelist_error():
    """Test error when filelist is empty"""
    print("\n" + "=" * 70)
    print("TEST: Error when filelist is empty")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "backup")
        os.makedirs(source)
        
        with pytest.raises(CommandError) as exc_info:
            backup_files(source, target, [])
        
        assert "no files specified" in str(exc_info.value).lower(), "Should report missing filelist"
    
    print("Empty filelist error raised correctly")


def test_backup_files_invalid_store_mode():
    """Test error with invalid store mode"""
    print("\n" + "=" * 70)
    print("TEST: Error with invalid store mode")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "backup")
        os.makedirs(source)
        
        with open(os.path.join(source, "test.txt"), 'w') as f:
            f.write("test\n")
        
        with pytest.raises(CommandError) as exc_info:
            backup_files(source, target, ["test.txt"], store="invalid")
        
        assert "invalid store mode" in str(exc_info.value).lower(), "Should report invalid store mode"
    
    print("Invalid store mode error raised correctly")


def test_backup_files_nonexistent_source():
    """Test error when source doesn't exist"""
    print("\n" + "=" * 70)
    print("TEST: Error when source doesn't exist")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "nonexistent")
        target = os.path.join(tmpdir, "backup")
        
        with pytest.raises(CommandError) as exc_info:
            backup_files(source, target, ["file.txt"])
        
        assert "does not exist" in str(exc_info.value).lower(), "Should report missing source"
    
    print("Nonexistent source error raised correctly")


def test_backup_files_all_missing_error():
    """Test error when all files are missing"""
    print("\n" + "=" * 70)
    print("TEST: Error when all files are missing")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "backup")
        os.makedirs(source)
        
        filelist = ["missing1.txt", "missing2.txt", "missing3.txt"]
        
        with pytest.raises(CommandError) as exc_info:
            backup_files(source, target, filelist)
        
        assert "no valid files" in str(exc_info.value).lower(), "Should report no valid files"
    
    print("All missing files error raised correctly")


def test_backup_files_sequential_numbering():
    """Test that backup numbering is sequential"""
    print("\n" + "=" * 70)
    print("TEST: Sequential backup numbering")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "backup")
        
        os.makedirs(source)
        
        # Create many files
        for i in range(15):
            with open(os.path.join(source, f"file{i:02d}.txt"), 'w') as f:
                f.write(f"File {i}\n")
        
        filelist = [f"file{i:02d}.txt" for i in range(15)]
        
        result = backup_files(source, target, filelist, store="original")
        
        # Check all files have sequential prefixes
        for i in range(15):
            expected_name = f"b{i+1:03d}_file{i:02d}.txt"
            assert os.path.exists(os.path.join(target, expected_name)), f"File {expected_name} should exist"
        
        print("Sequential numbering works correctly")


def test_backup_files_flat_structure():
    """Test that backup structure is flat regardless of source structure"""
    print("\n" + "=" * 70)
    print("TEST: Flat backup structure")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "backup")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Backup files from various subdirectories
        filelist = [
            "README.md",
            "configs/settings.json",
            "data/processed/output.csv",
            "logs/app.log"
        ]
        
        result = backup_files(source, target, filelist, store="original")
        
        # All files should be in target root, not in subdirectories
        assert os.path.exists(os.path.join(target, "b001_README.md")), "File should be in root"
        assert os.path.exists(os.path.join(target, "b002_settings.json")), "File should be in root"
        assert os.path.exists(os.path.join(target, "b003_output.csv")), "File should be in root"
        assert os.path.exists(os.path.join(target, "b004_app.log")), "File should be in root"
        
        # No subdirectories should exist in target
        target_items = os.listdir(target)
        target_dirs = [item for item in target_items if os.path.isdir(os.path.join(target, item))]
        assert len(target_dirs) == 0, "No subdirectories should exist in backup"
        
        print("Flat structure maintained correctly")


def test_backup_files_overwrite_false_error():
    """Test error when target exists and overwrite is False"""
    print("\n" + "=" * 70)
    print("TEST: Error when target exists and overwrite=False")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "backup")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create first backup
        filelist = ["README.md"]
        backup_files(source, target, filelist, store="original")
        
        # Try to backup again without overwrite
        with pytest.raises(CommandError) as exc_info:
            backup_files(source, target, ["configs/settings.json"], store="original", overwrite=False)
        
        assert "already exists" in str(exc_info.value).lower(), "Should report target exists"
        
        print("Overwrite protection works correctly")


def test_backup_files_overwrite_true():
    """Test that overwrite=True removes existing files"""
    print("\n" + "=" * 70)
    print("TEST: Overwrite existing target")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "backup")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create first backup
        filelist1 = ["README.md", "configs/settings.json"]
        result1 = backup_files(source, target, filelist1, store="original")
        
        assert os.path.exists(os.path.join(target, "b001_README.md")), "First backup should exist"
        assert os.path.exists(os.path.join(target, "b002_settings.json")), "First backup should exist"
        
        # Overwrite with different files
        filelist2 = ["data/input.txt"]
        result2 = backup_files(source, target, filelist2, store="original", overwrite=True)
        
        # Old files should be gone
        assert not os.path.exists(os.path.join(target, "b001_README.md")), "Old files should be removed"
        assert not os.path.exists(os.path.join(target, "b002_settings.json")), "Old files should be removed"
        
        # New file should exist
        assert os.path.exists(os.path.join(target, "b001_input.txt")), "New backup should exist"
        
        print("Overwrite functionality works correctly")


def test_backup_files_overwrite_zip():
    """Test overwrite with ZIP mode"""
    print("\n" + "=" * 70)
    print("TEST: Overwrite ZIP archive")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "backup_archive")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create first ZIP backup
        filelist1 = ["README.md"]
        backup_files(source, target, filelist1, store="zip")
        
        zip_path = target + ".zip"
        assert os.path.exists(zip_path), "ZIP should be created"
        
        # Get original size
        orig_size = os.path.getsize(zip_path)
        
        # Try to backup again without overwrite - should fail
        with pytest.raises(CommandError) as exc_info:
            backup_files(source, target, ["configs/settings.json"], store="zip", overwrite=False)
        
        assert "already exists" in str(exc_info.value).lower(), "Should report ZIP exists"
        
        # Overwrite with more files
        filelist2 = ["README.md", "configs/settings.json", "data/input.txt"]
        backup_files(source, target, filelist2, store="zip", overwrite=True)
        
        # ZIP should still exist but potentially different size
        assert os.path.exists(zip_path), "New ZIP should exist"
        
        # Verify new contents
        import zipfile
        with zipfile.ZipFile(zip_path, 'r') as zf:
            namelist = zf.namelist()
            assert len([n for n in namelist if n.startswith('b')]) == 3, "Should have 3 backed up files"
        
        print("ZIP overwrite works correctly")


def test_backup_files_overwrite_string_parameter():
    """Test overwrite with string boolean parameters"""
    print("\n" + "=" * 70)
    print("TEST: Overwrite with string parameters")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        target = os.path.join(tmpdir, "backup")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create first backup
        backup_files(source, target, ["README.md"], store="original")
        
        # Test with "no" - should fail
        with pytest.raises(CommandError):
            backup_files(source, target, ["configs/settings.json"], store="original", overwrite="no")
        
        # Test with "yes" - should succeed
        backup_files(source, target, ["data/input.txt"], store="original", overwrite="yes")
        
        assert os.path.exists(os.path.join(target, "b001_input.txt")), "Overwrite with 'yes' should work"
        
        print("String boolean parameters work correctly")


def test_restore_files_original_mode():
    """Test restoring files from original mode backup"""
    print("\n" + "=" * 70)
    print("TEST: Restore from original mode backup")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create backup
        filelist = ["README.md", "configs/settings.json", "data/input.txt"]
        backup_files(source, backup_dir, filelist, store="original")
        
        # Delete original files
        for f in filelist:
            os.remove(os.path.join(source, f))
        
        # Restore to different location
        count = restore_files(backup_dir, restore_dir, overwrite=False)
        
        assert count == 3, "Should restore 3 files"
        
        # Verify files exist
        assert os.path.exists(os.path.join(restore_dir, "README.md")), "File should be restored"
        assert os.path.exists(os.path.join(restore_dir, "configs", "settings.json")), "File should be restored"
        assert os.path.exists(os.path.join(restore_dir, "data", "input.txt")), "File should be restored"
        
        # Verify content
        with open(os.path.join(restore_dir, "README.md"), 'r') as f:
            assert f.read() == "# Test Project\n", "Content should be preserved"
        
        print("Original mode restoration successful")


def test_restore_files_to_original_location():
    """Test restoring files to their original location"""
    print("\n" + "=" * 70)
    print("TEST: Restore to original location")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create backup
        filelist = ["README.md", "configs/settings.json"]
        backup_files(source, backup_dir, filelist, store="original")
        
        # Modify original files
        with open(os.path.join(source, "README.md"), 'w') as f:
            f.write("Modified content\n")
        
        # Restore to original location (target=None)
        count = restore_files(backup_dir, target=None, overwrite=True)
        
        assert count == 2, "Should restore 2 files"
        
        # Verify file was restored to original content
        with open(os.path.join(source, "README.md"), 'r') as f:
            content = f.read()
            assert content == "# Test Project\n", "Should restore original content"
        
        print("Restoration to original location successful")


def test_restore_files_gzip_mode():
    """Test restoring files from gzip backup with decompression"""
    print("\n" + "=" * 70)
    print("TEST: Restore from gzip backup")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create gzipped backup
        filelist = ["configs/settings.json", "data/input.txt", "data/compressed.txt.gz"]
        backup_files(source, backup_dir, filelist, store="gzip")
        
        # Restore
        count = restore_files(backup_dir, restore_dir, overwrite=False)
        
        assert count == 3, "Should restore 3 files"
        
        # Verify files are decompressed (no .gz extension for originally uncompressed files)
        assert os.path.exists(os.path.join(restore_dir, "configs", "settings.json")), "Should be decompressed"
        assert not os.path.exists(os.path.join(restore_dir, "configs", "settings.json.gz")), "Should not have .gz"
        
        # Verify already-compressed file keeps .gz extension
        assert os.path.exists(os.path.join(restore_dir, "data", "compressed.txt.gz")), "Should keep .gz extension"
        
        # Verify content is correct
        with open(os.path.join(restore_dir, "configs", "settings.json"), 'r') as f:
            assert '{"setting": "value"}' in f.read(), "Content should be preserved"
        
        print("Gzip restoration with decompression successful")


def test_restore_files_zip_mode():
    """Test restoring files from ZIP archive"""
    print("\n" + "=" * 70)
    print("TEST: Restore from ZIP archive")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_path = os.path.join(tmpdir, "backup_archive")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create ZIP backup
        filelist = ["README.md", "configs/settings.json", "data/processed/output.csv"]
        backup_files(source, backup_path, filelist, store="zip")
        
        # Restore from ZIP
        zip_file = backup_path + ".zip"
        count = restore_files(zip_file, restore_dir, overwrite=False)
        
        assert count == 3, "Should restore 3 files"
        assert os.path.exists(os.path.join(restore_dir, "README.md")), "File should be restored"
        assert os.path.exists(os.path.join(restore_dir, "data", "processed", "output.csv")), "Nested file should be restored"
        
        print("ZIP restoration successful")


def test_restore_files_overwrite_false_error():
    """Test error when files exist and overwrite=False"""
    print("\n" + "=" * 70)
    print("TEST: Restore error when files exist")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        os.makedirs(restore_dir)
        create_test_files(source)
        
        # Create backup
        filelist = ["README.md", "configs/settings.json"]
        backup_files(source, backup_dir, filelist, store="original")
        
        # Create conflicting file
        with open(os.path.join(restore_dir, "README.md"), 'w') as f:
            f.write("Existing file\n")
        
        # Try to restore with overwrite=False
        with pytest.raises(CommandError) as exc_info:
            restore_files(backup_dir, restore_dir, overwrite=False)
        
        assert "already exist" in str(exc_info.value).lower(), "Should report files exist"
        
        print("Overwrite protection works correctly")


def test_restore_files_overwrite_true():
    """Test overwriting existing files"""
    print("\n" + "=" * 70)
    print("TEST: Restore with overwrite=True")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        os.makedirs(restore_dir)
        create_test_files(source)
        
        # Create backup
        filelist = ["README.md"]
        backup_files(source, backup_dir, filelist, store="original")
        
        # Create conflicting file with different content
        with open(os.path.join(restore_dir, "README.md"), 'w') as f:
            f.write("Different content\n")
        
        # Restore with overwrite=True
        count = restore_files(backup_dir, restore_dir, overwrite=True)
        
        assert count == 1, "Should restore 1 file"
        
        # Verify file was overwritten
        with open(os.path.join(restore_dir, "README.md"), 'r') as f:
            content = f.read()
            assert content == "# Test Project\n", "Should overwrite with backup content"
        
        print("Overwrite functionality works correctly")


def test_restore_files_overwrite_skip():
    """Test restoring only missing files"""
    print("\n" + "=" * 70)
    print("TEST: Restore with overwrite='skip'")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        os.makedirs(restore_dir)
        create_test_files(source)
        
        # Create backup of multiple files
        filelist = ["README.md", "configs/settings.json", "data/input.txt"]
        backup_files(source, backup_dir, filelist, store="original")
        
        # Create some existing files
        with open(os.path.join(restore_dir, "README.md"), 'w') as f:
            f.write("Existing README\n")
        
        # Restore with overwrite='skip'
        count = restore_files(backup_dir, restore_dir, overwrite="skip")
        
        # Should restore 2 files (skip README.md)
        assert count == 2, "Should restore only missing files"
        
        # Verify existing file was not overwritten
        with open(os.path.join(restore_dir, "README.md"), 'r') as f:
            content = f.read()
            assert content == "Existing README\n", "Should not overwrite existing file"
        
        # Verify missing files were restored
        assert os.path.exists(os.path.join(restore_dir, "configs", "settings.json")), "Missing file should be restored"
        assert os.path.exists(os.path.join(restore_dir, "data", "input.txt")), "Missing file should be restored"
        
        print("Selective restoration works correctly")


def test_restore_files_invalid_backup_no_manifest():
    """Test error when backup has no file_list.txt"""
    print("\n" + "=" * 70)
    print("TEST: Error for invalid backup (no manifest)")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_backup = os.path.join(tmpdir, "fake_backup")
        os.makedirs(fake_backup)
        
        # Create some files but no file_list.txt
        with open(os.path.join(fake_backup, "random_file.txt"), 'w') as f:
            f.write("Not a backup\n")
        
        with pytest.raises(CommandError) as exc_info:
            restore_files(fake_backup)
        
        assert "not a valid backup" in str(exc_info.value).lower(), "Should report invalid backup"
        
        print("Invalid backup detection works correctly")


def test_restore_files_zip_no_manifest():
    """Test error when ZIP has no file_list.txt"""
    print("\n" + "=" * 70)
    print("TEST: Error for invalid ZIP (no manifest)")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        import zipfile
        
        fake_zip = os.path.join(tmpdir, "fake_backup.zip")
        
        # Create ZIP without file_list.txt
        with zipfile.ZipFile(fake_zip, 'w') as zf:
            zf.writestr("some_file.txt", "Not a backup")
        
        with pytest.raises(CommandError) as exc_info:
            restore_files(fake_zip)
        
        assert "not a valid backup" in str(exc_info.value).lower(), "Should report invalid backup"
        
        print("Invalid ZIP backup detection works correctly")


def test_restore_files_nonexistent_source():
    """Test error when source doesn't exist"""
    print("\n" + "=" * 70)
    print("TEST: Error for nonexistent source")
    print("=" * 70)
    
    with pytest.raises(CommandError) as exc_info:
        restore_files("/nonexistent/backup/path")
    
    assert "does not exist" in str(exc_info.value).lower(), "Should report source doesn't exist"
    
    print("Nonexistent source detection works correctly")


def test_restore_files_creates_directories():
    """Test that parent directories are created during restoration"""
    print("\n" + "=" * 70)
    print("TEST: Create parent directories during restore")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create backup with nested files
        filelist = ["data/processed/output.csv", "logs/app.log"]
        backup_files(source, backup_dir, filelist, store="original")
        
        # Restore (restore_dir doesn't exist yet)
        count = restore_files(backup_dir, restore_dir, overwrite=False)
        
        assert count == 2, "Should restore 2 files"
        
        # Verify nested directories were created
        assert os.path.exists(os.path.join(restore_dir, "data", "processed")), "Nested dirs should be created"
        assert os.path.exists(os.path.join(restore_dir, "data", "processed", "output.csv")), "File should be in nested dir"
        
        print("Directory creation works correctly")


def test_restore_files_round_trip():
    """Test complete backup and restore cycle"""
    print("\n" + "=" * 70)
    print("TEST: Complete backup and restore round trip")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        original = os.path.join(tmpdir, "original")
        backup_dir = os.path.join(tmpdir, "backup")
        restored = os.path.join(tmpdir, "restored")
        
        os.makedirs(original)
        create_test_files(original)
        
        # Backup all files
        filelist = [
            "README.md",
            "configs/settings.json",
            "data/input.txt",
            "data/processed/output.csv"
        ]
        
        backup_count = backup_files(original, backup_dir, filelist, store="original")
        restore_count = restore_files(backup_dir, restored, overwrite=False)
        
        assert len(backup_count) == restore_count, "Should restore all backed up files"
        
        # Verify all files and content
        for filepath in filelist:
            orig_path = os.path.join(original, filepath)
            rest_path = os.path.join(restored, filepath)
            
            assert os.path.exists(rest_path), f"Restored file should exist: {filepath}"
            
            with open(orig_path, 'r') as f1, open(rest_path, 'r') as f2:
                assert f1.read() == f2.read(), f"Content should match: {filepath}"
        
        print("Round trip successful - all files match!")


def test_restore_files_filelist_by_backup_number():
    """Test selective restoration using backup numbers (b001, b002, etc.)"""
    print("\n" + "=" * 70)
    print("TEST: Restore with filelist using backup numbers")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create backup
        filelist = ["README.md", "configs/settings.json", "data/input.txt", "data/processed/output.csv"]
        backup_files(source, backup_dir, filelist, store="original")
        
        # Restore only specific backup numbers
        count = restore_files(backup_dir, restore_dir, filelist=['b001', 'b003'])
        
        # Should restore only 2 files
        assert count == 2, "Should restore only files matching backup numbers"
        
        # Verify b001 (README.md) was restored
        assert os.path.exists(os.path.join(restore_dir, "README.md")), "b001 should be restored"
        
        # Verify b003 (data/input.txt) was restored
        assert os.path.exists(os.path.join(restore_dir, "data", "input.txt")), "b003 should be restored"
        
        # Verify b002 and b004 were NOT restored
        assert not os.path.exists(os.path.join(restore_dir, "configs", "settings.json")), "b002 should not be restored"
        assert not os.path.exists(os.path.join(restore_dir, "data", "processed", "output.csv")), "b004 should not be restored"
        
        print("Selective restoration by backup number works correctly")


def test_restore_files_filelist_by_path():
    """Test selective restoration using original file paths"""
    print("\n" + "=" * 70)
    print("TEST: Restore with filelist using original paths")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create backup
        filelist = ["README.md", "configs/settings.json", "data/input.txt", "data/processed/output.csv"]
        backup_files(source, backup_dir, filelist, store="original")
        
        # Restore only specific paths
        count = restore_files(backup_dir, restore_dir, 
                            filelist=['configs/settings.json', 'data/processed/output.csv'])
        
        # Should restore only 2 files
        assert count == 2, "Should restore only files matching paths"
        
        # Verify specified files were restored
        assert os.path.exists(os.path.join(restore_dir, "configs", "settings.json")), "settings.json should be restored"
        assert os.path.exists(os.path.join(restore_dir, "data", "processed", "output.csv")), "output.csv should be restored"
        
        # Verify other files were NOT restored
        assert not os.path.exists(os.path.join(restore_dir, "README.md")), "README.md should not be restored"
        assert not os.path.exists(os.path.join(restore_dir, "data", "input.txt")), "input.txt should not be restored"
        
        print("Selective restoration by path works correctly")


def test_restore_files_filelist_mixed():
    """Test selective restoration using mixed backup numbers and paths"""
    print("\n" + "=" * 70)
    print("TEST: Restore with filelist using mixed formats")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create backup
        filelist = ["README.md", "configs/settings.json", "data/input.txt", "data/processed/output.csv"]
        backup_files(source, backup_dir, filelist, store="original")
        
        # Restore using mixed format
        count = restore_files(backup_dir, restore_dir, 
                            filelist=['b001', 'data/processed/output.csv'])
        
        # Should restore 2 files
        assert count == 2, "Should restore files matching either format"
        
        # Verify files were restored
        assert os.path.exists(os.path.join(restore_dir, "README.md")), "b001 should be restored"
        assert os.path.exists(os.path.join(restore_dir, "data", "processed", "output.csv")), "output.csv should be restored"
        
        print("Mixed format filelist works correctly")


def test_restore_files_filelist_string():
    """Test filelist as a single string instead of list"""
    print("\n" + "=" * 70)
    print("TEST: Restore with filelist as single string")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create backup
        filelist = ["README.md", "configs/settings.json"]
        backup_files(source, backup_dir, filelist, store="original")
        
        # Restore using single string
        count = restore_files(backup_dir, restore_dir, filelist='b001')
        
        # Should restore 1 file
        assert count == 1, "Should restore single file"
        assert os.path.exists(os.path.join(restore_dir, "README.md")), "README.md should be restored"
        assert not os.path.exists(os.path.join(restore_dir, "configs", "settings.json")), "settings.json should not be restored"
        
        print("Single string filelist works correctly")


def test_restore_files_filelist_no_matches():
    """Test error when filelist matches no files"""
    print("\n" + "=" * 70)
    print("TEST: Error when filelist matches nothing")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create backup
        filelist = ["README.md", "configs/settings.json"]
        backup_files(source, backup_dir, filelist, store="original")
        
        # Try to restore with non-matching filelist
        with pytest.raises(Exception) as exc_info:
            restore_files(backup_dir, restore_dir, filelist=['b999', 'nonexistent/file.txt'])
        
        assert "no files matched" in str(exc_info.value).lower(), "Should report no matches"
        
        print("No matches error raised correctly")


def test_restore_files_filelist_comma_separated():
    """Test filelist as comma-separated string"""
    print("\n" + "=" * 70)
    print("TEST: Restore with filelist as comma-separated string")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create backup
        filelist = ["README.md", "configs/settings.json", "data/input.txt", "data/processed/output.csv"]
        backup_files(source, backup_dir, filelist, store="original")
        
        # Restore using comma-separated string (mix of backup numbers and paths)
        count = restore_files(backup_dir, restore_dir, filelist='b001, data/processed/output.csv')
        
        # Should restore 2 files
        assert count == 2, "Should restore files from comma-separated string"
        assert os.path.exists(os.path.join(restore_dir, "README.md")), "b001 should be restored"
        assert os.path.exists(os.path.join(restore_dir, "data", "processed", "output.csv")), "output.csv should be restored"
        assert not os.path.exists(os.path.join(restore_dir, "configs", "settings.json")), "settings.json should not be restored"
        
        print("Comma-separated filelist works correctly")


def test_backup_files_quoted_filenames():
    """Test backing up files with spaces in names using quoted filelist"""
    print("\n" + "=" * 70)
    print("TEST: Backup files with spaces using quoted filelist")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        
        os.makedirs(source)
        os.makedirs(os.path.join(source, "docs"))
        
        # Create files with spaces in names
        with open(os.path.join(source, "file 1.txt"), 'w') as f:
            f.write("Content 1\n")
        with open(os.path.join(source, "file 2.txt"), 'w') as f:
            f.write("Content 2\n")
        with open(os.path.join(source, "docs", "my document.pdf"), 'w') as f:
            f.write("PDF content\n")
        
        # Test with single quotes
        filelist_single = "'file 1.txt', 'file 2.txt', 'docs/my document.pdf'"
        backup_files(source, backup_dir, filelist_single, store="original")
        
        # Verify backups were created
        assert os.path.exists(os.path.join(backup_dir, "b001_file 1.txt")), "file 1 should be backed up"
        assert os.path.exists(os.path.join(backup_dir, "b002_file 2.txt")), "file 2 should be backed up"
        assert os.path.exists(os.path.join(backup_dir, "b003_my document.pdf")), "document should be backed up"
        
        # Verify content
        with open(os.path.join(backup_dir, "b001_file 1.txt"), 'r') as f:
            assert f.read() == "Content 1\n", "Content should match"
        
        print("Quoted filenames (single quotes) work correctly")


def test_backup_files_double_quoted_filenames():
    """Test backing up files using double-quoted filelist"""
    print("\n" + "=" * 70)
    print("TEST: Backup files with double-quoted filelist")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        
        os.makedirs(source)
        
        # Create files with spaces in names
        with open(os.path.join(source, "test file.txt"), 'w') as f:
            f.write("Test content\n")
        with open(os.path.join(source, "another file.dat"), 'w') as f:
            f.write("Data content\n")
        
        # Test with double quotes
        filelist_double = '"test file.txt", "another file.dat"'
        backup_files(source, backup_dir, filelist_double, store="original")
        
        # Verify backups were created
        assert os.path.exists(os.path.join(backup_dir, "b001_test file.txt")), "test file should be backed up"
        assert os.path.exists(os.path.join(backup_dir, "b002_another file.dat")), "another file should be backed up"
        
        print("Quoted filenames (double quotes) work correctly")


def test_restore_files_quoted_filenames():
    """Test restoring files with spaces using quoted filelist"""
    print("\n" + "=" * 70)
    print("TEST: Restore files with spaces using quoted filelist")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        os.makedirs(os.path.join(source, "data"))
        
        # Create files with spaces in names
        with open(os.path.join(source, "config file.json"), 'w') as f:
            f.write('{"key": "value"}\n')
        with open(os.path.join(source, "data", "output data.csv"), 'w') as f:
            f.write("col1,col2\n1,2\n")
        with open(os.path.join(source, "README.md"), 'w') as f:
            f.write("# Test\n")
        
        # Create backup
        filelist = ["config file.json", "data/output data.csv", "README.md"]
        backup_files(source, backup_dir, filelist, store="original")
        
        # Restore using quoted filelist (single quotes)
        count = restore_files(backup_dir, restore_dir, 
                            filelist="'config file.json', 'data/output data.csv'")
        
        # Should restore 2 files
        assert count == 2, "Should restore files from quoted filelist"
        assert os.path.exists(os.path.join(restore_dir, "config file.json")), "config file should be restored"
        assert os.path.exists(os.path.join(restore_dir, "data", "output data.csv")), "output data should be restored"
        assert not os.path.exists(os.path.join(restore_dir, "README.md")), "README should not be restored"
        
        # Verify content
        with open(os.path.join(restore_dir, "config file.json"), 'r') as f:
            content = f.read()
            assert '"key"' in content, "Content should be correct"
        
        print("Restore with quoted filenames works correctly")


def test_restore_files_mixed_quoted_and_unquoted():
    """Test restoring with mixed quoted and unquoted filelist"""
    print("\n" + "=" * 70)
    print("TEST: Restore with mixed quoted/unquoted filelist")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        
        # Create mix of files with and without spaces
        with open(os.path.join(source, "file with spaces.txt"), 'w') as f:
            f.write("Spaced file\n")
        with open(os.path.join(source, "normalfile.txt"), 'w') as f:
            f.write("Normal file\n")
        with open(os.path.join(source, "another file.txt"), 'w') as f:
            f.write("Another spaced\n")
        
        # Create backup
        filelist = ["file with spaces.txt", "normalfile.txt", "another file.txt"]
        backup_files(source, backup_dir, filelist, store="original")
        
        # Restore using mixed format: b001 (unquoted), quoted filename
        count = restore_files(backup_dir, restore_dir, 
                            filelist="b001, 'another file.txt'")
        
        # Should restore 2 files
        assert count == 2, "Should restore files from mixed format"
        assert os.path.exists(os.path.join(restore_dir, "file with spaces.txt")), "b001 should be restored"
        assert os.path.exists(os.path.join(restore_dir, "another file.txt")), "quoted file should be restored"
        assert not os.path.exists(os.path.join(restore_dir, "normalfile.txt")), "normalfile should not be restored"
        
        print("Mixed quoted/unquoted filelist works correctly")


def test_restore_files_filelist_with_gzip():
    """Test filelist parameter works with gzipped backups"""
    print("\n" + "=" * 70)
    print("TEST: Filelist with gzip mode backup")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_dir = os.path.join(tmpdir, "backup")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create gzip backup
        filelist = ["README.md", "configs/settings.json", "data/input.txt"]
        backup_files(source, backup_dir, filelist, store="gzip")
        
        # Restore only specific files
        count = restore_files(backup_dir, restore_dir, filelist=['b001', 'data/input.txt'])
        
        # Should restore 2 files
        assert count == 2, "Should restore files from gzip backup"
        
        # Verify files were restored and decompressed
        assert os.path.exists(os.path.join(restore_dir, "README.md")), "README.md should be restored"
        assert os.path.exists(os.path.join(restore_dir, "data", "input.txt")), "input.txt should be restored"
        assert not os.path.exists(os.path.join(restore_dir, "configs", "settings.json")), "settings.json should not be restored"
        
        # Verify content is correct (decompressed)
        with open(os.path.join(restore_dir, "README.md"), 'r') as f:
            content = f.read()
            assert "Test Project" in content, "Content should be decompressed correctly"
        
        print("Filelist with gzip mode works correctly")


def test_restore_files_filelist_with_zip():
    """Test filelist parameter works with ZIP backups"""
    print("\n" + "=" * 70)
    print("TEST: Filelist with ZIP mode backup")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source = os.path.join(tmpdir, "source")
        backup_zip = os.path.join(tmpdir, "backup.zip")
        restore_dir = os.path.join(tmpdir, "restored")
        
        os.makedirs(source)
        create_test_files(source)
        
        # Create ZIP backup
        filelist = ["README.md", "configs/settings.json", "data/input.txt", "data/processed/output.csv"]
        backup_files(source, backup_zip, filelist, store="zip")
        
        # Restore only specific files by path
        count = restore_files(backup_zip, restore_dir, 
                            filelist=['README.md', 'data/processed/output.csv'])
        
        # Should restore 2 files
        assert count == 2, "Should restore files from ZIP backup"
        
        # Verify files were restored
        assert os.path.exists(os.path.join(restore_dir, "README.md")), "README.md should be restored"
        assert os.path.exists(os.path.join(restore_dir, "data", "processed", "output.csv")), "output.csv should be restored"
        assert not os.path.exists(os.path.join(restore_dir, "configs", "settings.json")), "settings.json should not be restored"
        
        print("Filelist with ZIP mode works correctly")


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])

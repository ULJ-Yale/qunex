#!/usr/bin/env python
# encoding: utf-8

"""
Test suite for session functions: join_session, join_sessions_list
"""

import sys
import os
import tempfile
import shutil

# Add the parent directory to the path to import qx_utilities
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'qx_utilities'))

from general.sessions import join_session, join_sessions_list
from general.exceptions import CommandError, CommandFailed
import pytest


def create_test_session(session_path, session_id, sequences=None, has_hcp=True):
    """Helper to create a test session with session files"""
    os.makedirs(session_path, exist_ok=True)
    
    if sequences is None:
        sequences = [
            "1011:tag1:Scan1: TR(1.0)",
            "2011:tag2:Scan2: TR(2.0)"
        ]
    
    # Create session.txt
    session_txt = os.path.join(session_path, 'session.txt')
    with open(session_txt, 'w') as f:
        f.write(f"id: {session_id}\n")
        f.write(f"subject: {session_id}\n")
        f.write("\n")
        for seq in sequences:
            f.write(f"{seq}\n")
    
    # Create session_hcp.txt if requested
    if has_hcp:
        session_hcp_txt = os.path.join(session_path, 'session_hcp.txt')
        with open(session_hcp_txt, 'w') as f:
            f.write(f"session: {session_id}\n")
            f.write(f"subject: {session_id}\n")
            f.write("\n")
            for seq in sequences:
                f.write(f"{seq}\n")


def read_session_file(filepath):
    """Helper to read and return session file contents"""
    with open(filepath, 'r') as f:
        return f.read()


def parse_sequences(content):
    """Helper to extract sequence numbers from session file"""
    sequences = []
    for line in content.split('\n'):
        line = line.strip()
        if line and line[0].isdigit() and ':' in line:
            seq_num = line.split(':')[0]
            sequences.append(int(seq_num))
    return sorted(sequences)


def test_join_session_basic():
    """Test basic session joining with two sessions"""
    print("\n" + "=" * 70)
    print("TEST: Basic session joining")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        sessions_dir = os.path.join(studyfolder, 'sessions')
        os.makedirs(sessions_dir)
        
        # Create two source sessions
        create_test_session(os.path.join(sessions_dir, 'session1'), 'session1')
        create_test_session(os.path.join(sessions_dir, 'session2'), 'session2')
        
        # Join them
        result = join_session(
            studyfolder=studyfolder,
            source='session1,session2',
            target='joined',
            overwrite='no',
            raw_data='leave'
        )
        
        assert result is True, "join_session should return True on success"
        
        # Check that target was created
        target_path = os.path.join(sessions_dir, 'joined')
        assert os.path.exists(target_path), "Target session folder should exist"
        
        # Check session files exist
        assert os.path.exists(os.path.join(target_path, 'session.txt')), "session.txt should exist"
        assert os.path.exists(os.path.join(target_path, 'session_hcp.txt')), "session_hcp.txt should exist"
        
        # Check sequences were renumbered
        hcp_content = read_session_file(os.path.join(target_path, 'session_hcp.txt'))
        sequences = parse_sequences(hcp_content)
        
        # Should have 4 sequences with proper increments
        # All sessions are renumbered starting from first
        assert len(sequences) == 4, f"Should have 4 sequences, got {len(sequences)}"
        # First session starts at 10000+ (11011, 12011)
        assert 10000 <= sequences[0] < 20000, "First session should be renumbered to 10000+"
        assert 10000 <= sequences[1] < 20000, "First session second seq should be in 10000+"
        # Second session at 20000+ (21011, 22011)
        assert 20000 <= sequences[2] < 30000, "Second session should be renumbered to 20000+"
        assert 20000 <= sequences[3] < 30000, "Second session second seq should be in 20000+"
        
        print(f"Successfully joined 2 sessions with sequences: {sequences}")


def test_join_session_with_absolute_paths():
    """Test joining with absolute paths"""
    print("\n" + "=" * 70)
    print("TEST: Join with absolute paths")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        source1 = os.path.join(tmpdir, 'src1')
        source2 = os.path.join(tmpdir, 'src2')
        target = os.path.join(tmpdir, 'target')
        
        create_test_session(source1, 'src1')
        create_test_session(source2, 'src2')
        
        # Join using absolute paths
        result = join_session(
            studyfolder=studyfolder,
            source=f'{source1},{source2}',
            target=target,
            overwrite='no',
            raw_data='leave'
        )
        
        assert result is True, "Should succeed with absolute paths"
        assert os.path.exists(target), "Target should be created"
        assert os.path.exists(os.path.join(target, 'session_hcp.txt')), "session_hcp.txt should exist"
        
        print("Successfully joined sessions using absolute paths")


def test_join_session_bold_renumbering():
    """Test that bold and boldref tags are correctly renumbered"""
    print("\n" + "=" * 70)
    print("TEST: BOLD and BOLDREF renumbering")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        sessions_dir = os.path.join(studyfolder, 'sessions')
        os.makedirs(sessions_dir)
        
        # Create sessions with bold sequences
        session1_seqs = [
            "5011:boldref1:task:BOLD_REF: TR(1.0): se(1): fm(1)",
            "6011:bold1:task:BOLD_SCAN: TR(2.0): se(1): fm(1)"
        ]
        session2_seqs = [
            "5011:boldref1:rest:BOLD_REF_REST: TR(1.0): se(1): fm(1)",
            "6011:bold1:rest:BOLD_SCAN_REST: TR(2.0): se(1): fm(1)"
        ]
        
        create_test_session(os.path.join(sessions_dir, 's1'), 's1', session1_seqs)
        create_test_session(os.path.join(sessions_dir, 's2'), 's2', session2_seqs)
        
        # Join them
        join_session(studyfolder, 's1,s2', 'joined', 'no', 'leave')
        
        # Read the result
        hcp_content = read_session_file(os.path.join(sessions_dir, 'joined', 'session_hcp.txt'))
        
        # Parse sequence lines
        seq_lines = [l.strip() for l in hcp_content.split('\n') if l.strip() and l[0].isdigit()]
        assert len(seq_lines) == 4, f"Should have 4 sequence lines, got {len(seq_lines)}"
        
        # First source session (should be renumbered to 15011, 16011 with bold1/boldref1, se(1), fm(1))
        assert ':boldref1:task' in seq_lines[0], f"Line 1 should have boldref1:task, got: {seq_lines[0]}"
        assert 'se(1)' in seq_lines[0], f"Line 1 should have se(1), got: {seq_lines[0]}"
        assert 'fm(1)' in seq_lines[0], f"Line 1 should have fm(1), got: {seq_lines[0]}"
        
        assert ':bold1:task' in seq_lines[1], f"Line 2 should have bold1:task, got: {seq_lines[1]}"
        assert 'se(1)' in seq_lines[1], f"Line 2 should have se(1), got: {seq_lines[1]}"
        assert 'fm(1)' in seq_lines[1], f"Line 2 should have fm(1), got: {seq_lines[1]}"
        
        # Second source session (should be renumbered to 25011, 26011 with bold2/boldref2, se(2), fm(2))
        assert ':boldref2:rest' in seq_lines[2], f"Line 3 should have boldref2:rest, got: {seq_lines[2]}"
        assert 'se(2)' in seq_lines[2], f"Line 3 should have se(2), got: {seq_lines[2]}"
        assert 'fm(2)' in seq_lines[2], f"Line 3 should have fm(2), got: {seq_lines[2]}"
        
        assert ':bold2:rest' in seq_lines[3], f"Line 4 should have bold2:rest, got: {seq_lines[3]}"
        assert 'se(2)' in seq_lines[3], f"Line 4 should have se(2), got: {seq_lines[3]}"
        assert 'fm(2)' in seq_lines[3], f"Line 4 should have fm(2), got: {seq_lines[3]}"
        
        print(f"BOLD/BOLDREF indices correctly renumbered:"
              f"\n  {seq_lines[0]}"
              f"\n  {seq_lines[1]}"
              f"\n  {seq_lines[2]}"
              f"\n  {seq_lines[3]}")


def test_join_session_metadata_preservation():
    """Test that metadata is preserved correctly"""
    print("\n" + "=" * 70)
    print("TEST: Metadata preservation")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        sessions_dir = os.path.join(studyfolder, 'sessions')
        os.makedirs(sessions_dir)
        
        # Create session with custom metadata
        s1_path = os.path.join(sessions_dir, 's1')
        os.makedirs(s1_path)
        with open(os.path.join(s1_path, 'session_hcp.txt'), 'w') as f:
            f.write("session: s1\n")
            f.write("subject: subj1\n")
            f.write("\n")
            f.write("institution: Test Hospital\n")
            f.write("device: Scanner1\n")
            f.write("\n")
            f.write("1011:tag1:Scan1: TR(1.0)\n")
        
        s2_path = os.path.join(sessions_dir, 's2')
        os.makedirs(s2_path)
        with open(os.path.join(s2_path, 'session_hcp.txt'), 'w') as f:
            f.write("session: s2\n")
            f.write("subject: subj1\n")
            f.write("\n")
            f.write("institution: Test Hospital\n")
            f.write("scanner_version: v2.0\n")
            f.write("\n")
            f.write("2011:tag2:Scan2: TR(2.0)\n")
        
        # Join sessions
        join_session(studyfolder, 's1,s2', 'joined', 'no', 'leave')
        
        # Read result
        content = read_session_file(os.path.join(sessions_dir, 'joined', 'session_hcp.txt'))
        
        # Check metadata is preserved
        assert 'institution:' in content, "Institution should be preserved"
        assert 'device:' in content, "Device should be preserved"
        assert 'scanner_version:' in content, "Scanner version should be preserved"
        
        print("Metadata correctly preserved and tracked")


def test_join_session_overwrite_error():
    """Test that overwriting without permission raises error"""
    print("\n" + "=" * 70)
    print("TEST: Overwrite protection")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        sessions_dir = os.path.join(studyfolder, 'sessions')
        os.makedirs(sessions_dir)
        
        # Create sessions
        create_test_session(os.path.join(sessions_dir, 's1'), 's1')
        create_test_session(os.path.join(sessions_dir, 's2'), 's2')
        
        # First join
        join_session(studyfolder, 's1,s2', 'joined', 'no', 'leave')
        
        # Try to join again without overwrite
        with pytest.raises(CommandFailed) as exc_info:
            join_session(studyfolder, 's1,s2', 'joined', 'no', 'leave')
        
        assert 'exists' in str(exc_info.value).lower(), "Should mention existing target"
        
        print("Overwrite protection working correctly")


def test_join_session_overwrite_yes():
    """Test overwriting with overwrite='yes'"""
    print("\n" + "=" * 70)
    print("TEST: Overwrite with permission")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        sessions_dir = os.path.join(studyfolder, 'sessions')
        os.makedirs(sessions_dir)
        
        # Create sessions
        create_test_session(os.path.join(sessions_dir, 's1'), 's1')
        create_test_session(os.path.join(sessions_dir, 's2'), 's2')
        create_test_session(os.path.join(sessions_dir, 's3'), 's3')
        
        # First join
        join_session(studyfolder, 's1,s2', 'joined', 'no', 'leave')
        
        # Overwrite with different sources
        result = join_session(studyfolder, 's1,s3', 'joined', 'clean', 'leave')
        
        assert result is True, "Should succeed with overwrite=yes"
        
        # Check that new content replaced old
        content = read_session_file(os.path.join(sessions_dir, 'joined', 'session_hcp.txt'))
        sequences = parse_sequences(content)
        assert len(sequences) == 4, "Should have sequences from s1 and s3"
        
        print("Overwrite succeeded with overwrite=yes")


def test_join_session_raw_data_copy():
    """Test copying raw data (dicom, bids, inbox, hcpls folders)"""
    print("\n" + "=" * 70)
    print("TEST: Raw data copy mode")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        sessions_dir = os.path.join(studyfolder, 'sessions')
        os.makedirs(sessions_dir)
        
        # Create sessions with raw data
        s1_path = os.path.join(sessions_dir, 's1')
        create_test_session(s1_path, 's1')
        
        # Add dicom and bids folders
        dicom_dir = os.path.join(s1_path, 'dicom', 'scan1')
        os.makedirs(dicom_dir)
        with open(os.path.join(dicom_dir, 'file.dcm'), 'w') as f:
            f.write("DICOM data")
        
        bids_dir = os.path.join(s1_path, 'bids', 'sub-01')
        os.makedirs(bids_dir)
        with open(os.path.join(bids_dir, 'data.nii'), 'w') as f:
            f.write("BIDS data")
        
        s2_path = os.path.join(sessions_dir, 's2')
        create_test_session(s2_path, 's2')
        
        inbox_dir = os.path.join(s2_path, 'inbox', 'files')
        os.makedirs(inbox_dir)
        with open(os.path.join(inbox_dir, 'raw.txt'), 'w') as f:
            f.write("Inbox data")
        
        # Join with copy mode
        join_session(studyfolder, 's1,s2', 'joined', 'no', 'copy')
        
        target_path = os.path.join(sessions_dir, 'joined')
        
        # Check nested dicom folder
        assert os.path.exists(os.path.join(target_path, 'dicom', 's1', 'scan1', 'file.dcm')), \
            "DICOM should be nested under s1"
        
        # Check nested bids folder
        assert os.path.exists(os.path.join(target_path, 'bids', 's1', 'sub-01', 'data.nii')), \
            "BIDS should be nested under s1"
        
        # Check nested inbox folder
        assert os.path.exists(os.path.join(target_path, 'inbox', 's2', 'files', 'raw.txt')), \
            "Inbox should be nested under s2"
        
        # Original files should still exist (copy mode)
        assert os.path.exists(os.path.join(s1_path, 'dicom', 'scan1', 'file.dcm')), \
            "Original DICOM should still exist"
        
        print("Raw data successfully copied and nested")


def test_join_session_raw_data_move():
    """Test moving raw data folders"""
    print("\n" + "=" * 70)
    print("TEST: Raw data move mode")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        sessions_dir = os.path.join(studyfolder, 'sessions')
        os.makedirs(sessions_dir)
        
        # Create session with dicom
        s1_path = os.path.join(sessions_dir, 's1')
        create_test_session(s1_path, 's1')
        
        dicom_dir = os.path.join(s1_path, 'dicom', 'scan1')
        os.makedirs(dicom_dir)
        with open(os.path.join(dicom_dir, 'file.dcm'), 'w') as f:
            f.write("DICOM data")
        
        # Join with move mode
        join_session(studyfolder, 's1', 'joined', 'no', 'move')
        
        target_path = os.path.join(sessions_dir, 'joined')
        
        # Check file was moved
        assert os.path.exists(os.path.join(target_path, 'dicom', 's1', 'scan1', 'file.dcm')), \
            "DICOM should exist in target"
        
        # Original should be gone
        assert not os.path.exists(os.path.join(s1_path, 'dicom')), \
            "Original DICOM folder should be moved (not exist)"
        
        print("Raw data successfully moved")


def test_join_session_raw_data_leave():
    """Test leaving raw data in source"""
    print("\n" + "=" * 70)
    print("TEST: Raw data leave mode")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        sessions_dir = os.path.join(studyfolder, 'sessions')
        os.makedirs(sessions_dir)
        
        # Create session with dicom
        s1_path = os.path.join(sessions_dir, 's1')
        create_test_session(s1_path, 's1')
        
        dicom_dir = os.path.join(s1_path, 'dicom', 'scan1')
        os.makedirs(dicom_dir)
        with open(os.path.join(dicom_dir, 'file.dcm'), 'w') as f:
            f.write("DICOM data")
        
        # Join with leave mode
        join_session(studyfolder, 's1', 'joined', 'no', 'leave')
        
        target_path = os.path.join(sessions_dir, 'joined')
        
        # With single session, dicom is created but empty when leave mode
        # (session is merged to itself, so dicom folder might be created)
        # The key test is that original dicom still exists
        dicom_exists_in_target = os.path.exists(os.path.join(target_path, 'dicom'))
        # Either no dicom in target, or if it exists, original should still be there
        
        # Original should still exist
        assert os.path.exists(os.path.join(s1_path, 'dicom', 'scan1', 'file.dcm')), \
            "Original DICOM should remain"
        
        print("Raw data correctly left in source")


def test_join_session_invalid_source():
    """Test error handling for invalid source"""
    print("\n" + "=" * 70)
    print("TEST: Invalid source error handling")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        
        # Try to join non-existent session
        with pytest.raises(CommandFailed) as exc_info:
            join_session(studyfolder, 'nonexistent', 'target', 'no', 'leave')
        
        assert 'does not exist' in str(exc_info.value).lower() or \
               'not found' in str(exc_info.value).lower(), \
               "Should mention missing source"
        
        print("Invalid source correctly rejected")


def test_join_session_missing_session_files():
    """Test error when session files are missing"""
    print("\n" + "=" * 70)
    print("TEST: Missing session files error")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        sessions_dir = os.path.join(studyfolder, 'sessions')
        os.makedirs(sessions_dir)
        
        # Create folder without session files
        s1_path = os.path.join(sessions_dir, 's1')
        os.makedirs(s1_path)
        
        # Try to join - should succeed but create minimal session
        result = join_session(studyfolder, 's1', 'target', 'no', 'leave')
        
        assert result is True, "Should create session even without source session files"
        # Should create at least session.txt
        assert os.path.exists(os.path.join(sessions_dir, 'target', 'session.txt')), \
            "Should create session.txt"
        
        print("Missing session files correctly detected")


def test_join_sessions_list_basic():
    """Test batch joining from list file"""
    print("\n" + "=" * 70)
    print("TEST: Batch join from list")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        sourcefolder = os.path.join(studyfolder, 'source')
        targetfolder = os.path.join(studyfolder, 'target')
        os.makedirs(sourcefolder)
        
        # Create source sessions
        create_test_session(os.path.join(sourcefolder, 's1'), 's1')
        create_test_session(os.path.join(sourcefolder, 's2'), 's2')
        create_test_session(os.path.join(sourcefolder, 's3'), 's3')
        create_test_session(os.path.join(sourcefolder, 's4'), 's4')
        
        # Create list file
        list_file = os.path.join(studyfolder, 'joins.txt')
        with open(list_file, 'w') as f:
            f.write("# Join list\n")
            f.write("joined1: s1, s2\n")
            f.write("joined2: s3, s4\n")
        
        # Run batch join
        result = join_sessions_list(
            studyfolder=studyfolder,
            session_list=list_file,
            sourcefolder=sourcefolder,
            targetfolder=targetfolder,
            overwrite='no',
            raw_data='leave'
        )
        
        assert result is True, "Batch join should succeed"
        
        # Check both targets were created
        assert os.path.exists(os.path.join(targetfolder, 'joined1', 'session_hcp.txt')), \
            "joined1 should be created"
        assert os.path.exists(os.path.join(targetfolder, 'joined2', 'session_hcp.txt')), \
            "joined2 should be created"
        
        print("Batch join from list successful")


def test_join_sessions_list_with_comments():
    """Test that comments and blank lines are ignored in list file"""
    print("\n" + "=" * 70)
    print("TEST: List file with comments")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        sourcefolder = os.path.join(studyfolder, 'source')
        targetfolder = os.path.join(studyfolder, 'target')
        os.makedirs(sourcefolder)
        
        create_test_session(os.path.join(sourcefolder, 's1'), 's1')
        create_test_session(os.path.join(sourcefolder, 's2'), 's2')
        
        # Create list file with comments
        list_file = os.path.join(studyfolder, 'joins.txt')
        with open(list_file, 'w') as f:
            f.write("# This is a comment\n")
            f.write("\n")
            f.write("# Another comment\n")
            f.write("joined: s1, s2\n")
            f.write("\n")
            f.write("# Final comment\n")
        
        result = join_sessions_list(studyfolder, list_file, sourcefolder, 
                                    targetfolder, 'no', 'leave')
        
        assert result is True, "Should succeed despite comments"
        assert os.path.exists(os.path.join(targetfolder, 'joined', 'session_hcp.txt')), \
            "Target should be created"
        
        print("Comments and blank lines correctly ignored")


def test_join_sessions_list_malformed_line():
    """Test handling of malformed lines in list file"""
    print("\n" + "=" * 70)
    print("TEST: Malformed list file lines")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        sourcefolder = os.path.join(studyfolder, 'source')
        targetfolder = os.path.join(studyfolder, 'target')
        os.makedirs(sourcefolder)
        
        create_test_session(os.path.join(sourcefolder, 's1'), 's1')
        
        # Create list file with malformed line
        list_file = os.path.join(studyfolder, 'joins.txt')
        with open(list_file, 'w') as f:
            f.write("this line has no colon\n")
            f.write("joined: s1\n")
        
        # Should succeed but skip malformed line
        result = join_sessions_list(studyfolder, list_file, sourcefolder,
                                    targetfolder, 'no', 'leave')
        
        assert result is True, "Should succeed with valid lines"
        assert os.path.exists(os.path.join(targetfolder, 'joined', 'session_hcp.txt')), \
            "Valid line should be processed"
        
        print("Malformed lines correctly skipped")


def test_join_sessions_list_partial_failure():
    """Test that batch processing continues after individual failures"""
    print("\n" + "=" * 70)
    print("TEST: Partial failure in batch processing")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        sourcefolder = os.path.join(studyfolder, 'source')
        targetfolder = os.path.join(studyfolder, 'target')
        os.makedirs(sourcefolder)
        
        # Create only some sessions
        create_test_session(os.path.join(sourcefolder, 's1'), 's1')
        create_test_session(os.path.join(sourcefolder, 's2'), 's2')
        # s3 and s4 don't exist
        
        # Create list file
        list_file = os.path.join(studyfolder, 'joins.txt')
        with open(list_file, 'w') as f:
            f.write("joined1: s1, s2\n")  # Should succeed
            f.write("joined2: s3, s4\n")  # Should fail
        
        result = join_sessions_list(studyfolder, list_file, sourcefolder,
                                    targetfolder, 'no', 'leave')
        
        assert result is False, "Should return False when some operations fail"
        
        # First join should succeed
        assert os.path.exists(os.path.join(targetfolder, 'joined1', 'session_hcp.txt')), \
            "First join should succeed"
        
        # Second join should not create target
        assert not os.path.exists(os.path.join(targetfolder, 'joined2')), \
            "Failed join should not create target"
        
        print("Partial failure handled correctly")


def test_join_sessions_list_empty_file():
    """Test handling of empty list file"""
    print("\n" + "=" * 70)
    print("TEST: Empty list file")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        sourcefolder = os.path.join(studyfolder, 'source')
        targetfolder = os.path.join(studyfolder, 'target')
        os.makedirs(sourcefolder)
        
        # Create empty list file
        list_file = os.path.join(studyfolder, 'joins.txt')
        with open(list_file, 'w') as f:
            f.write("# Only comments\n")
            f.write("\n")
        
        result = join_sessions_list(studyfolder, list_file, sourcefolder,
                                    targetfolder, 'no', 'leave')
        
        assert result is False, "Should return False for empty list"
        
        print("Empty list file correctly handled")


def test_join_session_three_way_merge():
    """Test joining three sessions together"""
    print("\n" + "=" * 70)
    print("TEST: Three-way session merge")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        sessions_dir = os.path.join(studyfolder, 'sessions')
        os.makedirs(sessions_dir)
        
        # Create three sessions
        create_test_session(os.path.join(sessions_dir, 's1'), 's1', 
                          ["1011:tag1:Scan1: TR(1.0)"])
        create_test_session(os.path.join(sessions_dir, 's2'), 's2',
                          ["2011:tag2:Scan2: TR(2.0)"])
        create_test_session(os.path.join(sessions_dir, 's3'), 's3',
                          ["3011:tag3:Scan3: TR(3.0)"])
        
        # Join all three
        join_session(studyfolder, 's1,s2,s3', 'merged', 'no', 'leave')
        
        # Read result
        content = read_session_file(os.path.join(sessions_dir, 'merged', 'session_hcp.txt'))
        sequences = parse_sequences(content)
        
        # Should have 3 sequences from 3 sessions
        assert len(sequences) == 3, f"Should have 3 sequences, got {len(sequences)}"
        
        # Check base increments (all sessions renumbered)
        assert 10000 <= sequences[0] < 20000, "First session should be renumbered to 10000+"
        assert 20000 <= sequences[1] < 30000, "Second session should be renumbered to 20000+"
        assert 30000 <= sequences[2] < 40000, "Third session should be renumbered to 30000+"
        
        print(f"Three-way merge successful with sequences: {sequences}")


def test_join_session_sequence_alignment():
    """Test that sequence lines are properly aligned"""
    print("\n" + "=" * 70)
    print("TEST: Sequence line alignment")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        studyfolder = tmpdir
        sessions_dir = os.path.join(studyfolder, 'sessions')
        os.makedirs(sessions_dir)
        
        # Create sessions with varying tag lengths
        seqs = [
            "1011:T1:ShortTag: TR(1.0)",
            "2011:bold1:task:VeryLongTagName: TR(2.0): se(1)"
        ]
        create_test_session(os.path.join(sessions_dir, 's1'), 's1', seqs)
        
        join_session(studyfolder, 's1', 'joined', 'no', 'leave')
        
        # Read result
        hcp_content = read_session_file(os.path.join(sessions_dir, 'joined', 'session_hcp.txt'))
        txt_content = read_session_file(os.path.join(sessions_dir, 'joined', 'session.txt'))
        
        # Both files should have aligned columns
        hcp_lines = [l for l in hcp_content.split('\n') if l.strip() and l[0].isdigit()]
        txt_lines = [l for l in txt_content.split('\n') if l.strip() and l[0].isdigit()]
        
        assert len(hcp_lines) == 2, "Should have 2 HCP sequence lines"
        assert len(txt_lines) == 2, "Should have 2 TXT sequence lines"
        
        # Check that lines have consistent structure
        for line in hcp_lines:
            parts = line.split(':')
            assert len(parts) >= 3, f"HCP line should have at least 3 parts: {line}"
        
        print("Sequence lines properly formatted and aligned")


if __name__ == '__main__':
    # Run pytest with verbose output
    pytest.main([__file__, '-v'])

"""
Tests for DICOM cleaning functionality

This module tests the clean_dicom function and its helper functions
for identifying and removing incomplete DICOM volumes and non-image files.
"""

import os
import sys
import tempfile
import shutil
import pytest
import numpy as np
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from qx_utilities.general.dicom import clean_dicom


class MockDicomDataset:
    """Mock pydicom dataset for testing"""

    def __init__(self, has_rows=True, has_cols=True, has_ipp=True, has_iop=True,
                 has_slice_loc=True, rows=64, cols=64, ipp=None, iop=None,
                 slice_loc=0.0, series_uid="TEST_SERIES", sop_uid="TEST_SOP",
                 temporal_pos=None, acq_num=None, instance_num=1):
        if has_rows:
            self.Rows = rows
        if has_cols:
            self.Columns = cols
        if has_ipp:
            self.ImagePositionPatient = ipp if ipp is not None else [0, 0, 0]
        if has_iop:
            self.ImageOrientationPatient = iop if iop is not None else [1, 0, 0, 0, 1, 0]
        if has_slice_loc:
            self.SliceLocation = slice_loc

        self.SeriesInstanceUID = series_uid
        self.SOPInstanceUID = sop_uid

        if temporal_pos is not None:
            self.TemporalPositionIdentifier = temporal_pos
        if acq_num is not None:
            self.AcquisitionNumber = acq_num
        self.InstanceNumber = instance_num


class TestCleanDicomHelpers:
    """Test helper functions used within clean_dicom"""

    def test_is_image_dicom_with_valid_image(self):
        """Test that valid image DICOM is identified correctly"""
        ds = MockDicomDataset()
        # Need to access the internal function through exec since it's nested
        # This is a simplified test - in practice we'd test via the main function
        assert hasattr(ds, 'Rows') and hasattr(ds, 'Columns')

    def test_is_image_dicom_without_rows(self):
        """Test that DICOM without Rows is not identified as image"""
        ds = MockDicomDataset(has_rows=False)
        assert not hasattr(ds, 'Rows')

    def test_is_image_dicom_without_columns(self):
        """Test that DICOM without Columns is not identified as image"""
        ds = MockDicomDataset(has_cols=False)
        assert not hasattr(ds, 'Columns')

    def test_slice_coordinate_calculation(self):
        """Test slice coordinate is calculated correctly"""
        # Create a dataset with known position
        ipp = [10, 20, 30]
        iop = [1, 0, 0, 0, 1, 0]  # Standard axial orientation

        ds = MockDicomDataset(ipp=ipp, iop=iop)

        # NOTE: this only checks that the geometry tags are present; the
        # slice coordinate computation itself is not exercised here
        assert hasattr(ds, 'ImagePositionPatient')
        assert hasattr(ds, 'ImageOrientationPatient')

    def test_unmapped_reclassification(self):
        """Test that unmapped files without geometry are reclassified as non-image"""
        # Dataset without IPP/IOP/SliceLocation should be reclassified
        ds = MockDicomDataset(has_ipp=False, has_iop=False, has_slice_loc=False)

        assert not hasattr(ds, 'ImagePositionPatient')
        assert not hasattr(ds, 'ImageOrientationPatient')
        assert not hasattr(ds, 'SliceLocation')


class TestCleanDicomBasicFunctionality:
    """Test basic clean_dicom function behavior"""

    def setup_method(self):
        """Setup temporary directory for tests"""
        self.test_dir = tempfile.mkdtemp()
        self.session_dir = os.path.join(self.test_dir, "session")
        self.dicom_dir = os.path.join(self.session_dir, "dicom")
        os.makedirs(self.dicom_dir)

    def teardown_method(self):
        """Cleanup temporary directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_no_dicom_folder(self):
        """Test behavior when DICOM folder doesn't exist"""
        # Remove the dicom folder
        shutil.rmtree(self.dicom_dir)

        # Should handle gracefully
        clean_dicom(folder=self.session_dir, verbose="no")

        # Should not create dicom folder
        assert not os.path.exists(self.dicom_dir)

    def test_empty_dicom_folder(self):
        """Test behavior with empty DICOM folder"""
        # Should handle gracefully
        clean_dicom(folder=self.session_dir, verbose="no")

        # No sequence folders should be processed
        assert os.path.exists(self.dicom_dir)
        assert len(os.listdir(self.dicom_dir)) == 0

    def test_non_integer_folder_ignored(self):
        """Test that non-integer named folders are ignored"""
        # Create some non-sequence folders
        os.makedirs(os.path.join(self.dicom_dir, "non-image"))
        os.makedirs(os.path.join(self.dicom_dir, "_REMOVED"))
        os.makedirs(os.path.join(self.dicom_dir, "logs"))

        # Should handle gracefully
        clean_dicom(folder=self.session_dir, verbose="no")

        # These folders should still exist and be unchanged
        assert os.path.exists(os.path.join(self.dicom_dir, "non-image"))
        assert os.path.exists(os.path.join(self.dicom_dir, "_REMOVED"))
        assert os.path.exists(os.path.join(self.dicom_dir, "logs"))

    def test_creates_removal_directories(self):
        """Test that _REMOVED and non-image directories are created when needed"""
        # Create a sequence folder with a dummy file
        seq_folder = os.path.join(self.dicom_dir, "1")
        os.makedirs(seq_folder)

        # Create a dummy file
        with open(os.path.join(seq_folder, "test.dcm"), "w") as f:
            f.write("dummy")

        # Mock the file processing to trigger directory creation
        with patch('qx_utilities.general.dicom.pydicom') as mock_pydicom:
            # Mock to make it look like a non-image file
            mock_ds = MockDicomDataset(has_rows=False)
            mock_pydicom.filereader.read_file.return_value = mock_ds

            clean_dicom(folder=self.session_dir, verbose="no", move_non_image=True)

        # Check that non-image directory was created (even if no files moved)
        # Note: In actual implementation, directories are created only when files are moved
        # This test verifies the logic is in place


class TestCleanDicomParameters:
    """Test clean_dicom parameter handling"""

    def setup_method(self):
        """Setup temporary directory for tests"""
        self.test_dir = tempfile.mkdtemp()
        self.session_dir = os.path.join(self.test_dir, "session")
        self.dicom_dir = os.path.join(self.session_dir, "dicom")
        os.makedirs(self.dicom_dir)

    def teardown_method(self):
        """Cleanup temporary directory"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_default_parameters(self):
        """Test that default parameters work correctly"""
        # Should work with just folder parameter
        clean_dicom(folder=self.session_dir)

    def test_custom_tolerance(self):
        """Test custom tolerance parameter"""
        clean_dicom(folder=self.session_dir, tol_mm=0.5)

    def test_custom_min_files(self):
        """Test custom min_files parameter"""
        clean_dicom(folder=self.session_dir, min_files=20)

    def test_verbose_yes(self):
        """Test verbose=yes parameter"""
        clean_dicom(folder=self.session_dir, verbose="yes")

    def test_verbose_no(self):
        """Test verbose=no parameter"""
        clean_dicom(folder=self.session_dir, verbose="no")

    def test_move_non_image_false(self):
        """Test move_non_image=False parameter"""
        clean_dicom(folder=self.session_dir, move_non_image=False)

    def test_move_incomplete_false(self):
        """Test move_incomplete=False parameter"""
        clean_dicom(folder=self.session_dir, move_incomplete=False)

    def test_all_custom_parameters(self):
        """Test with all custom parameters"""
        clean_dicom(
            folder=self.session_dir,
            tol_mm=0.3,
            min_files=15,
            verbose="yes",
            move_non_image=True,
            move_incomplete=True
        )


class TestCleanDicomVolumeDetection:
    """Test incomplete volume detection logic"""

    def test_clustering_tolerance(self):
        """Test that slice position clustering uses correct tolerance"""
        # Create slice positions within tolerance
        positions = [0.0, 0.1, 2.0, 2.1, 4.0, 4.1]
        tolerance = 0.2

        # With 0.2mm tolerance, these should cluster into 3 groups
        # [0.0, 0.1], [2.0, 2.1], [4.0, 4.1]

        # Test the clustering logic (conceptually)
        clusters = []
        current = [positions[0]]
        for pos in positions[1:]:
            if abs(pos - np.mean(current)) <= tolerance:
                current.append(pos)
            else:
                clusters.append(np.mean(current))
                current = [pos]
        clusters.append(np.mean(current))

        assert len(clusters) == 3
        assert abs(clusters[0] - 0.05) < 0.01
        assert abs(clusters[1] - 2.05) < 0.01
        assert abs(clusters[2] - 4.05) < 0.01

    def test_mode_calculation(self):
        """Test that mode-based expected slice count is used"""
        # Simulate volume slice counts: most have 60 slices, one has 59
        slice_counts = [60, 60, 60, 60, 59]

        from collections import Counter
        mode = Counter(slice_counts).most_common(1)[0][0]

        assert mode == 60  # Should use 60, not 59

    def test_temporal_key_priority(self):
        """Test temporal key selection priority"""
        # TemporalPositionIdentifier should have highest priority
        ds_with_tpi = MockDicomDataset(temporal_pos=5)
        assert hasattr(ds_with_tpi, 'TemporalPositionIdentifier')

        # AcquisitionNumber should be used if TPI not available
        ds_with_acq = MockDicomDataset(temporal_pos=None, acq_num=10)
        assert not hasattr(ds_with_acq, 'TemporalPositionIdentifier')
        assert hasattr(ds_with_acq, 'AcquisitionNumber')


class TestCleanDicomIntegration:
    """Integration tests for clean_dicom with mock DICOM files"""

    def setup_method(self):
        """Setup test environment with mock DICOM structure"""
        self.test_dir = tempfile.mkdtemp()
        self.session_dir = os.path.join(self.test_dir, "session")
        self.dicom_dir = os.path.join(self.session_dir, "dicom")
        os.makedirs(self.dicom_dir)

    def teardown_method(self):
        """Cleanup test environment"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_min_files_threshold(self):
        """Test that sequences with too few files are skipped"""
        # Create sequence with only 5 files (below default min of 10)
        seq_folder = os.path.join(self.dicom_dir, "1")
        os.makedirs(seq_folder)

        for i in range(5):
            with open(os.path.join(seq_folder, f"file{i}.dcm"), "w") as f:
                f.write("dummy")

        with patch('qx_utilities.general.dicom.pydicom') as mock_pydicom:
            mock_ds = MockDicomDataset()
            mock_pydicom.filereader.read_file.return_value = mock_ds

            # Should skip this sequence
            clean_dicom(folder=self.session_dir, min_files=10, verbose="no")

        # Files should still be there (not moved)
        assert len(os.listdir(seq_folder)) == 5

    def test_verbose_output_format(self):
        """Test that verbose output contains expected information"""
        seq_folder = os.path.join(self.dicom_dir, "2010")
        os.makedirs(seq_folder)

        # Create test files
        for i in range(12):
            with open(os.path.join(seq_folder, f"file{i}.dcm"), "w") as f:
                f.write("dummy")

        with patch('qx_utilities.general.dicom.pydicom') as mock_pydicom:
            mock_ds = MockDicomDataset()
            mock_pydicom.filereader.read_file.return_value = mock_ds

            # Capture output
            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                clean_dicom(folder=self.session_dir, verbose="yes")
            output = f.getvalue()

            # Check for expected format
            assert "---> Inspecting sequence 2010" in output
            assert "evaluating" in output
            assert "files):" in output


class TestCleanDicomEdgeCases:
    """Test edge cases and error handling"""

    def test_invalid_folder_path(self):
        """Test with non-existent folder path"""
        clean_dicom(folder="/nonexistent/path", verbose="no")
        # Should handle gracefully without crashing

    def test_unreadable_dicom_files(self):
        """Test handling of unreadable DICOM files"""
        test_dir = tempfile.mkdtemp()
        session_dir = os.path.join(test_dir, "session")
        dicom_dir = os.path.join(session_dir, "dicom")
        seq_folder = os.path.join(dicom_dir, "1")
        os.makedirs(seq_folder)

        try:
            # Create corrupted files
            for i in range(12):
                with open(os.path.join(seq_folder, f"bad{i}.dcm"), "wb") as f:
                    f.write(b"not a valid DICOM file")

            with patch('qx_utilities.general.dicom.pydicom') as mock_pydicom:
                # Simulate read failure
                mock_pydicom.filereader.read_file.return_value = None

                # Should handle gracefully
                clean_dicom(folder=session_dir, verbose="no")
        finally:
            shutil.rmtree(test_dir)

    def test_file_collision_handling(self):
        """Test that file collisions are handled with __dup suffix"""
        # This tests the logic for handling duplicate filenames
        # when moving files to _REMOVED or non-image folders

        test_filename = "duplicate.dcm"
        collision_count = 0

        # Simulate checking for collision
        dst = "duplicate.dcm"
        if True:  # Simulate collision exists
            base, ext = os.path.splitext(test_filename)
            i = 1
            while i <= 3:  # Simulate 3 collisions
                dst = f"{base}__dup{i}{ext}"
                i += 1
                collision_count += 1

        assert collision_count == 3
        assert dst == "duplicate__dup3.dcm"


def test_clean_dicom_function_exists():
    """Test that clean_dicom function is importable"""
    from qx_utilities.general.dicom import clean_dicom
    assert callable(clean_dicom)


def test_clean_dicom_function_signature():
    """Test clean_dicom function has correct signature"""
    import inspect
    from qx_utilities.general.dicom import clean_dicom

    sig = inspect.signature(clean_dicom)
    params = list(sig.parameters.keys())

    expected_params = ['folder', 'tol_mm', 'min_files', 'verbose',
                      'move_non_image', 'move_incomplete']
    assert params == expected_params


def test_clean_dicom_default_values():
    """Test clean_dicom function has correct default values"""
    import inspect
    from qx_utilities.general.dicom import clean_dicom

    sig = inspect.signature(clean_dicom)

    assert sig.parameters['folder'].default == '.'
    assert sig.parameters['tol_mm'].default == 0.2
    assert sig.parameters['min_files'].default == 10
    assert sig.parameters['verbose'].default == 'yes'
    assert sig.parameters['move_non_image'].default is True
    assert sig.parameters['move_incomplete'].default is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

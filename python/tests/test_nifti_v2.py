#!/usr/bin/env python
# encoding: utf-8

"""
Comprehensive test suite for NIfTI v1 and v2 support in niftihdr class.

This test suite includes:
- Basic header creation and validation tests
- Format conversion tests (v1 <-> v2)
- In-memory I/O roundtrip tests
- Actual file I/O tests
- Large dimension support tests
- Affine transform preservation tests
"""

import sys
import os
import struct
import tempfile
import io

from qx_utilities.general.img import niftihdr, printniftihdr


# =============================================================================
# Basic Header Creation and Validation Tests
# =============================================================================

def test_nifti_v1_creation():
    """Test creating a NIfTI-1 header from scratch"""
    print("Testing NIfTI-1 header creation...")
    hdr = niftihdr()

    assert hdr.nifti_version == 1
    assert hdr.sizex == 48
    assert hdr.sizey == 64
    assert hdr.sizez == 48
    assert hdr.frames == 1
    assert hdr.vox_offset == 352

    # Pack the header
    packed = hdr.pack_hdr()
    assert len(packed) == 352, f"Expected 352 bytes, got {len(packed)}"

    # Check header size marker
    header_size = struct.unpack(">i", packed[:4])[0]
    if header_size != 348:
        header_size = struct.unpack("<i", packed[:4])[0]
    assert header_size == 348, f"Expected header size 348, got {header_size}"

    print("✓ NIfTI-1 header creation passed")


def test_nifti_v2_creation():
    """Test creating a NIfTI-2 header"""
    print("\nTesting NIfTI-2 header creation...")
    hdr = niftihdr()
    hdr.convert_to_v2()

    assert hdr.nifti_version == 2
    assert hdr.vox_offset == 544

    # Pack the header
    packed = hdr.pack_hdr()
    assert len(packed) == 544, f"Expected 544 bytes, got {len(packed)}"

    # Check header size marker
    header_size = struct.unpack(">i", packed[:4])[0]
    if header_size != 540:
        header_size = struct.unpack("<i", packed[:4])[0]
    assert header_size == 540, f"Expected header size 540, got {header_size}"

    # Check magic string
    magic = packed[4:12].decode("utf-8", errors="ignore")
    assert magic.startswith("ni2") or magic.startswith("n+2"), f"Invalid magic: {magic}"

    print("✓ NIfTI-2 header creation passed")


def test_nifti_header_string_repr():
    """Test string representation includes version info"""
    print("\nTesting header string representation...")
    hdr1 = niftihdr()
    str1 = str(hdr1)
    assert "Version 1" in str1

    hdr2 = niftihdr()
    hdr2.convert_to_v2()
    str2 = str(hdr2)
    assert "Version 2" in str2

    print("✓ Header string representation test passed")


# =============================================================================
# Format Conversion Tests
# =============================================================================

def test_nifti_v1_to_v2_conversion():
    """Test converting NIfTI-1 to NIfTI-2"""
    print("\nTesting NIfTI-1 to NIfTI-2 conversion...")
    hdr = niftihdr()
    hdr.sizex = 256
    hdr.sizey = 256
    hdr.sizez = 180
    hdr.frames = 100

    # Convert to V2
    hdr.convert_to_v2()

    assert hdr.nifti_version == 2
    assert hdr.sizex == 256
    assert hdr.sizey == 256
    assert hdr.sizez == 180
    assert hdr.frames == 100

    print("✓ NIfTI-1 to NIfTI-2 conversion passed")


def test_nifti_v2_to_v1_conversion():
    """Test converting NIfTI-2 to NIfTI-1"""
    print("\nTesting NIfTI-2 to NIfTI-1 conversion...")
    hdr = niftihdr()
    hdr.convert_to_v2()
    hdr.sizex = 128
    hdr.sizey = 128
    hdr.sizez = 90

    # Convert back to V1
    hdr.convert_to_v1()

    assert hdr.nifti_version == 1
    assert hdr.sizex == 128
    assert hdr.sizey == 128
    assert hdr.sizez == 90

    print("✓ NIfTI-2 to NIfTI-1 conversion passed")


def test_nifti_v2_large_dimensions_conversion():
    """Test that large dimensions prevent conversion to NIfTI-1"""
    print("\nTesting NIfTI-2 large dimensions conversion restriction...")
    hdr = niftihdr()
    hdr.convert_to_v2()
    hdr.sizex = 50000  # Larger than int16 can hold
    hdr.sizey = 256
    hdr.sizez = 180

    # Pack and verify
    packed = hdr.pack_hdr()
    assert len(packed) == 544

    # Try to convert to V1 (should fail)
    try:
        hdr.convert_to_v1()
        assert False, "Should have raised ValueError for dimensions too large"
    except ValueError as e:
        assert "too large" in str(e)

    print("✓ NIfTI-2 large dimensions conversion restriction passed")


# =============================================================================
# In-Memory I/O Roundtrip Tests
# =============================================================================

def test_nifti_v1_roundtrip():
    """Test packing and unpacking NIfTI-1 header"""
    print("\nTesting NIfTI-1 in-memory roundtrip...")

    # Create a NIfTI-1 header
    hdr1 = niftihdr()
    hdr1.sizex = 128
    hdr1.sizey = 128
    hdr1.sizez = 64
    hdr1.frames = 200
    hdr1.pixdim_x = 2.0
    hdr1.pixdim_y = 2.0
    hdr1.pixdim_z = 2.5
    hdr1.descrip = "Test NIfTI-1 image"

    # Pack it
    packed = hdr1.pack_hdr()

    # Unpack it
    hdr2 = niftihdr()
    stream = io.BytesIO(packed)
    hdr2.unpack_hdr(stream)

    # Verify
    assert hdr2.nifti_version == 1
    assert hdr2.sizex == 128
    assert hdr2.sizey == 128
    assert hdr2.sizez == 64
    assert hdr2.frames == 200
    assert abs(hdr2.pixdim_x - 2.0) < 0.001
    assert abs(hdr2.pixdim_y - 2.0) < 0.001
    assert abs(hdr2.pixdim_z - 2.5) < 0.001
    assert "Test NIfTI-1" in hdr2.descrip

    print("✓ NIfTI-1 in-memory roundtrip passed")


def test_nifti_v2_roundtrip():
    """Test packing and unpacking NIfTI-2 header"""
    print("\nTesting NIfTI-2 in-memory roundtrip...")

    # Create a NIfTI-2 header
    hdr1 = niftihdr()
    hdr1.convert_to_v2()
    hdr1.sizex = 256
    hdr1.sizey = 256
    hdr1.sizez = 180
    hdr1.frames = 500
    hdr1.pixdim_x = 1.5
    hdr1.pixdim_y = 1.5
    hdr1.pixdim_z = 2.0
    hdr1.descrip = "Test NIfTI-2 image"
    hdr1.qoffset_x = 125.0
    hdr1.qoffset_y = -130.0
    hdr1.qoffset_z = 85.5

    # Pack it
    packed = hdr1.pack_hdr()

    # Unpack it
    hdr2 = niftihdr()
    stream = io.BytesIO(packed)
    hdr2.unpack_hdr(stream)

    # Verify
    assert hdr2.nifti_version == 2
    assert hdr2.sizex == 256
    assert hdr2.sizey == 256
    assert hdr2.sizez == 180
    assert hdr2.frames == 500
    assert abs(hdr2.pixdim_x - 1.5) < 0.001
    assert abs(hdr2.pixdim_y - 1.5) < 0.001
    assert abs(hdr2.pixdim_z - 2.0) < 0.001
    assert abs(hdr2.qoffset_x - 125.0) < 0.001
    assert abs(hdr2.qoffset_y - (-130.0)) < 0.001
    assert abs(hdr2.qoffset_z - 85.5) < 0.001
    assert "Test NIfTI-2" in hdr2.descrip

    print("✓ NIfTI-2 in-memory roundtrip passed")


def test_nifti_v2_large_dimensions_roundtrip():
    """Test NIfTI-2 with dimensions that exceed NIfTI-1 limits"""
    print("\nTesting NIfTI-2 large dimensions in-memory roundtrip...")

    # Create a NIfTI-2 header with large dimensions
    hdr1 = niftihdr()
    hdr1.convert_to_v2()
    hdr1.sizex = 40000  # Exceeds int16 max
    hdr1.sizey = 256
    hdr1.sizez = 180
    hdr1.frames = 10

    # Pack it
    packed = hdr1.pack_hdr()

    # Unpack it
    hdr2 = niftihdr()
    stream = io.BytesIO(packed)
    hdr2.unpack_hdr(stream)

    # Verify
    assert hdr2.nifti_version == 2
    assert hdr2.sizex == 40000
    assert hdr2.sizey == 256
    assert hdr2.sizez == 180
    assert hdr2.frames == 10

    print("✓ NIfTI-2 large dimensions in-memory roundtrip passed")


def test_nifti_version_detection():
    """Test that version is correctly detected from packed header"""
    print("\nTesting NIfTI version auto-detection...")

    # Create V1 header
    hdr1 = niftihdr()
    packed1 = hdr1.pack_hdr()

    # Detect version from packed data
    hdr_test1 = niftihdr()
    stream1 = io.BytesIO(packed1)
    hdr_test1.unpack_hdr(stream1)
    assert hdr_test1.nifti_version == 1

    # Create V2 header
    hdr2 = niftihdr()
    hdr2.convert_to_v2()
    packed2 = hdr2.pack_hdr()

    # Detect version from packed data
    hdr_test2 = niftihdr()
    stream2 = io.BytesIO(packed2)
    hdr_test2.unpack_hdr(stream2)
    assert hdr_test2.nifti_version == 2

    print("✓ NIfTI version auto-detection passed")


def test_nifti_affine_transforms():
    """Test that affine transform matrices are preserved"""
    print("\nTesting NIfTI affine transform preservation...")

    # Test with V1
    hdr1_v1 = niftihdr()
    hdr1_v1.srow_x = [2.0, 0.0, 0.0, -90.0]
    hdr1_v1.srow_y = [0.0, 2.0, 0.0, -126.0]
    hdr1_v1.srow_z = [0.0, 0.0, 2.0, -72.0]

    packed_v1 = hdr1_v1.pack_hdr()
    hdr2_v1 = niftihdr()
    hdr2_v1.unpack_hdr(io.BytesIO(packed_v1))

    assert hdr2_v1.srow_x == hdr1_v1.srow_x
    assert hdr2_v1.srow_y == hdr1_v1.srow_y
    assert hdr2_v1.srow_z == hdr1_v1.srow_z

    # Test with V2
    hdr1_v2 = niftihdr()
    hdr1_v2.convert_to_v2()
    hdr1_v2.srow_x = [1.5, 0.0, 0.0, -120.0]
    hdr1_v2.srow_y = [0.0, 1.5, 0.0, -150.0]
    hdr1_v2.srow_z = [0.0, 0.0, 2.5, -80.0]

    packed_v2 = hdr1_v2.pack_hdr()
    hdr2_v2 = niftihdr()
    hdr2_v2.unpack_hdr(io.BytesIO(packed_v2))

    for i in range(4):
        assert abs(hdr2_v2.srow_x[i] - hdr1_v2.srow_x[i]) < 0.001
        assert abs(hdr2_v2.srow_y[i] - hdr1_v2.srow_y[i]) < 0.001
        assert abs(hdr2_v2.srow_z[i] - hdr1_v2.srow_z[i]) < 0.001

    print("✓ NIfTI affine transform preservation passed")


# =============================================================================
# Real File I/O Tests
# =============================================================================

def test_write_and_read_nifti_v1_file():
    """Test writing and reading an actual NIfTI-1 file"""
    print("\nTesting NIfTI-1 file write/read...")

    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp:
        tmpfile = tmp.name

    try:
        # Create and write a header
        hdr1 = niftihdr()
        hdr1.sizex = 64
        hdr1.sizey = 64
        hdr1.sizez = 32
        hdr1.frames = 100
        hdr1.pixdim_x = 2.5
        hdr1.pixdim_y = 2.5
        hdr1.pixdim_z = 3.0
        hdr1.descrip = "Test V1 file"
        hdr1.write_header(tmpfile)

        # Read it back
        hdr2 = niftihdr(tmpfile)

        # Verify
        assert hdr2.nifti_version == 1
        assert hdr2.sizex == 64
        assert hdr2.sizey == 64
        assert hdr2.sizez == 32
        assert hdr2.frames == 100
        assert abs(hdr2.pixdim_x - 2.5) < 0.001
        assert abs(hdr2.pixdim_y - 2.5) < 0.001
        assert abs(hdr2.pixdim_z - 3.0) < 0.001
        assert "Test V1 file" in hdr2.descrip

        print("✓ NIfTI-1 file write/read passed")

    finally:
        # Clean up
        if os.path.exists(tmpfile):
            os.remove(tmpfile)


def test_write_and_read_nifti_v2_file():
    """Test writing and reading an actual NIfTI-2 file"""
    print("\nTesting NIfTI-2 file write/read...")

    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp:
        tmpfile = tmp.name

    try:
        # Create and write a header
        hdr1 = niftihdr()
        hdr1.convert_to_v2()
        hdr1.sizex = 128
        hdr1.sizey = 128
        hdr1.sizez = 64
        hdr1.frames = 200
        hdr1.pixdim_x = 1.5
        hdr1.pixdim_y = 1.5
        hdr1.pixdim_z = 2.0
        hdr1.descrip = "Test V2 file"
        hdr1.write_header(tmpfile)

        # Read it back
        hdr2 = niftihdr(tmpfile)

        # Verify
        assert hdr2.nifti_version == 2
        assert hdr2.sizex == 128
        assert hdr2.sizey == 128
        assert hdr2.sizez == 64
        assert hdr2.frames == 200
        assert abs(hdr2.pixdim_x - 1.5) < 0.001
        assert abs(hdr2.pixdim_y - 1.5) < 0.001
        assert abs(hdr2.pixdim_z - 2.0) < 0.001
        assert "Test V2 file" in hdr2.descrip

        print("✓ NIfTI-2 file write/read passed")

    finally:
        # Clean up
        if os.path.exists(tmpfile):
            os.remove(tmpfile)


def test_printniftihdr_function():
    """Test the printniftihdr function with actual files"""
    print("\nTesting printniftihdr function...")

    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp:
        tmpfile = tmp.name

    try:
        # Create and write a header
        hdr = niftihdr()
        hdr.sizex = 64
        hdr.sizey = 64
        hdr.sizez = 32
        hdr.descrip = "Test printniftihdr"
        hdr.write_header(tmpfile)

        # This should not raise an error (suppress output for cleaner test results)
        import io as stdio
        old_stdout = sys.stdout
        sys.stdout = stdio.StringIO()
        try:
            printniftihdr(tmpfile)
        finally:
            sys.stdout = old_stdout

        print("✓ printniftihdr function passed")

    finally:
        # Clean up
        if os.path.exists(tmpfile):
            os.remove(tmpfile)


# =============================================================================
# Main Test Runner
# =============================================================================

def main():
    print("=" * 70)
    print("NIfTI v1 and v2 Comprehensive Test Suite")
    print("=" * 70)

    test_count = 0
    failed_tests = []

    tests = [
        # Basic tests
        ("Basic Header Creation", [
            test_nifti_v1_creation,
            test_nifti_v2_creation,
            test_nifti_header_string_repr,
        ]),
        # Conversion tests
        ("Format Conversion", [
            test_nifti_v1_to_v2_conversion,
            test_nifti_v2_to_v1_conversion,
            test_nifti_v2_large_dimensions_conversion,
        ]),
        # In-memory I/O tests
        ("In-Memory I/O", [
            test_nifti_v1_roundtrip,
            test_nifti_v2_roundtrip,
            test_nifti_v2_large_dimensions_roundtrip,
            test_nifti_version_detection,
            test_nifti_affine_transforms,
        ]),
        # Real file I/O tests
        ("Real File I/O", [
            test_write_and_read_nifti_v1_file,
            test_write_and_read_nifti_v2_file,
            test_printniftihdr_function,
        ]),
    ]

    try:
        for category, test_funcs in tests:
            print(f"\n{'=' * 70}")
            print(f"Category: {category}")
            print('=' * 70)
            for test_func in test_funcs:
                test_count += 1
                try:
                    test_func()
                except Exception as e:
                    failed_tests.append((test_func.__name__, str(e)))
                    print(f"✗ {test_func.__name__} FAILED: {e}")
                    import traceback
                    traceback.print_exc()

        print("\n" + "=" * 70)
        print(f"Test Results: {test_count - len(failed_tests)}/{test_count} passed")
        print("=" * 70)

        if failed_tests:
            print("\nFailed tests:")
            for test_name, error in failed_tests:
                print(f"  ✗ {test_name}: {error}")
            return 1
        else:
            print("\n✓ All tests passed!")
            return 0

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

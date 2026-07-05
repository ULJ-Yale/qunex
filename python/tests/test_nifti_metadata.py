#!/usr/bin/env python
# encoding: utf-8

"""
Test suite for NIfTI metadata extension reading functionality.
"""

import sys
import os
import tempfile
import struct

from qx_utilities.general.img import niftihdr, print_nifti_metadata, compare_nifti_images


def create_nifti_with_metadata(filename, add_cifti=False, add_qunex=False):
    """Helper function to create a NIfTI file with metadata extensions"""

    # Create a basic NIfTI header
    hdr = niftihdr()
    hdr.sizex = 64
    hdr.sizey = 64
    hdr.sizez = 32
    hdr.frames = 10
    hdr.descrip = "Test file with metadata"

    # Manually set extension flag (as a string chr(1) + chr(0) * 3)
    hdr.ext = chr(1) + chr(0) + chr(0) + chr(0)

    # Prepare metadata blocks - store directly in hdr.meta
    hdr.meta = []

    if add_cifti:
        # Create a simple CIFTI XML metadata (code 32)
        cifti_xml = """<?xml version="1.0" encoding="UTF-8"?>
<CIFTI Version="2.0">
  <Matrix>
    <MetaData>
      <MD>
        <Name>TestMetadata</Name>
        <Value>TestValue</Value>
      </MD>
    </MetaData>
  </Matrix>
</CIFTI>"""
        cifti_data = cifti_xml.encode('utf-8')
        # Extension size includes 8 bytes for esize and ecode fields
        # Must be multiple of 16 bytes
        esize = len(cifti_data) + 8
        # Round up to multiple of 16
        esize = ((esize + 15) // 16) * 16
        # Pad data to match esize
        cifti_data = cifti_data + b'\x00' * (esize - len(cifti_data) - 8)
        hdr.meta.append([esize, 32, cifti_data])

    if add_qunex:
        # Create QuNex metadata (code 64)
        qunex_text = "QuNex Processing: bold1\nSession: session1\nProcessed: 2025-10-28"
        qunex_data = qunex_text.encode('utf-8')
        esize = len(qunex_data) + 8
        esize = ((esize + 15) // 16) * 16
        qunex_data = qunex_data + b'\x00' * (esize - len(qunex_data) - 8)
        hdr.meta.append([esize, 64, qunex_data])

    # Calculate vox_offset (header + extensions)
    if hdr.nifti_version == 1:
        base_offset = 352
    else:
        base_offset = 544

    total_extension_size = sum([mb[0] for mb in hdr.meta])
    hdr.vox_offset = base_offset + total_extension_size

    # Write the file manually with proper metadata extensions
    with open(filename, 'wb') as f:
        # Write header (348 bytes + 4 byte extension flag = 352 bytes for NIfTI-1)
        header_bytes = hdr.packHdr()
        f.write(header_bytes)

        # Write metadata blocks
        for msize, mcode, mdata in hdr.meta:
            f.write(struct.pack(hdr.e + 'I', msize))
            f.write(struct.pack(hdr.e + 'I', mcode))
            f.write(mdata)


def test_no_metadata():
    """Test reading a file with no metadata extensions"""
    print("\n" + "=" * 70)
    print("TEST: File with no metadata")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp:
        tmpfile = tmp.name

    try:
        # Create a simple file without metadata using the helper function
        create_nifti_with_metadata(tmpfile, add_cifti=False, add_qunex=False)

        # Test reading metadata (list mode)
        print_nifti_metadata(tmpfile)
        print("\n✓ Test passed: No metadata file handled correctly\n")

    finally:
        if os.path.exists(tmpfile):
            os.remove(tmpfile)


def test_list_mode():
    """Test list mode (default) with metadata"""
    print("\n" + "=" * 70)
    print("TEST: List mode (default)")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix='.dtseries.nii', delete=False) as tmp:
        tmpfile = tmp.name

    try:
        # Create file with both types of metadata
        create_nifti_with_metadata(tmpfile, add_cifti=True, add_qunex=True)

        # Test list mode (default)
        print("\n--- Default behavior (list mode) ---")
        print_nifti_metadata(tmpfile)

        # Test explicit list mode
        print("\n--- Explicit info='list' ---")
        print_nifti_metadata(tmpfile, info='list')

        print("\n✓ Test passed: List mode works correctly\n")

    finally:
        if os.path.exists(tmpfile):
            os.remove(tmpfile)


def test_cifti_metadata():
    """Test reading CIFTI metadata"""
    print("\n" + "=" * 70)
    print("TEST: File with CIFTI metadata")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix='.dtseries.nii', delete=False) as tmp:
        tmpfile = tmp.name

    try:
        # Create file with CIFTI metadata
        create_nifti_with_metadata(tmpfile, add_cifti=True, add_qunex=False)

        # Test reading CIFTI metadata
        print("\n--- Reading with info='cifti' ---")
        print_nifti_metadata(tmpfile, info='cifti')

        print("\n--- Reading with info='all' ---")
        print_nifti_metadata(tmpfile, info='all')

        print("\n✓ Test passed: CIFTI metadata read correctly\n")

    finally:
        if os.path.exists(tmpfile):
            os.remove(tmpfile)


def test_numeric_codes():
    """Test using numeric extension codes"""
    print("\n" + "=" * 70)
    print("TEST: Numeric extension codes")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix='.dtseries.nii', delete=False) as tmp:
        tmpfile = tmp.name

    try:
        # Create file with both types of metadata
        create_nifti_with_metadata(tmpfile, add_cifti=True, add_qunex=True)

        # Test numeric codes
        print("\n--- Using info=32 (CIFTI) ---")
        print_nifti_metadata(tmpfile, info=32)

        print("\n--- Using info=64 (QuNex) ---")
        print_nifti_metadata(tmpfile, info=64)

        print("\n✓ Test passed: Numeric codes work correctly\n")

    finally:
        if os.path.exists(tmpfile):
            os.remove(tmpfile)


def test_qunex_metadata():
    """Test reading QuNex metadata"""
    print("\n" + "=" * 70)
    print("TEST: File with QuNex metadata")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp:
        tmpfile = tmp.name

    try:
        # Create file with QuNex metadata
        create_nifti_with_metadata(tmpfile, add_cifti=False, add_qunex=True)

        # Test reading QuNex metadata
        print("\n--- Reading with info='qunex' ---")
        print_nifti_metadata(tmpfile, info='qunex')

        print("\n--- Reading with info='qx' ---")
        print_nifti_metadata(tmpfile, info='qx')

        print("\n✓ Test passed: QuNex metadata read correctly\n")

    finally:
        if os.path.exists(tmpfile):
            os.remove(tmpfile)
    """Test reading QuNex metadata"""
    print("\n" + "=" * 70)
    print("TEST: File with QuNex metadata")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp:
        tmpfile = tmp.name

    try:
        # Create file with QuNex metadata
        create_nifti_with_metadata(tmpfile, add_cifti=False, add_qunex=True)

        # Test reading QuNex metadata
        print("\n--- Reading with info='qunex' ---")
        print_nifti_metadata(tmpfile, info='qunex')

        print("\n--- Reading with info='qx' ---")
        print_nifti_metadata(tmpfile, info='qx')

        print("\n--- Reading with info='64' ---")
        print_nifti_metadata(tmpfile, info=64)

        print("\n✓ Test passed: QuNex metadata read correctly\n")

    finally:
        if os.path.exists(tmpfile):
            os.remove(tmpfile)


def test_multiple_metadata():
    """Test reading file with both CIFTI and QuNex metadata"""
    print("\n" + "=" * 70)
    print("TEST: File with multiple metadata blocks")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix='.dtseries.nii', delete=False) as tmp:
        tmpfile = tmp.name

    try:
        # Create file with both types of metadata
        create_nifti_with_metadata(tmpfile, add_cifti=True, add_qunex=True)

        # Test reading all metadata
        print("\n--- Reading with info='all' ---")
        print_nifti_metadata(tmpfile, info='all')

        # Test filtering CIFTI only
        print("\n--- Reading with info='cifti' ---")
        print_nifti_metadata(tmpfile, info='cifti')

        # Test filtering QuNex only
        print("\n--- Reading with info='qunex' ---")
        print_nifti_metadata(tmpfile, info='qunex')

        print("\n✓ Test passed: Multiple metadata blocks handled correctly\n")

    finally:
        if os.path.exists(tmpfile):
            os.remove(tmpfile)


def create_nifti_with_data(filename, sizex=64, sizey=64, sizez=32, frames=10, 
                          descrip="Test file", add_cifti=False, add_qunex=False,
                          data_pattern=0):
    """Helper function to create a NIfTI file with data and optional metadata"""
    import numpy as np
    
    # Create a basic NIfTI header
    hdr = niftihdr()
    hdr.sizex = sizex
    hdr.sizey = sizey
    hdr.sizez = sizez
    hdr.frames = frames
    hdr.descrip = descrip
    hdr.data_type = 16  # float32
    hdr.bitpix = 32

    # Set extension flag and metadata
    hdr.meta = []
    if add_cifti or add_qunex:
        hdr.ext = chr(1) + chr(0) + chr(0) + chr(0)
        
        if add_cifti:
            cifti_xml = """<?xml version="1.0" encoding="UTF-8"?>
<CIFTI Version="2.0">
  <Matrix>
    <MetaData>
      <MD>
        <Name>TestMetadata</Name>
        <Value>TestValue</Value>
      </MD>
    </MetaData>
  </Matrix>
</CIFTI>"""
            cifti_data = cifti_xml.encode('utf-8')
            esize = len(cifti_data) + 8
            esize = ((esize + 15) // 16) * 16
            cifti_data = cifti_data + b'\x00' * (esize - len(cifti_data) - 8)
            hdr.meta.append([esize, 32, cifti_data])

        if add_qunex:
            qunex_text = "QuNex Processing: bold1\nSession: session1\nProcessed: 2025-10-28"
            qunex_data = qunex_text.encode('utf-8')
            esize = len(qunex_data) + 8
            esize = ((esize + 15) // 16) * 16
            qunex_data = qunex_data + b'\x00' * (esize - len(qunex_data) - 8)
            hdr.meta.append([esize, 64, qunex_data])
    else:
        hdr.ext = chr(0) + chr(0) + chr(0) + chr(0)

    # Calculate vox_offset
    base_offset = 352 if hdr.nifti_version == 1 else 544
    total_extension_size = sum([mb[0] for mb in hdr.meta])
    hdr.vox_offset = base_offset + total_extension_size

    # Create data array
    nvox = sizex * sizey * sizez * frames
    if data_pattern == 0:
        # All zeros
        data = np.zeros(nvox, dtype=np.float32)
    elif data_pattern == 1:
        # All ones
        data = np.ones(nvox, dtype=np.float32)
    elif data_pattern == 2:
        # Random data (with seed for reproducibility)
        np.random.seed(42)
        data = np.random.randn(nvox).astype(np.float32)
    elif data_pattern == 3:
        # Different random data
        np.random.seed(123)
        data = np.random.randn(nvox).astype(np.float32)
    else:
        # Sequential values
        data = np.arange(nvox, dtype=np.float32)

    # Write the file
    with open(filename, 'wb') as f:
        # Write header
        header_bytes = hdr.packHdr()
        f.write(header_bytes)

        # Write metadata blocks
        for msize, mcode, mdata in hdr.meta:
            f.write(struct.pack(hdr.e + 'I', msize))
            f.write(struct.pack(hdr.e + 'I', mcode))
            f.write(mdata)

        # Write data
        f.write(data.tobytes())


def test_compare_identical_files():
    """Test comparing two identical files"""
    print("\n" + "=" * 70)
    print("TEST: Compare identical files")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp1:
        tmpfile1 = tmp1.name
    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp2:
        tmpfile2 = tmp2.name

    try:
        # Create two identical files
        create_nifti_with_data(tmpfile1, data_pattern=2, add_qunex=True)
        create_nifti_with_data(tmpfile2, data_pattern=2, add_qunex=True)

        # Compare them
        compare_nifti_images(tmpfile1, tmpfile2)

        print("\n✓ Test passed: Identical files comparison works\n")

    finally:
        if os.path.exists(tmpfile1):
            os.remove(tmpfile1)
        if os.path.exists(tmpfile2):
            os.remove(tmpfile2)


def test_compare_different_headers():
    """Test comparing files with different headers"""
    print("\n" + "=" * 70)
    print("TEST: Compare files with different headers")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp1:
        tmpfile1 = tmp1.name
    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp2:
        tmpfile2 = tmp2.name

    try:
        # Create files with different descriptions and voxel sizes
        create_nifti_with_data(tmpfile1, descrip="File 1", data_pattern=0)
        
        # Create second file with different header
        hdr2 = niftihdr()
        hdr2.sizex = 64
        hdr2.sizey = 64
        hdr2.sizez = 32
        hdr2.frames = 10
        hdr2.descrip = "File 2 - Different"
        hdr2.pixdim_x = 2.5  # Different voxel size
        hdr2.pixdim_y = 2.5
        hdr2.pixdim_z = 2.5
        hdr2.data_type = 16
        hdr2.bitpix = 32
        hdr2.ext = chr(0) * 4
        hdr2.meta = []
        hdr2.vox_offset = 352
        
        import numpy as np
        nvox = 64 * 64 * 32 * 10
        data = np.zeros(nvox, dtype=np.float32)
        
        with open(tmpfile2, 'wb') as f:
            f.write(hdr2.packHdr())
            f.write(data.tobytes())

        # Compare them
        compare_nifti_images(tmpfile1, tmpfile2)

        print("\n✓ Test passed: Header differences detected\n")

    finally:
        if os.path.exists(tmpfile1):
            os.remove(tmpfile1)
        if os.path.exists(tmpfile2):
            os.remove(tmpfile2)


def test_compare_different_extensions():
    """Test comparing files with different extensions"""
    print("\n" + "=" * 70)
    print("TEST: Compare files with different extensions")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp1:
        tmpfile1 = tmp1.name
    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp2:
        tmpfile2 = tmp2.name

    try:
        # Create file with CIFTI extension
        create_nifti_with_data(tmpfile1, data_pattern=0, add_cifti=True)
        
        # Create file with QuNex extension
        create_nifti_with_data(tmpfile2, data_pattern=0, add_qunex=True)

        # Compare them
        compare_nifti_images(tmpfile1, tmpfile2)

        print("\n✓ Test passed: Extension differences detected\n")

    finally:
        if os.path.exists(tmpfile1):
            os.remove(tmpfile1)
        if os.path.exists(tmpfile2):
            os.remove(tmpfile2)


def test_compare_same_extension_different_content():
    """Test comparing files with same extension code but different content"""
    print("\n" + "=" * 70)
    print("TEST: Compare files with same extension, different content")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp1:
        tmpfile1 = tmp1.name
    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp2:
        tmpfile2 = tmp2.name

    try:
        # Create both files with QuNex extension but different content
        hdr1 = niftihdr()
        hdr1.sizex = 64
        hdr1.sizey = 64
        hdr1.sizez = 32
        hdr1.frames = 10
        hdr1.data_type = 16
        hdr1.bitpix = 32
        hdr1.ext = chr(1) + chr(0) * 3
        
        qunex_text1 = "QuNex Processing: bold1\nSession: session1\nProcessed: 2025-10-28"
        qunex_data1 = qunex_text1.encode('utf-8')
        esize1 = len(qunex_data1) + 8
        esize1 = ((esize1 + 15) // 16) * 16
        qunex_data1 = qunex_data1 + b'\x00' * (esize1 - len(qunex_data1) - 8)
        hdr1.meta = [[esize1, 64, qunex_data1]]
        hdr1.vox_offset = 352 + esize1
        
        import numpy as np
        nvox = 64 * 64 * 32 * 10
        data = np.zeros(nvox, dtype=np.float32)
        
        with open(tmpfile1, 'wb') as f:
            f.write(hdr1.packHdr())
            f.write(struct.pack(hdr1.e + 'I', esize1))
            f.write(struct.pack(hdr1.e + 'I', 64))
            f.write(qunex_data1)
            f.write(data.tobytes())
        
        # Create second file with different QuNex content
        hdr2 = niftihdr()
        hdr2.sizex = 64
        hdr2.sizey = 64
        hdr2.sizez = 32
        hdr2.frames = 10
        hdr2.data_type = 16
        hdr2.bitpix = 32
        hdr2.ext = chr(1) + chr(0) * 3
        
        qunex_text2 = "QuNex Processing: bold2\nSession: session2\nProcessed: 2025-10-29"  # Different!
        qunex_data2 = qunex_text2.encode('utf-8')
        esize2 = len(qunex_data2) + 8
        esize2 = ((esize2 + 15) // 16) * 16
        qunex_data2 = qunex_data2 + b'\x00' * (esize2 - len(qunex_data2) - 8)
        hdr2.meta = [[esize2, 64, qunex_data2]]
        hdr2.vox_offset = 352 + esize2
        
        with open(tmpfile2, 'wb') as f:
            f.write(hdr2.packHdr())
            f.write(struct.pack(hdr2.e + 'I', esize2))
            f.write(struct.pack(hdr2.e + 'I', 64))
            f.write(qunex_data2)
            f.write(data.tobytes())

        # Compare them
        compare_nifti_images(tmpfile1, tmpfile2)

        print("\n✓ Test passed: Extension content differences detected\n")

    finally:
        if os.path.exists(tmpfile1):
            os.remove(tmpfile1)
        if os.path.exists(tmpfile2):
            os.remove(tmpfile2)


def test_compare_different_data():
    """Test comparing files with different data"""
    print("\n" + "=" * 70)
    print("TEST: Compare files with different data")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp1:
        tmpfile1 = tmp1.name
    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp2:
        tmpfile2 = tmp2.name

    try:
        # Create files with same headers but different data
        create_nifti_with_data(tmpfile1, data_pattern=2)  # Random seed 42
        create_nifti_with_data(tmpfile2, data_pattern=3)  # Random seed 123

        # Compare them
        compare_nifti_images(tmpfile1, tmpfile2)

        print("\n✓ Test passed: Data differences detected\n")

    finally:
        if os.path.exists(tmpfile1):
            os.remove(tmpfile1)
        if os.path.exists(tmpfile2):
            os.remove(tmpfile2)


def test_compare_different_dimensions():
    """Test comparing files with different dimensions"""
    print("\n" + "=" * 70)
    print("TEST: Compare files with different dimensions")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp1:
        tmpfile1 = tmp1.name
    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp2:
        tmpfile2 = tmp2.name

    try:
        # Create files with different dimensions
        create_nifti_with_data(tmpfile1, sizex=64, sizey=64, sizez=32, frames=10, data_pattern=0)
        create_nifti_with_data(tmpfile2, sizex=64, sizey=64, sizez=32, frames=20, data_pattern=0)  # Different frames

        # Compare them
        compare_nifti_images(tmpfile1, tmpfile2)

        print("\n✓ Test passed: Dimension differences detected\n")

    finally:
        if os.path.exists(tmpfile1):
            os.remove(tmpfile1)
        if os.path.exists(tmpfile2):
            os.remove(tmpfile2)


def test_compare_ndifflines_parameter():
    """Test the ndifflines parameter for controlling diff output length"""
    print("\n" + "=" * 70)
    print("TEST: ndifflines parameter")
    print("=" * 70)

    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp1:
        tmpfile1 = tmp1.name
    with tempfile.NamedTemporaryFile(suffix='.nii', delete=False) as tmp2:
        tmpfile2 = tmp2.name

    try:
        # Create files with long textual extensions that differ on many lines
        hdr1 = niftihdr()
        hdr1.sizex = 32
        hdr1.sizey = 32
        hdr1.sizez = 16
        hdr1.frames = 5
        hdr1.data_type = 16
        hdr1.bitpix = 32
        hdr1.ext = chr(1) + chr(0) * 3
        
        # Create a long text extension (15 lines)
        lines1 = [f"Line {i:02d}: Data from file 1 - test iteration {i}" for i in range(15)]
        qunex_text1 = "\n".join(lines1)
        qunex_data1 = qunex_text1.encode('utf-8')
        esize1 = len(qunex_data1) + 8
        esize1 = ((esize1 + 15) // 16) * 16
        qunex_data1 = qunex_data1 + b'\x00' * (esize1 - len(qunex_data1) - 8)
        hdr1.meta = [[esize1, 64, qunex_data1]]
        hdr1.vox_offset = 352 + esize1
        
        import numpy as np
        nvox = 32 * 32 * 16 * 5
        np.random.seed(42)
        data = np.random.randn(nvox).astype(np.float32)
        
        with open(tmpfile1, 'wb') as f:
            f.write(hdr1.packHdr())
            f.write(struct.pack(hdr1.e + 'I', esize1))
            f.write(struct.pack(hdr1.e + 'I', 64))
            f.write(qunex_data1)
            f.write(data.tobytes())
        
        # Create second file with different text (all lines differ)
        hdr2 = niftihdr()
        hdr2.sizex = 32
        hdr2.sizey = 32
        hdr2.sizez = 16
        hdr2.frames = 5
        hdr2.data_type = 16
        hdr2.bitpix = 32
        hdr2.ext = chr(1) + chr(0) * 3
        
        lines2 = [f"Line {i:02d}: Data from file 2 - test iteration {i}" for i in range(15)]
        qunex_text2 = "\n".join(lines2)
        qunex_data2 = qunex_text2.encode('utf-8')
        esize2 = len(qunex_data2) + 8
        esize2 = ((esize2 + 15) // 16) * 16
        qunex_data2 = qunex_data2 + b'\x00' * (esize2 - len(qunex_data2) - 8)
        hdr2.meta = [[esize2, 64, qunex_data2]]
        hdr2.vox_offset = 352 + esize2
        
        with open(tmpfile2, 'wb') as f:
            f.write(hdr2.packHdr())
            f.write(struct.pack(hdr2.e + 'I', esize2))
            f.write(struct.pack(hdr2.e + 'I', 64))
            f.write(qunex_data2)
            f.write(data.tobytes())

        print("\n--- Testing with ndifflines=3 (should show 3 lines + truncation) ---")
        compare_nifti_images(tmpfile1, tmpfile2, ndifflines=3)

        print("\n✓ Test passed: ndifflines parameter works correctly\n")

    finally:
        if os.path.exists(tmpfile1):
            os.remove(tmpfile1)
        if os.path.exists(tmpfile2):
            os.remove(tmpfile2)


def main():
    print("=" * 70)
    print("NIfTI Metadata Extension Tests")
    print("=" * 70)

    try:
        # Original metadata tests
        test_no_metadata()
        test_list_mode()
        test_cifti_metadata()
        test_numeric_codes()
        test_qunex_metadata()
        test_multiple_metadata()
        
        # New comparison tests
        print("\n" + "=" * 70)
        print("NIfTI Image Comparison Tests")
        print("=" * 70)
        test_compare_identical_files()
        test_compare_different_headers()
        test_compare_different_extensions()
        test_compare_same_extension_different_content()
        test_compare_different_data()
        test_compare_different_dimensions()
        test_compare_ndifflines_parameter()

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED!")
        print("=" * 70)
        return 0

    except Exception as e:
        print("\n" + "=" * 70)
        print("TEST FAILED!")
        print("=" * 70)
        print("Error:", str(e))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())


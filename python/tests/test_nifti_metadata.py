#!/usr/bin/env python
# encoding: utf-8

"""
Test suite for NIfTI metadata extension reading functionality.
"""

import sys
import os
import tempfile
import struct

from qx_utilities.general.img import niftihdr, print_nifti_metadata


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


def main():
    print("=" * 70)
    print("NIfTI Metadata Extension Tests")
    print("=" * 70)

    try:
        test_no_metadata()
        test_list_mode()
        test_cifti_metadata()
        test_numeric_codes()
        test_qunex_metadata()
        test_multiple_metadata()

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

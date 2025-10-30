#!/usr/bin/env python
# encoding: utf-8

"""
Demonstration script for the print_nifti_metadata function.

This script shows how to use the print_nifti_metadata function to inspect
NIfTI extension blocks in various scenarios.
"""

import sys
import os
import tempfile

# Add the parent directory to the path to import qx_utilities
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'qx_utilities'))

from general.img import niftihdr, print_nifti_metadata


def create_demo_file():
    """Create a demo NIfTI file with both CIFTI and QuNex metadata"""

    # Create temporary file
    tmpfile = tempfile.NamedTemporaryFile(suffix='.dtseries.nii', delete=False)
    tmpfile.close()
    filename = tmpfile.name

    # Create header
    hdr = niftihdr()
    hdr.sizex = 91282  # Typical CIFTI dense timeseries size
    hdr.sizey = 1
    hdr.sizez = 1
    hdr.frames = 1200  # 10 minutes at TR=0.5s
    hdr.pixdim_t = 0.5
    hdr.descrip = "Demo CIFTI file with metadata"

    # Set extension flag
    hdr.ext = chr(1) + chr(0) * 3

    # Add CIFTI metadata
    cifti_xml = """<?xml version="1.0" encoding="UTF-8"?>
<CIFTI Version="2.0" NumberOfMatrices="1">
  <Matrix>
    <MetaData>
      <MD>
        <Name>SurfaceResolution</Name>
        <Value>32k_fs_LR</Value>
      </MD>
      <MD>
        <Name>Parcellation</Name>
        <Value>Gordon333</Value>
      </MD>
      <MD>
        <Name>Processing</Name>
        <Value>HCP Pipeline v3.27.0</Value>
      </MD>
    </MetaData>
    <MatrixIndicesMap AppliesToMatrixDimension="0" IndicesMapToDataType="CIFTI_INDEX_TYPE_SERIES">
      <TimeStep>0.5</TimeStep>
      <NumberOfSeriesPoints>1200</NumberOfSeriesPoints>
    </MatrixIndicesMap>
    <MatrixIndicesMap AppliesToMatrixDimension="1" IndicesMapToDataType="CIFTI_INDEX_TYPE_BRAIN_MODELS">
      <BrainModel IndexOffset="0" IndexCount="29696" ModelType="SURFACE" BrainStructure="CORTEX_LEFT"/>
      <BrainModel IndexOffset="29696" IndexCount="29716" ModelType="SURFACE" BrainStructure="CORTEX_RIGHT"/>
      <BrainModel IndexOffset="59412" IndexCount="31870" ModelType="VOXELS" BrainStructure="SUBCORTICAL"/>
    </MatrixIndicesMap>
  </Matrix>
</CIFTI>"""

    cifti_data = cifti_xml.encode('utf-8')
    esize = len(cifti_data) + 8
    esize = ((esize + 15) // 16) * 16
    cifti_data = cifti_data + b'\x00' * (esize - len(cifti_data) - 8)

    # Add QuNex metadata
    qunex_info = """QuNex Processing Information
=============================
Session ID: HCP_123456
Study: HCP_Development
Batch: batch001
Bold Run: bold1
Processing Date: 2025-10-28 14:30:00
Pipeline: hcp_fmri_volume
QuNex Version: 0.99.5

Processing Steps:
- Motion correction completed
- Distortion correction applied
- Registration to T1w performed
- Surface mapping executed
- ICA-FIX denoising applied

Quality Metrics:
- Mean FD: 0.12 mm
- Max FD: 0.85 mm
- DVARS: 1.23
- SNR: 45.7 dB
"""

    qunex_data = qunex_info.encode('utf-8')
    esize = len(qunex_data) + 8
    esize = ((esize + 15) // 16) * 16
    qunex_data = qunex_data + b'\x00' * (esize - len(qunex_data) - 8)

    # Set metadata
    hdr.meta = [
        [((len(cifti_xml.encode('utf-8')) + 8 + 15) // 16) * 16, 32, cifti_data],
        [((len(qunex_info.encode('utf-8')) + 8 + 15) // 16) * 16, 64, qunex_data]
    ]

    # Update vox_offset
    hdr.vox_offset = 352 + sum([m[0] for m in hdr.meta])

    # Write the file
    hdr.writeHeader(filename)

    return filename


def main():
    print("=" * 70)
    print("NIfTI Metadata Inspection Demo")
    print("=" * 70)
    print()

    # Create demo file
    print("Creating demo NIfTI file with CIFTI and QuNex metadata...")
    demo_file = create_demo_file()
    print(f"Created: {demo_file}")
    print()

    # Demo 1: List metadata (default)
    print("\n" + "#" * 70)
    print("# DEMO 1: List metadata (default behavior)")
    print("#" * 70)
    print()
    print("Command: print_nifti_metadata(filename)")
    print("         # or explicitly: print_nifti_metadata(filename, info='list')")
    print()
    print_nifti_metadata(demo_file)

    input("\nPress Enter to continue to next demo...")

    # Demo 2: Print all metadata with content
    print("\n" + "#" * 70)
    print("# DEMO 2: Print ALL metadata with full content")
    print("#" * 70)
    print()
    print("Command: print_nifti_metadata(filename, info='all')")
    print()
    print_nifti_metadata(demo_file, info='all')

    input("\nPress Enter to continue to next demo...")

    # Demo 3: Print only CIFTI metadata
    print("\n" + "#" * 70)
    print("# DEMO 3: Print CIFTI metadata only")
    print("#" * 70)
    print()
    print("Command: print_nifti_metadata(filename, info='cifti')")
    print()
    print_nifti_metadata(demo_file, info='cifti')

    input("\nPress Enter to continue to next demo...")

    # Demo 4: Print only QuNex metadata
    print("\n" + "#" * 70)
    print("# DEMO 4: Print QuNex metadata only")
    print("#" * 70)
    print()
    print("Command: print_nifti_metadata(filename, info='qunex')")
    print()
    print_nifti_metadata(demo_file, info='qunex')

    input("\nPress Enter to continue to next demo...")

    # Demo 5: Using numeric codes
    print("\n" + "#" * 70)
    print("# DEMO 5: Using numeric extension codes")
    print("#" * 70)
    print()
    print("Command: print_nifti_metadata(filename, info=32)  # CIFTI code")
    print()
    print_nifti_metadata(demo_file, info=32)

    print()
    print("Command: print_nifti_metadata(filename, info=64)  # QuNex code")
    print()
    print_nifti_metadata(demo_file, info=64)

    print()
    print("=" * 70)
    print("Demo complete!")
    print("=" * 70)
    print()
    print("Temporary file created:", demo_file)
    print("You can inspect it manually or delete it.")

    # Clean up
    response = input("\nDelete demo file? (y/n): ")
    if response.lower() == 'y':
        os.remove(demo_file)
        print(f"Deleted: {demo_file}")
    else:
        print(f"Kept: {demo_file}")


if __name__ == '__main__':
    main()

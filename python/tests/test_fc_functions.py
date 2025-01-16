#'octave -q --eval'

import os
import tempfile
import nibabel as nib
import numpy as np
import pandas as pd

from datetime import datetime
from pymatreader import read_mat
from general import matlab as gm


if "QUNEXMCOMMAND" not in os.environ:
    print("WARNING: QUNEXMCOMMAND environment variable not set. Matlab will be run by default!")
    mcommand = "matlab -nodisplay -nosplash -r"
else:
    mcommand = os.environ['QUNEXMCOMMAND']

PREPARE_REF_DATA = False  # set to True to prepare reference data
REF_DATA_DIR = os.path.join(f'{os.environ.get("QUNEXPATH", "")}', 'qx_library', 'matlab_tests')
if PREPARE_REF_DATA:
    OUTPUT_DIR = REF_DATA_DIR
else:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_DIR = os.path.join(tempfile.gettempdir(), 'fc_tests', timestamp)
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _run_fc_function(command, ref_dir, output_subdir, args, tolerance=0):
    os.makedirs(output_subdir, exist_ok=True)
    gm.run(command, args)
    if PREPARE_REF_DATA:
        return

    test_files = os.listdir(ref_dir)
    for file in test_files:
        ref_file = os.path.join(ref_dir, file)
        output_file = os.path.join(output_subdir, file)
        print(f'... checking {file}')
        if file.endswith('.nii') or file.endswith('.nii.gz'):
            nii_ref = nib.load(ref_file).get_fdata()
            nii_output = nib.load(output_file).get_fdata()

            # flatten, remove nan and inf values
            nii_ref = nii_ref.flatten()
            nii_ref = nii_ref[~np.isnan(nii_ref)]
            nii_ref = nii_ref[~np.isinf(nii_ref)]
            nii_output = nii_output.flatten()
            nii_output = nii_output[~np.isnan(nii_output)]
            nii_output = nii_output[~np.isinf(nii_output)]

            if len(nii_ref) > 0 and len(nii_output) > 0:
                print(nii_ref)
                print(nii_output)
                r = np.corrcoef(nii_ref, nii_output)
                print(f'    ... correlation between reference and output nii file: {r[0, 1]}')
                max_diff = np.max(np.abs(nii_ref - nii_output))
                print(f'    ... max difference between reference and output nii file: {max_diff}')
                assert np.allclose(nii_ref, nii_output, atol=tolerance)


        elif file.endswith('') or file.endswith('.txt'):
            with open(ref_file, 'r') as f:
                ref_data = f.readlines()
            with open(output_file, 'r') as f:
                output_data = f.readlines()

            # remove first line, because it contains the date
            if ref_data[0].startswith('# Created by'):
                ref_data = ref_data[1:]
                output_data = output_data[1:]

            assert ref_data == output_data

        elif file.endswith('.tsv'):
            df_ref = pd.read_csv(ref_file, sep='\t')
            df_output = pd.read_csv(output_file, sep='\t')

            assert df_ref.equals(df_output)

        elif file.endswith('.mat'):
            mat_ref = read_mat(ref_file)
            mat_output = read_mat(output_file)

            assert mat_ref == mat_output


def test_fc_compute_seedmaps_1():
    ref_dir = os.path.join(REF_DATA_DIR, 'fc_compute_seedmaps', '1')
    output_subdir = os.path.join(OUTPUT_DIR, 'fc_compute_seedmaps', '1')
    args = {
        'flist': os.path.join(REF_DATA_DIR, 'rest_cifti.list'),
        'roiinfo': os.path.join(REF_DATA_DIR, 'ROI', 'acc_dlpfc.names'),
        'frames': '0',
        'targetf': output_subdir,
        'options': 'ignore:use|fcmeasure:r|savegroup:none|saveind:all_joint|saveindname:yes|itargetf:gfolder|verbose:true|debug:true'
    }
    _run_fc_function('fc_compute_seedmaps', ref_dir, output_subdir, args, tolerance=0.00001)


def test_fc_compute_seedmaps_2():
    ref_dir = os.path.join(REF_DATA_DIR, 'fc_compute_seedmaps', '2')
    output_subdir = os.path.join(OUTPUT_DIR, 'fc_compute_seedmaps', '2')
    args = {
        'flist': os.path.join(REF_DATA_DIR, 'rest_cifti.list'),
        'roiinfo': os.path.join(REF_DATA_DIR, 'ROI', 'acc_dlpfc.names'),
        'frames': '0',
        'targetf': output_subdir,
        'options': 'ignore:use|fcmeasure:r|savegroup:all|saveind:none|saveindname:yes|itargetf:gfolder|verbose:true|debug:true'
    }
    _run_fc_function('fc_compute_seedmaps', ref_dir, output_subdir, args, tolerance=0.00001)


def test_fc_compute_seedmaps_3():
    ref_dir = os.path.join(REF_DATA_DIR, 'fc_compute_seedmaps', '3')
    output_subdir = os.path.join(OUTPUT_DIR, 'fc_compute_seedmaps', '3')
    args = {
        'flist': os.path.join(REF_DATA_DIR, 'rest_cifti.list'),
        'roiinfo': os.path.join(REF_DATA_DIR, 'ROI', 'acc_dlpfc.names'),
        'frames': '0',
        'targetf': output_subdir,
        'options': 'ignore:use|fcmeasure:cv|savegroup:mean_r,group_z|saveind:none|saveindname:yes|itargetf:gfolder|verbose:true|debug:true'
    }
    _run_fc_function('fc_compute_seedmaps', ref_dir, output_subdir, args)


def test_fc_compute_roifc_1():
    ref_dir = os.path.join(REF_DATA_DIR, 'fc_compute_roifc', '1')
    output_subdir = os.path.join(OUTPUT_DIR, 'fc_compute_roifc', '1')
    args = {
        'flist': os.path.join(REF_DATA_DIR, 'rest_cifti.list'),
        'roiinfo': os.path.join(REF_DATA_DIR, 'ROI', 'acc_dlpfc.names'),
        'frames': '0',
        'targetf': output_subdir,
        'options': 'ignore:use|fcmeasure:r|savegroup:mat,all_long,all_wide_single,all_wide_separate|saveind:long,wide_single,wide_separate,mat|savesessionid:yes|itargetf:gfolder|verbose:true|debug:true'
    }
    _run_fc_function('fc_compute_roifc', ref_dir, output_subdir, args)


def test_fc_compute_roifc_2():
    ref_dir = os.path.join(REF_DATA_DIR, 'fc_compute_roifc', '2')
    output_subdir = os.path.join(OUTPUT_DIR, 'fc_compute_roifc', '2')
    args = {
        'flist': os.path.join(REF_DATA_DIR, 'rest_cifti.list'),
        'roiinfo': os.path.join(REF_DATA_DIR, 'ROI', 'acc_dlpfc.names'),
        'frames': '0',
        'targetf': output_subdir,
        'options': 'ignore:use|fcmeasure:cv|savegroup:all_long|saveind:long|savesessionid:true|itargetf:sfolder|verbose:true|debug:true'
    }
    _run_fc_function('fc_compute_roifc', ref_dir, output_subdir, args)


def test_fc_extract_roi_timeseries_1():
    ref_dir = os.path.join(REF_DATA_DIR, 'fc_extract_roi_timeseries', '1')
    output_subdir = os.path.join(OUTPUT_DIR, 'fc_extract_roi_timeseries', '1')
    args = {
        'flist': os.path.join(REF_DATA_DIR, 'rest_cifti.list'),
        'roiinfo': os.path.join(REF_DATA_DIR, 'ROI', 'acc_dlpfc.names'),
        'frames': '0',
        'targetf': output_subdir,
        'options': 'ignore:use|savegroup:mat,long,wide|saveind:long,wide,mat|savesessionid:yes|itargetf:gfolder|verbose:true|debug:true'
    }
    _run_fc_function('fc_extract_roi_timeseries', ref_dir, output_subdir, args)


def test_fc_extract_roi_timeseries_2():
    ref_dir = os.path.join(REF_DATA_DIR, 'fc_extract_roi_timeseries', '2')
    output_subdir = os.path.join(OUTPUT_DIR, 'fc_extract_roi_timeseries', '2')
    args = {
        'flist': os.path.join(REF_DATA_DIR, 'rest_cifti.list'),
        'roiinfo': os.path.join(REF_DATA_DIR, 'ROI', 'acc_dlpfc.names'),
        'frames': '0',
        'targetf': output_subdir,
        'options': 'ignore:use|savegroup:long|saveind:long|savesessionid:true|itargetf:sfolder|verbose:true|debug:true'
    }
    _run_fc_function('fc_extract_roi_timeseries', ref_dir, output_subdir, args)


def test_fc_compute_gbc_1():
    ref_dir = os.path.join(REF_DATA_DIR, 'fc_compute_gbc', '1')
    output_subdir = os.path.join(OUTPUT_DIR, 'fc_compute_gbc', '1')
    args = {
        'flist': os.path.join(REF_DATA_DIR, 'rest_cifti.list'),
        'sroiinfo': os.path.join(REF_DATA_DIR, 'ROI', 'acc_dlpfc.names'),
        'troiinfo': os.path.join(REF_DATA_DIR, 'ROI', 'acc_dlpfc.names'),
        'frames': '0',
        'targetf': output_subdir,
        'options': 'ignore:use|fcmeasure:cv|savegroup:all|saveind:none|saveindname:yes|itargetf:gfolder|verbose:true|debug:false|time=true|step=48000',
        'command': 'mFc:0.2|aFc:0.1|pFc:0.15|nFc:-0.2|aD:0.5|pD:0.7|nD:-.6'
    }
    _run_fc_function('fc_compute_gbc', ref_dir, output_subdir, args, tolerance=0.00001)


def test_fc_compute_gbc_2():
    ref_dir = os.path.join(REF_DATA_DIR, 'fc_compute_gbc', '2')
    output_subdir = os.path.join(OUTPUT_DIR, 'fc_compute_gbc', '2')
    args = {
        'flist': os.path.join(REF_DATA_DIR, 'rest_cifti.list'),
        'sroiinfo': os.path.join(REF_DATA_DIR, 'ROI', 'acc_dlpfc.names'),
        'troiinfo': os.path.join(REF_DATA_DIR, 'ROI', 'HCP.Parcelation.LR.dlabel.nii|rois:1,2,3,4,5,6,7,8,9,10,11,12,13,14'),
        'frames': '0',
        'targetf': output_subdir,
        'options': 'ignore:use|fcmeasure:r|savegroup:all|saveind:none|saveindname:yes|itargetf:gfolder|verbose:true|debug:false|time=true|step=48000',
        'command': 'mFz:0.2|aFz:0.1|pFz:0.15|nFz:-0.2'
    }
    _run_fc_function('fc_compute_gbc', ref_dir, output_subdir, args, tolerance=0.001)


def test_fc_compute_gbc_3():
    ref_dir = os.path.join(REF_DATA_DIR, 'fc_compute_gbc', '3')
    output_subdir = os.path.join(OUTPUT_DIR, 'fc_compute_gbc', '3')
    args = {
        'flist': os.path.join(REF_DATA_DIR, 'rest_cifti.list'),
        'sroiinfo': '',
        'troiinfo': '',
        'frames': '0',
        'targetf': output_subdir,
        'options': 'ignore:use|fcmeasure:r|savegroup:all|saveind:none|saveindname:yes|itargetf:gfolder|verbose:true|debug:false|time=true|step=48000',
        'command': 'mFz:0.2|aFz:0.1|pFz:0.15|nFz:-0.2'
    }
    _run_fc_function('fc_compute_gbc', ref_dir, output_subdir, args, tolerance=0.5)


def test_fc_compute_gbc_4():
    ref_dir = os.path.join(REF_DATA_DIR, 'fc_compute_gbc', '4')
    output_subdir = os.path.join(OUTPUT_DIR, 'fc_compute_gbc', '4')
    args = {
        'flist': os.path.join(REF_DATA_DIR, 'rest_cifti.list'),
        'sroiinfo': os.path.join(REF_DATA_DIR, 'ROI', 'acc_dlpfc.names'),
        'troiinfo': os.path.join(REF_DATA_DIR, 'ROI', 'HCP.Parcelation.LR.dlabel.nii|rois:1,2,3,4,5,6,7,8,9,10,11,12,13,14'),
        'frames': '0',
        'targetf': output_subdir,
        'options': 'ignore:use|fcmeasure:r|savegroup:none|saveind:all|saveindname:yes|itargetf:gfolder|verbose:true|debug:true',
        'command': 'mFcp:3|aFcp:4|mFcs:2|pFcs:3|nFcs:2|aFcs:3'
    }
    _run_fc_function('fc_compute_gbc', ref_dir, output_subdir, args)


def test_fc_compute_gbc_5():
    ref_dir = os.path.join(REF_DATA_DIR, 'fc_compute_gbc', '5')
    output_subdir = os.path.join(OUTPUT_DIR, 'fc_compute_gbc', '5')
    args = {
        'flist': os.path.join(REF_DATA_DIR, 'rest_cifti.list'),
        'sroiinfo': os.path.join(REF_DATA_DIR, 'ROI', 'acc_dlpfc.names'),
        'troiinfo': os.path.join(REF_DATA_DIR, 'ROI', 'acc_dlpfc.names'),
        'frames': '0',
        'targetf': output_subdir,
        'options': 'ignore:use|fcmeasure:r|savegroup:none|saveind:all|saveindname:yes|itargetf:gfolder|verbose:true|debug:true',
        'command': 'mFzp:3|aFzp:4|mFzs:2|pFzs:3|nFzs:2|aFzs:3'
    }
    _run_fc_function('fc_compute_gbc', ref_dir, output_subdir, args)

#'octave -q --eval'

import os
import tempfile
import nibabel as nib
import numpy as np

from datetime import datetime
from general import matlab as gm


if "QUNEXMCOMMAND" not in os.environ:
    print("WARNING: QUNEXMCOMMAND environment variable not set. Matlab will be run by default!")
    mcommand = "matlab -nodisplay -nosplash -r"
else:
    mcommand = os.environ['QUNEXMCOMMAND']

PREPARE_REF_DATA = False  # Set to True to prepare reference data
REF_DATA_DIR = '../../qx_library/matlab_tests/'
if PREPARE_REF_DATA:
    OUTPUT_DIR = REF_DATA_DIR
else:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_DIR = os.path.join(tempfile.gettempdir(), 'fc_tests', timestamp, '/')
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def _fc_compute_seedmaps(ref_dir, output_subdir, args):
    gm.run('fc_compute_seedmaps', args)
    if PREPARE_REF_DATA:
        return

    test_files = os.listdir(ref_dir)
    for file in test_files:
        nii_test = nib.load(f'{ref_dir}/{file}')
        nii_tmp = nib.load(f'{output_subdir}/{file}')
        print(f'... checking {file}')

        assert np.array_equal(nii_test.get_fdata(), nii_tmp.get_fdata())

def test_fc_compute_seedmaps_1():
    ref_dir = f'{REF_DATA_DIR}fc_compute_seedmaps/1'
    output_subdir = f'{OUTPUT_DIR}fc_compute_seedmaps/1'
    os.makedirs(output_subdir, exist_ok=True)
    args = {'flist': f'{REF_DATA_DIR}rest_cifti.list',
            'roiinfo': f'{REF_DATA_DIR}ROI/acc_dlpfc.names',
            'frames': '0',
            'targetf': output_subdir,
            'options': 'ignore:use|fcmeasure:r|savegroup:none|saveind:all_joint|saveindname:yes|itargetf:gfolder|verbose:true|debug:true'}
    _fc_compute_seedmaps(ref_dir, output_subdir, args)

def test_fc_compute_seedmaps_2():
    ref_dir = f'{REF_DATA_DIR}fc_compute_seedmaps/2'
    output_subdir = f'{OUTPUT_DIR}fc_compute_seedmaps/2'
    os.makedirs(output_subdir, exist_ok=True)
    args = {'flist': f'{REF_DATA_DIR}rest_cifti.list',
            'roiinfo': f'{REF_DATA_DIR}ROI/acc_dlpfc.names',
            'frames': '0',
            'targetf': output_subdir,
            'options': 'ignore:use|fcmeasure:r|savegroup:all|saveind:none|saveindname:yes|itargetf:gfolder|verbose:true|debug:true'}
    _fc_compute_seedmaps(ref_dir, output_subdir, args)

def test_fc_compute_seedmaps_3():
    ref_dir = f'{REF_DATA_DIR}fc_compute_seedmaps/3'
    output_subdir = f'{OUTPUT_DIR}fc_compute_seedmaps/3'
    os.makedirs(output_subdir, exist_ok=True)
    args = {'flist': f'{REF_DATA_DIR}rest_cifti.list',
            'roiinfo': f'{REF_DATA_DIR}ROI/acc_dlpfc.names',
            'frames': '0',
            'targetf': output_subdir,
            'options': 'ignore:use|fcmeasure:cv|savegroup:mean_r,group_z|saveind:none|saveindname:yes|itargetf:gfolder|verbose:true|debug:true'}
    _fc_compute_seedmaps(ref_dir, output_subdir, args)

// SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
//
// SPDX-License-Identifier: GPL-3.0-or-later

#include <math.h>
#include <matrix.h>
#include <mex.h>
#include <stdio.h>

#include "qx_nifti.h"
#include "znzlib.h"

// function [] = img_read_nifti_mx(filename, hdr, data, meta, doswap, verbose)
//
// To compile run: mex -lz img_save_nifti1.cpp qx_nifti.c znzlib.c
//



void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[])
{

    const mxArray          *hdr, *data, *meta, *doswap, *fname;
    int                     swap=0, v=1, verbose=0;

    mxClassID               dtype;
    int                     bsize;
    size_t                  dlen, mlen, hlen, ir;

    char                   *filename;
    znzFile                 filestream;

    char                   *hdrdata, *metadata;
    void                   *datapt;


    // --- map variables

    if (nrhs > 5){
        if (mxIsLogicalScalarTrue(prhs[5])){
            verbose = 1;
        }
    }

    if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "tic");

    if (nrhs < 4) {
        mexPrintf("ERROR: %d instead of at least 3 (hdr, data, meta) input arguments provided!\n", nrhs);
        mexErrMsgTxt("ERROR: Aborting!");
        return;
    }

    fname  = prhs[0];
    hdr    = prhs[1];
    data   = prhs[2];
    meta   = prhs[3];

    hdrdata  = (char *) mxGetPr(hdr);
    metadata = (char *) mxGetPr(meta);
    datapt   = mxGetPr(data);

    filename = mxArrayToString(fname);

    // --- Get sizes and deduce NIfTI version

    dlen = (size_t) mxGetNumberOfElements(data);
    mlen = (size_t) mxGetNumberOfElements(meta);
    hlen = (size_t) mxGetNumberOfElements(hdr);

    if (hlen == F_NIFTI2){
        v = 2;
    }

    if (verbose) mexPrintf("\n---> img_save_nifti_mx\n");
    if (verbose) mexPrintf("---> Saving %s as NIfTI-%d image.\n", filename, v);

    // ---> are we swapping

    if (nrhs > 4){
        doswap = prhs[4];
        if (mxIsLogicalScalarTrue(doswap)){
            swap = 1;
            if (verbose) mexPrintf("---> Endian swapping turned on.\n");
        }
    }

    // --- Get Data Type

    dtype = mxGetClassID(data);

    switch (dtype) {
        case mxSINGLE_CLASS:
            bsize = 4;
            break;
        case mxINT32_CLASS:
            bsize = 4;
            break;
        case mxUINT8_CLASS:
            bsize = 1;
            break;
        case mxINT16_CLASS:
            bsize = 2;
            break;
        case mxDOUBLE_CLASS:
            bsize = 8;
            break;
    }


    // --- do the swapping if needed

    if (swap){

        // --- header

        if (v == 1) {
            if (verbose) mexPrintf("---> Swapping NIfTI1 header        ");
            if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");
            swap_nifti_1_header((struct nifti_1_header *) hdrdata);
        } else {
            if (verbose) mexPrintf("---> Swapping NIfTI2 header        ");
            if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");
            swap_nifti_2_header((struct nifti_2_header *) hdrdata);
        }

        // --- data

        if (verbose) mexPrintf("---> Swapping Data                 ");
        if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");
        nifti_swap_Nbytes(dlen, bsize, datapt);

    }


    // --- Open file

    if (verbose) mexPrintf("---> Opening file                  ");
    if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");

    filestream = znzopen(filename, "wb", nifti_is_gzfile(filename));
    if (znz_isnull(filestream)){
        mexPrintf("ERROR: Failed to open file %s for writing!\n", filename);
        mexErrMsgTxt("ERROR: Aborting!");
        return;
    }

    // --- Dump contents

    if (verbose) mexPrintf("---> Saving header                 ");
    if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");

    ir = znzwrite(hdrdata, sizeof(char), hlen, filestream);
    if (ir != hlen){
        znzclose(filestream);
        mexPrintf("ERROR: Written %d out of %d header elements!\n", ir, hlen);
        mexErrMsgTxt("ERROR: Aborting!");
        return;
    }

    if (verbose) mexPrintf("---> Saving metadata               ");
    if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");

    ir = znzwrite(metadata, sizeof(char), mlen, filestream);
    if (ir != mlen){
        znzclose(filestream);
        mexPrintf("ERROR: Written %d out of %d metadata elements!\n", ir, mlen);
        mexErrMsgTxt("ERROR: Aborting!");
        return;
    }

    if (verbose) mexPrintf("---> Saving data                   ");
    if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");


    ir = znzwrite(datapt, (size_t) bsize, dlen, filestream);
    if (ir != dlen){
        znzclose(filestream);
        mexPrintf("ERROR: Written %d out of %d metadata elements!\n", ir, dlen);
        mexErrMsgTxt("ERROR: Aborting!");
        return;
    }

    if (verbose) mexPrintf("---> Closing file                  ");
    if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");

    znzclose(filestream);

    if (verbose) mexPrintf("---> Done                          ");
    if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");

    return;

}


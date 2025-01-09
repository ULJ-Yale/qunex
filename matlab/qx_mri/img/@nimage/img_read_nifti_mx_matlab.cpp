// SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
//
// SPDX-License-Identifier: GPL-3.0-or-later

#include <math.h>
#include <matrix.h>
#include <mex.h>
#include <stdio.h>

#include "qx_nifti.h"
#include "znzlib.h"

// function [hdr, data, meta, doswap] = img_read_nifti_mx(filename, verbose)
//
// To compile run:
//   cp img_read_nifti_mx_matlab.cpp img_read_nifti_mx.cpp
//   mex -lz img_read_nifti_mx.cpp qx_nifti.c znzlib.c
//   rm img_read_nifti_mx.cpp

void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[])
{
    struct nii_info         ninfo;
    nifti_type_ele         *dinfo;

    char                   *filename;
    znzFile                 filestream;
    int                     readlen;
    int                     hsizeof;

    mxArray                *hdr, *data, *meta, *doswap;
    char                   *inpoint, *hdrdata, *metadata;
    void                   *datapt;
    void                   *mbuff;
    mxClassID               dtype;

    int                     i, ii, bsize, swap=0, verbose=0;
    size_t                  ir;
    int                     status=1;

    // --- verbosity
    if (nrhs > 1){
        if (mxIsLogicalScalarTrue(prhs[1])){
            verbose = 1;
            mexCallMATLAB(0, NULL, 0, NULL, "tic");
        }
    }

    // --- Open file
    filename = mxArrayToString(prhs[0]);

    if (verbose) mexPrintf("\n---> img_read_nifti_mx\n");
    if (verbose) mexPrintf("---> Reading %s \n", filename);

    filestream = znzopen(filename, "rb", nifti_is_gzfile(filename));
    if (znz_isnull(filestream)){
        mexPrintf("ERROR: Failed to read file %s!\n", filename);
        mexErrMsgTxt("ERROR: Aborting!");
        return;
    }

    if (verbose) mexPrintf("---> Read header                   ");
    if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");

    // --- Read and check size
    ii = (int) znzread(&hsizeof, 1, sizeof(int), filestream);
    ii = (int) znzseek(filestream, 0, SEEK_SET);

    // --- Read header and set up info
    switch(hsizeof){
        case F_NIFTI1:
            if (verbose) mexPrintf("---> Unpacking unswapped NIfTI1    ");
            status = read_nifti1_hdr(&ninfo, filestream, 0);
            if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");
            break;
        case F_NIFTI1_SWAP:
            if (verbose) mexPrintf("---> Unpacking swapped NIfTI1      ");
            status = read_nifti1_hdr(&ninfo, filestream, 1);
            swap   = 1;
            if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");
            break;
        case F_NIFTI2:
            if (verbose) mexPrintf("---> Unpacking unswapped NIfTI2    ");
            status = read_nifti2_hdr(&ninfo, filestream, 0);
            if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");
            break;
        case F_NIFTI2_SWAP:
            if (verbose) mexPrintf("---> Unpacking swapped NIfTI2      ");
            status = read_nifti2_hdr(&ninfo, filestream, 1);
            if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");
            swap   = 1;
            break;
    }

    if (!status){
        mexPrintf("ERROR: Failed to process header from file %s!\n", filename);
        mexErrMsgTxt("ERROR: Aborting!");
        return;
    }

    // --- Embed header
    hdr = mxCreateNumericMatrix(ninfo.hlen, 1, mxUINT8_CLASS, mxREAL);
    hdrdata = (char *) mxGetData(hdr);
    inpoint = (char *) ninfo.hdata;
    for (i=0; i < ninfo.hlen; i++){
        hdrdata[i] = inpoint[i];
    }

    if (verbose) {
        mexPrintf("\nDIMENSIONS\n");
        for (i=1; i<7; i++) {
            mexPrintf("dim[%d]: %d\n", i, ninfo.dim[i]);
        }
    }

    // mexPrintf("hlen: %d, dstart: %d, dlen: %d, dtype: %d, mstart: %d, mlen: %d!\n", ninfo.hlen, ninfo.dstart, ninfo.dlen, ninfo.dtype, ninfo.mstart, ninfo.mlen);
    if (verbose) mexPrintf("\nPOSITIONS\nhlen:   %d\ndstart: %d\ndlen:   %d\ndtype:  %d\nmstart: %d\nmlen:   %d\n", ninfo.hlen, ninfo.dstart, ninfo.dlen, ninfo.dtype, ninfo.mstart, ninfo.mlen);

    plhs[0] = hdr;

    // --- Embed data
    dinfo = nifti_datatype_to_ele(ninfo.dtype);
    // mexPrintf("data type: %d, nbyper: %d, swapsize: %d, name: %s\n", dinfo->type, dinfo->nbyper, dinfo->swapsize, dinfo->name);
    if (verbose) mexPrintf("\nDATA\ndata type: %d\nnbyper:    %d\nswapsize:  %d\nname:      %s\n\n", dinfo->type, dinfo->nbyper, dinfo->swapsize, dinfo->name);

    switch (dinfo->type) {
        case DT_INT8:
            dtype = mxINT8_CLASS;
            break;
        case DT_UINT8:
            dtype = mxUINT8_CLASS;
            break;
        case DT_INT16:
            dtype = mxINT16_CLASS;
            break;
        case DT_UINT16:
            dtype = mxUINT16_CLASS;
            break;
        case DT_INT32:
            dtype = mxINT32_CLASS;
            break;
        case DT_UINT32:
            dtype = mxUINT32_CLASS;
            break;
        case DT_INT64:
            dtype = mxINT64_CLASS;
            break;
        case DT_UINT64:
            dtype = mxUINT64_CLASS;
            break;
        case DT_FLOAT:
            dtype = mxSINGLE_CLASS;
            break;
        case DT_DOUBLE:
            dtype = mxDOUBLE_CLASS;
            break;
        default:
            mexPrintf("ERROR: Datatype that can not be converted to MATLAB equivalent in file %s!\n", filename);
            mexErrMsgTxt("ERROR: Aborting!");
            return;
    }

    data = mxCreateNumericMatrix(0, 0, dtype, mxREAL);
    mxSetM(data, ninfo.dlen);
    mxSetN(data, 1);
    datapt = mxMalloc(ninfo.dlen * dinfo->nbyper);
    mxSetData(data, datapt);

    ir = znzseek(filestream, (long) ninfo.dstart, SEEK_SET);
    ir = znzread(datapt, (size_t) dinfo->nbyper, (size_t) ninfo.dlen, filestream);
    if (ir < ninfo.dlen) {
        mexPrintf("ERROR: Failed to read full image data from file %s! [%d of %d]\n", filename, ir, ninfo.dlen);
        mexErrMsgTxt("ERROR: Aborting!");
        return;
    }

    if (verbose) mexPrintf("---> Read data                     ");
    if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");

    if (swap) {
        nifti_swap_Nbytes((size_t) ninfo.dlen, (int) dinfo->swapsize, datapt);

        if (verbose) mexPrintf("---> Swapped                       ");
        if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");
    }

    plhs[1] = data;

    // --- Embed raw metadata
    meta = mxCreateNumericMatrix(ninfo.mlen, 1, mxUINT8_CLASS, mxREAL);
    metadata = (char *) mxGetData(meta);
    ir = znzseek(filestream, (long) ninfo.mstart, SEEK_SET);
    ir = znzread(metadata, (size_t) sizeof(char), (size_t) ninfo.mlen, filestream);
    if (ir < ninfo.mlen) {
        mexPrintf("ERROR: Failed to read full meta data from file %s! [%d of %d]\n", filename, ir, ninfo.mlen);
        mexErrMsgTxt("ERROR: Aborting!");
        return;
    }
    plhs[2] = meta;

    if (verbose) mexPrintf("---> Read metadata                 ");
    if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");

    // --- Report swapping
    doswap = mxCreateNumericMatrix(1, 1, mxUINT8_CLASS, mxREAL);
    metadata = (char *) mxGetData(doswap);
    metadata[0] = (char) swap;

    plhs[3] = doswap;

    // --- Close the file
    znzclose(filestream);

    if (verbose) mexPrintf("---> Done                          ");
    if (verbose) mexCallMATLAB(0, NULL, 0, NULL, "toc");
}

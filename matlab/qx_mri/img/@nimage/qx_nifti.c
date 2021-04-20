// SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
//
// SPDX-License-Identifier: GPL-3.0-or-later

#include "qx_nifti.h"
#include <mex.h>


/*  ---> swapping code         */


void swap_nifti_1_header(struct nifti_1_header *h)
{

   nifti_swap_4bytes(1, &h->sizeof_hdr);
   nifti_swap_4bytes(1, &h->extents);
   nifti_swap_2bytes(1, &h->session_error);

   nifti_swap_2bytes(8, h->dim);
   nifti_swap_4bytes(1, &h->intent_p1);
   nifti_swap_4bytes(1, &h->intent_p2);
   nifti_swap_4bytes(1, &h->intent_p3);

   nifti_swap_2bytes(1, &h->intent_code);
   nifti_swap_2bytes(1, &h->datatype);
   nifti_swap_2bytes(1, &h->bitpix);
   nifti_swap_2bytes(1, &h->slice_start);

   nifti_swap_4bytes(8, h->pixdim);

   nifti_swap_4bytes(1, &h->vox_offset);
   nifti_swap_4bytes(1, &h->scl_slope);
   nifti_swap_4bytes(1, &h->scl_inter);
   nifti_swap_2bytes(1, &h->slice_end);

   nifti_swap_4bytes(1, &h->cal_max);
   nifti_swap_4bytes(1, &h->cal_min);
   nifti_swap_4bytes(1, &h->slice_duration);
   nifti_swap_4bytes(1, &h->toffset);
   nifti_swap_4bytes(1, &h->glmax);
   nifti_swap_4bytes(1, &h->glmin);

   nifti_swap_2bytes(1, &h->qform_code);
   nifti_swap_2bytes(1, &h->sform_code);

   nifti_swap_4bytes(1, &h->quatern_b);
   nifti_swap_4bytes(1, &h->quatern_c);
   nifti_swap_4bytes(1, &h->quatern_d);
   nifti_swap_4bytes(1, &h->qoffset_x);
   nifti_swap_4bytes(1, &h->qoffset_y);
   nifti_swap_4bytes(1, &h->qoffset_z);

   nifti_swap_4bytes(4, h->srow_x);
   nifti_swap_4bytes(4, h->srow_y);
   nifti_swap_4bytes(4, h->srow_z);

   return ;
}


/*  ---> swapping code  ~~~ NIfTI 2 - NOT YET DONE ~~~       */


void swap_nifti_2_header(struct nifti_2_header *h)
{

   nifti_swap_4bytes(1, &h->sizeof_hdr);
   nifti_swap_2bytes(1, &h->datatype);
   nifti_swap_2bytes(1, &h->bitpix);
   nifti_swap_8bytes(8, h->dim);

   nifti_swap_8bytes(1, &h->intent_p1);
   nifti_swap_8bytes(1, &h->intent_p2);
   nifti_swap_8bytes(1, &h->intent_p3);

   nifti_swap_8bytes(8, h->pixdim);
   nifti_swap_8bytes(1, &h->vox_offset);

   nifti_swap_8bytes(1, &h->scl_slope);
   nifti_swap_8bytes(1, &h->scl_inter);
   nifti_swap_8bytes(1, &h->cal_max);
   nifti_swap_8bytes(1, &h->cal_min);
   nifti_swap_8bytes(1, &h->slice_duration);
   nifti_swap_8bytes(1, &h->toffset);

   nifti_swap_8bytes(1, &h->slice_start);
   nifti_swap_8bytes(1, &h->slice_end);

   nifti_swap_2bytes(1, &h->qform_code);
   nifti_swap_2bytes(1, &h->sform_code);

   nifti_swap_8bytes(1, &h->quatern_b);
   nifti_swap_8bytes(1, &h->quatern_c);
   nifti_swap_8bytes(1, &h->quatern_d);
   nifti_swap_8bytes(1, &h->qoffset_x);
   nifti_swap_8bytes(1, &h->qoffset_y);
   nifti_swap_8bytes(1, &h->qoffset_z);

   nifti_swap_8bytes(4, h->srow_x);
   nifti_swap_8bytes(4, h->srow_y);
   nifti_swap_8bytes(4, h->srow_z);

   nifti_swap_2bytes(1, &h->slice_code);
   nifti_swap_2bytes(1, &h->xyzt_units);
   nifti_swap_2bytes(1, &h->intent_code);

   return ;
}


/*---------------------------------------------------------------------------*/
/* Routines to swap byte arrays in various ways:
    -  2 at a time:  ab               -> ba               [short]
    -  4 at a time:  abcd             -> dcba             [int, float]
    -  8 at a time:  abcdDCBA         -> ABCDdcba         [long long, double]
    - 16 at a time:  abcdefghHGFEDCBA -> ABCDEFGHhgfedcba [long double]
-----------------------------------------------------------------------------*/

void nifti_swap_2bytes(size_t n, void *ar)
{
   register size_t ii ;
   unsigned char  *cp1 = (unsigned char *)ar, * cp2;
   unsigned char   tval;

   for(ii=0 ; ii < n ; ii++){
       cp2 = cp1 + 1;
       tval = *cp1;  *cp1 = *cp2;  *cp2 = tval;
       cp1 += 2;
   }
   return;
}


void nifti_swap_4bytes(size_t n, void *ar)
{
   register size_t ii;
   unsigned char  *cp0 = (unsigned char *)ar, *cp1, *cp2;
   register unsigned char tval;

   for(ii=0 ; ii < n ; ii++){
       cp1 = cp0; cp2 = cp0+3;
       tval = *cp1;  *cp1 = *cp2;  *cp2 = tval;
       cp1++;  cp2--;
       tval = *cp1;  *cp1 = *cp2;  *cp2 = tval;
       cp0 += 4;
   }
   return ;
}


void nifti_swap_8bytes(size_t n , void *ar)
{
   register size_t ii;
   unsigned char  *cp0 = (unsigned char *)ar, *cp1, *cp2;
   register unsigned char tval;

   for(ii=0 ; ii < n ; ii++){
       cp1 = cp0;  cp2 = cp0+7;
       while ( cp2 > cp1 )      /* unroll? */
       {
           tval = *cp1 ; *cp1 = *cp2 ; *cp2 = tval ;
           cp1++; cp2--;
       }
       cp0 += 8;
   }
   return ;
}


void nifti_swap_16bytes(size_t n, void *ar)
{
   register size_t ii;
   unsigned char  *cp0 = (unsigned char *)ar, *cp1, *cp2;
   register unsigned char tval;

   for(ii=0 ; ii < n ; ii++){
       cp1 = cp0;  cp2 = cp0+15;
       while ( cp2 > cp1 )
       {
           tval = *cp1 ; *cp1 = *cp2 ; *cp2 = tval ;
           cp1++; cp2--;
       }
       cp0 += 16;
   }
   return ;
}

void nifti_swap_Nbytes(size_t n, int siz, void *ar)
{
   switch( siz ){
     case 2:  nifti_swap_2bytes (n, ar); break;
     case 4:  nifti_swap_4bytes (n, ar); break;
     case 8:  nifti_swap_8bytes (n, ar); break;
     case 16: nifti_swap_16bytes(n, ar); break;
     default:
        mexPrintf("\n** NIfTI: cannot swap in %d byte blocks\n", siz);
        break ;
   }
   return ;
}




//  ---> check whether zipped or not

int nifti_is_gzfile(const char* fname)
{
    if (fname == NULL) { return 0; }
    int len;
    len = (int)strlen(fname);
    if (len < 3) return 0;
    if (fileext_compare(fname + strlen(fname) - 3,".gz")==0) { return 1; }
    return 0;
}

int fileext_compare(const char * test_ext, const char * known_ext)
{
   char caps[8] = "";
   int  c, cmp, len;

   /* if equal, don't need to check case (store to avoid multiple calls) */
   cmp = strcmp(test_ext, known_ext);
   if( cmp == 0 ) return cmp;

   /* if anything odd, use default */
   if( !test_ext || !known_ext ) return cmp;

   len = strlen(known_ext);
   if( len > 7 ) return cmp;

   /* if here, strings are different but need to check upper-case */

   for(c = 0; c < len; c++ ) caps[c] = toupper(known_ext[c]);
   caps[c] = '\0';

   return strcmp(test_ext, caps);
}









// ---> Support functions


// ---> Read Nifti 1 header

int read_nifti1_hdr(struct nii_info *ninfo, znzFile filestream, int swapit)
{

    struct nifti_1_header  nhdr, *hptr ;
    int                    ii,i ;
    long                   size ;

    ii = (int) znzread(&nhdr, 1, sizeof(nhdr), filestream);

    if (ii < (int) sizeof(nhdr)) {
        return 0;
    }

    if (swapit) swap_nifti_1_header(&nhdr);
    hptr = (nifti_1_header *)malloc(sizeof(nifti_1_header));
    memcpy(hptr, &nhdr, sizeof(nifti_1_header));

    size = 1;
    for (i=1; i<7; i++) {
        if (nhdr.dim[i] > 0) size *= nhdr.dim[i];
        ninfo->dim[i] = (int) nhdr.dim[i];
    }

    ninfo->hlen   = 348                        ;
    ninfo->hdata  = (char *)  hptr             ;
    ninfo->dstart = (long)    nhdr.vox_offset  ;
    ninfo->dlen   = (long)    size             ;
    ninfo->dtype  = (int)     nhdr.datatype    ;
    ninfo->mstart = 348                        ; // 352
    ninfo->mlen   = nhdr.vox_offset - 348      ;

    return 1;

}

// ---> Read Nifti 2 header ~~~ NOT YET CHECKED ~~~

int read_nifti2_hdr(struct nii_info *ninfo, znzFile filestream, int swapit)
{

    struct nifti_2_header  nhdr, *hptr ;
    int                    ii,i ;
    long                   size ;

    ii = (int) znzread(&nhdr, 1, sizeof(nhdr), filestream);

    if (ii < (int) sizeof(nhdr)) {
        return 0;
    }

    if (swapit) swap_nifti_2_header(&nhdr);
    hptr = (nifti_2_header *)malloc(sizeof(nifti_2_header));
    memcpy(hptr, &nhdr, sizeof(nifti_2_header));

    size = 1;
    for (i=1; i<7; i++) {
        if (nhdr.dim[i] > 0) size *= nhdr.dim[i];
        ninfo->dim[i] = (int) nhdr.dim[i];
    }

    ninfo->hlen   = 540                        ;
    ninfo->hdata  = (char *)  hptr             ;
    ninfo->dstart = (long)    nhdr.vox_offset  ;
    ninfo->dlen   = (long)    size             ;
    ninfo->dtype  = (int)     nhdr.datatype    ;
    ninfo->mstart = 540                        ; // 553
    ninfo->mlen   = nhdr.vox_offset - 540      ;

    return 1;

}



/*! global nifti types structure list (per type, ordered oldest to newest) */
static nifti_type_ele nifti_type_list[] = {
    /* type  nbyper  swapsize   name  */
    {    0,     0,       0,   "DT_UNKNOWN"              },
    {    0,     0,       0,   "DT_NONE"                 },
    {    1,     0,       0,   "DT_BINARY"               },  /* not usable */
    {    2,     1,       0,   "DT_UNSIGNED_CHAR"        },
    {    2,     1,       0,   "DT_UINT8"                },
    {    2,     1,       0,   "NIFTI_TYPE_UINT8"        },
    {    4,     2,       2,   "DT_SIGNED_SHORT"         },
    {    4,     2,       2,   "DT_INT16"                },
    {    4,     2,       2,   "NIFTI_TYPE_INT16"        },
    {    8,     4,       4,   "DT_SIGNED_INT"           },
    {    8,     4,       4,   "DT_INT32"                },
    {    8,     4,       4,   "NIFTI_TYPE_INT32"        },
    {   16,     4,       4,   "DT_FLOAT"                },
    {   16,     4,       4,   "DT_FLOAT32"              },
    {   16,     4,       4,   "NIFTI_TYPE_FLOAT32"      },
    {   32,     8,       4,   "DT_COMPLEX"              },
    {   32,     8,       4,   "DT_COMPLEX64"            },
    {   32,     8,       4,   "NIFTI_TYPE_COMPLEX64"    },
    {   64,     8,       8,   "DT_DOUBLE"               },
    {   64,     8,       8,   "DT_FLOAT64"              },
    {   64,     8,       8,   "NIFTI_TYPE_FLOAT64"      },
    {  128,     3,       0,   "DT_RGB"                  },
    {  128,     3,       0,   "DT_RGB24"                },
    {  128,     3,       0,   "NIFTI_TYPE_RGB24"        },
    {  255,     0,       0,   "DT_ALL"                  },
    {  256,     1,       0,   "DT_INT8"                 },
    {  256,     1,       0,   "NIFTI_TYPE_INT8"         },
    {  512,     2,       2,   "DT_UINT16"               },
    {  512,     2,       2,   "NIFTI_TYPE_UINT16"       },
    {  768,     4,       4,   "DT_UINT32"               },
    {  768,     4,       4,   "NIFTI_TYPE_UINT32"       },
    { 1024,     8,       8,   "DT_INT64"                },
    { 1024,     8,       8,   "NIFTI_TYPE_INT64"        },
    { 1280,     8,       8,   "DT_UINT64"               },
    { 1280,     8,       8,   "NIFTI_TYPE_UINT64"       },
    { 1536,    16,      16,   "DT_FLOAT128"             },
    { 1536,    16,      16,   "NIFTI_TYPE_FLOAT128"     },
    { 1792,    16,       8,   "DT_COMPLEX128"           },
    { 1792,    16,       8,   "NIFTI_TYPE_COMPLEX128"   },
    { 2048,    32,      16,   "DT_COMPLEX256"           },
    { 2048,    32,      16,   "NIFTI_TYPE_COMPLEX256"   },
    { 2304,     4,       0,   "DT_RGBA32"               },
    { 2304,     4,       0,   "NIFTI_TYPE_RGBA32"       },
};



/*---------------------------------------------------------------------*/
/*! Given a NIFTI_TYPE string, such as "NIFTI_TYPE_INT16", return the
 *  corresponding integral type code.  The type code is the macro
 *  value defined in nifti1.h.
*//*-------------------------------------------------------------------*/
int nifti_datatype_from_string( const char * name )
{
    int tablen = sizeof(nifti_type_list)/sizeof(nifti_type_ele);
    int c;

    if( !name ) return DT_UNKNOWN;

    for( c = tablen-1; c > 0; c-- )
        if( !strcmp(name, nifti_type_list[c].name) )
            break;

    return nifti_type_list[c].type;
}


/*---------------------------------------------------------------------*/
/*! Given a NIFTI_TYPE value, such as NIFTI_TYPE_INT16, return the
 *  corresponding macro label as a string.  The dtype code is the
 *  macro value defined in nifti1.h.
*//*-------------------------------------------------------------------*/
char * nifti_datatype_to_string( int dtype )
{
    int tablen = sizeof(nifti_type_list)/sizeof(nifti_type_ele);
    int c;

    for( c = tablen-1; c > 0; c-- )
        if( nifti_type_list[c].type == dtype )
            break;

    return nifti_type_list[c].name;
}



nifti_type_ele * nifti_datatype_to_ele(int dtype)
{
    int tablen = sizeof(nifti_type_list)/sizeof(nifti_type_ele);
    int c;

    for( c = tablen-1; c > 0; c-- )
        if( nifti_type_list[c].type == dtype )
            break;

    return &nifti_type_list[c];
}




/*---------------------------------------------------------------------*/
/*! Determine whether dtype is a valid NIFTI_TYPE.
 *
 *  DT_UNKNOWN is considered invalid
 *
 *  The only difference 'for_nifti' makes is that DT_BINARY
 *  should be invalid for a NIfTI dataset.
*//*-------------------------------------------------------------------*/
int nifti_datatype_is_valid( int dtype, int for_nifti )
{
    int tablen = sizeof(nifti_type_list)/sizeof(nifti_type_ele);
    int c;

    /* special case */
    if( for_nifti && dtype == DT_BINARY ) return 0;

    for( c = tablen-1; c > 0; c-- )
        if( nifti_type_list[c].type == dtype )
            return 1;

    return 0;
}


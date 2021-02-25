/**

  qx_nifti

  A NIfTI file reader header for the gmri Matlab package.

  Adopted from nifti1.h with added NIfTI2 code.

  Messed up by Grega Repovs - 2014-05-10

 */

#ifndef _NIFTI_HEADER_
#define _NIFTI_HEADER_

/*=================*/
#ifdef  __cplusplus
extern "C" {
#endif
/*=================*/


#include "znzlib.h"
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

/*

    NIfTI-1 Header

*/
                        /*************************/  /************************/
struct nifti_1_header { /* NIFTI-1 usage         */  /* ANALYZE 7.5 field(s) */
                        /*************************/  /************************/
                                           /*--- was header_key substruct ---*/
 int   sizeof_hdr;    /*!< MUST be 348           */  /* int sizeof_hdr;      */
 char  data_type[10]; /*!< ++UNUSED++            */  /* char data_type[10];  */
 char  db_name[18];   /*!< ++UNUSED++            */  /* char db_name[18];    */
 int   extents;       /*!< ++UNUSED++            */  /* int extents;         */
 short session_error; /*!< ++UNUSED++            */  /* short session_error; */
 char  regular;       /*!< ++UNUSED++            */  /* char regular;        */
 char  dim_info;      /*!< MRI slice ordering.   */  /* char hkey_un0;       */

                                      /*--- was image_dimension substruct ---*/
 short dim[8];        /*!< Data array dimensions.*/  /* short dim[8];        */
 float intent_p1 ;    /*!< 1st intent parameter. */  /* short unused8;       */
                                                     /* short unused9;       */
 float intent_p2 ;    /*!< 2nd intent parameter. */  /* short unused10;      */
                                                     /* short unused11;      */
 float intent_p3 ;    /*!< 3rd intent parameter. */  /* short unused12;      */
                                                     /* short unused13;      */
 short intent_code ;  /*!< NIFTI_INTENT_* code.  */  /* short unused14;      */
 short datatype;      /*!< Defines data type!    */  /* short datatype;      */
 short bitpix;        /*!< Number bits/voxel.    */  /* short bitpix;        */
 short slice_start;   /*!< First slice index.    */  /* short dim_un0;       */
 float pixdim[8];     /*!< Grid spacings.        */  /* float pixdim[8];     */
 float vox_offset;    /*!< Offset into .nii file */  /* float vox_offset;    */
 float scl_slope ;    /*!< Data scaling: slope.  */  /* float funused1;      */
 float scl_inter ;    /*!< Data scaling: offset. */  /* float funused2;      */
 short slice_end;     /*!< Last slice index.     */  /* float funused3;      */
 char  slice_code ;   /*!< Slice timing order.   */
 char  xyzt_units ;   /*!< Units of pixdim[1..4] */
 float cal_max;       /*!< Max display intensity */  /* float cal_max;       */
 float cal_min;       /*!< Min display intensity */  /* float cal_min;       */
 float slice_duration;/*!< Time for 1 slice.     */  /* float compressed;    */
 float toffset;       /*!< Time axis shift.      */  /* float verified;      */
 int   glmax;         /*!< ++UNUSED++            */  /* int glmax;           */
 int   glmin;         /*!< ++UNUSED++            */  /* int glmin;           */

                                         /*--- was data_history substruct ---*/
 char  descrip[80];   /*!< any text you like.    */  /* char descrip[80];    */
 char  aux_file[24];  /*!< auxiliary filename.   */  /* char aux_file[24];   */

 short qform_code ;   /*!< NIFTI_XFORM_* code.   */  /*-- all ANALYZE 7.5 ---*/
 short sform_code ;   /*!< NIFTI_XFORM_* code.   */  /*   fields below here  */
                                                     /*   are replaced       */
 float quatern_b ;    /*!< Quaternion b param.   */
 float quatern_c ;    /*!< Quaternion c param.   */
 float quatern_d ;    /*!< Quaternion d param.   */
 float qoffset_x ;    /*!< Quaternion x shift.   */
 float qoffset_y ;    /*!< Quaternion y shift.   */
 float qoffset_z ;    /*!< Quaternion z shift.   */

 float srow_x[4] ;    /*!< 1st row affine transform.   */
 float srow_y[4] ;    /*!< 2nd row affine transform.   */
 float srow_z[4] ;    /*!< 3rd row affine transform.   */

 char intent_name[16];/*!< 'name' or meaning of data.  */

 char magic[4] ;      /*!< MUST be "ni1\0" or "n+1\0". */

};                   /**** 348 bytes total ****/

typedef struct nifti_1_header nifti_1_header;





/*

    NIfTI-2 Header ~~~ NOT YET DONE ~~~

*/
/* hopefully cross-platform solution to byte padding added by some compilers */
#pragma pack(push)
#pragma pack(1)

                         /***************************/ /**********************/ /************/
struct nifti_2_header {  /* NIFTI-2 usage           */ /* NIFTI-1 usage      */ /*  offset  */
                         /***************************/ /**********************/ /************/
   int   sizeof_hdr;     /*!< MUST be 540           */ /* int sizeof_hdr; (348) */   /*   0 */
   char  magic[8] ;      /*!< MUST be valid signature. */  /* char magic[4];    */   /*   4 */
   int16_t datatype;     /*!< Defines data type!    */ /* short datatype;       */   /*  12 */
   int16_t bitpix;       /*!< Number bits/voxel.    */ /* short bitpix;         */   /*  14 */
   int64_t dim[8];       /*!< Data array dimensions.*/ /* short dim[8];         */   /*  16 */
   double intent_p1 ;    /*!< 1st intent parameter. */ /* float intent_p1;      */   /*  80 */
   double intent_p2 ;    /*!< 2nd intent parameter. */ /* float intent_p2;      */   /*  88 */
   double intent_p3 ;    /*!< 3rd intent parameter. */ /* float intent_p3;      */   /*  96 */
   double pixdim[8];     /*!< Grid spacings.        */ /* float pixdim[8];      */   /* 104 */
   int64_t vox_offset;   /*!< Offset into .nii file */ /* float vox_offset;     */   /* 168 */
   double scl_slope ;    /*!< Data scaling: slope.  */ /* float scl_slope;      */   /* 176 */
   double scl_inter ;    /*!< Data scaling: offset. */ /* float scl_inter;      */   /* 184 */
   double cal_max;       /*!< Max display intensity */ /* float cal_max;        */   /* 192 */
   double cal_min;       /*!< Min display intensity */ /* float cal_min;        */   /* 200 */
   double slice_duration;/*!< Time for 1 slice.     */ /* float slice_duration; */   /* 208 */
   double toffset;       /*!< Time axis shift.      */ /* float toffset;        */   /* 216 */
   int64_t slice_start;  /*!< First slice index.    */ /* short slice_start;    */   /* 224 */
   int64_t slice_end;    /*!< Last slice index.     */ /* short slice_end;      */   /* 232 */
   char  descrip[80];    /*!< any text you like.    */ /* char descrip[80];     */   /* 240 */
   char  aux_file[24];   /*!< auxiliary filename.   */ /* char aux_file[24];    */   /* 320 */
   int qform_code ;      /*!< NIFTI_XFORM_* code.   */ /* short qform_code;     */   /* 344 */
   int sform_code ;      /*!< NIFTI_XFORM_* code.   */ /* short sform_code;     */   /* 348 */
   double quatern_b ;    /*!< Quaternion b param.   */ /* float quatern_b;      */   /* 352 */
   double quatern_c ;    /*!< Quaternion c param.   */ /* float quatern_c;      */   /* 360 */
   double quatern_d ;    /*!< Quaternion d param.   */ /* float quatern_d;      */   /* 368 */
   double qoffset_x ;    /*!< Quaternion x shift.   */ /* float qoffset_x;      */   /* 376 */
   double qoffset_y ;    /*!< Quaternion y shift.   */ /* float qoffset_y;      */   /* 384 */
   double qoffset_z ;    /*!< Quaternion z shift.   */ /* float qoffset_z;      */   /* 392 */
   double srow_x[4] ;    /*!< 1st row affine transform. */  /* float srow_x[4]; */   /* 400 */
   double srow_y[4] ;    /*!< 2nd row affine transform. */  /* float srow_y[4]; */   /* 432 */
   double srow_z[4] ;    /*!< 3rd row affine transform. */  /* float srow_z[4]; */   /* 464 */
   int slice_code ;      /*!< Slice timing order.   */ /* char slice_code;      */   /* 496 */
   int xyzt_units ;      /*!< Units of pixdim[1..4] */ /* char xyzt_units;      */   /* 500 */
   int intent_code ;     /*!< NIFTI_INTENT_* code.  */ /* short intent_code;    */   /* 504 */
   char intent_name[16]; /*!< 'name' or meaning of data. */ /* char intent_name[16]; */  /* 508 */
   char dim_info;        /*!< MRI slice ordering.   */      /* char dim_info;        */  /* 524 */
   char unused_str[15];  /*!< unused, filled with \0 */                                  /* 525 */
} ;                   /**** 540 bytes total ****/
typedef struct nifti_2_header nifti_2_header ;

/* restore packing behavior */
#pragma pack(pop)





/*---------------------------------------------------------------------------*/
/* HEADER EXTENSIONS:
   -----------------
   After the end of the 348 byte header (e.g., after the magic field),
   the next 4 bytes are a char array field named "extension". By default,
   all 4 bytes of this array should be set to zero. In a .nii file, these
   4 bytes will always be present, since the earliest start point for
   the image data is byte #352. In a separate .hdr file, these bytes may
   or may not be present. If not present (i.e., if the length of the .hdr
   file is 348 bytes), then a NIfTI-1 compliant program should use the
   default value of extension={0,0,0,0}. The first byte (extension[0])
   is the only value of this array that is specified at present. The other
   3 bytes are reserved for future use.

   If extension[0] is nonzero, it indicates that extended header information
   is present in the bytes following the extension array. In a .nii file,
   this extended header data is before the image data (and vox_offset
   must be set correctly to allow for this). In a .hdr file, this extended
   data follows extension and proceeds (potentially) to the end of the file.

   The format of extended header data is weakly specified. Each extension
   must be an integer multiple of 16 bytes long. The first 8 bytes of each
   extension comprise 2 integers:
      int esize , ecode ;
   These values may need to be byte-swapped, as indicated by dim[0] for
   the rest of the header.
     * esize is the number of bytes that form the extended header data
       + esize must be a positive integral multiple of 16
       + this length includes the 8 bytes of esize and ecode themselves
     * ecode is a non-negative integer that indicates the format of the
       extended header data that follows
       + different ecode values are assigned to different developer groups
       + at present, the "registered" values for code are
         = 0 = unknown private format (not recommended!)
         = 2 = DICOM format (i.e., attribute tags and values)
         = 4 = AFNI group (i.e., ASCII XML-ish elements)
   In the interests of interoperability (a primary rationale for NIfTI),
   groups developing software that uses this extension mechanism are
   encouraged to document and publicize the format of their extensions.
   To this end, the NIfTI DFWG will assign even numbered codes upon request
   to groups submitting at least rudimentary documentation for the format
   of their extension; at present, the contact is mailto:rwcox@nih.gov.
   The assigned codes and documentation will be posted on the NIfTI
   website. All odd values of ecode (and 0) will remain unassigned;
   at least, until the even ones are used up, when we get to 2,147,483,646.

   Note that the other contents of the extended header data section are
   totally unspecified by the NIfTI-1 standard. In particular, if binary
   data is stored in such a section, its byte order is not necessarily
   the same as that given by examining dim[0]; it is incumbent on the
   programs dealing with such data to determine the byte order of binary
   extended header data.

   Multiple extended header sections are allowed, each starting with an
   esize,ecode value pair. The first esize value, as described above,
   is at bytes #352-355 in the .hdr or .nii file (files start at byte #0).
   If this value is positive, then the second (esize2) will be found
   starting at byte #352+esize1 , the third (esize3) at byte #352+esize1+esize2,
   et cetera.  Of course, in a .nii file, the value of vox_offset must
   be compatible with these extensions. If a malformed file indicates
   that an extended header data section would run past vox_offset, then
   the entire extended header section should be ignored. In a .hdr file,
   if an extended header data section would run past the end-of-file,
   that extended header data should also be ignored.

   With the above scheme, a program can successively examine the esize
   and ecode values, and skip over each extended header section if the
   program doesn't know how to interpret the data within. Of course, any
   program can simply ignore all extended header sections simply by jumping
   straight to the image data using vox_offset.
-----------------------------------------------------------------------------*/

/*! \struct nifti1_extender
    \brief This structure represents a 4-byte string that should follow the
           binary nifti_1_header data in a NIFTI-1 header file.  If the char
           values are {1,0,0,0}, the file is expected to contain extensions,
           values of {0,0,0,0} imply the file does not contain extensions.
           Other sequences of values are not currently defined.
 */
struct nifti1_extender { char extension[4] ; } ;
typedef struct nifti1_extender nifti1_extender ;

/*! \struct nifti1_extension
    \brief Data structure defining the fields of a header extension.
 */
struct nifti1_extension {
   int    esize ; /*!< size of extension, in bytes (must be multiple of 16) */
   int    ecode ; /*!< extension code, one of the NIFTI_ECODE_ values       */
   char * edata ; /*!< raw data, with no byte swapping (length is esize-8)  */
} ;
typedef struct nifti1_extension nifti1_extension ;


// ---- definitions to identify the header


#define F_NIFTI1                 348
#define F_NIFTI1_SWAP     1543569408
#define F_NIFTI2                 540
#define F_NIFTI2_SWAP      469893120


// ---- basic file info

struct nii_info {
    int    hlen   ;   // ---> length of the header
    char  *hdata  ;   // ---> header data as a char stream
    long   dstart ;   // ---> start of data
    long   dlen   ;   // ---> length of data
    int    dtype  ;   // ---> type of data
    int    mstart ;   // ---> start of metadata
    int    mlen   ;   // ---> length of metadata
    char  *mdata  ;   // ---> metadata as stream
    int    dim[8] ;   // ---> image dimensions
};
typedef struct nii_info nii_info;

// ---- voxelinfo

typedef struct {
    int    type;           /* should match the NIFTI_TYPE_ #define */
    int    nbyper;         /* bytes per value, matches nifti_image */
    int    swapsize;       /* bytes per swap piece, matches nifti_image */
    char * name;           /* text string to match #define */
} nifti_type_ele;



// ----- swap functions

void  swap_nifti_1_header (struct nifti_1_header *h);
void  swap_nifti_2_header (struct nifti_2_header *h);

void  nifti_swap_2bytes (size_t n, void *ar);
void  nifti_swap_4bytes (size_t n, void *ar);
void  nifti_swap_8bytes (size_t n, void *ar);
void  nifti_swap_16bytes(size_t n, void *ar);
void  nifti_swap_Nbytes (size_t n, int siz, void *ar);

// ----- check functions

int nifti_is_gzfile(const char* fname);
int fileext_compare(const char *test_ext, const char *known_ext);
nifti_type_ele * nifti_datatype_to_ele(int dtype);


// ----- read functions

int read_nifti1_hdr(struct nii_info *ninfo, znzFile filestream, int swapit);
int read_nifti2_hdr(struct nii_info *ninfo, znzFile filestream, int swapit);



#undef DT_UNKNOWN  /* defined in dirent.h on some Unix systems */

/*! \defgroup NIFTI1_DATATYPES
    \brief nifti1 datatype codes
    @{
 */
                            /*--- the original ANALYZE 7.5 type codes ---*/
#define DT_NONE                    0
#define DT_UNKNOWN                 0     /* what it says, dude           */
#define DT_BINARY                  1     /* binary (1 bit/voxel)         */
#define DT_UNSIGNED_CHAR           2     /* unsigned char (8 bits/voxel) */
#define DT_SIGNED_SHORT            4     /* signed short (16 bits/voxel) */
#define DT_SIGNED_INT              8     /* signed int (32 bits/voxel)   */
#define DT_FLOAT                  16     /* float (32 bits/voxel)        */
#define DT_COMPLEX                32     /* complex (64 bits/voxel)      */
#define DT_DOUBLE                 64     /* double (64 bits/voxel)       */
#define DT_RGB                   128     /* RGB triple (24 bits/voxel)   */
#define DT_ALL                   255     /* not very useful (?)          */

                            /*----- another set of names for the same ---*/
#define DT_UINT8                   2
#define DT_INT16                   4
#define DT_INT32                   8
#define DT_FLOAT32                16
#define DT_COMPLEX64              32
#define DT_FLOAT64                64
#define DT_RGB24                 128

                            /*------------------- new codes for NIFTI ---*/
#define DT_INT8                  256     /* signed char (8 bits)         */
#define DT_UINT16                512     /* unsigned short (16 bits)     */
#define DT_UINT32                768     /* unsigned int (32 bits)       */
#define DT_INT64                1024     /* long long (64 bits)          */
#define DT_UINT64               1280     /* unsigned long long (64 bits) */
#define DT_FLOAT128             1536     /* long double (128 bits)       */
#define DT_COMPLEX128           1792     /* double pair (128 bits)       */
#define DT_COMPLEX256           2048     /* long double pair (256 bits)  */
#define DT_RGBA32               2304     /* 4 byte RGBA (32 bits/voxel)  */
/* @} */


                            /*------- aliases for all the above codes ---*/

/*! \defgroup NIFTI1_DATATYPE_ALIASES
    \brief aliases for the nifti1 datatype codes
    @{
 */

#define NIFTI_TYPE_UINT8           2    /*! unsigned char. */
#define NIFTI_TYPE_INT16           4    /*! signed short. */
#define NIFTI_TYPE_INT32           8    /*! signed int. */
#define NIFTI_TYPE_FLOAT32        16    /*! 32 bit float. */
#define NIFTI_TYPE_COMPLEX64      32    /*! 64 bit complex = 2 32 bit floats. */
#define NIFTI_TYPE_FLOAT64        64    /*! 64 bit float = double. */
#define NIFTI_TYPE_RGB24         128    /*! 3 8 bit bytes. */
#define NIFTI_TYPE_INT8          256    /*! signed char. */
#define NIFTI_TYPE_UINT16        512    /*! unsigned short. */
#define NIFTI_TYPE_UINT32        768    /*! unsigned int. */
#define NIFTI_TYPE_INT64        1024    /*! signed long long. */
#define NIFTI_TYPE_UINT64       1280    /*! unsigned long long. */
#define NIFTI_TYPE_FLOAT128     1536    /*! 128 bit float = long double. */
#define NIFTI_TYPE_COMPLEX128   1792    /*! 128 bit complex = 2 64 bit floats. */
#define NIFTI_TYPE_COMPLEX256   2048    /*! 256 bit complex = 2 128 bit floats */
#define NIFTI_TYPE_RGBA32       2304    /*! 4 8 bit bytes. */
/* @} */


/*! \defgroup NIFTI1_SLICE_ORDER
    \brief nifti1 slice order codes, describing the acquisition order
           of the slices
    @{
 */
#define NIFTI_SLICE_UNKNOWN   0
#define NIFTI_SLICE_SEQ_INC   1
#define NIFTI_SLICE_SEQ_DEC   2
#define NIFTI_SLICE_ALT_INC   3
#define NIFTI_SLICE_ALT_DEC   4
#define NIFTI_SLICE_ALT_INC2  5  /* 05 May 2005: RWCox */
#define NIFTI_SLICE_ALT_DEC2  6  /* 05 May 2005: RWCox */
/* @} */

/*---------------------------------------------------------------------------*/
/* MISCELLANEOUS C MACROS
-----------------------------------------------------------------------------*/

/*.................*/
/*! Given a nifti_1_header struct, check if it has a good magic number.
    Returns NIFTI version number (1..9) if magic is good, 0 if it is not. */

#define NIFTI_VERSION(h)                               \
 ( ( (h).magic[0]=='n' && (h).magic[3]=='\0'    &&     \
     ( (h).magic[1]=='i' || (h).magic[1]=='+' ) &&     \
     ( (h).magic[2]>='1' && (h).magic[2]<='9' )   )    \
 ? (h).magic[2]-'0' : 0 )

/*.................*/
/*! Check if a nifti_1_header struct says if the data is stored in the
    same file or in a separate file.  Returns 1 if the data is in the same
    file as the header, 0 if it is not.                                   */

#define NIFTI_ONEFILE(h) ( (h).magic[1] == '+' )

/*.................*/
/*! Check if a nifti_1_header struct needs to be byte swapped.
    Returns 1 if it needs to be swapped, 0 if it does not.     */

#define NIFTI_NEEDS_SWAP(h) ( (h).dim[0] < 0 || (h).dim[0] > 7 )

/*.................*/
/*! Check if a nifti_1_header struct contains a 5th (vector) dimension.
    Returns size of 5th dimension if > 1, returns 0 otherwise.         */

#define NIFTI_5TH_DIM(h) ( ((h).dim[0]>4 && (h).dim[5]>1) ? (h).dim[5] : 0 )

/*****************************************************************************/

/*=================*/
#ifdef  __cplusplus
}
#endif
/*=================*/

#endif /* _NIFTI_HEADER_ */

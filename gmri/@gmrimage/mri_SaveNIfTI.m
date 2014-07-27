function [res] = mri_SaveNIfTI(img, filename, verbose)

%   function [res] = mri_SaveNIfTI(obj, filename, verbose)
%
%   Saves a NIfTI image based on the existing header information.
%
%   Required:
%     obj      - gmrimage object
%     filename - the filename to use
%
%   Grega Repovs - 2010-10-13
%   Grega Repovs - 2011-10-13 - Updated to write NIfTI-2
%   Grega Repovs - 2013-10-19 - Added call for embedding data
%   Grega Repovs - 2014-06-29 - Update to use MEX function
%

if nargin < 3, verbose = false; end

% ---> embedd extra data if available

if ~ismember(img.imageformat, {'CIFTI', 'CIFTI-1', 'CIFTI-2'}) && img.frames > 2
    img = img.mri_EmbedStats();
end

% ---> set up file to save

filename = strtrim(filename);
% unpack and set up

root = strrep(filename, '.hdr',      '');
root = strrep(root,     '.nii',      '');
root = strrep(root,     '.gz',       '');
root = strrep(root,     '.img',      '');
root = strrep(root,     '.dtseries', '');

img = img.unmaskimg;

% ---> save dimension information

switch img.imageformat
    case 'NIfTI'
        img.hdrnifti.dim(5) = img.frames;
        if img.frames > 1
            img.hdrnifti.dim(1) = 4;
        end
        file = [root '.nii'];

    case 'CIFTI-1'
        img.hdrnifti.dim(7) = img.frames;
        file = [root '.dtseries.nii'];

    case 'CIFTI-2'
        img.meta = framesHack(img.meta, img.hdrnifti.dim(6), img.frames);
        img.hdrnifti.dim(6) = img.frames;
        file = [root '.dtseries.nii'];

    otherwise
        file = filename;
end

% ---> flip before saving if needed

if ismember(img.imageformat, {'CIFTI', 'CIFTI-1', 'CIFTI-2'})
    img.data = single(img.data');
    % img.data = img.data';
end

% ---> setup datatype

switch class(img.data)
    case 'bitN'
        img.hdrnifti.datatype = 1;
        img.hdrnifti.bitpix = 8;
    case 'uchar'
        img.hdrnifti.datatype = 2;
        img.hdrnifti.bitpix = 8;
    case 'int16';
        img.hdrnifti.datatype = 4;
        img.hdrnifti.bitpix = 16;
    case 'int32'
        img.hdrnifti.datatype = 8;
        img.hdrnifti.bitpix = 32;
    case {'float32', 'single'};
        img.hdrnifti.datatype = 16;
        img.hdrnifti.bitpix = 32;
    case {'float64', 'double'};
        img.hdrnifti.datatype = 64;
        img.hdrnifti.bitpix = 64;
    case 'schar';
        img.hdrnifti.datatype = 256;
        img.hdrnifti.bitpix = 8;
    case 'uint16';
        img.hdrnifti.datatype = 512;
        img.hdrnifti.bitpix = 16;
    case 'uint32';
        img.hdrnifti.datatype = 768;
        img.hdrnifti.bitpix = 32;
    case 'int64';
        img.hdrnifti.datatype = 1024;
        img.hdrnifti.bitpix = 64;
    case 'uint64';
        img.hdrnifti.datatype = 1280;
        img.hdrnifti.bitpix = 64;
    otherwise
        error('Uknown datatype or datatype I can not handle!');
end

% ---> pack header

if img.hdrnifti.version == 1
    fhdr = packHeader_nifti1(img.hdrnifti);
elseif img.hdrnifti.version == 2
    fhdr = packHeader_nifti2(img.hdrnifti);
else
    error('ERROR: Unknown NIfTI version!');
end


% ---> save it

gmrimage.mri_SaveNIfTImx(filename, fhdr, img.data, img.meta, img.hdrnifti.swapped == 1, verbose);



% ----- Pack NIfTI-1 Header


function [s] = packHeader_nifti1(hdrnifti)

    if hdrnifti.swap
        sw = @(x, c) typecast(swapbytes(cast(x, c)), 'uint8');
    else
        sw = @(x, c) typecast(cast(x, c), 'uint8');
    end

    s = zeros(348, 1, 'uint8');

    s(1:4)     =   sw(348                     , 'int32');
    s(5:14)    =   sw(hdrnifti.data_type      , 'uint8');
    s(15:32)   =   sw(hdrnifti.db_name        , 'uint8');
    s(33:36)   =   sw(hdrnifti.extents        , 'int32');
    s(37:38)   =   sw(hdrnifti.session_error  , 'int16');
    s(39)      =   sw(hdrnifti.regular        , 'uint8');
    s(40)      =   sw(hdrnifti.dim_info       , 'uint8');
    s(41:56)   =   sw(hdrnifti.dim            , 'int16');
    s(57:60)   =   sw(hdrnifti.intent_p1      , 'single');
    s(61:64)   =   sw(hdrnifti.intent_p2      , 'single');
    s(65:68)   =   sw(hdrnifti.intent_p3      , 'single');
    s(69:70)   =   sw(hdrnifti.intent_code    , 'int16');
    s(71:72)   =   sw(hdrnifti.datatype       , 'int16');
    s(73:74)   =   sw(hdrnifti.bitpix         , 'int16');
    s(75:76)   =   sw(hdrnifti.slice_start    , 'int16');
    s(77:108)  =   sw(hdrnifti.pixdim         , 'single');
    s(109:112) =   sw(hdrnifti.vox_offset     , 'single');
    s(113:116) =   sw(hdrnifti.scl_slope      , 'single');
    s(117:120) =   sw(hdrnifti.scl_inter      , 'single');
    s(121:122) =   sw(hdrnifti.slice_end      , 'int16');
    s(123)     =   sw(hdrnifti.slice_code     , 'uint8');
    s(124)     =   sw(hdrnifti.xyzt_units     , 'uint8');
    s(125:128) =   sw(hdrnifti.cal_max        , 'single');
    s(129:132) =   sw(hdrnifti.cal_min        , 'single');
    s(133:136) =   sw(hdrnifti.slice_duration , 'single');
    s(137:140) =   sw(hdrnifti.toffset        , 'single');
    s(141:144) =   sw(hdrnifti.glmax          , 'int32');
    s(145:148) =   sw(hdrnifti.glmin          , 'int32');
    s(149:228) =   sw(hdrnifti.descrip        , 'uint8');
    s(229:252) =   sw(hdrnifti.aux_file       , 'uint8');
    s(253:254) =   sw(hdrnifti.qform_code     , 'int16');
    s(255:256) =   sw(hdrnifti.sform_code     , 'int16');
    s(257:260) =   sw(hdrnifti.quatern_b      , 'single');
    s(261:264) =   sw(hdrnifti.quatern_c      , 'single');
    s(265:268) =   sw(hdrnifti.quatern_d      , 'single');
    s(269:272) =   sw(hdrnifti.qoffset_x      , 'single');
    s(273:276) =   sw(hdrnifti.qoffset_y      , 'single');
    s(277:280) =   sw(hdrnifti.qoffset_z      , 'single');
    s(281:296) =   sw(hdrnifti.srow_x         , 'single');
    s(297:312) =   sw(hdrnifti.srow_y         , 'single');
    s(313:328) =   sw(hdrnifti.srow_z         , 'single');
    s(329:344) =   sw(hdrnifti.intent_name    , 'uint8');
    s(345:348) =   sw(hdrnifti.magic          , 'uint8');



% ----- Pack NIfTI-2 Header


function [s] = packHeader_nifti2(hdrnifti)

    if hdrnifti.swap
        sw = @(x, c) typecast(swapbytes(cast(x, c)), 'uint8');
    else
        sw = @(x, c) typecast(cast(x, c), 'uint8');
    end

    s = zeros(540, 1, 'uint8');

    s(1:4)     = sw(540,                     'int32');
    s(5:12)    = sw(hdrnifti.magic,          'uint8');
    s(13:14)   = sw(hdrnifti.datatype,       'int16');
    s(15:16)   = sw(hdrnifti.bitpix,         'int16');
    s(17:80)   = sw(hdrnifti.dim,            'int64');
    s(81:88)   = sw(hdrnifti.intent_p1,      'double');
    s(89:96)   = sw(hdrnifti.intent_p2,      'double');
    s(97:104)  = sw(hdrnifti.intent_p3,      'double');
    s(105:168) = sw(hdrnifti.pixdim,         'double');
    s(169:176) = sw(hdrnifti.vox_offset,     'int64');
    s(177:184) = sw(hdrnifti.scl_slope,      'double');
    s(185:192) = sw(hdrnifti.scl_inter,      'double');
    s(193:200) = sw(hdrnifti.cal_max,        'double');
    s(201:208) = sw(hdrnifti.cal_min,        'double');
    s(209:216) = sw(hdrnifti.slice_duration, 'double');
    s(217:224) = sw(hdrnifti.toffset,        'double');
    s(225:232) = sw(hdrnifti.slice_start,    'int64');
    s(233:240) = sw(hdrnifti.slice_end,      'int64');
    s(241:320) = sw(hdrnifti.descrip,        'uint8');
    s(321:344) = sw(hdrnifti.aux_file,       'uint8');
    s(345:348) = sw(hdrnifti.qform_code,     'int32');
    s(349:352) = sw(hdrnifti.sform_code,     'int32');
    s(353:360) = sw(hdrnifti.quatern_b,      'double');
    s(361:368) = sw(hdrnifti.quatern_c,      'double');
    s(369:376) = sw(hdrnifti.quatern_d,      'double');
    s(377:384) = sw(hdrnifti.qoffset_x,      'double');
    s(385:392) = sw(hdrnifti.qoffset_y,      'double');
    s(393:400) = sw(hdrnifti.qoffset_z,      'double');
    s(401:432) = sw(hdrnifti.srow_x,         'double');
    s(433:464) = sw(hdrnifti.srow_y,         'double');
    s(465:496) = sw(hdrnifti.srow_z,         'double');
    s(497:500) = sw(hdrnifti.slice_code,     'int32');
    s(501:504) = sw(hdrnifti.xyzt_units,     'int32');
    s(505:508) = sw(hdrnifti.intent_code,    'int32');
    s(509:524) = sw(hdrnifti.intent_name,    'uint8');
    s(525)     = sw(hdrnifti.dim_info,       'uint8');
    s(526:540) = sw(hdrnifti.unused_str,     'uint8');





function [meta] = framesHack(meta, oframes, nframes);

    if oframes == nframes
        return
    end

    s = cast(meta', 'char');
    olds = sprintf('SeriesPoints="%d"', oframes);
    news = sprintf('SeriesPoints="%d"', nframes);
    dlen = length(olds)-length(news);
    if dlen > 0
        news = [news repmat(' ', 1, dlen)];
    end
    sstart = strfind(s, olds);
    s(sstart:sstart+length(news)-1) = news;
    meta = cast(s', 'uint8');


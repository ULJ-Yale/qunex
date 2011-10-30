function [res] = mri_SaveNIfTI(img, filename, compressed)

%   function [res] = mri_SaveNIfTI(obj, filename, extra)
%
%   Saves a NIfTI image based on the existing header information.
%
%   Required:
%     obj      - gmrimage object
%     filename - the filename to use
%
%   Grega Repovs - 2010-10-13
%   Grega Repovs - 2011-10-13 - updated to write NIfTI-2
%

if nargin < 3
    compressed = [];
end

if isempty(compressed)
    compressed = img.hdrnifti.compressed;
end

% unpack and set up

img = img.unmaskimg;
img.hdrnifti.dim(5) = img.frames;
if img.frames > 1
	img.hdrnifti.dim(1) = 4;
end

root = strrep(filename, '.hdr', '');
root = strrep(root, '.nii', '');
root = strrep(root, '.gz', '');
root = strrep(root, '.img', '');

file = [root '.nii'];


% get datatype

switch img.hdrnifti.datatype
    case 1 
        datatype = 'bitN';
    case 2
        datatype = 'uchar';
        img.hdrnifti.bitpix = 8;
    case 4
        datatype = 'int16';
        img.hdrnifti.bitpix = 16;
    case 8
        datatype = 'int32'
        img.hdrnifti.bitpix = 32;
    case 16
        datatype = 'float32';
        img.hdrnifti.bitpix = 32;
    case 64
        datetype = 'float64';
        img.hdrnifti.bitpix = 64;
    case 256
        datatype = 'schar';
    case 512
        datatype = 'uint16';
        img.hdrnifti.bitpix = 16;
    case 768
        datatype = 'uint32';
        img.hdrnifti.bitpix = 32;
    case 1024
        datatype = 'int64';
        img.hdrnifti.bitpix = 64;
    case 1280
        datatype = 'uint64';
        img.hdrnifti.bitpix = 64;
    case 1280
        datatype = 'uint64';   
        img.hdrnifti.bitpix = 64;
    otherwise
        error('Uknown datatype or datatype I can not handle!');
end    




% save it

fid = fopen(file, 'w', img.mformat);

% ---> Write NIfTI-1

if img.hdrnifti.version == 1
    fwrite(fid, 348, 'int32');
    fwrite(fid, img.hdrnifti.data_type, 'char');
    fwrite(fid, img.hdrnifti.db_name, 'char');
    fwrite(fid, img.hdrnifti.extents, 'int32');
    fwrite(fid, img.hdrnifti.session_error, 'int16');
    fwrite(fid, img.hdrnifti.regular, 'char');
    fwrite(fid, img.hdrnifti.dim_info, 'char');
    fwrite(fid, img.hdrnifti.dim, 'int16');
    fwrite(fid, img.hdrnifti.intent_p1, 'float32');
    fwrite(fid, img.hdrnifti.intent_p2, 'float32');
    fwrite(fid, img.hdrnifti.intent_p3, 'float32');
    fwrite(fid, img.hdrnifti.intent_code, 'int16');
    fwrite(fid, img.hdrnifti.datatype, 'int16');
    fwrite(fid, img.hdrnifti.bitpix, 'int16');
    fwrite(fid, img.hdrnifti.slice_start, 'int16');
    fwrite(fid, img.hdrnifti.pixdim, 'float32');
    fwrite(fid, 352, 'float32');  % img.hdr.vox_offset
    fwrite(fid, img.hdrnifti.scl_slope, 'float32');
    fwrite(fid, img.hdrnifti.scl_inter, 'float32');
    fwrite(fid, img.hdrnifti.slice_end, 'int16');
    fwrite(fid, img.hdrnifti.slice_code, 'char');
    fwrite(fid, img.hdrnifti.xyzt_units, 'char');
    fwrite(fid, img.hdrnifti.cal_max, 'float32');
    fwrite(fid, img.hdrnifti.cal_min, 'float32');
    fwrite(fid, img.hdrnifti.slice_duration, 'float32');
    fwrite(fid, img.hdrnifti.toffset, 'float32');
    fwrite(fid, img.hdrnifti.glmax, 'int32');
    fwrite(fid, img.hdrnifti.glmin, 'int32');
    fwrite(fid, img.hdrnifti.descrip, 'char');
    fwrite(fid, img.hdrnifti.aux_file, 'char');
    fwrite(fid, img.hdrnifti.qform_code, 'int16');
    fwrite(fid, img.hdrnifti.sform_code, 'int16');
    fwrite(fid, img.hdrnifti.quatern_b, 'float32');
    fwrite(fid, img.hdrnifti.quatern_c, 'float32');
    fwrite(fid, img.hdrnifti.quatern_d, 'float32');
    fwrite(fid, img.hdrnifti.qoffset_x, 'float32');
    fwrite(fid, img.hdrnifti.qoffset_y, 'float32');
    fwrite(fid, img.hdrnifti.qoffset_z, 'float32');
    fwrite(fid, img.hdrnifti.srow_x, 'float32');
    fwrite(fid, img.hdrnifti.srow_y, 'float32');
    fwrite(fid, img.hdrnifti.srow_z, 'float32');
    fwrite(fid, img.hdrnifti.intent_name, 'char');
    fwrite(fid, img.hdrnifti.magic, 'char');
    fwrite(fid, 'repi', 'char');
end
    
% ---> Write NIfTI-2 
    
if img.hdrnifti.version == 2
    fwrite(fid, 540, 'int32');
    
    img.hdrnifti.magic = [img.hdrnifti.magic '        '];
    fwrite(fid, img.hdrnifti.magic(1:8),    'char');
    fwrite(fid, img.hdrnifti.datatype,      'int16');
    fwrite(fid, img.hdrnifti.bitpix,        'int16');
    fwrite(fid, img.hdrnifti.dim,           'int64');
    fwrite(fid, img.hdrnifti.intent_p1,     'float64');
    fwrite(fid, img.hdrnifti.intent_p2,     'float64');
    fwrite(fid, img.hdrnifti.intent_p3,     'float64');
    fwrite(fid, img.hdrnifti.pixdim,        'float64');
    fwrite(fid, 540,                        'float64');  % img.hdr.vox_offset  --------> set
    fwrite(fid, img.hdrnifti.scl_slope,     'float64');
    fwrite(fid, img.hdrnifti.scl_inter,     'float64');
    fwrite(fid, img.hdrnifti.cal_max,       'float64');
    fwrite(fid, img.hdrnifti.cal_min,       'float64');
    fwrite(fid, img.hdrnifti.slice_duration,'float64');
    fwrite(fid, img.hdrnifti.toffset,       'float64');
    fwrite(fid, img.hdrnifti.slice_start,   'int64');
    fwrite(fid, img.hdrnifti.slice_end,     'int64');
    
    img.hdrnifti.descrip = [img.hdrnifti.descrip '                                                                                '];
    img.hdrnifti.aux_file = [img.hdrnifti.aux_file '                        '];
    fwrite(fid, img.hdrnifti.descrip(1:80), 'char');
    fwrite(fid, img.hdrnifti.aux_file(1:24),'char');
    fwrite(fid, img.hdrnifti.qform_code,    'int32');
    fwrite(fid, img.hdrnifti.sform_code,    'int32');
    fwrite(fid, img.hdrnifti.quatern_b,     'float64');
    fwrite(fid, img.hdrnifti.quatern_c,     'float64');
    fwrite(fid, img.hdrnifti.quatern_d,     'float64');
    fwrite(fid, img.hdrnifti.qoffset_x,     'float64');
    fwrite(fid, img.hdrnifti.qoffset_y,     'float64');
    fwrite(fid, img.hdrnifti.qoffset_z,     'float64');
    fwrite(fid, img.hdrnifti.srow_x,        'float64');
    fwrite(fid, img.hdrnifti.srow_y,        'float64');
    fwrite(fid, img.hdrnifti.srow_z,        'float64');
    fwrite(fid, img.hdrnifti.slice_code,    'int32');
    fwrite(fid, img.hdrnifti.xyzt_units,    'int32');
    fwrite(fid, img.hdrnifti.intent_code,   'int32');

    img.hdrnifti.intent_name = [img.hdrnifti.intent_name '                '];
    img.hdrnifti.unused_str  = [img.hdrnifti.unused_str '               '];
    fwrite(fid, img.hdrnifti.intent_name(1:16), 'char');
    fwrite(fid, img.hdrnifti.dim_info,          'char');
    fwrite(fid, img.hdrnifti.unused_str(1:15),  'char');
    
end    
    
    
% ---> Add data ... 

fwrite(fid, img.data, datatype);
fclose(fid);

if compressed 
    gzip(file);
    delete(file);
end


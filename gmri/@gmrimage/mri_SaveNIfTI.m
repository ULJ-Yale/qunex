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
%

if nargin < 3
    compressed = [];
end

if isempty(compressed)
    compressed = img.hdrnifti.compressed;
end

% unpack and set up

img = img.unmaskimg;

root = strrep(filename, '.hdr', '');
root = strrep(root, '.nii', '');
root = strrep(root, '.gz', '');
root = strrep(root, '.img', '');

file = [root '.nii'];

% save it

fid = fopen(file, 'w', img.mformat);

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

% get datatype

switch img.hdrnifti.datatype
    case 1 
        datatype = 'bitN';
    case 2
        datatype = 'uchar';
    case 4
        datatype = 'int16';
    case 8
        datatype = 'int32'
    case 16
        datatype = 'float32';
    case 64
        datetype = 'float64';
    case 256
        datatype = 'schar';
    case 512
        datatype = 'uint16';
    case 768
        datatype = 'uint32';
    case 1024
        datatype = 'int64';
    case 1280
        datatype = 'uint64';
    case 1280
        datatype = 'uint64';    
    otherwise
        error('Uknown datatype or datatype I can not handle!');
end    

fwrite(fid, img.data, datatype);
fclose(fid);

if compressed 
    gzip(file);
    delete(file);
end



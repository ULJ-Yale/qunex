function [ok] = g_SaveNIfTI(filename, img)

%   
%   Saves nifti files in all shapes and forms
%   
%   filename - file structure to be saved
%   img - image data to be saved
%   .data - raw image data
%   .hdr  - header info
%   


% create the full filename

file = strrep(filename, '.gz', '');
separate = false;
mformat = 'b';


% save it

fid = fopen(file, 'w', mformat);

fwrite(fid, 348, 'int32');
fwrite(fid, img.hdr.data_type, 'char');
fwrite(fid, img.hdr.db_name, 'char');
fwrite(fid, img.hdr.extents, 'int32');
fwrite(fid, img.hdr.session_error, 'int16');
fwrite(fid, img.hdr.regular, 'char');
fwrite(fid, img.hdr.dim_info, 'char');
fwrite(fid, img.hdr.dim, 'int16');
fwrite(fid, img.hdr.intent_p1, 'float32');
fwrite(fid, img.hdr.intent_p2, 'float32');
fwrite(fid, img.hdr.intent_p3, 'float32');
fwrite(fid, img.hdr.intent_code, 'int16');
fwrite(fid, img.hdr.datatype, 'int16');
fwrite(fid, img.hdr.bitpix, 'int16');
fwrite(fid, img.hdr.slice_start, 'int16');
fwrite(fid, img.hdr.pixdim, 'float32');
fwrite(fid, 352, 'float32');  % img.hdr.vox_offset
fwrite(fid, img.hdr.scl_slope, 'float32');
fwrite(fid, img.hdr.scl_inter, 'float32');
fwrite(fid, img.hdr.slice_end, 'int16');
fwrite(fid, img.hdr.slice_code, 'char');
fwrite(fid, img.hdr.xyzt_units, 'char');
fwrite(fid, img.hdr.cal_max, 'float32');
fwrite(fid, img.hdr.cal_min, 'float32');
fwrite(fid, img.hdr.slice_duration, 'float32');
fwrite(fid, img.hdr.toffset, 'float32');
fwrite(fid, img.hdr.glmax, 'int32');
fwrite(fid, img.hdr.glmin, 'int32');
fwrite(fid, img.hdr.descrip, 'char');
fwrite(fid, img.hdr.aux_file, 'char');
fwrite(fid, img.hdr.qform_code, 'int16');
fwrite(fid, img.hdr.sform_code, 'int16');
fwrite(fid, img.hdr.quatern_b, 'float32');
fwrite(fid, img.hdr.quatern_c, 'float32');
fwrite(fid, img.hdr.quatern_d, 'float32');
fwrite(fid, img.hdr.qoffset_x, 'float32');
fwrite(fid, img.hdr.qoffset_y, 'float32');
fwrite(fid, img.hdr.qoffset_z, 'float32');
fwrite(fid, img.hdr.srow_x, 'float32');
fwrite(fid, img.hdr.srow_y, 'float32');
fwrite(fid, img.hdr.srow_z, 'float32');
fwrite(fid, img.hdr.intent_name, 'char');
fwrite(fid, img.hdr.magic, 'char');
fwrite(fid, 'repi', 'char');

% get datatype

switch img.hdr.datatype
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

gzip(file);
delete(file);





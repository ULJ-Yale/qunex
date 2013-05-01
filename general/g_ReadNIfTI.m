function [img] = g_ReadNIfTI(filename)

%   
%   Read nifti files in all shapes and forms
%   
%   filename - file to be read
%   img - output structure
%   .data - raw image data
%   .hdr  - header info
%   

% get the full filename

file = filename;
separate = false;
mformat = 'b';

% check what type it is

gunzipped = false;
if file(length(file)-2:end) == '.gz'
    gunzipped = true;
    filenames = gunzip(file, 'tmp_mat_gunzip');
    file = filenames{1};
end

% check for endianess

fid = fopen(file, 'r', mformat);
img.hdr.sizeof_hdr = fread(fid, 1, 'int32');
if img.hdr.sizeof_hdr ~= 348
    mformat = 'l';
    fclose(fid);
    fid = fopen(file, 'r', mformat);
    img.hdr.sizeof_hdr = fread(fid, 1, 'int32');
end

% read header fields

img.hdr.data_type = fread(fid, 10, '*char')';
img.hdr.db_name = fread(fid, 18, '*char')';
img.hdr.extents = fread(fid, 1, 'int32');
img.hdr.session_error = fread(fid, 1, 'int16');
img.hdr.regular = fread(fid, 1, '*char');
img.hdr.dim_info = fread(fid, 1, '*char');
img.hdr.dim = fread(fid, 8, 'int16');
img.hdr.intent_p1 = fread(fid, 1, 'float32');
img.hdr.intent_p2 = fread(fid, 1, 'float32');
img.hdr.intent_p3 = fread(fid, 1, 'float32');
img.hdr.intent_code = fread(fid, 1, 'int16');
img.hdr.datatype = fread(fid, 1, 'int16');
img.hdr.bitpix = fread(fid, 1, 'int16');
img.hdr.slice_start = fread(fid, 1, 'int16');
img.hdr.pixdim = fread(fid, 8, 'float32');
img.hdr.vox_offset = fread(fid, 1, 'float32');
img.hdr.scl_slope = fread(fid, 1, 'float32');
img.hdr.scl_inter = fread(fid, 1, 'float32');
img.hdr.slice_end = fread(fid, 1, 'int16');
img.hdr.slice_code = fread(fid, 1, '*char');
img.hdr.xyzt_units = fread(fid, 1, '*char');
img.hdr.cal_max = fread(fid, 1, 'float32');
img.hdr.cal_min = fread(fid, 1, 'float32');
img.hdr.slice_duration = fread(fid, 1, 'float32');
img.hdr.toffset = fread(fid, 1, 'float32');
img.hdr.glmax = fread(fid, 1, 'int32');
img.hdr.glmin = fread(fid, 1, 'int32');
img.hdr.descrip = fread(fid, 80, '*char')';
img.hdr.aux_file = fread(fid, 24, '*char')';
img.hdr.qform_code = fread(fid, 1, 'int16');
img.hdr.sform_code = fread(fid, 1, 'int16');
img.hdr.quatern_b = fread(fid, 1, 'float32');
img.hdr.quatern_c = fread(fid, 1, 'float32');
img.hdr.quatern_d = fread(fid, 1, 'float32');
img.hdr.qoffset_x = fread(fid, 1, 'float32');
img.hdr.qoffset_y = fread(fid, 1, 'float32');
img.hdr.qoffset_z = fread(fid, 1, 'float32');
img.hdr.srow_x = fread(fid, 4, 'float32');
img.hdr.srow_y = fread(fid, 4, 'float32');
img.hdr.srow_z = fread(fid, 4, 'float32');
img.hdr.intent_name = fread(fid, 16, '*char')';
img.hdr.magic = fread(fid, 4, '*char')';

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

fclose(fid);

% read the data

if img.hdr.magic(1:3) == 'n+1'
    fid = fopen(file, 'r', mformat);
    garbage = fread(fid, img.hdr.vox_offset, 'char');
    img.data = fread(fid, prod(img.hdr.dim(2:7)), datatype);
    fclose(fid);
else
    imgfile = strrep(file, '.hdr', '.img');
    fid = fopen(imgfile, 'r', mformat);
    img.data = fread(fid, prod(img.hdr.dim(2:7)), datatype);
    fclose(fid);
end

if gunzipped
    rmdir('tmp_mat_gunzip', 's');
end


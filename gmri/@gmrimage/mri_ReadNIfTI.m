function [img] = mri_ReadNIfTI(img, filename, dtype, frames)

%       function [img] = mri_ReadNIfTI(img, file, dtype, frames)
%
%		Reads in a NIfTI image into an image object
%
%       required:
%		    img       - mrimage object
%           filename  - filename (can be a .nii, .nii.gz or .hdr file)
%
%		optional:
%           dtype  - datatype to read into [single]
%           frames - number of frames to read [all]
%
%       Grega Repovs - 2010-10-13
%

if nargin < 4
	frames = [];
	if nargin < 3
	    dtype = 'single';
    end
end

if ~exist(filename)
    error('\n\nERROR: %s does not exist. Please check your paths!\n\n', filename);
end

% get the full filename

file       = filename;
separate   = false;
mformat    = 'b';
tempfolder = [];

% check what type it is

img.hdrnifti.compressed = false;

if file(length(file)-2:end) == '.gz'
    tempfolder  = ['tmp-' num2str(now)];
    filenames   = gunzip(file, tempfolder);
    file = filenames{1};
    img.hdrnifti.compressed = true;
end

% check for endianess

fid = fopen(file, 'r', mformat);
img.hdrnifti.sizeof_hdr = fread(fid, 1, 'int32');
if img.hdrnifti.sizeof_hdr ~= 348
    mformat = 'l';
    fclose(fid);
    fid = fopen(file, 'r', mformat);
    img.hdrnifti.sizeof_hdr = fread(fid, 1, 'int32');
end

% read header fields

img.hdrnifti.data_type       = fread(fid, 10, '*char')';
img.hdrnifti.db_name         = fread(fid, 18, '*char')';
img.hdrnifti.extents         = fread(fid, 1, 'int32');
img.hdrnifti.session_error   = fread(fid, 1, 'int16');
img.hdrnifti.regular         = fread(fid, 1, '*char');
img.hdrnifti.dim_info        = fread(fid, 1, '*char');
img.hdrnifti.dim             = fread(fid, 8, 'int16');
img.hdrnifti.intent_p1       = fread(fid, 1, 'float32');
img.hdrnifti.intent_p2       = fread(fid, 1, 'float32');
img.hdrnifti.intent_p3       = fread(fid, 1, 'float32');
img.hdrnifti.intent_code     = fread(fid, 1, 'int16');
img.hdrnifti.datatype        = fread(fid, 1, 'int16');
img.hdrnifti.bitpix          = fread(fid, 1, 'int16');
img.hdrnifti.slice_start     = fread(fid, 1, 'int16');
img.hdrnifti.pixdim          = fread(fid, 8, 'float32');
img.hdrnifti.vox_offset      = fread(fid, 1, 'float32');
img.hdrnifti.scl_slope       = fread(fid, 1, 'float32');
img.hdrnifti.scl_inter       = fread(fid, 1, 'float32');
img.hdrnifti.slice_end       = fread(fid, 1, 'int16');
img.hdrnifti.slice_code      = fread(fid, 1, '*char');
img.hdrnifti.xyzt_units      = fread(fid, 1, '*char');
img.hdrnifti.cal_max         = fread(fid, 1, 'float32');
img.hdrnifti.cal_min         = fread(fid, 1, 'float32');
img.hdrnifti.slice_duration  = fread(fid, 1, 'float32');
img.hdrnifti.toffset         = fread(fid, 1, 'float32');
img.hdrnifti.glmax           = fread(fid, 1, 'int32');
img.hdrnifti.glmin           = fread(fid, 1, 'int32');
img.hdrnifti.descrip         = fread(fid, 80, '*char')';
img.hdrnifti.aux_file        = fread(fid, 24, '*char')';
img.hdrnifti.qform_code      = fread(fid, 1, 'int16');
img.hdrnifti.sform_code      = fread(fid, 1, 'int16');
img.hdrnifti.quatern_b       = fread(fid, 1, 'float32');
img.hdrnifti.quatern_c       = fread(fid, 1, 'float32');
img.hdrnifti.quatern_d       = fread(fid, 1, 'float32');
img.hdrnifti.qoffset_x       = fread(fid, 1, 'float32');
img.hdrnifti.qoffset_y       = fread(fid, 1, 'float32');
img.hdrnifti.qoffset_z       = fread(fid, 1, 'float32');
img.hdrnifti.srow_x          = fread(fid, 4, 'float32');
img.hdrnifti.srow_y          = fread(fid, 4, 'float32');
img.hdrnifti.srow_z          = fread(fid, 4, 'float32');
img.hdrnifti.intent_name     = fread(fid, 16, '*char')';
img.hdrnifti.magic           = fread(fid, 4, '*char')';

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

fclose(fid);

% ------ Process header

% --- file root

root = strrep(filename, '.hdr', '');
root = strrep(root, '.nii', '');
root = strrep(root, '.gz', '');
root = strrep(root, '.img', '');

img.rootfilename = root;
img.filename     = [root '.4dfp.nii'];

% --- format and size details

img.imageformat = 'NIfTI';

img.TR = [];
img.frames = 1;
if img.hdrnifti.dim(1) == 4    % we probably have a BOLD (4D) file
    if frames
        img.hdrnifti.dim(5) = frames;
        img.frames = frames;
    else
        img.frames = img.hdrnifti.dim(5);
    end
    img.TR = img.hdrnifti.pixdim(5);
end

img.dim     = img.hdrnifti.dim(2:4);
img.voxels  = prod(img.dim);
img.vsizes  = img.hdrnifti.pixdim(2:4);
img.mformat = mformat;

% read the data

if img.hdrnifti.magic(1:3) == 'n+1'
    fid = fopen(file, 'r', mformat);
    garbage = fread(fid, img.hdrnifti.vox_offset, 'char');
    img.data = fread(fid, prod(img.hdrnifti.dim(2:7)), [datatype '=>' dtype]);
    fclose(fid);
else
    imgfile = strrep(file, '.hdr', '.img');
    fid = fopen(imgfile, 'r', mformat);
    img.data = fread(fid, prod(img.hdrnifti.dim(2:7)), [datatype '=>' dtype]);
    fclose(fid);
end

if tempfolder
    rmdir(tempfolder, 's');
end



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
%       Grega Repovs - 2011-10-13 - updated to read NIfTI-2
%

if nargin < 4
	frames = [];
	if nargin < 3
	    dtype = 'single';
    end
end

filename = strtrim(filename);

if ~exist(filename)
    error('\n\nERROR: %s does not exist. Please check your paths!\n\n', filename);
end

% get the full filename

file       = filename;
separate   = false;
mformat    = 'l';
tempfolder = [];

% check what type it is

img.hdrnifti.compressed = false;

if file(length(file)-2:end) == '.gz'
    tempfolder  = ['tmp-' num2str(now)];
    filenames   = gunzip(file, tempfolder);
    file = filenames{1};
    img.hdrnifti.compressed = true;
end

% check for endianess and nifti version

fid = fopen(file, 'r', mformat);
img.hdrnifti.sizeof_hdr = fread(fid, 1, 'int32');

switch img.hdrnifti.sizeof_hdr
    case 348
        img.hdrnifti = readHeader_nifti1(fid, img.hdrnifti);
    case 508
        img.hdrnifti = readHeader_nifti2(fid, img.hdrnifti);
    case 1543569408
        fclose(fid);
        mformat = 'b';
        fid = fopen(file, 'r', mformat);
        img.hdrnifti.sizeof_hdr = fread(fid, 1, 'int32');
        img.hdrnifti = readHeader_nifti1(fid, img.hdrnifti);
    case -67043328 
        fclose(fid);
        mformat = 'b';
        fid = fopen(file, 'r', mformat);
        img.hdrnifti.sizeof_hdr = fread(fid, 1, 'int32');
        img.hdrnifti = readHeader_nifti2(fid, img.hdrnifti);
    otherwise
        error('ERROR: %s does not have a valid NIfTI-1 or -2 header!');
end


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
img.filename     = [root '.nii'];

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

img.dim     = img.hdrnifti.dim(2:4)';
img.voxels  = prod(img.dim);
img.vsizes  = img.hdrnifti.pixdim(2:4)';
img.mformat = mformat;
img.runframes = img.frames;

% read the data

if img.hdrnifti.magic(1:3) == 'n+1'
    fid = fopen(file, 'r', mformat);
    garbage = fread(fid, img.hdrnifti.vox_offset, 'char');
    toread = img.hdrnifti.dim(2:7);
    toread = prod(toread(toread>0));
    img.data = fread(fid, toread, [datatype '=>' dtype]);
    fclose(fid);
else
    imgfile = strrep(file, '.hdr', '.img');
    fid = fopen(imgfile, 'r', mformat);
    toread = img.hdrnifti.dim(2:7);
    toread = prod(toread(toread>0));
    img.data = fread(fid, toread, [datatype '=>' dtype]);
    fclose(fid);
end

if tempfolder
    rmdir(tempfolder, 's');
end


% ---- Adjust datatype

img.hdrnifti.datatype = 16; 

switch dtype
    case 'single'
        img.hdrnifti.datatype = 16;     % --- float32
    case 'double'
        img.hdrnifti.datatype = 64;     % --- float64
end



% ----- Read NIfTI-1 Header


function [hdrnifti] = readHeader_nifti1(fid, hdrnifti)

    hdrnifti.data_type       = fread(fid, 10, '*char')';
    hdrnifti.db_name         = fread(fid, 18, '*char')';
    hdrnifti.extents         = fread(fid, 1, 'int32');
    hdrnifti.session_error   = fread(fid, 1, 'int16');
    hdrnifti.regular         = fread(fid, 1, '*char');
    hdrnifti.dim_info        = fread(fid, 1, '*char');
    hdrnifti.dim             = fread(fid, 8, 'int16');
    hdrnifti.intent_p1       = fread(fid, 1, 'float32');
    hdrnifti.intent_p2       = fread(fid, 1, 'float32');
    hdrnifti.intent_p3       = fread(fid, 1, 'float32');
    hdrnifti.intent_code     = fread(fid, 1, 'int16');
    hdrnifti.datatype        = fread(fid, 1, 'int16');
    hdrnifti.bitpix          = fread(fid, 1, 'int16');
    hdrnifti.slice_start     = fread(fid, 1, 'int16');
    hdrnifti.pixdim          = fread(fid, 8, 'float32');
    hdrnifti.vox_offset      = fread(fid, 1, 'float32');
    hdrnifti.scl_slope       = fread(fid, 1, 'float32');
    hdrnifti.scl_inter       = fread(fid, 1, 'float32');
    hdrnifti.slice_end       = fread(fid, 1, 'int16');
    hdrnifti.slice_code      = fread(fid, 1, '*char');
    hdrnifti.xyzt_units      = fread(fid, 1, '*char');
    hdrnifti.cal_max         = fread(fid, 1, 'float32');
    hdrnifti.cal_min         = fread(fid, 1, 'float32');
    hdrnifti.slice_duration  = fread(fid, 1, 'float32');
    hdrnifti.toffset         = fread(fid, 1, 'float32');
    hdrnifti.glmax           = fread(fid, 1, 'int32');
    hdrnifti.glmin           = fread(fid, 1, 'int32');
    hdrnifti.descrip         = fread(fid, 80, '*char')';
    hdrnifti.aux_file        = fread(fid, 24, '*char')';
    hdrnifti.qform_code      = fread(fid, 1, 'int16');
    hdrnifti.sform_code      = fread(fid, 1, 'int16');
    hdrnifti.quatern_b       = fread(fid, 1, 'float32');
    hdrnifti.quatern_c       = fread(fid, 1, 'float32');
    hdrnifti.quatern_d       = fread(fid, 1, 'float32');
    hdrnifti.qoffset_x       = fread(fid, 1, 'float32');
    hdrnifti.qoffset_y       = fread(fid, 1, 'float32');
    hdrnifti.qoffset_z       = fread(fid, 1, 'float32');
    hdrnifti.srow_x          = fread(fid, 4, 'float32');
    hdrnifti.srow_y          = fread(fid, 4, 'float32');
    hdrnifti.srow_z          = fread(fid, 4, 'float32');
    hdrnifti.intent_name     = fread(fid, 16, '*char')';
    hdrnifti.magic           = fread(fid, 4, '*char')';
    hdrnifti.version         = 1;


    % ----- Read NIfTI-1 Header


function [hdrnifti] = readHeader_nifti2(fid, hdrnifti)

    hdrnifti.magic           = fread(fid, 8, '*char')';
    hdrnifti.datatype        = fread(fid, 1, 'int16');
    hdrnifti.bitpix          = fread(fid, 1, 'int16');
    hdrnifti.dim             = fread(fid, 8, 'int64');
    hdrnifti.intent_p1       = fread(fid, 1, 'float64');
    hdrnifti.intent_p2       = fread(fid, 1, 'float64');
    hdrnifti.intent_p3       = fread(fid, 1, 'float64');
    hdrnifti.pixdim          = fread(fid, 8, 'float64');
    hdrnifti.vox_offset      = fread(fid, 1, 'int64');
    hdrnifti.scl_slope       = fread(fid, 1, 'float64');
    hdrnifti.scl_inter       = fread(fid, 1, 'float64');
    hdrnifti.cal_max         = fread(fid, 1, 'float64');
    hdrnifti.cal_min         = fread(fid, 1, 'float64');
    hdrnifti.slice_duration  = fread(fid, 1, 'float64');
    hdrnifti.toffset         = fread(fid, 1, 'float64');
    hdrnifti.slice_start     = fread(fid, 1, 'int64');
    hdrnifti.slice_end       = fread(fid, 1, 'int64');
    hdrnifti.descrip         = fread(fid, 80, '*char')';
    hdrnifti.aux_file        = fread(fid, 24, '*char')';
    hdrnifti.qform_code      = fread(fid, 1, 'int32');
    hdrnifti.sform_code      = fread(fid, 1, 'int32');
    hdrnifti.quatern_b       = fread(fid, 1, 'float64');
    hdrnifti.quatern_c       = fread(fid, 1, 'float64');
    hdrnifti.quatern_d       = fread(fid, 1, 'float64');
    hdrnifti.qoffset_x       = fread(fid, 1, 'float64');
    hdrnifti.qoffset_y       = fread(fid, 1, 'float64');
    hdrnifti.qoffset_z       = fread(fid, 1, 'float64');
    hdrnifti.srow_x          = fread(fid, 4, 'float64');
    hdrnifti.srow_y          = fread(fid, 4, 'float64');
    hdrnifti.srow_z          = fread(fid, 4, 'float64');
    hdrnifti.slice_code      = fread(fid, 1, 'int32');
    hdrnifti.xyzt_units      = fread(fid, 1, 'int32');
    hdrnifti.intent_code     = fread(fid, 1, 'int32');
    hdrnifti.intent_name     = fread(fid, 16, '*char')';
    hdrnifti.dim_info        = fread(fid, 1, '*char');
    hdrnifti.unused_str      = fread(fid, 15, '*char');
    hdrnifti.version         = 2;
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    





function [img] = mri_ReadNIfTI(img, filename, dtype, frames, verbose)

%function [img] = mri_ReadNIfTI(img, file, dtype, frames, verbose)
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
%       Grega Repovs - 2013-10-20 - added verbose option
%       Grega Repovs - 2014-05-04 - rewrite to support direct gunzipping
%       Grega Repovs - 2014-06-29 - rewrite to support mex reading
%

if nargin < 5 verbose = false;  end
if nargin < 4 frames = [];      end
if nargin < 3 dtype = [];       end

filename = strtrim(filename);

if isempty(dtype)
    dtype = 'single';
end

if ~exist(filename)
    error('\n\nERROR: %s does not exist. Please check your paths!\n\n', filename);
end

% --- read the file

[fhdr fdata fmeta fswap] = mri_ReadNIfTImx(filename, verbose);

img.hdrnifti.swap    = false;
img.hdrnifti.swapped = fswap;

% --- process header

switch numel(fhdr)
    case 348
        img.hdrnifti = readHeader_nifti1(fhdr, img.hdrnifti);
    case 540
        img.hdrnifti = readHeader_nifti2(fhdr, img.hdrnifti);
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
        datatype = 'single';
    case 64
        datetype = 'double';
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

% ------ Process header

% --- file root

if strfind(filename, 'dtseries')
    img.imageformat = 'CIFTI';
else
    img.imageformat = 'NIfTI';
end

root = strrep(filename, '.hdr', '');
root = strrep(root, '.nii', '');
root = strrep(root, '.gz', '');
root = strrep(root, '.img', '');
root = strrep(root, '.dtseries', '');

img.rootfilename = root;
img.filename     = [root '.nii'];

% --- format and size details

if strcmp(img.imageformat, 'NIfTI')
    img.TR = [];
    img.frames = 1;
    if img.hdrnifti.dim(1) == 4    % we probably have a BOLD (4D) file
        if ~isempty(frames)
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
    % img.mformat = mformat;
    img.runframes = img.frames;

elseif strcmp(img.imageformat, 'CIFTI')
    img.TR = [];
    img.frames = 1;
    if img.hdrnifti.dim(1) == 6    % we probably have a BOLD (4D) file
        if ~isempty(frames)
            img.hdrnifti.dim(7) = frames;
            img.frames = frames;
        else
            img.frames = img.hdrnifti.dim(7);
        end
    end
    img.dim     = img.hdrnifti.dim(6:7)';
    img.voxels  = img.hdrnifti.dim(6);
    img.vsizes  = [];
    % img.mformat = mformat;
    img.runframes = img.frames;
end


% ---- Map data and adjust datatype

img.data = reshape(fdata, img.voxels, []);
img.data = img.data(:,1:img.frames);

img.hdrnifti.datatype = 16;

switch dtype
    case 'single'
        img.hdrnifti.datatype = 16;     % --- float32
        if ~strcmp(dtype, datatype)
            img.data = single(img.data);
        end
    case 'double'
        img.hdrnifti.datatype = 64;     % --- float64
        if ~strcmp(dtype, datatype)
            img.data = double(img.data);
        end
end

% ---- Map metadata

img.meta = fmeta;



% ----- Read NIfTI-1 Header


function [hdrnifti] = readHeader_nifti1(s, hdrnifti)

    if hdrnifti.swap
        sw = @(x) swapbytes(x);
    else
        sw = @(x) x;
    end

    hdrnifti.data_type       = char(s(5:14))';                              % 10
    hdrnifti.db_name         = char(s(15:32))';                             % 18
    hdrnifti.extents         = double(sw(typecast(s(33:36),   'int32')));   % 1
    hdrnifti.session_error   = double(sw(typecast(s(37:38),   'int16')));   % 1
    hdrnifti.regular         = char(s(39));                                 % 1
    hdrnifti.dim_info        = char(s(40));                                 % 1
    hdrnifti.dim             = double(sw(typecast(s(41:56),   'int16')));   % 8
    hdrnifti.intent_p1       = sw(typecast(s(57:60),   'single'));          % 1
    hdrnifti.intent_p2       = sw(typecast(s(61:64),   'single'));          % 1
    hdrnifti.intent_p3       = sw(typecast(s(65:68),   'single'));          % 1
    hdrnifti.intent_code     = double(sw(typecast(s(69:70),   'int16')));   % 1
    hdrnifti.datatype        = double(sw(typecast(s(71:72),   'int16')));   % 1
    hdrnifti.bitpix          = double(sw(typecast(s(73:74),   'int16')));   % 1
    hdrnifti.slice_start     = double(sw(typecast(s(75:76),   'int16')));   % 1
    hdrnifti.pixdim          = sw(typecast(s(77:108),  'single'));          % 8
    hdrnifti.vox_offset      = sw(typecast(s(109:112), 'single'));          % 1
    hdrnifti.scl_slope       = sw(typecast(s(113:116), 'single'));          % 1
    hdrnifti.scl_inter       = sw(typecast(s(117:120), 'single'));          % 1
    hdrnifti.slice_end       = double(sw(typecast(s(121:122), 'int16')));   % 1
    hdrnifti.slice_code      = char(s(123))';                               % 1
    hdrnifti.xyzt_units      = char(s(124))';                               % 1
    hdrnifti.cal_max         = sw(typecast(s(125:128), 'single'));          % 1
    hdrnifti.cal_min         = sw(typecast(s(129:132), 'single'));          % 1
    hdrnifti.slice_duration  = sw(typecast(s(133:136), 'single'));          % 1
    hdrnifti.toffset         = sw(typecast(s(137:140), 'single'));          % 1
    hdrnifti.glmax           = double(sw(typecast(s(141:144), 'int32')));   % 1
    hdrnifti.glmin           = double(sw(typecast(s(145:148), 'int32')));   % 1
    hdrnifti.descrip         = char(s(149:228))';                           % 80
    hdrnifti.aux_file        = char(s(229:252))';                           % 24
    hdrnifti.qform_code      = double(sw(typecast(s(253:254), 'int16')));   % 1
    hdrnifti.sform_code      = double(sw(typecast(s(255:256), 'int16')));   % 1
    hdrnifti.quatern_b       = sw(typecast(s(257:260), 'single'));          % 1
    hdrnifti.quatern_c       = sw(typecast(s(261:264), 'single'));          % 1
    hdrnifti.quatern_d       = sw(typecast(s(265:268), 'single'));          % 1
    hdrnifti.qoffset_x       = sw(typecast(s(269:272), 'single'));          % 1
    hdrnifti.qoffset_y       = sw(typecast(s(273:276), 'single'));          % 1
    hdrnifti.qoffset_z       = sw(typecast(s(277:280), 'single'));          % 1
    hdrnifti.srow_x          = sw(typecast(s(281:296), 'single'));          % 4
    hdrnifti.srow_y          = sw(typecast(s(297:312), 'single'));          % 4
    hdrnifti.srow_z          = sw(typecast(s(313:328), 'single'));          % 4
    hdrnifti.intent_name     = char(s(329:344))';                           % 16
    hdrnifti.magic           = char(s(345:348))';                           % 4
    hdrnifti.version         = 1;


    % ----- Read NIfTI-2 Header


function [hdrnifti] = readHeader_nifti2(s, hdrnifti)

    if hdrnifti.swap
        sw = @(x) swapbytes(x);
    else
        sw = @(x) x;
    end

    hdrnifti.magic           = char(s(5:12))';                                 % 8
    hdrnifti.datatype        = double(sw(typecast(s(13:14), 'int16')));        % 1
    hdrnifti.bitpix          = double(sw(typecast(s(15:16), 'int16')));        % 1
    hdrnifti.dim             = double(sw(typecast(s(17:80), 'int64')));        % 8
    hdrnifti.intent_p1       = sw(typecast(s(81:88), 'double'));               % 1
    hdrnifti.intent_p2       = sw(typecast(s(89:96), 'double'));               % 1
    hdrnifti.intent_p3       = sw(typecast(s(97:104), 'double'));              % 1
    hdrnifti.pixdim          = sw(typecast(s(105:168), 'double'));             % 8
    hdrnifti.vox_offset      = double(sw(typecast(s(169:176), 'int64')));      % 1
    hdrnifti.scl_slope       = sw(typecast(s(177:184), 'double'));             % 1
    hdrnifti.scl_inter       = sw(typecast(s(185:192), 'double'));             % 1
    hdrnifti.cal_max         = sw(typecast(s(193:200), 'double'));             % 1
    hdrnifti.cal_min         = sw(typecast(s(201:208), 'double'));             % 1
    hdrnifti.slice_duration  = sw(typecast(s(209:216), 'double'));             % 1
    hdrnifti.toffset         = sw(typecast(s(217:224), 'double'));             % 1
    hdrnifti.slice_start     = double(sw(typecast(s(225:232), 'int64')));      % 1
    hdrnifti.slice_end       = double(sw(typecast(s(233:240), 'int64')));      % 1
    hdrnifti.descrip         = char(s(241:320))';                              % 80
    hdrnifti.aux_file        = char(s(321:344))';                              % 24
    hdrnifti.qform_code      = double(sw(typecast(s(345:348), 'int32')));      % 1
    hdrnifti.sform_code      = double(sw(typecast(s(349:352), 'int32')));      % 1
    hdrnifti.quatern_b       = sw(typecast(s(353:360), 'double'));             % 1
    hdrnifti.quatern_c       = sw(typecast(s(361:368), 'double'));             % 1
    hdrnifti.quatern_d       = sw(typecast(s(369:376), 'double'));             % 1
    hdrnifti.qoffset_x       = sw(typecast(s(377:384), 'double'));             % 1
    hdrnifti.qoffset_y       = sw(typecast(s(385:392), 'double'));             % 1
    hdrnifti.qoffset_z       = sw(typecast(s(393:400), 'double'));             % 1
    hdrnifti.srow_x          = sw(typecast(s(401:432), 'double'));             % 4
    hdrnifti.srow_y          = sw(typecast(s(433:464), 'double'));             % 4
    hdrnifti.srow_z          = sw(typecast(s(465:496), 'double'));             % 4
    hdrnifti.slice_code      = double(sw(typecast(s(497:500), 'int32')));      % 1
    hdrnifti.xyzt_units      = double(sw(typecast(s(501:504), 'int32')));      % 1
    hdrnifti.intent_code     = double(sw(typecast(s(505:508), 'int32')));      % 1
    hdrnifti.intent_name     = char(s(509:524))';                              % 16
    hdrnifti.dim_info        = char(s(525));                                   % 1
    hdrnifti.unused_str      = char(s(526:540))';                              % 15
    hdrnifti.version         = 2;




















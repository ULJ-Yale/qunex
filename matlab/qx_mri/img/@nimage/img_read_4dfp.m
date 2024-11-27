function [img] = img_read_4dfp(img, file, dtype, frames, verbose)

%``img_read_4dfp(img, file, dtype, frames, verbose)``
%
%   Reads in a 4dfp image into an image object
%
%   INPUTS
%   ======
%
%   --img         mrimage object
%   --file        filename (can be a .conc., .ifh or .img file)
%   --dtype       number format to use ['single']
%   --frames      number of frames to read [all]
%   --verbose     should it report the details [false]
%
%   OUTPUT
%   ======
%
%   img
%  

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 5
    verbose = false;
    if nargin < 4
        frames = [];
        if nargin < 3
            dtype = 'single';
        end
    end
end

file = strtrim(file);
if FileType(file)

    img = nimage(file);

else
    fileinfo = general_check_image_file(filename);

    img.filepath      = fileinfo.path;
    img.filepaths     = {fileinfo.path};
    img.rootfilename  = fileinfo.rootname;
    img.rootfilenames = {fileinfo.rootname};
    img.filename      = fileinfo.basename;
    img.filenames     = {fileinfo.basename};

    root = fullfile(img.filepath, img.rootfilename);
    
    img.hdr4dfp = img.img_read_ifh([root '.4dfp.ifh']);

    img.imageformat = '4dfp';
    img.TR = [];

    x = str2double(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'matrix size [1]'}))));
    y = str2double(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'matrix size [2]'}))));
    z = str2double(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'matrix size [3]'}))));
    img.dim = [x y z];
    img.voxels = x*y*z;

    mformat = 'b';
    if ismember('littleendian', img.hdr4dfp.value)
        mformat = 'l';
    end

    [fim message] = fopen([root '.4dfp.img'], 'r', mformat);
    if fim == -1
        error('\n\nERROR: Could not open %s for reading. Please check your paths!\n\nMatlab message: %s', file, message);
    end
    if isempty(frames)
        img.data = fread(fim, ['float32=>' dtype]);
    else
        img.data = fread(fim, img.voxels*frames, ['float32=>' dtype]);
    end
    fclose(fim);

    img.frames    = length(img.data)/sum(img.voxels);
    img.runframes = img.frames;
    img.hdr4dfp.value{ismember(img.hdr4dfp.key, {'matrix size [4]'})} = num2str(img.frames);

    xmm = str2double(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'scaling factor (mm/pixel) [1]'}))));
    ymm = str2double(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'scaling factor (mm/pixel) [2]'}))));
    zmm = str2double(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'scaling factor (mm/pixel) [3]'}))));
    img.vsizes = [xmm ymm zmm];
end



% --- Create general NIfTI header

img.hdrnifti.magic           = 'n+1';                                          % --- needs to be adjusted when saving
img.hdrnifti.datatype        = 16;
img.hdrnifti.bitpix          = 32;
img.hdrnifti.dim             = [4 img.dim img.frames 0 0 0];
img.hdrnifti.intent_code     = 0;
img.hdrnifti.intent_name     = char(ones(1,16)*32);
img.hdrnifti.intent_p1       = 0;
img.hdrnifti.intent_p2       = 0;
img.hdrnifti.intent_p3       = 0;
img.hdrnifti.pixdim          = [1 img.vsizes 1 0 0 0];
img.hdrnifti.vox_offset      = 352;                                            % --- set for n1, needs to be adjusted when saving
img.hdrnifti.scl_slope       = 0;
img.hdrnifti.scl_inter       = 0;
img.hdrnifti.cal_max         = 0;
img.hdrnifti.cal_min         = 0;
img.hdrnifti.slice_duration  = 0;
img.hdrnifti.toffset         = 0;
img.hdrnifti.slice_start     = 0;
img.hdrnifti.slice_end       = 0;
img.hdrnifti.descrip         = char(ones(1,80)*32);
img.hdrnifti.aux_file        = char(ones(1,24)*32);
img.hdrnifti.qform_code      = 0;
img.hdrnifti.sform_code      = guessSpace(img.dim);
img.hdrnifti.quatern_b       = 0;
img.hdrnifti.quatern_c       = 0;
img.hdrnifti.quatern_d       = 0;
img.hdrnifti.qoffset_x       = 0;
img.hdrnifti.qoffset_y       = 0;
img.hdrnifti.qoffset_z       = 0;
img.hdrnifti.slice_code      = 0;
img.hdrnifti.xyzt_units      = 10;
img.hdrnifti.dim_info        = char(0);
img.hdrnifti.unused_str      = char(ones(1,24)*32);
img.hdrnifti.version         = 1;                                              % --- adjust when saving

[img.hdrnifti.srow_x, img.hdrnifti.srow_y, img.hdrnifti.srow_z] = ifh2af(img.dim, str2num(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'mmppix'})))), str2num(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'center'})))));

% --- add NIfTI-1 specific fields

img.hdrnifti.data_type       = char(ones(1,10)*32);
img.hdrnifti.db_name         = char(ones(1,18)*32);
img.hdrnifti.extents         = 0;
img.hdrnifti.session_error   = 0;
img.hdrnifti.regular         = char(0);
img.hdrnifti.glmax           = 0;
img.hdrnifti.glmin           = 0;

img.hdrnifti.swap    = false;
img.hdrnifti.swapped = false;

function [space] = guessSpace(dim)
    space = 4;
    if (length(dim) == 3)
        if min(dim == [48 64 48]) | min(dim == [176 208 176])
            space = 3;
        end
    end


function [x, y, z] = ifh2af(dim, mmppix, center)
    x = [-mmppix(1); 0; 0; (dim(1) - center(1)/mmppix(1)) * mmppix(1)];
    y = [0;  mmppix(2); 0;          -center(2)                       ];
    z = [0; 0; -mmppix(3); (dim(3) - center(3)/mmppix(3)) * mmppix(3)];

    % y = [0; -mmppix(2); 0; (dim(2) - center(2)/mmppix(2)) * mmppix(2)]; % --- would be the flipped version


function [ftype] = FileType(filename)

if strcmp(filename(length(filename)-4:end), '.conc')
    ftype = 1;
elseif strcmp(filename(length(filename)-3:end), '.img')
    ftype = 0;
else
    error('\n%s is neither a conc nor an image file! Aborting', filename);
end


function [img] = img_read_nifti(img, filename, dtype, frames, verbose)

%``img_read_nifti(img, file, dtype, frames, verbose)``
%
%    Reads in a NIfTI image into an image object
%
%   INPUTS
%   ======
%
%   --img           mrimage object
%   --filename      filename (can be a .nii, .nii.gz or .hdr file)
%   --dtype         datatype to read into ['single']
%   --frames        number of frames to read [all]
%
%   OUTPUT
%   ======
%
%   img
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

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
[fhdr fdata fmeta fswap] = nimage.img_read_nifti_mx(filename, verbose);

% fmeta to str (remove starting chars before < as they are not UTF-8)
idx = find(fmeta' == 60, 1);
fmeta_str = char(fmeta(idx:end)');
fmeta_bytes = uint8(fmeta_str);
fmeta_str = fmeta_bytes(fmeta_bytes >= 32 & fmeta_bytes <= 127);

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
datatype = 'None';
switch  img.hdrnifti.datatype
    case 1
        datatype = 'bitN';
    case 2
        datatype = 'uchar';
    case 4
        datatype = 'int16';
    case 8
        datatype = 'int32';
    case 16
        datatype = 'single';
    case 64
        datatype = 'double';
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
    otherwise
        error('Uknown datatype or datatype I can not handle!');
end

if verbose , fprintf('\n---> Datatype: %s\n', datatype); end

% ------ Process header
% --- file root
fileinfo = general_check_image_file(filename);

img.filenamepath = filename;
img.filenamepaths = {filename};
img.filetype      = img.img_filetype();

% --- format and size details
if img.hdrnifti.dim(1) > 4
    img.imageformat = 'CIFTI';
else
    img.imageformat = 'NIfTI';
end

if strcmp(img.imageformat, 'NIfTI')
    img.TR = [];
    img.frames = 1;

    % we probably have a BOLD (4D) file
    if img.hdrnifti.dim(1) == 4
        if ~isempty(frames)
            img.hdrnifti.dim(5) = frames;
            img.frames = frames;
        else
            img.frames = img.hdrnifti.dim(5);
        end
        img.TR = img.hdrnifti.pixdim(5);
    end
    img.dim       = img.hdrnifti.dim(2:4)';
    img.voxels    = prod(img.dim);
    img.vsizes    = img.hdrnifti.pixdim(2:4)';
    % img.mformat = mformat;
    img.runframes = img.frames;

    % ---- Map data and adjust datatype
    img.data = reshape(fdata, img.voxels, []);
    img.data = img.data(:,1:img.frames);

    img.hdrnifti.datatype = 16;

elseif strcmp(img.imageformat, 'CIFTI')
    img.TR     = [];

    % we probably have a 2d cifti file
    if img.hdrnifti.dim(1) == 6
        cver = regexp(fmeta_str, 'CIFTI Version="(.)"', 'tokens');
        if length(cver) == 0
            error('\nERROR: Could not find information on CIFTI version of the file [%s]!\n', img.filenamepath);
        end
        cver = cver{1};
        if strcmp(cver, '1')
            img.imageformat = 'CIFTI-1';
            img.dim = img.hdrnifti.dim(6)';
            img.frames = img.hdrnifti.dim(7);
        elseif strcmp(cver, '2')
            img.imageformat = 'CIFTI-2';
            img.dim = img.hdrnifti.dim([7])';
            img.frames = img.hdrnifti.dim(6);
        else
            error('\nERROR: Unknown CIFTI version (%s) of the file [%s]!\n', cver, img.filenamepath);
        end
    else
        img.dim    = img.hdrnifti.dim(6);
        img.frames = 1;
    end

    if strcmp(img.filetype, 'pconn')
        if length(img.dim) > 1
            img.voxels  = img.dim(1) .* img.dim(2);
        else
            img.voxels = img.dim ^ 2;
        end
        img.frames  = 1;
    else
        img.voxels  = img.dim(1);
        img.vsizes  = [];
    end
    % img.mformat = mformat;

    % ---- Reorganize and map data
    img.data = reshape(fdata, img.frames, img.voxels);

    if ~isempty(frames)
        img.frames = frames;
        img.data   = img.data(1:frames,:);
    end

    img.data      = img.data';
    img.runframes = img.frames;

    % ---- Adjust datatype
    img.hdrnifti.datatype = 16;
end

switch dtype
    case 'single'
        img.hdrnifti.datatype = 16;     % --- float32
        img.hdrnifti.bitpix   = 32;
        if ~strcmp(dtype, datatype)
            if verbose , fprintf('---> Switching to single\n'); end
            img.data = single(img.data);
        end
    case 'double'
        img.hdrnifti.datatype = 64;     % --- float64
        img.hdrnifti.bitpix   = 64;
        if ~strcmp(dtype, datatype)
            if verbose , fprintf('---> Switching to double\n'); end
            img.data = double(img.data);
        end
end

% ---- Map metadata
if img.hdrnifti.swap
    sw = @(x) swapbytes(x);
else
    sw = @(x) x;
end

ext = double(typecast(fmeta(1:4), 'int8'));
mi  = 0;
try
if ext(1) > 0
    pt = 4;
    while length(fmeta) >= pt + 8
        mi = mi + 1;
        img.meta(mi).size = double(typecast(fmeta(pt+1:pt+4), 'int32'));
        img.meta(mi).code = double(typecast(fmeta(pt+5:pt+8), 'int32'));
        if length(fmeta) >= pt + img.meta(mi).size - 1
            img.meta(mi).data = fmeta(pt+9:pt+img.meta(mi).size);
            if verbose , fprintf('---> Read metablock %d, code: %d, size %d.\n', mi, img.meta(mi).code, img.meta(mi).size); end
        else
            if verbose , fprintf('---> WARNING: Meta block size (%d) reported larger than available data (%d)!\n', img.meta(mi).size, length(fmeta) - pt); end
        end
        pt = pt + img.meta(mi).size;
    end
end
catch
    if verbose, fprintf('---> WARNING: Could not read metadata!\n'); end
    img.meta = [];
    mi = 0;
end

% ---- Process metadata
if mi > 0
    keepmeta = true(1, mi);
    for m = 1:mi
        if img.meta(m).code == 64
            ms = cast(img.meta(m).data, 'char');
            [mdata, mhdr, mmeta] = general_read_table(ms);

            if strcmp(mmeta.meta, 'GLM')
                keepmeta(m)     = false;
                img.glm         = mmeta;
                img.glm.event   = textscan(img.glm.event, '%s'); img.glm.event = img.glm.event{1}';
                img.glm.effects = textscan(img.glm.effects, '%s'); img.glm.effects = img.glm.effects{1}';
                img.glm.effect  = sscanf(img.glm.effect, '%d')';
                img.glm.eindex  = sscanf(img.glm.eindex, '%d')';
                img.glm.frame   = sscanf(img.glm.frame, '%d')';
                img.glm.bolds   = sscanf(img.glm.bolds, '%d')';
                if isfield(img.glm, 'use')
                    img.glm.use     = sscanf(img.glm.use, '%d')';
                end
                img.glm.A       = mdata;
                img.glm.hdr     = mhdr;
                [img.glm.Nrow, img.glm.Mcol] = size(mdata);

                ltest = [img.frames img.glm.Mcol length(img.glm.effect) length(img.glm.eindex) length(img.glm.event) length(img.glm.hdr)];

                if sum(abs(diff(ltest)))
                    error('\nERROR: Corrupt GLM file! Number of frames (%d), matrix columns (%d), effects (%d), effect indeces (%d), events (%d), \nand header items (%d) does not match!\n', img.frames, img.glm.Mcol, length(img.glm.effect), length(img.glm.event), length(img.glm.hdr));
                end

                % --- copy out grand mean and sd images
                img.data = img.image2D;
                midx  = find(ismember(img.glm.event, 'gmean'));
                sdidx = find(ismember(img.glm.event, 'sd'));
                if ~isempty(midx)
                    img.glm.gmean = img.data(:, midx);
                end
                if ~isempty(midx)
                    img.glm.sd = img.data(:, sdidx);
                end

            elseif strcmp(mmeta.meta, 'list')
                keepmeta(m) = false;
                img.list    = mmeta;
                lists       = fields(img.list);
                lists       = lists(~ismember(lists, 'meta'));
                ltest       = [img.frames];
                for l = lists(:)'
                    l = l{1};
                    if max(isstrprop(strrep(img.list.(l), 'e', ''), 'alpha'))
                        img.list.(l) = strread(img.list.(l), '%s')';
                    else
                        img.list.(l) = strread(img.list.(l), '%f')';
                    end
                    ltest = [ltest length(img.list.(l))];
                end
                if sum(abs(diff(ltest)))
                    error('\nERROR: Corrupt list file! Number of frames (%d) and list items ([%s]) does not match!\n', img.frames, num2str(ltest(2:end)));
                end
            end
        end

        % --- cifti metadata
        if img.meta(m).code == 32

            % ---- set to be removed after processing
            keepmeta(m) = false;

            % ---- Initialize variables

            img.cifti.longnames  = {};
            img.cifti.shortnames = {};
            img.cifti.start      = [];
            img.cifti.end        = [];
            img.cifti.length     = [];
            img.cifti.maps       = {};
            img.cifti.parcels    = {};
            img.cifti.labels     = {};

            short2long_structure = containers.Map({'ACCUMBENS_LEFT', 'ACCUMBENS_RIGHT', 'ALL_WHITE_MATTER', 'ALL_GREY_MATTER', 'AMYGDALA_LEFT', 'AMYGDALA_RIGHT', 'BRAIN_STEM', 'CAUDATE_LEFT', 'CAUDATE_RIGHT', 'CEREBELLAR_WHITE_MATTER_LEFT', 'CEREBELLAR_WHITE_MATTER_RIGHT', 'CEREBELLUM', 'CEREBELLUM_LEFT', 'CEREBELLUM_RIGHT', 'CEREBRAL_WHITE_MATTER_LEFT', 'CEREBRAL_WHITE_MATTER_RIGHT', 'CORTEX', 'CORTEX_LEFT', 'CORTEX_RIGHT', 'DIENCEPHALON_VENTRAL_LEFT', 'DIENCEPHALON_VENTRAL_RIGHT', 'HIPPOCAMPUS_LEFT', 'HIPPOCAMPUS_RIGHT', 'OTHER', 'OTHER_GREY_MATTER', 'OTHER_WHITE_MATTER', 'PALLIDUM_LEFT', 'PALLIDUM_RIGHT', 'PUTAMEN_LEFT', 'PUTAMEN_RIGHT', 'THALAMUS_LEFT', 'THALAMUS_RIGHT'}, {'CIFTI_STRUCTURE_ACCUMBENS_LEFT', 'CIFTI_STRUCTURE_ACCUMBENS_RIGHT', 'CIFTI_STRUCTURE_ALL_WHITE_MATTER', 'CIFTI_STRUCTURE_ALL_GREY_MATTER', 'CIFTI_STRUCTURE_AMYGDALA_LEFT', 'CIFTI_STRUCTURE_AMYGDALA_RIGHT', 'CIFTI_STRUCTURE_BRAIN_STEM', 'CIFTI_STRUCTURE_CAUDATE_LEFT', 'CIFTI_STRUCTURE_CAUDATE_RIGHT', 'CIFTI_STRUCTURE_CEREBELLAR_WHITE_MATTER_LEFT', 'CIFTI_STRUCTURE_CEREBELLAR_WHITE_MATTER_RIGHT', 'CIFTI_STRUCTURE_CEREBELLUM', 'CIFTI_STRUCTURE_CEREBELLUM_LEFT', 'CIFTI_STRUCTURE_CEREBELLUM_RIGHT', 'CIFTI_STRUCTURE_CEREBRAL_WHITE_MATTER_LEFT', 'CIFTI_STRUCTURE_CEREBRAL_WHITE_MATTER_RIGHT', 'CIFTI_STRUCTURE_CORTEX', 'CIFTI_STRUCTURE_CORTEX_LEFT', 'CIFTI_STRUCTURE_CORTEX_RIGHT', 'CIFTI_STRUCTURE_DIENCEPHALON_VENTRAL_LEFT', 'CIFTI_STRUCTURE_DIENCEPHALON_VENTRAL_RIGHT', 'CIFTI_STRUCTURE_HIPPOCAMPUS_LEFT', 'CIFTI_STRUCTURE_HIPPOCAMPUS_RIGHT', 'CIFTI_STRUCTURE_OTHER', 'CIFTI_STRUCTURE_OTHER_GREY_MATTER', 'CIFTI_STRUCTURE_OTHER_WHITE_MATTER', 'CIFTI_STRUCTURE_PALLIDUM_LEFT', 'CIFTI_STRUCTURE_PALLIDUM_RIGHT', 'CIFTI_STRUCTURE_PUTAMEN_LEFT', 'CIFTI_STRUCTURE_PUTAMEN_RIGHT', 'CIFTI_STRUCTURE_THALAMUS_LEFT', 'CIFTI_STRUCTURE_THALAMUS_RIGHT'});

            % ---- Process CIFTI metadata

            if strcmp(img.imageformat, 'CIFTI-2')
                img.cifti.metadata = cifti_read_metadata(cast(img.meta(m).data, 'char')', img.hdrnifti, img.filenamepath);

                % -- get parcel or structure info
                if strcmp(img.cifti.metadata.diminfo{1}.type, 'parcels')
                    img.cifti.parcels = {img.cifti.metadata.diminfo{1}.parcels.name};
                elseif strcmp(img.cifti.metadata.diminfo{1}.type, 'dense');
                    for istruct = 1:length(img.cifti.metadata.diminfo{1}.models)
                        img.cifti.longnames{istruct}  = short2long_structure(img.cifti.metadata.diminfo{1}.models{istruct}.struct);
                        img.cifti.shortnames{istruct} = img.cifti.metadata.diminfo{1}.models{istruct}.struct;
                        img.cifti.start{istruct}      = img.cifti.metadata.diminfo{1}.models{istruct}.start;
                        img.cifti.end{istruct}        = img.cifti.metadata.diminfo{1}.models{istruct}.start + img.cifti.metadata.diminfo{1}.models{istruct}.count -1;
                        img.cifti.length{istruct}     = img.cifti.metadata.diminfo{1}.models{istruct}.count;
                    end
                end

                % -- get maps or TR
                if strcmp(img.cifti.metadata.diminfo{2}.type, 'scalars')
                    img.cifti.maps = {img.cifti.metadata.diminfo{2}.maps.name};
                elseif strcmp(img.cifti.metadata.diminfo{2}.type, 'series')
                    img.TR = img.cifti.metadata.diminfo{2}.seriesStep;
                elseif strcmp(img.cifti.metadata.diminfo{2}.type, 'labels')
                    img.cifti.maps = {img.cifti.metadata.diminfo{2}.maps.name};
                    for imap = 1:length(img.cifti.metadata.diminfo{2}.maps);
                        img.cifti.labels{imap} = img.cifti.metadata.diminfo{2}.maps(imap).table;
                    end
                end

            else
                % ---- We are assumning that this holds for CIFTI-I, it might not!
                fprintf('\nWARNING: file %s is in CIFTI-1 format.\n         Please transform to CIFTI-2 format (e.g. using wb_command) to ensure correct processing of XML metadata!\n', img.filenamepath);

                img.cifti.longnames  = {'CIFTI_STRUCTURE_CORTEX_LEFT', 'CIFTI_STRUCTURE_CORTEX_RIGHT', 'CIFTI_STRUCTURE_ACCUMBENS_LEFT', 'CIFTI_STRUCTURE_ACCUMBENS_RIGHT', 'CIFTI_STRUCTURE_AMYGDALA_LEFT', 'CIFTI_STRUCTURE_AMYGDALA_RIGHT', 'CIFTI_STRUCTURE_BRAIN_STEM', 'CIFTI_STRUCTURE_CAUDATE_LEFT', 'CIFTI_STRUCTURE_CAUDATE_RIGHT', 'CIFTI_STRUCTURE_CEREBELLUM_LEFT', 'CIFTI_STRUCTURE_CEREBELLUM_RIGHT', 'CIFTI_STRUCTURE_DIENCEPHALON_VENTRAL_LEFT', 'CIFTI_STRUCTURE_DIENCEPHALON_VENTRAL_RIGHT', 'CIFTI_STRUCTURE_HIPPOCAMPUS_LEFT', 'CIFTI_STRUCTURE_HIPPOCAMPUS_RIGHT', 'CIFTI_STRUCTURE_PALLIDUM_LEFT', 'CIFTI_STRUCTURE_PALLIDUM_RIGHT', 'CIFTI_STRUCTURE_PUTAMEN_LEFT', 'CIFTI_STRUCTURE_PUTAMEN_RIGHT', 'CIFTI_STRUCTURE_THALAMUS_LEFT', 'CIFTI_STRUCTURE_THALAMUS_RIGHT'};
                img.cifti.shortnames = {'CORTEX_LEFT', 'CORTEX_RIGHT', 'ACCUMBENS_LEFT', 'ACCUMBENS_RIGHT', 'AMYGDALA_LEFT', 'AMYGDALA_RIGHT', 'BRAIN_STEM', 'CAUDATE_LEFT', 'CAUDATE_RIGHT', 'CEREBELLUM_LEFT', 'CEREBELLUM_RIGHT', 'DIENCEPHALON_VENTRAL_LEFT', 'DIENCEPHALON_VENTRAL_RIGHT', 'HIPPOCAMPUS_LEFT', 'HIPPOCAMPUS_RIGHT', 'PALLIDUM_LEFT', 'PALLIDUM_RIGHT', 'PUTAMEN_LEFT', 'PUTAMEN_RIGHT', 'THALAMUS_LEFT', 'THALAMUS_RIGHT'};
                img.cifti.start      = [1 29697 59413 59548 59688 60003 60335 63807 64535 65290 73999 83143 83849 84561 85325 86120 86417 86677 87737 88747 90035];
                img.cifti.end        = [29696 59412 59547 59687 60002 60334 63806 64534 65289 73998 83142 83848 84560 85324 86119 86416 86676 87736 88746 90034 91282];
                img.cifti.length     = [29696 29716 135 140 315 332 3472 728 755 8709 9144 706 712 764 795 297 260 1060 1010 1288 1248];
                img.cifti.maps       = {};
                img.cifti.parcels    = {};
            end
        end
    end
    img.meta = img.meta(keepmeta);
end

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

    % --- add NIfTI-2 fields
    hdrnifti.unused_str      = char(ones(1,24)*32);

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

    % --- add NIfTI-1 fields

    hdrnifti.data_type       = '          ';
    hdrnifti.db_name         = '                  ';
    hdrnifti.extents         = 0;
    hdrnifti.session_error   = 0;
    hdrnifti.regular         = ' ';
    hdrnifti.glmax           = 0;
    hdrnifti.glmin           = 0;

function [img] = img_read_glm(img, fname, dtype, verbose)

%``img_read_glm(img, fname, dtype, verbose)``
%
%   Reads in a fidl glm image into an image object
%
%   INPUTS
%   ======
%
%    img         mrimage object
%   fname       filename (a .glm file)
%   dtype       number format to use ['single']
%   verbose     whether to be talkative [false]
%
%   OUTPUT
%   ======
%
%   img
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 4
    verbose = [];
       if nargin < 3
           dtype = [];
    end
end

if isempty(verbose), verbose = false; end
if isempty(dtype), dtype = 'single'; end

%
% --- Open the file and read the header
%

fin = fopen(fname, 'r', 'b');
img.hdr4dfp = readHeader(fin);
img.mformat = 'b';
img.imageformat = '4dfp';

if ismember('littleendian', img.hdr4dfp.value)
    if verbose, fprintf('\n ---> switching to littleendian'); end
    fclose(fin);
    fin = fopen(fname, 'r', 'l');
    img.hdr4dfp = readHeader(fin);
    img.mformat = 'l';
end

img = processHeader(img, fin);

fileinfo = general_check_image_file(filename);
img.filepath      = fileinfo.path;
img.filepaths     = {fileinfo.path};
img.rootfilename  = fileinfo.rootname;
img.rootfilenames = {fileinfo.rootname};
img.filename      = fileinfo.basename;
img.filenames     = {fileinfo.basename};

% [img.data, count] = fread(fin, img.voxels * img.frames, ['float32=>' dtype]);
[img.data, count] = fread(fin, inf, ['float32=>' dtype]);
img.frames = count/img.voxels;
img.hdr4dfp.value{ismember(img.hdr4dfp.key, 'matrix size [4]')} = num2str(img.frames);

if verbose, fprintf('\n ---> read %d voxels\n', count); end
fclose(fin);


% -------------------------------------------------------------
%                                              helper functions


function [hdr] = readHeader(fin)

    hdr = {};
    l = fgetl(fin);
    c = 0;
    while ~strcmp(l, 'START_BINARY')
        c = c + 1;
        [key, value] = strtok(l, ':=');
        value = strtrim(strrep(value, ':=', ''));
        key = strtrim(key);
        hdr.key{c} = key;
        hdr.value{c} = value;
        l = fgetl(fin);
        % fprintf('\n ---> "%s"', l);
    end

function [img] = processHeader(img, fin)

    % --- set how many volumes of estimates

    img.frames = str2double(img.hdr4dfp.value{ismember(img.hdr4dfp.key, 'glm total number of estimates')});
    % img.frames = img.frames + str2double(img.hdr4dfp.value{ismember(img.hdr4dfp.key, 'glm number of contrasts')});
    img.hdr4dfp.value{ismember(img.hdr4dfp.key, 'matrix size [4]')} = num2str(img.frames);
    img.dim = 4;

    % --- set the original dimensions

    x = str2double(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'matrix size [1]'}))));
    y = str2double(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'matrix size [2]'}))));
    z = str2double(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'matrix size [3]'}))));
    img.dim = [x y z];
    img.voxels = x*y*z;

    % --- set dimension scale

    xmm = str2double(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'scaling factor (mm/pixel) [1]'}))));
    ymm = str2double(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'scaling factor (mm/pixel) [2]'}))));
    zmm = str2double(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'scaling factor (mm/pixel) [3]'}))));
    img.vsizes = [xmm ymm zmm];

    % --- set TR

    img.TR = str2double(char(img.hdr4dfp.value(ismember(img.hdr4dfp.key, {'glm temporal sampling rate'}))));

    % --- read mask if one exists

    % keyn = find(ismember(img.hdr4dfp.key, 'glm mask file'));
    % if ~isempty(keyn) && ~isempty(img.hdr4dfp.value{keyn})
    %     mfile = img.hdr4dfp.value{keyn};
    %     mask  = nimage(mfile);
    %     img.mask   = mask.data > 0;
    %     img.masked = true;
    %     img.voxels = sum(sum(img.mask > 0));
    % end

    % --- set glm info

    img.glm.ntrials  = str2double(img.hdr4dfp.value{ismember(img.hdr4dfp.key, 'glm number of trials')});
    img.glm.df       = str2double(img.hdr4dfp.value{ismember(img.hdr4dfp.key, 'glm degrees of freedom')});
    img.glm.all_eff  = str2double(img.hdr4dfp.value{ismember(img.hdr4dfp.key, 'glm total number of effects')});
    img.glm.tot_eff  = str2double(img.hdr4dfp.value{ismember(img.hdr4dfp.key, 'glm number of effects of interest')});
    img.glm.rev      = str2double(img.hdr4dfp.value{ismember(img.hdr4dfp.key, 'glm revision number')});
    img.glm.Mcol     = str2double(img.hdr4dfp.value{ismember(img.hdr4dfp.key, 'glm total number of estimates')});
    img.glm.Nrow     = str2double(img.hdr4dfp.value{ismember(img.hdr4dfp.key, 'glm number of usable frames')});
    img.glm.nc       = str2double(img.hdr4dfp.value{ismember(img.hdr4dfp.key, 'glm number of contrasts')});
    img.glm.nF       = str2double(img.hdr4dfp.value{ismember(img.hdr4dfp.key, 'glm number of F statistics')});
    img.glm.tdim     = str2double(img.hdr4dfp.value{ismember(img.hdr4dfp.key, 'glm number of frames in raw')});
    img.glm.bolds    = str2double(img.hdr4dfp.value{ismember(img.hdr4dfp.key, 'glm number of bold files')});

    img.glm.effects  = {};
    img.glm.effect   = zeros(1, img.frames);
    img.glm.eindex   = zeros(1, img.frames);

    keys   = img.hdr4dfp.key;
    values = img.hdr4dfp.value;
    nkeys = length(keys);

    ename   = [];
    elen    = [];
    ecol    = [];
    c       = 0;

    % --- Set up effects info

    for k = 1:nkeys

        % --- read values

        if strcmp(keys{k}, 'glm effect label')
            ename = values{k};
            elen  = [];
            ecol  = [];
            c     = c + 1;
        elseif strcmp(keys{k}, 'glm effect length')
            elen = str2double(values{k});
        elseif strcmp(keys{k}, 'glm effect column')
            ecol = str2double(values{k});
        end

        % --- embed information

        if ~sum(cellfun(@isempty, {ename, elen, ecol}))
            img.glm.effects{c} = ename;
            img.glm.effect(ecol+1:ecol+elen) = c;
            img.glm.eindex(ecol+1:ecol+elen) = 1:elen;
            ename = [];
            ecol  = [];
            elen  = [];
        end
    end

    % --- Read contrast names

    % fseek(fin, 0, 'bof');
    % ttt = fread(fin, 40, '*char')';
    % while ttt(end-12:end-1) ~= 'START_BINARY'
    %     ttt = [ttt fread(fin, 1, '*char')];
    % end

    ncontrasts = str2double(values{ismember(keys, 'glm number of contrasts')});
    for n = 1:ncontrasts
        clen = fread(fin, 1, 'int16');
        % fprintf('\n-> contrast %d: %d', n, clen);
        if clen > 25
            % fprintf('\nWARNING: clen of contrast too long: %d', clen);
        end
        if clen > 0
            cname = fread(fin, clen, '*char');
        else
            cname = '';
        end
        img.glm.contrasts{n} = cname;
    end

    % --- Read supplementary data

    img.glm.A = fread(fin, [img.glm.Nrow, img.glm.Mcol], 'float32');
    img.glm.c = fread(fin, [img.glm.nc, img.glm.Mcol], 'float32');
    img.glm.cnorm = fread(fin, [img.glm.nc, img.glm.tot_eff], 'float32');

    img.glm.valid_frms = fread(fin, img.glm.tdim, 'float32');
    img.glm.delay      = fread(fin, img.glm.tot_eff, 'float32');
    img.glm.stimlen    = fread(fin, img.glm.tot_eff, 'float32');
    img.glm.lcfunc     = fread(fin, img.glm.tot_eff, 'int16');
    img.glm.start_data = fread(fin, 1, 'int32');

    img.glm.ATAm1 = fread(fin, [img.glm.Mcol, img.glm.Mcol], 'float64');

    img.glm.sd    = fread(fin, img.voxels, 'float32');
    img.glm.var   = fread(fin, img.voxels, 'float64');

    if img.glm.nF >= 1
        img.glm.fzstat = fread(fin, [img.voxels, img.glm.nF], 'float32');
    end
    img.glm.x     = fread(fin, img.voxels, 'float32');
    img.glm.gmean = fread(fin, img.voxels, 'float32');



%  ----- GLM file specification
%
%
%   IFH variables
%
%
%       ifh->glm_rev            glm revision number
%       ifh->glm_Mcol           glm total number of estimates
%       ifh->glm_M_interest     glm estimates of interest
%       ifh->glm_xdim           glm column dimension of estimates
%       ifh->glm_ydim           glm row dimension of estimates
%       ifh->glm_zdim           glm axial dimension of estimates
%       ifh->glm_tdim           glm number of frames in raw
%       ifh->glm_Nrow           glm number of usable frames
%       ifh->glm_df             glm degrees of freedom
%       ifh->glm_nc             glm number of contrasts
%       ifh->glm_period         glm BOLD response duration
%       ifh->glm_num_trials     glm number of trials
%       ifh->glm_TR             glm temporal sampling rate
%       ifh->glm_tot_eff        glm number of effects of interest
%       ifh->glm_input_data_space   glm input data space
%       ifh->glm_fwhm           glm fwhm in voxels
%       ifh->glm_all_eff        glm total number of effects
%           ifh->glm_effect_label[i]    glm effect label
%           ifh->glm_effect_length[i]   glm effect length
%           ifh->glm_effect_column[i]   glm effect column
%           ifh->glm_funclen[i]         glm length of encoded function
%           ifh->glm_functype[i]        glm type of encoded function
%           ifh->glm_effect_TR[i]       glm effective TR
%           ifh->glm_effect_shift_TR[i] glm shift TR
%       ifh->glm_num_files          glm number of bold files
%       ifh->glm_W                  glm random field smoothness
%       ifh->glm_dxdy               glm transverse voxel dimension
%       ifh->glm_dz                 glm axial voxel dimension
%       ifh->glm_nF                 glm number of F statistics
%           ifh->glm_F_names[i]         glm description of F statistic
%       ifh->glm_event_file         glm event file
%       ifh->nregions
%           ifh->region_names[i]        region names
%       ifh->nbehav
%           ifh->behavior_names[i]  behavior names
%       ifh->nregfiles
%           ifh->regfiles[i]        region file
%
%
%   GLM CONTENT
%
%   START_BINARY\n
%   for nc
%       label len       (short)
%       label           (char:   len)
%   glm->A              (float:  Mcol * Nrow)  [design matrix]
%   glm->c              (float:  Mcon * nc)    [contrasts]
%   glm->cnorm          (float:  tot_eff * nc)   [contrasts for Hotteling T2]
%   glm->valid_frms     (float:  tdim)
%   glm->delay          (float:  tot_eff)
%   glm->stimlen        (float:  tot_eff)
%   glm->lcfunc         (short:  tot_eff)
%   glm->start_data     (int:    1)
%   glm->ATAm1          (double: Mcol * Mcol)
%   glm->sd             (float:  lenvol)
%   glm->var            (double: lenvol)
%   glm->fzstat         (float:  nF * lenvol)
%
%   startb = start_data
%           + double(Mcol*Mcol: ATAm1)
%           + float(vol: sd)
%           + float(vol*nF: fzstat)
%           + float(vol: grand_mean)
%           + double(vol: var) (if glm_rev <= -25)

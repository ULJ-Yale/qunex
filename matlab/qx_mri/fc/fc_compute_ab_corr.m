function [] = fc_compute_ab_corr(flist, smask, tmask, mask, root, options, verbose)

%``function [] = fc_compute_ab_corr(flist, smask, tmask, mask, root, options, verbose)``
%
%   Computes the correlation of each source mask voxel with each target mask
%   voxel.
%
%   Parameters:
%       --flist (str):
%           File list with information on sessions bold runs and
%           segmentation files, or a well strucutured string (see
%           general_read_file_list).
%       --smask (str):
%           Path to .names file for source mask definition.
%       --tmask (str):
%           Path to .names file for target mask roi definition.
%       --mask (int | logical | vector, default []):
%           Either number of frames to omit or a mask of frames to use.
%       --root (str, default []):
%           The root of the filename where results are to be saved.
%       --options (str, default 'g'):
%           A string specifying what correlations to save:
%
%           - 'g'
%               compute mean correlation across sessions (only makes
%               sense with the same sROI for each session)
%
%           - 'i'
%               save individual sessions' results.
%
%       --verbose (str, default 'none'):
%           How to report the progress: 'full', 'script' or 'none'.
%
%   Output files:
%       If group correlations are selected, the resulting files are:
%
%       - <root>_group_ABCor_Fz
%           Mean Fisher Z value across participants.
%
%       - <root>_group_ABCor_r
%           Mean Pearson r (converted from Fz) value across participants.
%
%       If individual correlations are selected, the resulting files are:
%
%       - <root>_<session id>_ABCor
%           Pearson r correlations for the individual.
%
%       If root is not specified, it is taken to be the root of the flist.
%
%   Notes:
%       Use the function to compute individual and/or group correlations of each
%       smask voxel with each tmask voxel. tmask voxels are spread across the
%       volume and smask voxels are spread across the volumes. For more details
%       see `img_compute_ab_correlation` - nimage method.
%
%   Examples:
%       ::
%
%           fc_compute_ab_corr('scz.list', 'PFC.names', 'ACC.names', 5, ...
%               'SCZ_PFC-ACC', 'g', 'full');
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 7 || isempty(verbose), verbose = 'none'; end
if nargin < 6 || isempty(options), options = 'g';    end
if nargin < 5 root = []; end
if nargin < 4 mask = []; end
if nargin < 3 error('ERROR: At least file list, source and target masks must be specified to run fc_compute_ab_corr!'); end


if strcmp(verbose, 'full')
    script = true;
    method = true;
else
    if strcmp(verbose, 'script')
        script = true;
        method = false;
    else
        script = false;
        method = false;
    end
end

if strfind(options, 'g')
    group = true;
else
    group = false;
end
if strfind(options, 'i')
    indiv = true;
else
    indiv = false;
end



if script, fprintf('\n\nStarting ...'), end


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------------- make a list of all the files to process

if script, fprintf('\n ... listing files to process'), end

[session, nsessions, nfiles, listname] = general_read_file_list(flist, verbose);

if isempty(root)
    root = listname;
end

if script, fprintf(' ... done.'), end


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------- The main loop ... go through all the sessions

%   --- Get variables ready first

sROI = nimage.img_read_roi(smask, session(1).roi);
tROI = nimage.img_read_roi(tmask, session(1).roi);

if length(sROI.roi.roicodes2) == 1 & length(sROI.roi.roicodes2{1}) == 0
    sROIload = false;
else
    sROIload = true;
end

if length(tROI.roi.roicodes2) == 1 & length(tROI.roi.roicodes2{1}) == 0
    tROIload = false;
else
    tROIload = true;
end

if group
    nframes = sum(sum(sROI.image2D > 0));
    gres = sROI.zeroframes(nframes);
    gcnt = sROI.zeroframes(1);
    gcnt.data = gcnt.image2D;
end

%   --- Start the loop

for s = 1:nsessions

    %   --- reading in image files
    if script, tic, end
    if script, fprintf('\n------\nProcessing %s', session(s).id), end
    if script, fprintf('\n... reading file(s) '), end

    % --- check if we need to load the session region file

    if ~strcmp(session(s).roi, 'none')
        if tROIload | sROIload
            roif = nimage(session(s).roi);
        end
    end

    if tROIload
        tROI = nimage.img_read_roi(tmask, roif);
    end
    if sROIload
        sROI = nimage.img_read_roi(smask, roif);
    end

    % --- load bold data

    nfiles = length(session(s).files);

    img = nimage(session(s).files{1});
    if mask, img = img.sliceframes(mask); end
    if script, fprintf('1'), end
    if nfiles > 1
        for n = 2:nfiles
            new = nimage(session(s).files{n});
            if mask, new = new.sliceframes(mask); end
            img = [img new];
            if script, fprintf(', %d', n), end
        end
    end
    if script, fprintf('\n'), end

    ABCor = img.img_compute_ab_correlation(sROI, tROI, method);
    ABCor = ABCor.unmaskimg;

    if indiv
        ifile = [root '_' session(s).id '_ABCor'];
        if script, fprintf('\n... saving %s\n', ifile); end
        ABCor.img_saveimage(ifile);
    end

    if group
        if script, fprintf('\n... computing group results\n'); end
        gres.data = gres.data + fc_fisher(ABCor.data);
        if tROIload
            gcnt.data = gcnt.data + tROI.image2D > 0;
        end
    end

    if script, fprintf('... done [%.1fs]\n', toc); end
end

if group
    if script, fprintf('\n=======\nSaving group results'), end

    if ~tROIload
        gcnt.data = (tROI.image2D > 0) .* nsessions;
    end

    gres.data = gres.data ./ repmat(gcnt.data,1,nframes);
    gres.img_saveimage([root '_group_ABCor_Fz']);
    gres.data = fc_fisherinv(gres.data);
    gres.img_saveimage([root '_group_ABCor_r']);
end


if script, fprintf('\nDONE!\n\n'), end


function [] = fc_compute_ab_corr(flist, sroi, troi, frames, root, options, verbose)

%``fc_compute_ab_corr(flist, sroi, troi, frames, root, options, verbose)``
%
%   Compute the correlation of each source ROI voxel with each target ROI
%   voxel.
%
%   .. qx_command:
%       type: matlab
%
%   Parameters:
%       --flist (str):
%           File list with information on sessions bold runs and
%           segmentation files, or a well strucutured string (see
%           general_read_file_list).
%
%       --sroi (str, nimage):
%           Input to img_prep_roi roi parameter that defines the source ROI, 
%           usually a path to .names file, but it can also be any other 
%           path that results in an roi image, or an nimage object. See options
%           parameter for behavior when there are multiple source ROI defined.
%
%       --troi (str):
%           Input to img_prep_roi roi parameter that defines the target ROI,
%           usually a path to .names file, but it can also be any other
%           path that results in an roi image, or an nimage object. See options
%           parameter for behavior when there are multiple target ROI defined.
%
%           Both ROI have to be defined over the same rows as the bold files
%           they are used on: a dense ROI file (e.g. .dlabel.nii,
%           .dscalar.nii) for dense (.dtseries.nii) bold files, and a
%           parcellated label file (.plabel.nii) of the same parcellation for
%           parcellated (.ptseries.nii) bold files, which it matches row for
%           row. Use the 'rois' option to work with a subset of the regions
%           the file defines, by name or by index, e.g.
%           '<path>.plabel.nii|rois:Visual1-55_L-Thalamus'.
%
%       --frames (int | logical | vector, default ''):
%           Either number of frames to omit or a mask of frames to use.
%
%       --root (str, default ''):
%           The root of the filename where results are to be saved.
%
%       --options (str, default 'save:group|source_roi:1|target_roi:1'):
%           A pipe separated '<key>:<value>|<key>:<value>' string
%           specifying further options. 
%
%           The possible options are:
%
%           - save : group ('group' | 'individual')
%               Whether to compute mean correlation across sessions ('group')
%               (only makes sense with the same sROI for each session), and/or
%               save individual sessions' results ('individual')
%           - source_roi : 1 (integer)
%               In case of multiple ROI, which ones to use as source.
%           - target_roi : 1 (integer)
%               In case of multiple ROI, which ones to use as target.
%
%       --verbose (str, default 'none'):
%           How to report the progress: 'full', 'script' or 'none'.
%
%   Output files:
%       If group correlations are selected, the resulting files are:
%
%       - <root>_group_ABCor_<source_roi>_<target_roi>_Fz
%           Mean Fisher Z value across participants.
%
%       - <root>_group_ABCor_<source_roi>_<target_roi>_r
%           Mean Pearson r (converted from Fz) value across participants.
%
%       If individual correlations are selected, the resulting files are:
%
%       - <root>_<session id>_ABCor_<source_roi>_<target_roi>_r
%           Pearson r correlations for the individual.
%
%       If root is not specified, it is taken to be the root of the flist.
%
%   Notes:
%       Use the function to compute individual and/or group correlations of each
%       sroi voxel with each troi voxel. troi voxels are spread across the
%       volume and sroi voxels are spread across the volumes. For more details
%       see `img_compute_ab_correlation` - nimage method.
%
%   Examples:
%       ::
%
%           qunex fc_compute_ab_corr \
%               --flist='scz.list' \
%               --sroi='PFC.names' \
%               --troi='ACC.names' \
%               --frames=5 \
%               --root='SCZ_PFC-ACC' \
%               --options='g' \
%               --verbose='full'
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 7 || isempty(verbose), verbose = 'none'; end
if nargin < 6 || isempty(options), options = 'g';    end
if nargin < 5 root = []; end
if nargin < 4 frames = []; end
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

list = general_read_file_list(flist, 'all', [], verbose);

if isempty(root)
    root = list.listname;
end

if script, fprintf(' ... done.'), end


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------- The main loop ... go through all the sessions

%   --- Get variables ready first

% individual roi files are optional in a file list, and asking for one that
% is not there fails before any session is read

if isfield(list.session(1), 'roi')
    sroifile = list.session(1).roi;
else
    sroifile = [];
end

s_roi = nimage.img_prep_roi(sroi, sroifile);
t_roi = nimage.img_prep_roi(troi, sroifile);

if isempty([s_roi.roi(:).roicodes2])
    sROIload = false;
else
    sROIload = true;
end

if isempty([t_roi.roi(:).roicodes2])
    tROIload = false;
else
    tROIload = true;
end

if group
    nframes = sum(sum(s_roi.image2D > 0));
    gres = s_roi.zeroframes(nframes);
    gcnt = s_roi.zeroframes(1);
    gcnt.data = gcnt.image2D;

    % The accumulators are shaped like the source ROI but hold correlations
    % rather than region codes. Saving them under the ROI file's own type
    % asks for one label table per frame, and a label file carries one, so
    % a label ROI file (.dlabel.nii / .plabel.nii) failed on the group save.

    gres.filetype = scalar_filetype(gres.filetype);
    gcnt.filetype = scalar_filetype(gcnt.filetype);
end

%   --- Start the loop

for s = 1:list.nsessions

    %   --- reading in image files
    if script, tic, end
    if script, fprintf('\n------\nProcessing %s', list.session(s).id), end
    if script, fprintf('\n... reading file(s) '), end

    % --- check if we need to load the session region file

    if isfield(list.session(s), 'roi') && ~strcmp(list.session(s).roi, 'none')
        if tROIload | sROIload
            roif = nimage(list.session(s).roi);
        end
    end

    if tROIload
        tROI = nimage.img_read_roi(troi, roif);
    end
    if sROIload
        s_roi = nimage.img_read_roi(sroi, roif);
    end

    % --- load bold data

    nfiles = length(list.session(s).files);

    img = nimage(list.session(s).files{1});
    if frames, img = img.sliceframes(frames); end
    if script, fprintf('1'), end
    if nfiles > 1
        for n = 2:nfiles
            new = nimage(list.session(s).files{n});
            if frames, new = new.sliceframes(frames); end
            img = [img new];
            if script, fprintf(', %d', n), end
        end
    end
    if script, fprintf('\n'), end

    ABCor = img.img_compute_ab_correlation(s_roi, t_roi, method);
    ABCor = ABCor.unmaskimg;

    if indiv
        ifile = [root '_' list.session(s).id '_ABCor'];
        if script, fprintf('\n... saving %s\n', ifile); end
        ABCor.img_saveimage(ifile);
    end

    if group
        if script, fprintf('\n... computing group results\n'); end
        gres.data = gres.data + fc_fisher(ABCor.data);
        if tROIload
            gcnt.data = gcnt.data + t_roi.image2D > 0;
        end
    end

    if script, fprintf('... done [%.1fs]\n', toc); end
end

if group
    if script, fprintf('\n=======\nSaving group results'), end

    if ~tROIload
        gcnt.data = (t_roi.image2D > 0) .* list.nsessions;
    end

    gres.data = gres.data ./ repmat(gcnt.data,1,nframes);
    gres.img_saveimage([root '_group_ABCor_Fz']);
    gres.data = fc_fisherinv(gres.data);
    gres.img_saveimage([root '_group_ABCor_r']);
end


if script, fprintf('\nDONE!\n\n'), end


% --------------------------------------------------------------------------------------------
%                                                                              scalar_filetype

function [filetype] = scalar_filetype(filetype)

    % The scalar CIFTI type matching a dense or parcellated one, for data
    % that has a value per map rather than a timeseries or a label table.

    switch lower(filetype)
        case {'dtseries', 'dlabel', 'dscalar'}
            filetype = 'dscalar';
        case {'ptseries', 'plabel', 'pscalar'}
            filetype = 'pscalar';
    end

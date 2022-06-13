function [] = fc_segment_mri(flist, smask, tmask, mask, root, options, verbose)

%``function [] = fc_segment_mri(flist, smask, tmask, mask, root, options, verbose)``
%
%   Segments the voxels in smask based on their connectivity with tmask ROI.
%   Uses WTA to select the region the voxel is most correlated with.
%
%   Parameters:
%       --flist (str):
%           A .list file information on sessions bold runs and segmentation
%           files.
%       --smask (str):
%           A .names file for source mask definition.
%       --tmask (str):
%           A .names file for target mask roi definition
%       --mask (int | logical | vector, default []):
%           Either number of frames to omit or a mask of frames to use.
%       --root (str, default ''):
%           The root of the filename where results are to be saved. If no root
%           is specified, the root of the flist is used.
%       --options (str, default 'raw'):
%           Whether to use 'raw', 'absolute' or 'partial' correlations.
%       --verbose (str, default 'none'):
%           Whether to report the progress 'full', 'script', 'none'.
%
%   Output files:
%       - <root>_corr_roi
%           Correlations of each session with the target roi.
%
%       - <root>_segs
%           Segmentations for each session.
%
%       - <root>_scorr
%           Final segmentation and probabilities of segmentation for each
%           target ROI across the group.
%
%       - <root>_gseg
%           Final segmentation based on group mean correlations.
%
%   Notes:
%           Use the function to segment voxels specified in smask roi file based
%           on the correlation with ROI specifed in the tmask file. Each voxel
%           is assigned the code of the target ROI it most correlates with. For
%           more information see img_fcmri_segment() nimage method.
%
%   Examples:
%       ::
%
%           qunex fc_segment_mri \
%               --flist='con.list' \
%               --smask='thalamus.names' \
%               --tmask='yeo7.names' \
%               --mask=0 \
%               --root='Th-yeo-seg' \
%               --options='partial' \
%               --verbose='script'
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 7 || isempty(verbose),  verbose = 'none'; end
if nargin < 6 || isempty(options),  options = 'raw';  end
if nargin < 5, root = '';                             end
if nargin < 4, mask = [];                             end
if nargin < 3, error('ERROR: At least file list, source and target masks must be specified to run fc_segment_mri!'); end

if isempty(root)
    [ps, root, ext, v] = fileparts(root);
    root = fullfile(ps, root);
end

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


if script, fprintf('\n\nStarting ...'), end


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------------- make a list of all the files to process

if script, fprintf('\n ... listing files to process'), end

files = fopen(flist);
c = 0;
while feof(files) == 0
    s = fgetl(files);
    if ~isempty(strfind(s, 'session id:'))
        c = c + 1;
        [t, s] = strtok(s, ':');
        session(c).id = s(2:end);
        nf = 0;
    elseif ~isempty(strfind(s, 'roi:'))
        [t, s] = strtok(s, ':');
        session(c).roi = s(2:end);
        checkFile(session(c).roi);
    elseif ~isempty(strfind(s, 'file:'))
        nf = nf + 1;
        [t, s] = strtok(s, ':');
        session(c).files{nf} = s(2:end);
        checkFile(s(2:end));
    end
end


if script, fprintf(' ... done.'), end


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------- The main loop ... go through all the sessions

%   --- Get variables ready first

tROI = nimage.img_read_roi(tmask, session(1).roi);

nroi = length(tROI.roi.roinames);
nsessions = length(session);

template = tROI.zeroframes(nsessions);
template.data = template.image2D();

for n = 1:nroi
    corrs(n) = template;
end
segs = template.zeroframes(nsessions);
gseg = template.zeroframes(nroi+1);
gcorr = template.zeroframes(nroi+1);
gZ = template.zeroframes(nroi+1);

clear('template');
clear('tROI');

for s = 1:nsessions

    %   --- reading in image files
    if script, tic, end
    if script, fprintf('\n------\nProcessing %s', session(s).id), end
    if script, fprintf('\n... reading file(s) '), end

    roif = nimage(session(s).roi);
    tROI = nimage.img_read_roi(tmask, roif);
    sROI = nimage.img_read_roi(smask, roif);

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

    seg = img.img_fcmri_segment(sROI, tROI, options, method);
    seg = seg.unmaskimg();
    for r = 1:nroi
        corrs(r).data(:,s) = seg.data(:,r+1);
    end
    segs.data(:,s) = seg.data(:,1);

    if script, fprintf(' [%.1fs]\n', toc); end
end

if script, fprintf('\n------\nSaving results'), end

for r = 1:nroi
    fname = [root '_corr_' segs.roi.roinames{r}];
    if script, fprintf('\n... %s', fname), end
    corrs(r).img_saveimage(fname);

    f = fc_fisher(corrs(r).data);
    gcorr.data(:,r+1) = fc_fisherinv(mean(f,2));

    [h, p] = ttest(f, 0, 0.05, 'both', 2);
    Z = norminv((1-(p/2)), 0, 1);
    gZ.data(:,r+1) = Z .* sign(mean(f, 2));

    gseg.data(:,r+1) = sum(ismember(segs.data,r),2)./nsessions;
end

[G gcorr.data(:,1)] = max(gcorr.data(:,2:nroi+1),[],2);
gcorr.data(G==0) = 0;

[X gZ.data(:,1)] = max(gZ.data(:,2:nroi+1),[],2);
gZ.data(G==0) = 0;

[G gseg.data(:,1)] = max(gseg.data(:,2:nroi+1),[],2);
gseg.data(G==0) = 0;

if script, fprintf('\n... %s', [root '_gcorr']), end
gcorr.img_saveimage([root '_gcorr']);

if script, fprintf('\n... %s', [root '_gZ']), end
gZ.img_saveimage([root '_gZ']);

if script, fprintf('\n... %s', [root '_gseg']), end
gseg.img_saveimage([root '_gseg']);

if script, fprintf('\n... %s', [root '_segs']), end
segs.img_saveimage([root '_segs']);

if script, fprintf('\nDONE!\n\n'), end

end

%
%   ---- Auxilary functions
%

function [ok] = checkFile(filename)

ok = exist(filename, 'file');
if ~ok
    error('ERROR: File %s does not exists! Aborting processing!', filename);
end

end


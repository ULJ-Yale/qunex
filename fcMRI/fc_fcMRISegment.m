function [] = fc_fcMRISegment(flist, smask, tmask, mask, root, options, verbose)

%function [] = fc_fcMRISegment(flist, smask, tmask, verbose)
%
%	Segments the voxels in smask based on their connectivity with tmask ROI.
%   Uses WTA to select the region the voxel is most correlated with.
%
%   INPUT
%       flist   - A .list file information on subjects bold runs and segmentation files.
%       smask   - .names file for source mask definition
%       tmask   - .names file for target mask roi definition
%       mask    - Either number of frames to omit or a mask of frames to use [0].
%       root    - The root of the filename where results are to be saved [''].
%       options - Whether to use 'raw', 'absolute' or 'partial' correlations ['raw'].
%       verbose - Whether to report the progress 'full', 'script', 'none' ['none'].
%
%	RESULTS
%   <root>_corr_roi - correlations of each subject with the target roi
%   <root>_segs     - segmentations for each subject
%   <root>_scorr    - final segmentation and probabilities of segmentation for each target ROI across the group
%   <root>_gseg     - final segmentation based on group mean correlations
%
%   USE
%   Use the function to segment voxels specified in smask roi file based on the
%   correlation with ROI specifed in the tmask file. Each voxel is assigned the
%   code of the target ROI it most correlates with. For more information see
%   img_fcMRISegment() nimage method.
%
%   If no root is specified, the root of the flist is used.
%
%   EXAMPLE USE
%   >>> fc_fcMRISegment('con.list', 'thalamus.names', 'yeo7.names', 0, 'Th-yeo-seg', 'partial', 'script');
%
%   ---
% 	Written by Grega Repovš, 2010-08-07.
%
%   Changelog
%   2017-03-19 Grega Repovs
%            - Cleaned code, updated documentation
%   2018-06-25 Grega Repovs
%            - Replaced icdf with norminv to support Octave
%


if nargin < 7 || isempty(verbose),  verbose = 'none'; end
if nargin < 6 || isempty(options),  options = 'raw';  end
if nargin < 5, root = '';                             end
if nargin < 4, mask = [];                             end
if nargin < 3, error('ERROR: At least file list, source and target masks must be specified to run fc_fcMRISegment!'); end

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
    if ~isempty(strfind(s, 'subject id:'))
        c = c + 1;
        [t, s] = strtok(s, ':');
        subject(c).id = s(2:end);
        nf = 0;
    elseif ~isempty(strfind(s, 'roi:'))
        [t, s] = strtok(s, ':');
        subject(c).roi = s(2:end);
        checkFile(subject(c).roi);
    elseif ~isempty(strfind(s, 'file:'))
        nf = nf + 1;
        [t, s] = strtok(s, ':');
        subject(c).files{nf} = s(2:end);
        checkFile(s(2:end));
    end
end


if script, fprintf(' ... done.'), end


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------- The main loop ... go through all the subjects

%   --- Get variables ready first

tROI = nimage.img_ReadROI(tmask, subject(1).roi);

nroi = length(tROI.roi.roinames);
nsubjects = length(subject);

template = tROI.zeroframes(nsubjects);
template.data = template.image2D();

for n = 1:nroi
    corrs(n) = template;
end
segs = template.zeroframes(nsubjects);
gseg = template.zeroframes(nroi+1);
gcorr = template.zeroframes(nroi+1);
gZ = template.zeroframes(nroi+1);

clear('template');
clear('tROI');

for s = 1:nsubjects

    %   --- reading in image files
    if script, tic, end
	if script, fprintf('\n------\nProcessing %s', subject(s).id), end
	if script, fprintf('\n... reading file(s) '), end

    roif = nimage(subject(s).roi);
	tROI = nimage.img_ReadROI(tmask, roif);
	sROI = nimage.img_ReadROI(smask, roif);

	nfiles = length(subject(s).files);

	img = nimage(subject(s).files{1});
	if mask, img = img.sliceframes(mask); end
	if script, fprintf('1'), end
	if nfiles > 1
    	for n = 2:nfiles
    	    new = nimage(subject(s).files{n});
    	    if mask, new = new.sliceframes(mask); end
    	    img = [img new];
    	    if script, fprintf(', %d', n), end
        end
    end

    seg = img.img_fcMRISegment(sROI, tROI, options, method);
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

    f = fc_Fisher(corrs(r).data);
    gcorr.data(:,r+1) = fc_FisherInv(mean(f,2));

    [h, p] = ttest(f, 0, 0.05, 'both', 2);
    Z = norminv((1-(p/2)), 0, 1);
    gZ.data(:,r+1) = Z .* sign(mean(f, 2));

    gseg.data(:,r+1) = sum(ismember(segs.data,r),2)./nsubjects;
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


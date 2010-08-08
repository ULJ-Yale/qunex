function [] = fc_fcMRISegment(flist, smask, tmask, mask, root, options, verbose)

%function [] = fc_fcMRISegment(flist, smask, tmask, verbose)
%	
%	Segments the voxels in smask based on their connectivity with tmask ROI.
%   Uses WTA to select the region the voxel is most correlated with.
%	
%   flist   - file list with information on subjects bold runs and segmentation files
%   smask   - .names file for source mask definition
%   tmask   - .names file for target mask roi definition
%   mask    - either number of frames to omit or a mask of frames to use [0]
%   root    - the root of the filename where results are to be saved [flist]
%   options - whether to use raw or absolute correlations [raw]
%   verbose - whether to report the progress full, script, none [none]
%
%	output
%		: root_corr_roi - correlations of each subject with the target roi
%		: root_segs     - segmentations for each subject
%       : root_scorr    - final segmentation and probabilities of segmentation for each target ROI across the group
%       : root_gseg     - final segmentation based on group mean correlations
%	
% 	Created by Grega Repovš on 2010-08-07.
%
% 	Copyright (c) 2010. All rights reserved.


if nargin < 7
    verbose = none;
    if nargin < 6
        options = 'raw';
        if nargin < 5
            [ps, root, ext, v] = fileparts(root);
            root = fullfile(ps, root);
            if nargin < 4
                mask = [];
                if nargin < 3
                    error('ERROR: At least file list, source and target masks must be specified to run fc_fcMRISegment!');
                end
            end
        end
    end
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

tROI = gmrimage.mri_ReadROI(tmask, subject(1).roi);

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

clear('template');
clear('tROI');

for s = 1:nsubjects
    
    %   --- reading in image files
    if script, tic, end
	if script, fprintf('\n------\nProcessing %s', subject(s).id), end
	if script, fprintf('\n... reading file(s) '), end

    roif = gmrimage(subject(s).roi);
	tROI = gmrimage.mri_ReadROI(tmask, roif);
	sROI = gmrimage.mri_ReadROI(smask, roif);

	nfiles = length(subject(s).files);
	
	img = gmrimage(subject(s).files{1});
	if mask, img = img.sliceframes(mask); end
	if script, fprintf('1'), end
	if nfiles > 1
    	for n = 2:nfiles
    	    new = gmrimage(subject(s).files{n});
    	    if mask, new = new.sliceframes(mask); end
    	    img = [img new];
    	    if script, fprintf(', %d', n), end
        end
    end
    
    seg = img.mri_fcMRISegment(sROI, tROI, options, method);
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
    corrs(r).mri_saveimage(fname);
    gcorr.data(:,r+1) = fc_FisherInv(mean(fc_Fisher(corrs(r).data),2));
    gseg.data(:,r+1) = sum(ismember(segs.data,r),2)./nsubjects;
end

[G gcorr.data(:,1)] = max(gcorr.data(:,2:nroi+1),[],2);
gcorr.data(G==0) = 0;

[G gseg.data(:,1)] = max(gseg.data(:,2:nroi+1),[],2);
gseg.data(G==0) = 0;

if script, fprintf('\n... %s', [root '_gcorr']), end
gcorr.mri_saveimage([root '_gcorr']);

if script, fprintf('\n... %s', [root '_gseg']), end
gseg.mri_saveimage([root '_gseg']);

if script, fprintf('\n... %s', [root '_segs']), end
segs.mri_saveimage([root '_segs']);

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
    
    
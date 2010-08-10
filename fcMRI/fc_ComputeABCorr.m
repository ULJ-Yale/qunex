function [] = fc_ComputeABCorr(flist, smask, tmask, mask, root, options, verbose)

%function [] = fc_ComputeABCorr(flist, smask, tmask, verbose)
%	
%	Segments the voxels in smask based on their connectivity with tmask ROI.
%   Uses WTA to select the region the voxel is most correlated with.
%	
%   flist   - file list with information on subjects bold runs and segmentation files
%   smask   - .names file for source mask definition
%   tmask   - .names file for target mask roi definition
%   mask    - either number of frames to omit or a mask of frames to use [0]
%   root    - the root of the filename where results are to be saved [flist]
%   options - a list of:
%               : g - compute mean correlation across subjects (only makes sense with the same sROI for each subject)
%               : i - save individual subjects' results
%   verbose - whether to report the progress full, script, none [none]
%
%	output
%		: AB Correlation map for each listed subject
%	
% 	Created by Grega Repovš on 2010-08-09.
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
                    error('ERROR: At least file list, source and target masks must be specified to run fc_ComputeABCorr!');
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
nsubjects = length(subject);


if script, fprintf(' ... done.'), end


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------- The main loop ... go through all the subjects

%   --- Get variables ready first

sROI = gmrimage.mri_ReadROI(smask, subject(1).roi);
tROI = gmrimage.mri_ReadROI(tmask, subject(1).roi);

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

for s = 1:nsubjects
    
    %   --- reading in image files
    if script, tic, end
	if script, fprintf('\n------\nProcessing %s', subject(s).id), end
	if script, fprintf('\n... reading file(s) '), end

    % --- check if we need to load the subject region file

    if ~strcmp(subject(s).roi, 'none')
        if tROIload | sROIload
            roif = gmrimage(subject(s).roi);
        end
    end
    
    if tROIload
	    tROI = gmrimage.mri_ReadROI(tmask, roif);
    end
    if sROIload
	    sROI = gmrimage.mri_ReadROI(smask, roif);
    end

    % --- load bold data
    
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
    if script, fprintf('\n'), end
    
    ABCor = img.mri_ComputeABCor(sROI,tROI, method);
    ABCor = ABCor.unmaskimg; 
    
    if indiv
        ifile = [root '_' subject(s).id '_ABCor'];
        if script, fprintf('\n... saving %s\n', ifile); end
        ABCor.mri_saveimage(ifile);
    end
    
    if group
        if script, fprintf('\n... computing group results\n'); end
        gres.data = gres.data + fc_Fisher(ABCor.data);
        if tROIload
            gcnt.data = gcnt.data + tROI.image2D > 0;
        end
    end
    
    if script, fprintf('... done [%.1fs]\n', toc); end
end


if group
    if script, fprintf('\n=======\nSaving group results'), end
    
    if ~tROIload
        gcnt.data = (tROI.image2D > 0) .* nsubjects;
    end
    
    gres.data = gres.data ./ repmat(gcnt.data,0,nframes);
    gres.mri_saveimage([root '_group_ABCor_Fz']);
    gres.data = fc_FisherInv(gres.data);
    gres.mri_saveimage([root '_group_ABCor_r']);
end


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
    
    
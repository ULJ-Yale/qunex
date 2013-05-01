function [] = fc_ComputeABCorrKCA(flist, smask, tmask, nc, mask, root, options, verbose)

%function [] = fc_ComputeABCorrKCA(flist, smask, tmask, verbose)
%	
%	Segments the voxels in smask based on their connectivity pattern with tmask voxels.
%   Uses k-means to group voxels in smask.
%	
%   flist   - file list with information on subjects bold runs and segmentation files
%   smask   - .names file for source mask definition
%   tmask   - .names file for target mask roi definition
%   mask    - either number of frames to omit or a mask of frames to use [0]
%   root    - the root of the filename where results are to be saved [flist]
%   options - a list of:
%               : g - compute mean correlation across subjects (only makes sense with the same sROI for each subject)
%               : i - save individual subjects' results
%   nc      - number of clusters to make
%   verbose - whether to report the progress full, script, none [none]
%
%	output
%		: root_kn      - image with n clusters solution
%       : root_kc_cent - image with centroids for each of the clusters
%	
% 	Created by Grega Repovš on 2010-08-13.
%
% 	Copyright (c) 2010. All rights reserved.

if nargin < 8
    verbose = none;
    if nargin < 7
        options = 'raw';
        if nargin < 6
            [ps, root, ext, v] = fileparts(root);
            root = fullfile(ps, root);
            if nargin < 5
                mask = [];
                if nargin < 4
                    error('ERROR: At least file list, source and target masks and number of clusters must be specified to run fc_ComputeABCorrKCA!');
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
    if script, fprintf('\n... computing ABCor'), end
    
    ABCor = img.mri_ComputeABCor(sROI,tROI, method);
    
    if indiv
        data = fc_Fisher(ABCor.image2D');
        CA = sROI.maskimg(sROI);
        Cent = tROI.maskimg(tROI);
        
        for c = 1:length(nc)
            k = nc(c);

            if script, fprintf('\n... computing %d iCA solution', k), end
            ifile = [root '_' subject(s).id '_k' num2str(k)];
            
            Cent = Cent.zeroframes(k);
            [CA.data Cent.data] = kmeans(data, k, 'distance', 'correlation', 'replicates', 10);
            Cent.data = Cent.data';
        
            if script, fprintf('\n... saving %s\n', ifile); end
            CA.mri_saveimage(ifile);
            Cent.mri_saveimage([ifile '_cent']);
        end
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
    if script, fprintf('\n=======\nComputing group CA solution'), end
    
    if ~tROIload
        gcnt.data = (tROI.image2D > 0) .* nsubjects;
    end
    
    gres.data = gres.data ./ repmat(gcnt.data,1,nframes);
    CA = sROI.maskimg(sROI);
    Cent = tROI.maskimg(sROI);
    
    for c = 1:length(nc)
        k = nc(c);
        if script, fprintf(' k: %d', k), end
        
        Cent = Cent.zeroframes(k);
        [CA.data Cent.data] = kmeans(gres.data', k, 'distance', 'correlation', 'replicates', 10);
        Cent.data = Cent.data';
    
        if script, fprintf('\n... saving %s\n', ifile); end
        CA.mri_saveimage([root '_group_k' num2str(k)]);
        Cent.mri_saveimage([root '_group_k' num2str(k) '_cent']);
    end
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
    
    
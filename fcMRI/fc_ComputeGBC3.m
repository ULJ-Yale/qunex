function [] = fc_ComputeGBC3(flist, command, mask, verbose, target, targetf, rsmooth, rdilate)

%	
%	fc_ComputeGBC
%	
%	Computes GBC maps for individuals as well as group maps.
%	
%	flist   	- conc-like style list of subject image files or conc files: 
%                  subject id:<subject_id>
%                  roi:<path to the individual's ROI file>
%                  file:<path to bold files - one per line>
%   command     - the type of gbc to run: mFz, aFz, pFz, nFz, aD, pD, nD
%                  <type of gbc>:<threshold>|<type of gbc>:<threshold> ...
%	mask		- an array mask defining which frames to use (1) and which not (0)
%	verbose		- report what is going on
%   target      - array of ROI codes that define target ROI [default: FreeSurfer cortex codes]
%	targetf		- target folder for results
%   rmsooth     - radius for smoothing (no smoothing if empty)
%   rdilate     - radius for dilating mask (no dilation if empty)
%	
% 	Created by Grega Repovš on 2009-11-04.
% 	Modified by Grega Repovš on 2010-11-16.
% 	Modified by Grega Repovs on 2010-11-22.
% 	Modified by Grega Repovs on 2010-12-01.
%   - added in script smoothing and dilation
%
% 	Copyright (c) 2009. All rights reserved.


fprintf('\n\nStarting ...');

if nargin < 8
    rdilate = []
    if nargin < 7
        rsmooth = []
        if nargin < 6
        	targetf = '';
        	if nargin < 5
           		target = [];
           	 	if nargin < 4
                	verbose = false;
                	if nargin < 3
                	    mask = [];
                	end
            	end
            end
        end
    end
end

if isempty(target)
	target = [3 8 9 10 11 12 13 16 17 18 19 20 26 27 28 42 47 48 49 50 51 52 53 54 55 56 58 59 60 96 97];
end


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------------- make a list of all the files to process

fprintf('\n ... listing files to process');

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


fprintf(' ... done.');


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------- The main loop ... go through all the subjects

%   --- Get variables ready first

template  = gmrimage(subject(c).roi);
nvoxels   = template.voxels;
nsubjects = length(subject);
ncommands = sum(ismember(command, '|')) + 1;

template = template.zeroframes(nsubjects);
for n = 1:ncommands
    gbc(n) = template;
end
clear('template');

for s = 1:nsubjects
    
    %   --- reading in image files
    tic; 
	fprintf('\n ... processing %s', subject(s).id);
	fprintf('\n     ... reading image file(s) ');

	y = [];

	nfiles = length(subject(s).files);
	
	img = gmrimage(subject(s).files{1});
	if mask, img = img.sliceframes(mask); end
	fprintf('1');
	if nfiles > 1
    	for n = 2:nfiles
    	    new = gmrimage(subject(s).files{n});
    	    if mask, new = new.sliceframes(mask); end
    	    img = [img new];
    	    fprintf(', %d', n);
        end
    end
    
    imask = gmrimage(subject(s).roi);
    imask = imask.ismember(target);
    
    if rsmooth
        limit = ~isempty(rdilate);
        img = img.mri_Smooth3DMasked(imask, rsmooth, limit, verbose);
    end    

    if rdilate
        imask = imask.mri_GrowROI(rdilate);
    end
    
    img = img.maskimg(imask);
    [img commands] = img.mri_ComputeGBC(command, [], [], verbose);
    img = img.unmaskimg();
    
    for n = 1:ncommands
        gbc(n).data(:,s) = img.data(:,n);
    end
    fprintf(' [%.1fs]\n', toc);
end

[ps, root, ext, v] = fileparts(flist);

for c = 1:ncommands
    fname = [root '_gbc_' commands(c).command '_' num2str(commands(c).parameter)];
    gbc(c).mri_saveimage(fullfile(targetf,fname));
end

%
%   ---- Auxilary functions
%

function [ok] = checkFile(filename)

ok = exist(filename, 'file');
if ~ok
    fprintf('ERROR: File %s does not exists! Aborting processing!', filename);
    error;
end

    
    
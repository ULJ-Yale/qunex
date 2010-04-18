function [] = fc_ComputeGBC3(flist, command, mask, verbose)

%	
%	fc_ComputeGBC
%	
%	Computes GBC maps for individuals as well as group maps.
%	
%	flist   	- conc style list of subject image files or conc files, header row, one subject per line
%	mask		- an array mask defining which frames to use (1) and which not (0)
%	options		- a string defining which subject files to save
%       - undefined
%	tagetf		- the folder to save images in
%
%	It saves group files:
%		-unspecified
%	
% 	Created by Grega Repovš on 2009-11-04.
%
% 	Copyright (c) 2009. All rights reserved.

target = [3 8 9 10 11 12 13 16 17 18 19 20 26 27 28 42 47 48 49 50 51 52 53 54 55 56 58 59 60 96 97];
thr = 0.17;
fprintf('\n\nStarting ...');

if nargin < 4
    verbose = false;
    if nargin < 3
        mask = [];
    end
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
	fprintf('\n ... processing %s', subject(n).id);
	fprintf('\n     ... reading image file(s) ');

	y = [];

	nfiles = length(subject(s).files);
	
	img = gmrimage(subject(s).files{1});
	img = img.sliceframes(mask);
	fprintf('1');
	if nfiles > 1
    	for n = 2:nfiles
    	    new = gmrimage(subject(s).files{n});
    	    new = new.sliceframes(mask);
    	    img = [img new];
    	    fprintf(', %d', n);
        end
    end
    
    imask = gmrimage(subject(s).roi);
    imask = imask.ismember(target);
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
    gbc(c).mri_saveimage(fname);
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

    
    
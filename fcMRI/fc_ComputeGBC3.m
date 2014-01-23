function [] = fc_ComputeGBC3(flist, command, mask, verbose, target, targetf, rsmooth, rdilate, ignore)

%function [] = fc_ComputeGBC3(flist, command, mask, verbose, target, targetf, rsmooth, rdilate, ignore)
%
%	Computes GBC maps for individuals as well as group maps.
%
%	flist   	- conc-like style list of subject image files or conc files:
%                  subject id:<subject_id>
%                  roi:<path to the individual's ROI file>
%                  file:<path to bold files - one per line>
%   command     - the type of gbc to run: mFz, aFz, pFz, nFz, aD, pD, nD, mFzp, aFzp, ...
%                  <type of gbc>:<parameter>|<type of gbc>:<parameter> ...
%	mask		- an array mask defining which frames to use (1) and which not (0)
%	verbose		- report what is going on
%   target      - array of ROI codes that define target ROI [default: FreeSurfer cortex codes]
%	targetf		- target folder for results
%   rsmooth     - radius for smoothing (no smoothing if empty)
%   rdilate     - radius for dilating mask (no dilation if empty)
%   ignore      - the column in *_scrub.txt file that matches bold file to be used for ignore mask []
%
% 	Created by Grega Repovš on 2009-11-04.
% 	Modified by Grega Repovš on 2010-11-16.
% 	Modified by Grega Repovs on 2010-11-22.
% 	Modified by Grega Repovs on 2010-12-01.
%   - added in script smoothing and dilation
%   Modified by Grega Repovs on 2014-01-22
%   - took care of commands that return mulitiple volumes (e.g. mFzp)
%
% 	Copyright (c) 2009. All rights reserved.


fprintf('\n\nStarting ...');

if nargin < 9, ignore = [];     end
if nargin < 8, rdilate = [];    end
if nargin < 7, rsmooth = [];    end
if nargin < 6, targetf = '';    end
if nargin < 5, target = [];     end
if nargin < 4, verbose = false; end
if nargin < 3, mask = [];       end

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
desc      = parseCommand(command);
nvolumes  = length(ext);

template = template.zeroframes(nsubjects);
for n = 1:nvolumes
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

    fprintf('1');
	if ~isempty(mask),   img = img.sliceframes(mask); end
    if ~isempty(ignore), img = scrub(img, ignore); end

	if nfiles > 1
    	for n = 2:nfiles
    	    new = gmrimage(subject(s).files{n});
            fprintf(', %d', n);
    	    if ~isempty(mask),   new = new.sliceframes(mask); end
            if ~isempty(ignore), new = scrub(new, ignore); end
    	    img = [img new];
        end
    end

    imask = gmrimage(subject(s).roi);
    imask = imask.ismember(target);

    if rsmooth
        limit = isempty(rdilate);
        img = img.mri_Smooth3DMasked(imask, rsmooth, limit, verbose);
    end

    if rdilate
        imask = imask.mri_GrowROI(rdilate);
    end

    img = img.maskimg(imask);
    [img commands] = img.mri_ComputeGBC(command, [], [], verbose);
    img = img.unmaskimg();

    for n = 1:nvolumes
        gbc(n).data(:,s) = img.data(:,n);
    end
    fprintf(' [%.1fs]\n', toc);
end

[ps, root, ext] = fileparts(flist);

for c = 1:nvolumes
    fname = [root '_gbc_' desc{c})];
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

%   ---- Do the scrub

function [img] = scrub(img, ignore)

scol = ismember(img.scrub_hdr, ignore);
if sum(scol) == 1;
    mask = img.scrub(:,scol)';
    img  = img.sliceframes(mask==0);
    fprintf(' (scrubbed %d frames)', sum(mask));
else
    fprintf('\nWARNING: Field %s not present in scrubbing data, no frames scrubbed!', ignore);
end


%   ---- Parse the command

function [ext] = parseCommand(s)

    ext = {};

    a = splitby(s,'|');
    for n = 1:length(a)
        b = splitby(a{n}, ':');

        com = b{1};
        par = str2num(b{2});

        pre = com(1);
        pos = com(end);

        if ismember(pos, 'ps')
            if pos == 'p'
                sstep = 100 / par;
                parameter = floor([[1:sstep:100]', [1:sstep:100]'+(sstep-1)]);
                for p = 1:par
                    ext(end+1) = [com '_' num2str(parameter(p,1)) '_' num2str(parameter(p,2))];
                end
            else
                if ismember(pre, 'ap')
                    sv = 0;
                    ev = 1;
                    al = 1;
                elseif pre == 'm'
                    sv = -1;
                    ev = 1;
                    al = 1;
                else
                    sv = -1;
                    ev = 0;
                    al = 0;
                end
                sstep = (ev-sv) / par;
                parameter = [sv:sstep:ev];
                for p = 1:par
                    ext(end+1) = [com '_' num2str(parameter(p)) '_' num2str(parameter(p+1))];
                end

            end
        else
            ext(end+1) = [com '_' num2str(par)];
        end
    end
end

function [out] = splitby(s, d)
    c = 0;
    while length(s) >=1
        c = c+1;
        [t, s] = strtok(s, d);
        if length(s) > 1, s = s(2:end); end
        out{c} = t;
    end
end

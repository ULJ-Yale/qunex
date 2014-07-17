function [] = fc_ComputeGBCd(flist, command, roi, rcodes, nbands, mask, verbose, target, targetf, rsmooth, rdilate, ignore, time, method, weights, criterium)

%function [] = fc_ComputeGBCd(flist, command, roi, rcodes, nbands, mask, verbose, target, targetf, rsmooth, rdilate, ignore, time, method, weights, criterium)
%
%	Computes GBC averages for each specified ROI for n bands defined as distance from ROI.
%
%	flist   	- conc-like style list of subject image files or conc files:
%                  subject id:<subject_id>
%                  roi:<path to the individual's ROI file>
%                  file:<path to bold files - one per line>
%   command     - the type of gbc to run: mFz, aFz, pFz, nFz, aD, pD, nD, mFzp, aFzp, ...
%                  <type of gbc>:<parameter>|<type of gbc>:<parameter> ...
%   roi         - roi names file
%   rcodes      - codes of regions from roi file to compute GBC for (all if not provided or left empty)
%   nbands      - number of distance bands to compute GBC for
%	mask		- an array mask defining which frames to use (1) and which not (0)
%	verbose		- report what is going on
%   target      - array of ROI codes that define target ROI [default: FreeSurfer cortex codes]
%	targetf		- target folder for results
%   rsmooth     - radius for smoothing (no smoothing if empty)
%   rdilate     - radius for dilating mask (no dilation if empty)
%   ignore      - the column in *_scrub.txt file that matches bold file to be used for ignore mask []
%   time        - whether to time the processing
%
%   --- Extract ROI arguments
%
%       method  - method name [mean]
%          'mean'       - average value of the ROI
%          'pca'        - first eigenvariate of the ROI
%          'threshold'  - average of all voxels above threshold
%          'maxn'       - average of highest n voxels
%          'weighted'   - weighted average across ROI voxels
%       weights         - image file with weights to use []
%       criterium       - threshold or number of voxels to extract []
%
%   --- History
%
% 	Created by Grega Repovš on 2009-11-04.
% 	Modified by Grega Repovš on 2010-11-16.
% 	Modified by Grega Repovs on 2010-11-22.
% 	Modified by Grega Repovs on 2010-12-01.
%   - added in script smoothing and dilation
%   Modified by Grega Repovs on 2014-01-22
%   - took care of commands that return mulitiple volumes (e.g. mFzp)
%   Modified by Grega Repovs on 2014-02-16
%   - forked from fcComputeGBC3 to do distance based bands
%
% 	Copyright (c) 2009. All rights reserved.


fprintf('\n\nStarting ...');

if nargin < 13, time = true;    end
if nargin < 12, ignore = [];    end
if nargin < 11, rdilate = [];   end
if nargin < 10, rsmooth = [];   end
if nargin < 9, targetf = '';    end
if nargin < 8, target = [];     end
if nargin < 7, verbose = false; end
if nargin < 6, mask = [];       end
if nargin < 5, nbands = [];     end
if nargin < 4, rcodes = [];     end
if nargin < 3, error('\nERROR: At east first three arguments need to be provided to run fc_ComputeGBCd!\n'), end

if isempty(ignore)
    ignore = 'usevec';
end
if isempty(target)
	target = [3 8 9 10 11 12 13 16 17 18 19 20 26 27 28 42 47 48 49 50 51 52 53 54 55 56 58 59 60 96 97];
end

commands = regexp(command, '\|', 'split');

[ps, root, ext] = fileparts(flist);
fout = fopen([targetf '/' root '_GBCd.tab'], 'w');
fprintf(fout, 'subject\tcommand\troi\tband\tvalue');

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

nsubjects = length(subject);

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
    if ~isempty(ignore), img = img.mri_Scrub(ignore); end

	if nfiles > 1
    	for n = 2:nfiles
    	    new = gmrimage(subject(s).files{n});
            fprintf(', %d', n);
    	    if ~isempty(mask),   new = new.sliceframes(mask); end
            if ~isempty(ignore), new = new.mri_Scrub(ignore); end
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

    roiimg = gmrimage.mri_ReadROI(roi, subject(s).roi);

    [res, roiinfo, rdata] = img.mri_ComputeGBCd(command, roiimg, rcodes, nbands, [], imask);

    data.gbcd(s).gbc = res;
    data.gbcd(s).roiinfo = roiinfo;
    data.gbcd(s).rdata = rdata;

    %  'subject\tcommand\troi\tband\tvalue'

    for nc = 1:size(res,3)
        for nr = 1:size(res,2)
            for nb = 1:size(res,1)
                fprintf(fout, '\n%s\t%s\t%s\t%d\t%.6f', subject(s).id, commands{nc}, roiinfo.roinames{nr}, nb, res(nb, nr, nc));
            end
        end
    end

    fprintf(' [%.1fs]\n', toc);
end

data.roifile  = roi;
data.rcodes   = rcodes;
data.subjects = subject;

fclose(fout);
save([targetf '/' root '_GBCd'], data);




%
%   ---- Auxilary functions
%

function [ok] = checkFile(filename)

ok = exist(filename, 'file');
if ~ok
    error('ERROR: File %s does not exists! Aborting processing!', filename);
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
                    ext{end+1} = [com '_' num2str(parameter(p,1)) '_' num2str(parameter(p,2))];
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
            ext{end+1} = [com '_' num2str(par)];
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


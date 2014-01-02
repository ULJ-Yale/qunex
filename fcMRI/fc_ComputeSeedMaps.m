function [] = fc_ComputeSeedMaps(flist, roiinfo, inmask, event, targetf, method, ignore)

%function [] = fc_ComputeSeedMaps(flist, roiinfo, inmask, event, targetf, method, ignore)
%
%	fc_ComputeSeedMaps
%
%	A memory optimised version of the script.
%
%	Computes seed based correlations maps for individuals as well as group maps.
%
%	flist   	- conc style list of subject image files or conc files, header row, one subject per line
%	roif		- 4dfp image file with ROI
%	roinfile	- file with region names, one region per line in format: "value\tname"
%	inmask		- an array mask defining which frames to use (1) and which not (0)
%	event		- a string describing which events to extract timeseries for and the frame offset at start and end ('title1:event1,event2:2:2|title2:event3,event4:1:2')
%	tagetf		- the folder to save images in
%   method      - method for extracting timeseries - mean, pca [mean]
%   ignore      - do we omit frames to be ignored (
%               -> no:    do not ignore any additional frames
%               -> use:   ignore frames as marked in the use field of the bold file
%               -> event: ignore frames as marked in .fidl file
%               -> other: the column in *_scrub.txt file that matches bold file to be used for ignore mask%
%
%	It saves group files:
%		_group_Fz	- average Fz over all the subjects
%		_group_r	- average Fz converted back to Pearson r
%		_group_Z	- p values converted to Z scores based on t-test testing if Fz over subject differ significantly from 0 (two-tailed)
%
% 	Created by Grega Repovš on 2008-02-07.
%   2008-01-23 Adjusted for a different file list format and an additional ROI mask. [Grega Repovš]
%   2011-11-10 Changed to make use of gmrimage and allow ignoring of bad frames. [Grega Repovš]
%   2013-12-28 Moved to a more general name, added block event extraction and use of 'use' info. [Grega Repovš]
%
% 	Copyright (c) 2008. All rights reserved.


if nargin < 7 ignore  = []; end
if nargin < 6 method  = []; end
if nargin < 5 targetf = []; end
if nargin < 4 event   = []; end
if nargin < 3 inmask  = []; end
if nargin < 2 error('ERROR: At least boldlist and ROI .names file have to be specified!'); end


if isempty(targetf) targetf = '.'; end
if isempty(method)  method = 'mean'; end
if isempty(ignore)  ignore = 'use'; end
if ~ischar(ignore)  error('ERROR: Argument ignore has to be a string specifying whether and what to ignore!'); end

fignore = 'ignore';
eventbased = false;
if isa(inmask, 'char')
    eventbased = true;
    if strcmp(ignore, 'fidl')
        fignore = 'ignore';
    else
        fignore = 'no';
    end
end

% ----- Check if the files are there!

go = true;

fprintf('\n\nChecking ...\n');
go = go & g_CheckFile(flist, 'image file list', 'error');
go = go & g_CheckFile(roiinfo, 'ROI definition file', 'error');
g_CheckFolder(targetf, 'results folder');

if ~go
	fprintf('ERROR: Some files were not found. Please check the paths and start again!\n\n');
	return
end

% ---- list name

[fpathstr, fname, fext] = fileparts(flist);

lname = strrep(fname, '.list', '');
lname = strrep(lname, '.conc', '');
lname = strrep(lname, '.4dfp', '');
lname = strrep(lname, '.img', '');


% ---- Start

fprintf('\n\nStarting ...');

%   ------------------------------------------------------------------------------------------
%                                                                      parse events if present

if isempty(event)
    ana.name = '';
    fstring  = '';
else
    [ana fstring] = parseEvent(event);
end
nana = length(ana);


%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf('\n ... listing files to process');

subject = g_ReadSubjectsList(flist);
nsub = length(subject);

fprintf(' ... done.');


%   ------------------------------------------------------------------------------------------
%                                                The main loop ... go through all the subjects


for n = 1:nsub

    fprintf('\n ... processing %s', subject(n).id);

    % ---> reading ROI file

	fprintf('\n     ... creating ROI mask');

	if isfield(subject(n), 'roi')
	    sroifile = subject(n).roi;
	else
	    sroifile = [];
    end

	roi  = gmrimage.mri_ReadROI(roiinfo, sroifile);
    nroi = length(roi.roi.roinames);


	% ---> reading image files

	fprintf('\n     ... reading image file(s)');

	y = gmrimage(subject(n).files{1});
	for f = 2:length(subject(n).files)
	    y = [y gmrimage(subject(n).files{f})];
    end
    y = y.correlize;

    fprintf(' ... %d frames read, done.', y.frames);

    % ---> creating task mask

    if isempty(fstring)
        finfo = [];
    else
        finfo = g_CreateTaskRegressors(subject(n).fidl, y.runframes, fstring, fignore);
        matrix = [];
        for r = 1:length(finfo)
            matrix = [matrix; finfo(r).matrix];
        end
    end

    % ---> creating timeseries mask

    fprintf('\n     ... computing seed maps ');

    for a = 1:nana

        % --- if no events take all, otherwise take the mask of this regressor
        if isempty(finfo)
            mask = ones(1, y.frames);
        else
            mask = matrix(:,a)';
        end

        % --- if we have a long inmask, use it
        if length(inmask) > 1
            mask = mask & inmask;
        end

        % --- ignore frames that are marked not to be used
        mask = mask & y.use;

        % --- if we need to omit n starting frames - do it
        if length(inmask) == 1
            if length(y.runframes) == 1
                mask(1:inmask) = false;
            else
                for o = cumsum([0 y.runframes(1:end-1)])
                    mask(o+1:o+inmask) = false;
                end
            end
        end

        % --- we might add other frames to be ignored!


        % ---> slice up the timeseries, extract data

        t  = y.sliceframes(mask);
        ts = t.mri_ExtractROI(roi, [], method);
        pr = t.mri_ComputeCorrelations(ts');

        % ------> Embedd results

        nroi = length(roi.roi.roinames);
        for r = 1:nroi

            % -------> Create data files if it is the first run

            if n == 1
                ana(a).group(r).Fz = roi.zeroframes(nsub);
                ana(a).group(r).roi = roi.roi.roinames{r};
            end

            % -------> Embedd data

            ana(a).group(r).Fz.data(:,n) = fc_Fisher(pr.data(:,r));

	   end
    end
end


%   ---------------------------------------------
%   --- And now group results

fprintf('\n\n... computing group results');

for s = 1:nsub
    extra(s).key = ['subject ' int2str(s)];
    extra(s).value = subject(s).id;
end

for a = 1:nana
    fprintf('\n -> %s', ana(a).name);

    for r = 1:nroi



    	fprintf('\n    ... for region %s', ana(a).group(r).roi);

        [p Z M] = ana(a).group(r).Fz.mri_TTestZero();
    	pr = M.mri_FisherInv();

    	fprintf('... saving ...');
        if isempty(ana(a).name)
            tname = lname;
        else
            tname = [lname '_' ana(a).name];
        end

        pr.mri_saveimage([targetf '/' tname '_' ana(a).group(r).roi '_group_r'], extra);                  fprintf(' r');
        M.mri_saveimage([targetf '/' tname '_' ana(a).group(r).roi '_group_Fz'], extra);                  fprintf(' Fz');
        Z.mri_saveimage([targetf '/' tname '_' ana(a).group(r).roi '_group_Z'], extra);                   fprintf(' Z');
        ana(a).group(r).Fz.mri_saveimage([targetf '/' tname '_' ana(a).group(r).roi '_all_Fz'], extra);   fprintf(' all Fz');

    	fprintf(' ... done.');

    end
end



fprintf('\n\n FINISHED!\n\n');


%   ------------------------------------------------------------------------------------------
%                                                                         event string parsing

function [ana, fstring] = parseEvent(event)

    smaps   = regexp(event, '\|', 'split');
    nsmaps  = length(smaps);
    fstring = '';
    for m = 1:nsmaps
        fields = regexp(smaps{m}, ':', 'split');
        ana(m).name     = fields{1};
        % ana(m).events   = regexp(fields{2}, ',', 'split');
        % ana(m).startoff = str2num(fields{3})
        % ana(m).endoff   = str2num(fields{4});
        fstring         = [fstring fields{2} ':block:' fields{3} ':' fields{4}];
        if m < nsmaps, fstring = [fstring '|']; end
    end




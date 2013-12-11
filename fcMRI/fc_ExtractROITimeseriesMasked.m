function [] = fc_ExtractROITimeseriesMasked(flist, roiinfo, inmask, targetf, options, method, ignore, rcodes)

%function [] = fc_ExtractROITimeseriesMasked(flist, roiinfo, inmask, targetf, options, method, ignore, rcodes)
%
%	fc_ExtractROITimeseriesMasked
%
%	Extracts and saves region timeseries defined by provided roiinfo file
%
%	flist   	- conc style list of subject image files or conc files, header row, one subject per line
%   inmask      - per run mask information, number of frames to skip or a vector of frames to keep (1) and reject (0)
%               - or a string with definition used to extract event-defined timepoints only
%	roiinfo	    - file with region names, one region per line in format: "value|group roi values|subject roi values"
%	tagetf		- the matlab file to save timeseries in
%   options     - options for alternative output: t - create a tab delimited text file, m - create a matlab file (default)
%   method      - method for extracting timeseries - mean, pca [mean]
%   ignore      - do we omit frames to be ignored (
%               -> no:     do not ignore any additional frames
%               -> event:  ignore frames as marked in .fidl file
%               -> other:  the column in *_scrub.txt file that matches bold file to be used for ignore mask
%               -> usevec: as specified in the use vector
%
%
% 	Created by Grega Repovš on 2009-06-25.
%   2008-01-23 - Adjusted for a different file list format and an additional ROI mask
%   2011-02-11 - Rewritten to use gmrimage objects and ability for event defined masks
%   2012-07-30 - Added option to omit frames specified to be ignored in the fidl file
%   2013-12-11 - Added ignore as specified in use vector and rcodes to specify ROI.
%
% 	Copyright (c) 2008. All rights reserved.
%

if nargin < 8
    rcodes = [];
    if nargin < 7
        ignore = [];
        if nargin < 6
            method = 'mean';
            if nargin < 5
                options = 'm';
            end
        end
    end
end

if isempty(options)
    options = 'm';
end
if isempty(method)
    method = 'mean';
end

if isempty(ignore)
    ignore = 'no';
end

if ~ischar(ignore)
    error('ERROR: Argument ignore has to be a string specifying whether and what to ignore!');
end

eventbased = false;
if isa(inmask, 'char')
    eventbased = true;
    if strcmp(ignore, 'fidl')
        fignore = 'ignore';
    else
        fignore = 'no';
    end
end

fprintf('\n\nStarting ...');

%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf('\n ... listing files to process');

subject = g_ReadSubjectsList(flist);
nsub = length(subject);

fprintf(' ... done.');

%   ------------------------------------------------------------------------------------------
%                                                         set up datastructure to save results

for n = 1:nsub
    data.subjects{n} = subject(n).id;
    data.timeseries{n} = [];
end


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

	roi = gmrimage.mri_ReadROI(roiinfo, sroifile);


	% ---> reading image files

	fprintf('\n     ... reading image file(s)');

	y = gmrimage(subject(n).files{1});
	for f = 2:length(subject(n).files)
	    y = [y gmrimage(subject(n).files{f})];
    end

    fprintf(' ... %d frames read, done.', y.frames);

	% ---> creating timeseries mask

	if eventbased
	    mask = [];
	    if isfield(subject(n), 'fidl')
            if subject(n).fidl
                mask = g_CreateTaskRegressors(subject(n).fidl, y.runframes, inmask, fignore);
    	        nmask = [];
                for r = 1:length(mask)
                    nmask = [nmask; sum(mask(r).matrix,2)>0];
                end
                mask = nmask;
            end
        end
    else
        mask = inmask;
    end

    % ---> slicing image

    if length(mask) == 1
        y = y.sliceframes(mask, 'perrun');
    else
        y = y.sliceframes(mask);                % this might need to be changed to allow for per run timeseries masks
    end

    % ---> remove additional frames to be ignored

    if ~ismember(ignore, {'no', 'fidl'})
        y = y.mri_Scrub(ignore);
    end

	% ---> extracting timeseries

	fprintf('\n     ... extracting timeseries ');

    data.timeseries{n} = y.mri_ExtractROI(roi, [], method, rcodes);
    data.n_roi_vox{n}  = roi.roi.nvox;

    fprintf(' ... done!');

end

data.roinames  = roi.roi.roinames;
data.roicodes1 = roi.roi.roicodes1;
data.roicodes2 = roi.roi.roicodes2;



%   -------------------------------------------------------------
%                                                       save data

fprintf('... saving ...');

if ismember('m', options)
    save(targetf, 'data');
end

if ismember('t', options)

    % ---> open file and print header

    [fout message] = fopen([targetf '.txt'],'w');
    fprintf(fout, 'subject');
    for ir = 1:length(data.roinames)
        fprintf(fout, '\t%s', data.roinames{ir});
    end

    % ---> print data

    for is = 1:nsub
        ts = data.timeseries{is};
        tslen = size(ts,1);
        for it = 1:tslen
            fprintf(fout, '\n%s', data.subjects{is});
            fprintf(fout, '\t%.5f', ts(it,:));
        end
    end

    % -- close file

    fclose(fout);
end

fprintf('\n\n FINISHED!\n\n');





function [] = fc_ExtractROITimeseriesMasked(flist, roiinfo, inmask, targetf, options, method)

%function [] = fc_ExtractROITimeseriesMasked(flist, roiinfo, inmask, targetf, options, method)
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
%
%	
% 	Created by Grega Repovš on 2009-06-25.
%   Adjusted for a different file list format and an additional ROI mask - 2008-01-23
%   Rewritten to use gmrimage objects and ability for event defined masks - 2011-02-11
% 	Copyright (c) 2008. All rights reserved.

if nargin < 6
    method = 'mean';
    if nargin < 5
        options = 'm';
    end
end

eventbased = false;
if isa(inmask, 'char')
    eventbased = true;
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
	
	if isset(subject(n).roi)
	    sroifile = subject(n).roi;
	else
	    sroifile = [];
    end
	
	roi = mri_ReadROI(roiinfo, sroifile);

	
	% ---> reading image files
	
	fprintf('\n     ... reading image file(s)');
	
	y = gmrimage(subject(n).files{1});
	for f = 1:length(subject(n).files)
	    y = [y gmrimage(subject(n).files{f})];
    end
    
    fprintf(' ... %d frames read, done.', y.frames);
	
	% ---> creating timeseries mask 
	
	if eventbased
	    mask = [];
	    if isset(subject(n).fidl)
	        mask = g_CreateTaskRegressors(subject(n).fidl, y.runframes, inmask);
	        nmask = [];
	        for r = 1:length(mask)
	            nmask = [nmask; sum(mask(r).matrix,2)>0];
            end
            mask = nmask;
        end
    else
        mask = inmask;
    end
    
    % ---> slicing image

    y = y.sliceframes(inmask, 'perrun');        % this might need to be changed to allow for overall masks
	            
	% ---> extracting timeseries
	
	fprintf('\n     ... extracting timeseries ');
	
    data.timeseries{n} = y.mri_ExtractROI(roi, [], method);
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
    for ir = 1:nroi
        fprintf(fout, '\t%s', roiname{ir});
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



function [] = fc_ComputeSeedMapsMultiple(flist, roiinfo, inmask, options, targetf, method, ignore)

%function [] = fc_ComputeSeedMapsMultiple(flist, roiinfo, inmask, options, targetf, method, ignore)
%	
%	fc_ComputeSeedMapsMultiple
%
%	A memory optimised version of the script.
%	
%	Computes seed based correlations maps for individuals as well as group maps.
%	
%	flist   	- conc style list of subject image files or conc files, header row, one subject per line
%	roif		- 4dfp image file with ROI
%	roinfile	- file with region names, one region per line in format: "value\tname"
%	inmask		- an array mask defining which frames to use (1) and which not (0)
%	options		- a string defining which subject files to save
%		r		- save map of correlations
%		f		- save map of Fisher z values
%		z		- save map of Z scores
%	tagetf		- the folder to save images in
%   method      - method for extracting timeseries - mean, pca [mean]
%   ignore      - do we omit frames to be ignored (
%               -> no:    do not ignore any additional frames
%               -> event: ignore frames as marked in .fidl file
%               -> other: the column in *_scrub.txt file that matches bold file to be used for ignore mask
%
%	It saves group files:
%		_group_Fz	- average Fz over all the subjects
%		_group_r	- average Fz converted back to Pearson r
%		_group_Z	- p values converted to Z scores based on t-test testing if Fz over subject differ significantly from 0 (two-tailed)
%	
% 	Created by Grega Repovš on 2008-02-07.
%   2008-01-23 Adjusted for a different file list format and an additional ROI mask [Grega Repovš]
%   2011-11-10 Changed to make use of gmrimage and allow ignoring of bad frames [Grega Repovš]
% 	Copyright (c) 2008. All rights reserved.


if nargin < 7
    ignore = [];
    if nargin < 6
        method = [];
        if nargin < 5
            targetf = [];
            if nargin < 4
                options = [];
                if nargin < 3
                    inmask = [];
                    if nargin < 2
                        error('ERROR: At least boldlist and ROI .names file have to be specified!');
                    end
                end
            end
        end
    end
end


if isempty(targetf)
    method = '.';
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

% ----- Check if the files are there!

go = true;

fprintf('\n\nChecking ...\n');
go = go & g_CheckFile(flist, 'image file list','error');
go = go & g_CheckFile(roiinfo, 'ROI definition file','error');
g_CheckFolder(targetf, 'results folder');

if ~go
	fprintf('ERROR: Some files were not found. Please check the paths and start again!\n\n');
	return
end

% ---- list name

[fpathstr, fname, fext, fversn] = fileparts(flist);

lname = strrep(fname, '.list', '');
lname = strrep(lname, '.conc', '');
lname = strrep(lname, '.4dfp', '');
lname = strrep(lname, '.img', '');


% ---- Start

fprintf('\n\nStarting ...');

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
        scol = ismember(y.scrub_hdr, ignore);
        if sum(scol) == 1;
            mask = y.scrub(:,scol)';
            y = y.sliceframes(mask==0);
        else
            fprintf('\n         WARNING: Field %s not present in scrubbing data, no frames scrubbed!', ignore);
        end
    end
    
	% ---> extracting ROI timeseries
	
	fprintf('\n     ... extracting timeseries ');
	
    ts = y.mri_ExtractROI(roi, [], method);
    
    fprintf(' ... done!');
    
    fprintf('\n     ... computing seed maps ');
	
	if ~isempty(strfind(options, 'p')) || ~isempty(strfind(options, 'z'))
        [pr, p] = y.mri_ComputeCorrelations(ts');
        if strfind(options, 'z')
            z = p.mri_p2z(pr);
        end
    else
        pr = y.mri_ComputeCorrelations(ts');
    end
    
    fprintf(' ... done!');
    
    % ------> Embedd results
    
    nroi = length(roi.roi.roinames);
    for r = 1:nroi
        
        % -------> Create data files if it is the first run
        
        if n == 1
            group(r).Fz = roi.zeroframes(nsub);
            group(r).roi = roi.roi.roinames{r};
        end
        
        % -------> Embedd data
        
        group(r).Fz.data(:,n) = fc_Fisher(pr.data(:,r));
        
        % ----> if needed, save individual images
        
        if strfind(options, 'r')
            pr.mri_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' subject(n).id '_r']);   fprintf(' r');
    	end
    	if strfind(options, 'f')
            group(r).Fz.mri_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' subject(n).id '_Fz']);   fprintf(' Fz');
    	end
    	if strfind(options, 'p')
            p.mri_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' subject(n).id '_p']);   fprintf(' p');
    	end
    	if strfind(options, 'z')
    	    z.mri_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' subject(n).id '_Z']);   fprintf(' Z');
    	end
    	
	end
            
end


%   ---------------------------------------------
%   --- And now group results

fprintf('\n\n... computing group results');

for r = 1:nroi
    
    for s = 1:nsub
        extra(s).key = ['subject ' int2str(n)];
        extra(s).value = subject(n).id;
    end

	fprintf('\n    ... for region %s', group(r).roi);

    [p Z M] = group(r).Fz.mri_TTestZero();
	pr = M.mri_FisherInv();
	
	fprintf('... saving ...');
    
    pr.mri_saveimage([targetf '/' lname '_' group(r).roi '_group_r'], extra);            fprintf(' r');
    M.mri_saveimage([targetf '/' lname '_' group(r).roi '_group_Fz'], extra);           fprintf(' Fz');
    Z.mri_saveimage([targetf '/' lname '_' group(r).roi '_group_Z'], extra);            fprintf(' Z');
    group(r).Fz.mri_saveimage([targetf '/' lname '_' group(r).roi '_all_Fz'], extra);   fprintf(' all Fz');
	
	fprintf(' ... done.');

end



fprintf('\n\n FINISHED!\n\n');



function [] = fc_ComputeSeedMapsMultiple(flist, roiinfo, inmask, options, targetf, method, ignore, cv)

%function [] = fc_ComputeSeedMapsMultiple(flist, roiinfo, inmask, options, targetf, method, ignore, cv)
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
%       f       - save map of Fisher z values
%		cv		- save map of covariances
%		z		- save map of Z scores
%	tagetf		- the folder to save images in
%   method      - method for extracting timeseries - mean, pca [mean]
%   ignore      - do we omit frames to be ignored (
%               -> no:    do not ignore any additional frames
%               -> event: ignore frames as marked in .fidl file
%               -> other: the column in *_scrub.txt file that matches bold file to be used for ignore mask
%   cv          - whether covariances should be computed instead
%
%	It saves group files:
%		_group_Fz	- average Fz over all the subjects
%       _group_r    - average Fz converted back to Pearson r
%		_group_cov	- average covariance
%       _group_Z    - p values converted to Z scores based on t-test testing if Fz over subject differ significantly from 0 (two-tailed)
%       _all_Fz     - Fz values of all the participants
%		_all_cov	- covariances of all the participants
%
% 	Created by Grega Repovš on 2008-02-07.
%   2008-01-23 Adjusted for a different file list format and an additional ROI mask [Grega Repovš]
%   2011-11-10 Changed to make use of gmrimage and allow ignoring of bad frames [Grega Repovš]
%   2014-09-03 Added option for computing covariances [Grega Repovš]
% 	Copyright (c) 2008. All rights reserved.


if nargin < 7 || isempty(cv),      cv     = false;  end
if nargin < 7 || isempty(ignore),  ignore = 'no';   end
if nargin < 6 || isempty(method),  method = 'mean'; end
if nargin < 5 || isempty(targetf), targetf = '.';   end
if nargin < 4 options = []; end
if nargin < 3 inmask = [];  end
if nargin < 2 error('ERROR: At least boldlist and ROI .names file have to be specified!'); end

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

[fpathstr, fname, fext] = fileparts(flist);

lname = strrep(fname, '.list', '');
lname = strrep(lname, '.conc', '');
lname = strrep(lname, '.4dfp', '');
lname = strrep(lname, '.img', '');
lname = strrep(lname, '.nii', '');
lname = strrep(lname, '.gz', '');


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
	    sroifile = '';
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
        [pr, p] = y.mri_ComputeCorrelations(ts', false, cv);
        if strfind(options, 'z')
            z = p.mri_p2z(pr);
        end
    else
        pr = y.mri_ComputeCorrelations(ts', false, cv);
    end

    fprintf(' ... done!');

    % ------> Embedd results

    nroi = length(roi.roi.roinames);
    for r = 1:nroi

        % -------> Create data files if it is the first run

        if n == 1
            if cv
                group(r).cv = roi.zeroframes(nsub);
            else
                group(r).Fz = roi.zeroframes(nsub);
            end
            group(r).roi = roi.roi.roinames{r};
        end

        % -------> Embedd data

        if cv
            group(r).cv.data(:,n) = pr.data(:,r);
        else
            group(r).Fz.data(:,n) = fc_Fisher(pr.data(:,r));
        end

        % ----> if needed, save individual images

        if ~isempty(strfind(options, 'cv')) && cv
            pr.mri_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' subject(n).id '_cov']);   fprintf(' cov');
        end
        if ~isempty(strfind(options, 'r')) && ~cv
            pr.mri_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' subject(n).id '_r']);   fprintf(' r');
    	end
    	if ~isempty(strfind(options, 'f')) && ~cv
            group(r).Fz.mri_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' subject(n).id '_Fz']);   fprintf(' Fz');
    	end
    	if ~isempty(strfind(options, 'p')) && ~cv
            p.mri_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' subject(n).id '_p']);   fprintf(' p');
    	end
    	if ~isempty(strfind(options, 'z')) && ~cv
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

    if cv
        [p Z M] = group(r).cv.mri_TTestZero();
    else
        [p Z M] = group(r).Fz.mri_TTestZero();
        pr = M.mri_FisherInv();
    end

	fprintf('... saving ...');

    if cv
       M.mri_saveimage([targetf '/' lname '_' group(r).roi '_group_cov'], extra);           fprintf(' cov');
       group(r).cv.mri_saveimage([targetf '/' lname '_' group(r).roi '_all_cov'], extra);   fprintf(' all cov');
    else
       M.mri_saveimage([targetf '/' lname '_' group(r).roi '_group_Fz'], extra);            fprintf(' Fz');
       pr.mri_saveimage([targetf '/' lname '_' group(r).roi '_group_r'], extra);            fprintf(' r');
       group(r).Fz.mri_saveimage([targetf '/' lname '_' group(r).roi '_all_Fz'], extra);    fprintf(' all Fz');
    end

    Z.mri_saveimage([targetf '/' lname '_' group(r).roi '_group_Z'], extra);                fprintf(' Z');

	fprintf(' ... done.');

end



fprintf('\n\n FINISHED!\n\n');



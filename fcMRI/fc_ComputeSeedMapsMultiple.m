function [] = fc_ComputeSeedMapsMultiple(flist, roiinfo, inmask, options, targetf, method, ignore, cv)

%``function [] = fc_ComputeSeedMapsMultiple(flist, roiinfo, inmask, options, targetf, method, ignore, cv)``
%
%	Computes seed based correlations maps for individuals as well as group maps.
%
%   INPUTS
%   ======
%
%	--flist   	A .list file of session information, or a well strucutured 
%               string (see g_ReadFileList).
%	--roinfo	An ROI file.
%	--inmask    Either an array mask defining which frames to use (1) and which 
%               not (0) or an event string specifying the events and frames to 
%               extract [0]
%	--options	A string defining which session files to save ['']:
%
%	    	    - r   - save map of correlations
%               - f   - save map of Fisher z values
%	    	    - cv  - save map of covariances
%	    	    - z   - save map of Z scores
%
%	--targetf	The folder to save images in ['.'].
%   --method    Method for extracting timeseries - 'mean' or 'pca' ['mean'].
%   --ignore    Do we omit frames to be ignored ['no']
%
%               - no:    do not ignore any additional frames
%               - event: ignore frames as marked in .fidl file
%               - other: the column in *_scrub.txt file that matches bold file 
%               to be used for ignore mask
%
%   --cv          Whether covariances should be computed instead of correlations.
%
%   RESULTS
%   =======
%
%	It saves group files:
%
%   _group_Fz
%       average Fz over all the sessions

%   _group_r   
%       average Fz converted back to Pearson r

%   _group_Z   
%       p values converted to Z scores based on t-test testing if Fz over session differ significantly from 0 (two-tailed)

%   _all_Fz    
%       Fz values of all the participants
%
%   _group_cov 
%       average covariance

%   _all_cov
%       covariances of all the participants
%
%   USE
%   ===
%
%   The function computes seedmaps for the specified ROI and saves group results
%   as well as any specified individual results.
%
%   EXAMPLE USE
%   ===========
%
%   ::
%
%       fc_ComputeSeedMapsMultiple('con.list', 'DMN.names', 0, '', 'mean', ...
%       'udvarsme', false);

%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%
%   2008-02-07 Grega Repovš
%   2008-01-23 Grega Repovš
%            - Adjusted for a different file list format and an additional ROI mask []
%   2011-11-10 Grega Repovš
%            - Changed to make use of nimage and allow ignoring of bad frames
%   2014-09-03 Grega Repovš
%            - Added option for computing covariances
%   2017-03-19 Grega Repovš
%            - Updated documentation
%   2017-04-18 Grega Repovs
%            - Adjusted to use updated g_ReadFileList.
%


if nargin < 8 || isempty(cv),      cv     = false;  end
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
% go = go & g_CheckFile(flist, 'image file list','error');
go = go & g_CheckFile(roiinfo, 'ROI definition file','error');
g_CheckFolder(targetf, 'results folder');

if ~go
	error('ERROR: Some files were not found. Please check the paths and start again!\n\n');
end

% ---- Start

fprintf('\n\nStarting ...');

%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf('\n ... listing files to process');

[session, nsub, nfiles, listname] = g_ReadFileList(flist);

lname = strrep(listname, '.list', '');
lname = strrep(lname, '.conc', '');
lname = strrep(lname, '.4dfp', '');
lname = strrep(lname, '.img', '');

fprintf(' ... done.');


%   ------------------------------------------------------------------------------------------
%                                                The main loop ... go through all the sessions


for n = 1:nsub

    fprintf('\n ... processing %s', session(n).id);

    % ---> reading ROI file

	fprintf('\n     ... creating ROI mask');

	if isfield(session(n), 'roi')
	    sroifile = session(n).roi;
	else
	    sroifile = '';
    end

	roi = nimage.img_ReadROI(roiinfo, sroifile);


	% ---> reading image files

	fprintf('\n     ... reading image file(s)');

	y = nimage(session(n).files{1});
	for f = 2:length(session(n).files)
	    y = [y nimage(session(n).files{f})];
    end

    fprintf(' ... %d frames read, done.', y.frames);

    % ---> creating timeseries mask

	if eventbased
	    mask = [];
	    if isfield(session(n), 'fidl')
            if session(n).fidl
                mask = g_CreateTaskRegressors(session(n).fidl, y.runframes, inmask, fignore);
                mask = mask.run;
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
        fprintf('\n     ... removing first %d frames ', mask);
        y = y.sliceframes(mask, 'perrun');
    else
        y = y.sliceframes(mask);                % this might need to be changed to allow for per run timeseries masks
    end

    % ---> remove additional frames to be ignored

    if ~ismember(ignore, {'no', 'fidl'})
        scol = ismember(y.scrub_hdr, ignore);
        if sum(scol) == 1;
            mask = y.scrub(:,scol)';
            fprintf('\n     ... ignoring %d bad frames ', sum(mask));
            y = y.sliceframes(mask==0);
        else
            fprintf('\n         WARNING: Field %s not present in scrubbing data, no frames scrubbed!', ignore);
        end
    end

	% ---> extracting ROI timeseries

	fprintf('\n     ... extracting timeseries ');

    ts = y.img_ExtractROI(roi, [], method);

    fprintf(' ... done!');

    fprintf('\n     ... computing seed maps ');

	if ~isempty(strfind(options, 'p')) || ~isempty(strfind(options, 'z'))
        [pr, p] = y.img_ComputeCorrelations(ts', false, cv);
        if strfind(options, 'z')
            z = p.img_p2z(pr);
        end
    else
        pr = y.img_ComputeCorrelations(ts', false, cv);
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
            pr.img_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' session(n).id '_cov']);   fprintf(' cov');
        end
        if ~isempty(strfind(options, 'r')) && ~cv
            pr.img_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' session(n).id '_r']);   fprintf(' r');
    	end
    	if ~isempty(strfind(options, 'f')) && ~cv
            group(r).Fz.img_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' session(n).id '_Fz']);   fprintf(' Fz');
    	end
    	if ~isempty(strfind(options, 'p')) && ~cv
            p.img_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' session(n).id '_p']);   fprintf(' p');
    	end
    	if ~isempty(strfind(options, 'z')) && ~cv
    	    z.img_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' session(n).id '_Z']);   fprintf(' Z');
    	end

	end

end

%   ---------------------------------------------
%   --- And now group results

fprintf('\n\n... computing group results');

for r = 1:nroi

    for s = 1:nsub
        extra(s).key = ['session ' int2str(n)];
        extra(s).value = session(n).id;
    end

	fprintf('\n    ... for region %s', group(r).roi);

    if cv
        [p Z M] = group(r).cv.img_TTestZero();
    else
        [p Z M] = group(r).Fz.img_TTestZero();
        pr = M.img_FisherInv();
    end

	fprintf('... saving ...');

    if cv
       M.img_saveimage([targetf '/' lname '_' group(r).roi '_group_cov'], extra);           fprintf(' cov');
       group(r).cv.img_saveimage([targetf '/' lname '_' group(r).roi '_all_cov'], extra);   fprintf(' all cov');
    else
       M.img_saveimage([targetf '/' lname '_' group(r).roi '_group_Fz'], extra);            fprintf(' Fz');
       pr.img_saveimage([targetf '/' lname '_' group(r).roi '_group_r'], extra);            fprintf(' r');
       group(r).Fz.img_saveimage([targetf '/' lname '_' group(r).roi '_all_Fz'], extra);    fprintf(' all Fz');
    end

    Z.img_saveimage([targetf '/' lname '_' group(r).roi '_group_Z'], extra);                fprintf(' Z');

	fprintf(' ... done.');

end



fprintf('\n\n FINISHED!\n\n');



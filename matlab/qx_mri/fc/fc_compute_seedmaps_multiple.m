function [] = fc_compute_seedmaps_multiple(flist, roiinfo, inmask, options, targetf, method, ignore, cv)

%``fc_compute_seedmaps_multiple(flist, roiinfo, inmask, options, targetf, method, ignore, cv)``
%
%   Computes seed based correlations maps for individuals as well as group maps.
%
%   Parameters:
%       --flist (str):
%           A .list file of session information, or a well strucutured
%           string (see general_read_file_list).
%
%       --roinfo (str):
%           An ROI file.
%
%       --inmask (matrix | string, default ''):
%           Either an array mask defining which frames to use (1) and which
%           not (0) or an event string specifying the events and frames to
%           extract.
%
%       --options (str, default ''):
%           A string defining which session files to save:
%
%           - r   - save map of correlations
%           - f   - save map of Fisher z values
%           - cv  - save map of covariances
%           - z   - save map of Z scores
%           - []  - no files are saved.
%
%       --targetf (str, default '.'):
%           The folder to save images in.
%
%       --method (str, default 'mean'):
%           Method for extracting timeseries - 'mean' or 'pca'.
%
%       --ignore (str, default 'no'):
%           Do we omit frames to be ignored:
%
%           - no    - do not ignore any additional frames
%           - event - ignore frames as marked in .fidl file
%           - other - the column in ∗_scrub.txt file that matches bold file to be
%             used for ignore mask.
%
%       --cv (bool, default false):
%           Whether covariances should be computed instead of correlations.
%
%   Output files:
%       Function saves the following group files:
%
%       _group_Fz
%           average Fz over all the sessions
%
%       _group_r
%           average Fz converted back to Pearson r
%
%       _group_Z
%           p values converted to Z scores based on t-test testing if Fz
%           over session differ significantly from 0 (two-tailed)
%
%       _all_Fz
%           Fz values of all the participants
%
%       _group_cov
%           average covariance
%
%       _all_cov
%           covariances of all the participants.
%
%   Notes:
%       The function computes seedmaps for the specified ROI and saves group
%       results as well as any specified individual results.
%
%   Examples:
%       ::
%
%           qunex fc_compute_seedmaps_multiple \
%               --flist='con.list' \
%               --roinfo='DMN.names' \
%               --inmask=0 \
%               --targetf=mean \
%               --method=udvarsme \
%               --ignore=false
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

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

if cv 
    fcmeasure = 'cv';
else
    fcmeasure = 'r';
end

% ----- Check if the files are there!

go = true;

fprintf('\n\nChecking ...\n');
% go = go & general_check_file(flist, 'image file list','error');
go = go & general_check_file(roiinfo, 'ROI definition file','error');
general_check_folder(targetf, 'results folder');

if ~go
    error('ERROR: Some files were not found. Please check the paths and start again!\n\n');
end

% ---- Start

fprintf('\n\nStarting ...');

%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf('\n ... listing files to process');

list = general_read_file_list(flist, 'all', []);

lname = strrep(list.listname, '.list', '');
lname = strrep(lname, '.conc', '');
lname = strrep(lname, '.4dfp', '');
lname = strrep(lname, '.img', '');

fprintf(' ... done.');


%   ------------------------------------------------------------------------------------------
%                                                The main loop ... go through all the sessions


for n = 1:list.nsessions

    fprintf('\n ... processing %s', list.session(n).id);

    % ---> reading ROI file

    fprintf('\n     ... creating ROI mask');

    if isfield(list.session(n), 'roi')
        sroifile = list.session(n).roi;
    else
        sroifile = '';
    end

    roi = nimage.img_read_roi(roiinfo, sroifile);


    % ---> reading image files

    fprintf('\n     ... reading image file(s)');

    y = nimage(list.session(n).files{1});
    for f = 2:length(list.session(n).files)
        y = [y nimage(list.session(n).files{f})];
    end

    fprintf(' ... %d frames read, done.', y.frames);

    % ---> creating timeseries mask

    if eventbased
        mask = [];
        if isfield(list.session(n), 'fidl')
            if list.session(n).fidl
                mask = general_create_task_regressors(list.session(n).fidl, y.runframes, inmask, fignore);
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

    ts = y.img_extract_roi(roi, [], method);

    fprintf(' ... done!');

    fprintf('\n     ... computing seed maps ');

    if ~isempty(strfind(options, 'p'))
        [pr, z, p] = y.img_compute_correlations(ts', fcmeasure, false, false);
    elseif ~isempty(strfind(options, 'z'))
        [pr, z] = y.img_compute_correlations(ts', fcmeasure, false, false);
    else
        pr = y.img_compute_correlations(ts', fcmeasure, false, false);
    end

    fprintf(' ... done!');

    % ---> Embedd results

    nroi = length(roi.roi.roinames);
    for r = 1:nroi

        % ---> Create data files if it is the first run

        if n == 1
            if cv
                group(r).cv = roi.zeroframes(list.nsessions);
            else
                group(r).Fz = roi.zeroframes(list.nsessions);
            end
            group(r).roi = roi.roi.roinames{r};
        end

        % ---> Embedd data

        if cv
            group(r).cv.data(:,n) = pr.data(:,r);
        else
            group(r).Fz.data(:,n) = fc_fisher(pr.data(:,r));
        end

        % ---> if needed, save individual images

        if ~isempty(strfind(options, 'cv')) && cv
            pr.img_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' list.session(n).id '_cov']); fprintf(' cov');
        end
        if ~isempty(strfind(options, 'r')) && ~cv
            pr.img_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' list.session(n).id '_r']); fprintf(' r');
        end
        if ~isempty(strfind(options, 'f')) && ~cv
            group(r).Fz.img_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' list.session(n).id '_Fz']); fprintf(' Fz');
        end
        if ~isempty(strfind(options, 'p')) && ~cv
            p.img_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' list.session(n).id '_p']); fprintf(' p');
        end
        if ~isempty(strfind(options, 'z')) && ~cv
            z.img_saveimageframe(n, [targetf '/' lname '_' group(r).roi '_' list.session(n).id '_Z']); fprintf(' Z');
        end

    end

end

%   ---------------------------------------------
%   --- And now group results

fprintf('\n\n... computing group results');

for r = 1:nroi

    for s = 1:list.nsessions
        extra(s).key = ['session ' int2str(n)];
        extra(s).value = list.session(n).id;
    end

    fprintf('\n    ... for region %s', group(r).roi);

    if cv
        [p Z M] = group(r).cv.img_ttest_zero();
    else
        [p Z M] = group(r).Fz.img_ttest_zero();
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



function [] = fc_ComputeSeedMaps(flist, roiinfo, inmask, event, targetf, method, ignore, cv)

%function [] = fc_ComputeSeedMaps(flist, roiinfo, inmask, event, targetf, method, ignore, cv)
%
%   Computes seed based correlations maps for individuals as well as group maps.
%
%   INPUT
%       flist    - A .list file listing the subjects and their files for which to compute seedmaps,
%                  or a well strucutured string (see g_ReadFileList).
%       roiinfo  - A names file for the ROI seeds.
%       inmask   - An array mask defining which frames to use (1) and which not (0) or the number of frames to skip at start []
%       event    - A string describing which events to extract timeseries for and the frame offset at start and end
%                  in format: ('title1:event1,event2:2:2|title2:event3,event4:1:2') ['']
%       tagetf   - The folder to save images in ['.'].
%       method   - method for extracting timeseries - 'mean', 'pca' ['mean']
%       ignore   - do we omit frames to be ignored (
%                  -> no:    do not ignore any additional frames
%                  -> use:   ignore frames as marked in the use field of the bold file
%                  -> event: ignore frames as marked in .fidl file
%                  -> other: the column in *_scrub.txt file that matches bold file to be used for ignore mask
%       cv       - Whether to compute covariances instead of correlations [false].
%
%   RESULTS
%   It saves group files:
%
%   <targetf>/<root>[_<title>]_<roi>_group_r  ... Mean group Pearson correlations (converted from Fz).
%   <targetf>/<root>[_<title>]_<roi>_group_Fz ... Mean group Fisher Z values.
%   <targetf>/<root>[_<title>]_<roi>_group_Z  ... Z converted p values testing difference from 0.
%   <targetf>/<root>[_<title>]_<roi>_all_Fz   ... Fisher Z values for all participants.
%
%   <targetf>/<root>[_<title>]_<roi>_group_cov ... Mean group covariance.
%   <targetf>/<root>[_<title>]_<roi>_all_cov   ... Covariances for all participants.
%
%   <roi> is the name of the ROI for which the seed map was computed for.
%   <root> is the root name of the flist.
%   <title> is the title of the extraction event(s), if event string was
%   specified.
%
%   USE
%   The function computes seed maps for the specified ROI. If an event string is
%   provided, it uses each subject's .fidl file to extract only the specified
%   event related frames. The string format is:
%
%   <title>:<eventlist>:<frame offset1>:<frame offset2>
%
%   and multiple extractions can be specified by separating them using the pipe
%   '|' separator. Specifically, for each extraction, all the events listed in
%   a comma-separated eventlist will be considered (e.g. 'task1,task2') and for
%   each event all the frames starting from event start + offset1 to event end
%   + offset2 will be extracted and concatenated into a single timeseries. Do
%   note that the extracted frames depend on the length of the event specified
%   in the .fidl file!
%
%   EXAMPLE USE
%   To compute resting state seed maps using first eigenvariate of each ROI:
%   >>> fc_ComputeSeedMaps('scz.list', 'CCNet.names', 0, '', 'seed-maps', 'pca', 'udvarsme');
%
%   To compute resting state seed maps using mean of each region and covariances
%   instead of correlation:
%   >>> fc_ComputeSeedMaps('scz.list', 'CCNet.names', 0, '', 'seed-maps', 'mean', 'udvarsme', true);
%
%   To compute seed maps for third and fourth frame of incongruent and congruent
%   trials (listed as inc and con events in fidl files with duration 1) using
%   mean of each region and exclude only frames marked for exclusion in fidl
%   files:
%
%   >>> fc_ComputeSeedMaps('scz.list', 'CCNet.names', 0, 'incongruent:inc:2,3|congruent:con:2,3', 'seed-maps', 'mean', 'event');
%
%   To compute seed maps across all the tasks blocks, starting with the third
%   frame into the block and taking one additional frame after the end of the
%   block, use:
%
%   >>> fc_ComputeSeedMaps('scz.list', 'CCNet.names', 0, 'task:easyblock,hardblock:2,1', 'seed-maps', 'mean', 'event');
%
%   ---
%   Written by Grega Repovš 2008-02-07.
%
%   Changelog
%   2008-01-23 Grega Repovš - Adjusted for a different file list format and an additional ROI mask.
%   2011-11-10 Grega Repovš - Changed to make use of gmrimage and allow ignoring of bad frames.
%   2013-12-28 Grega Repovš - Moved to a more general name, added block event extraction and use of 'use' info.
%   2017-03-19 Grega Repovs - Cleaned code, updated documentation.
%   2017-04-18 Grega Repovs - Adjusted to use updated g_ReadFileList.
%

if nargin < 8 || isempty(cv),      cv      = false;  end
if nargin < 7 || isempty(ignore),  ignore  = 'use';  end
if nargin < 6 || isempty(method),  method  = 'mean'; end
if nargin < 5 || isempty(targetf), targetf = '.';    end
if nargin < 4 event   = []; end
if nargin < 3 inmask  = []; end
if nargin < 2 error('ERROR: At least boldlist and ROI .names file have to be specified!'); end

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
% go = go & g_CheckFile(flist, 'image file list', 'error');
go = go & g_CheckFile(roiinfo, 'ROI definition file', 'error');
g_CheckFolder(targetf, 'results folder');

if ~go
    fprintf('ERROR: Some files were not found. Please check the paths and start again!\n\n');
    return
end

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

[subject, nsub, nfiles, listname] = g_ReadFileList(flist);

lname = strrep(listname, '.list', '');
lname = strrep(lname, '.conc', '');
lname = strrep(lname, '.4dfp', '');
lname = strrep(lname, '.img', '');

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
        finfo = finfo.run;
        matrix = [];
        for r = 1:length(finfo)
            matrix = [matrix; finfo(r).matrix];
        end
    end

    % ---> creating timeseries mask

    fprintf('\n     ... computing seed maps [');

    for a = 1:nana

        % --- if no events take all, otherwise take the mask of this regressor
        if isempty(finfo)
            mask = ones(1, y.frames);
        else
            mask = matrix(:, a)';
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

        fprintf('%d ', sum(mask));

        t  = y.sliceframes(mask);
        ts = t.mri_ExtractROI(roi, [], method);
        pr = t.mri_ComputeCorrelations(ts', [], cv);

        % ------> Embedd results

        nroi = length(roi.roi.roinames);
        for r = 1:nroi

            % -------> Create data files if it is the first run

            if n == 1
                if cv
                    ana(a).group(r).cv = roi.zeroframes(nsub);
                else
                    ana(a).group(r).Fz = roi.zeroframes(nsub);
                end
                ana(a).group(r).roi = roi.roi.roinames{r};
            end

            % -------> Embedd data

            if cv
                ana(a).group(r).cz.data(:,n) = pr.data(:,r);
            else
                ana(a).group(r).Fz.data(:,n) = fc_Fisher(pr.data(:,r));
            end

       end
    end

    fprintf('frames]');
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

        if cv
            [p Z M] = ana(a).group(r).cv.mri_TTestZero();
        else
            [p Z M] = ana(a).group(r).Fz.mri_TTestZero();
            pr = M.mri_FisherInv();
        end

        fprintf('... saving ...');
        if isempty(ana(a).name)
            tname = lname;
        else
            tname = [lname '_' ana(a).name];
        end

        if cv
            M.mri_saveimage([targetf '/' tname '_' ana(a).group(r).roi '_group_cv'], extra);                  fprintf(' cv');
            ana(a).group(r).cv.mri_saveimage([targetf '/' tname '_' ana(a).group(r).roi '_all_cv'], extra);   fprintf(' all cv');
        else
            pr.mri_saveimage([targetf '/' tname '_' ana(a).group(r).roi '_group_r'], extra);                  fprintf(' r');
            M.mri_saveimage([targetf '/' tname '_' ana(a).group(r).roi '_group_Fz'], extra);                  fprintf(' Fz');
            ana(a).group(r).Fz.mri_saveimage([targetf '/' tname '_' ana(a).group(r).roi '_all_Fz'], extra);   fprintf(' all Fz');
        end

        Z.mri_saveimage([targetf '/' tname '_' ana(a).group(r).roi '_group_Z'], extra);                   fprintf(' Z');

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
        ana(m).name = fields{1};
        fstring     = [fstring fields{2} ':block:' fields{3} ':' fields{4}];
        if m < nsmaps, fstring = [fstring '|']; end
    end




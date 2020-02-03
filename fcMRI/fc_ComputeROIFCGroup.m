function [] = fc_ComputeROIFCGroup(flist, roiinfo, frames, targetf, options)

%function [] = fc_ComputeROIFCGroup(flist, roiinfo, frames, targetf, options)
%
%   Computes seed based correlations maps for individuals as well as group maps.
%
%   INPUT
%       flist     - A .list file listing the subjects and their files for which to compute seedmaps,
%                   or a well strucutured string (see g_ReadFileList).
%       roiinfo   - A names file for the ROI seeds.
%       frames    - The definition of which frames to use, it can be one of:
%                   -> a numeric array mask defining which frames to use (1) and which not (0) 
%                   -> a single number, specifying the number of frames to skip at start
%                   -> a string describing which events to extract timeseries for, and the frame offset from 
%                      the start and end of the event in format: ('fidlfile|title1:event1,event2:2:2|title2:event3,event4:1:2') 
%                   []
%       tagetf    - The folder to save images in ['.'].
%       options   - A string specifying additional analysis options formated as pipe separated pairs of colon separated
%                   key, value pairs: "<key>:<value>|<key>:<value>"
%                   It takes the following keys and values:
%                   -> roimethod ... what method to use to compute ROI signal, 'mean' or 'pca' ['mean']
%                   -> eventdata ... what data to use from the event:
%                                    -> all      ... use all identified frames of all events
%                                    -> mean     ... use the mean across frames of each identified event
%                                    -> min      ... use the minimum value across frames of each identified event
%                                    -> max      ... use the maximum value across frames of each identified event
%                                    -> median   ... use the median value across frames of each identified event
%                                    ['all']
%                   -> ignore    ... a comma separated list of information to identify frames to ignore, options are:
%                                    -> use      ... ignore frames as marked in the use field of the bold file
%                                    -> fidl     ... ignore frames as marked in .fidl file
%                                    -> <column> ... the column name in *_scrub.txt file that matches bold file to be used for ignore mask
%                                    ['use']
%                   -> badevents ... what to do with events that have frames marked as bad, options are:
%                                    -> use      ... use any frames that are not marked as bad
%                                    -> <number> ... use the frames that are not marked as bad if at least <number> ok frames exist
%                                    -> ignore   ... if any frame is marked as bad, ignore the full event
%                                    ['use']
%                   -> fcmeasure ... which functional connectivity measure to compute, the options are:
%                                    -> r        ... pearson's r value
%                                    -> cv       ... covariance estimate
%                                    ['r']
%                   -> savegroup ... a comma separated list of formats to use to save the group data:
%                                    -> txt      ... save the resulting data in a long format txt file
%                                    -> mat      ... save the resulting data in a matlab .mat file
%                                    ['']
%                   -> saveind   ... a comma separated list of formats to use to save the invidvidual data:
%                                    -> txt      ... save the resulting data in a long format txt file
%                                    -> mat      ... save the resulting data in a matlab .mat file
%                                    ['']
%                   -> itargetf  ... where to save the individual data:
%                                    -> gfolder  ... in the group target folder
%                                    -> sfolder  ... in the individual session folder
%                                    ['gfolder']
%                   -> verbose   ... whether to be verbose 'true' or not 'false', when running the analysis ['false']
%                   
%
%   RESULTS
%   =======
%
%   Based on specification it saves group files:
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
%   <title> is the title of the extraction event(s), if event string was specified.
%
%   USE
%   ===
%
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
%   ===========
% 
%   To compute resting state seed maps using first eigenvariate of each ROI:
%
%   >>> fc_ComputeSeedMaps('scz.list', 'CCNet.names', 0, '', 'seed-maps', 'pca', 'udvarsme');
%
%   To compute resting state seed maps using mean of each region and covariances
%   instead of correlation:
%
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
%   2018-03-16 Grega Repovs - Added verbose to the parameter list
%

if nargin < 5 || isempty(options), options = '';  end
if nargin < 4 || isempty(targetf), targetf = '.'; end
if nargin < 3 frames  = []; end
if nargin < 2 error('ERROR: At least boldlist and ROI .names file have to be specified!'); end

% ----- parse options

default = 'roimethod=mean|eventdata=all|badframes=none|badevents=use|fcmeasure=r|savegroup=|saveind=|itargetf=gfolder|verbose=false';
options = g_ParseOptions([], options, default);

g_PrintStruct(options, 'Options used');

if ~ismember(options.fcmeasure, {'r', 'cv'})
    error('ERROR: Invalid functional connectivity computation method: %s', options.fcmeasure);
end

cv = strcmp(options.fcmeasure, 'cv');
verbose = strcmp(options.verbose, 'true');

% ----- Check if the files are there!

go = true;

if verbose; fprintf('\n\nChecking ...\n'); end
go = go & g_CheckFile(flist, 'image file list', 'error');
go = go & g_CheckFile(roiinfo, 'ROI definition file', 'error');
g_CheckFolder(targetf, 'results folder');

if ~go
    error('ERROR: Some of the specified files were not found. Please check the paths and start again!\n\n');
end

% ---- Start

fprintf('\n\nStarting ...\n');


%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf(' ... listing files to process');

[subject, nsub, nfiles, listname] = g_ReadFileList(flist, verbose);

lname = strrep(listname, '.list', '');
lname = strrep(lname, '.conc', '');
lname = strrep(lname, '.4dfp', '');
lname = strrep(lname, '.img', '');

fprintf(' ... done.\n');


%   ------------------------------------------------------------------------------------------
%                                                The main loop ... go through all the subjects

c = 0;

for n = 1:nsub

    go = true;

    if verbose; fprintf('\n----------------------------------\nprocessing %s\n', subject(n).id); end

    % ---> setting up roidef parameter

    if isfield(subject(n), 'roi')
        go = go & g_CheckFile(subject(n).roi, [subject(n).id ' individual ROI file'], 'error');
        roidef = [roiinfo '|' subject(n).roi];
    else
        roidef = [roiinfo];
    end

    % ---> setting up bolds parameter

    if isfield(subject(n), 'files')
        for bold = subject(n).files
            go = go & g_CheckFile(bold{1}, 'bold file', 'error');
        end
        if strcmp(options.itargetf, 'sfolder')
            bolds = [lname '|' strjoin(subject(n).files, '|')];
        else
            bolds = [lname '_' subject(n).id '|' strjoin(subject(n).files, '|')];
        end
    elseif isfield(subject(n), 'conc')
        go = go & g_CheckFile(subject(n).conc, 'conc file', 'error');
        if strcmp(options.itargetf, 'sfolder')
            bolds = [lname '|' subject(n).conc];
        else
            bolds = [lname '_' subject(n).id '|' subject(n).conc];
        end
    else
        go = false
        fprintf(' ... ERROR: %s missing bold or conc file specification!\n', subject(n).id);
    end

    % ---> setting up frames parameter

    if isa(frames, 'char')
        if isfield(subject(n), 'fidl')
            go = go & g_CheckFile(subject(n).fidl, [subject(n).id ' fidl file'], 'error');
            sframes = [subject(n).fidl '|' frames];
        else
            go = false
            fprintf(' ... ERROR: %s missing fidl file specification!\n', subject(n).id);
        end
    else
        sframes = frames;
    end

    if ~go, continue; end

    % ---> setting up target folder for individual data

    if strcmp(options.itargetf, 'sfolder')
        reference = subject(n).files{1};
        if regexp(reference, '.conc$')
            reference = g_ReadConcFile(reference);
            reference = reference{1};
        end
        stargetf = fileparts(reference);
    else
        stargetf = targetf;
    end

    % ---> run individual subject
    try
        fcmat = fc_ComputeROIFC(bolds, roidef, sframes, stargetf, options);
    catch ME
        fprintf(' ... ERROR: Computation of ROI FC for %s failed with error: %s\n', subject(n).id, ME.message);
        continue
    end

    % ------> Reorganize results

    nset = length(fcmat);
    c = c + 1;

    for s = 1:nset

        fcset(s).name = fcmat(s).title;            
        fcset(s).roi  = fcmat(s).roi;                

        % -------> Embedd data

        fcset(s).subject(c).id = subject(n).id;

        if strcmp(options.fcmeasure, 'cv')
            fcset(s).subject(c).cv = fcmat(s).cv;
        else
            fcset(s).subject(c).r  = fcmat(s).r;
            fcset(s).subject(c).fz = fcmat(s).fz;
            fcset(s).subject(c).z  = fcmat(s).z;
            fcset(s).subject(c).p  = fcmat(s).p;
        end        
   end
end

noksub = c;

%   ------------------------------------------------------------------------------------------
%                                                                           Save group results

% ---> save results

if isempty(options.savegroup)
    if verbose; fprintf(' ... done\n'); end
    return; 
else
    options.savegroup = strtrim(regexp(options.savegroup, ',', 'split'));
end

if verbose; fprintf('\n----------------------------------\nSaving group results\n'); end

ftail = {'cor', 'cov'};
ftail = ftail{ismember({'r', 'cv'}, options.fcmeasure)};

basefilename = fullfile(targetf, sprintf('%s_%s', lname, ftail));

if ismember({'mat'}, options.savegroup)
    if verbose; fprintf('... saving mat file'); end
    save([basefilename '.mat'], 'fcset');
    if verbose; fprintf(' ... done\n'); end
end

if ismember({'txt'}, options.savegroup)
    
    if verbose; fprintf('... saving txt file'); end

    fout = fopen([basefilename '.txt'], 'w');

    if strcmp(options.fcmeasure, 'cv')
        fprintf(fout, 'name\ttitle\tsubject\troi1\troi2\tcv\n');
    else
        fprintf(fout, 'name\ttitle\tsubject\troi1\troi2\tr\tFz\tZ\tp\n');
    end

    for n = 1:length(fcset)
        if fcset(n).name, settitle = fcset(n).name; else settitle = 'ts'; end

        % --- set ROI names

        nroi = length(fcset(n).roi);

        idx  = repmat([1:nroi], nroi, 1);
        idx1 = tril(idx, -1);
        idx1 = idx1(idx1 > 0);
        idx2 = triu(idx, 1);
        idx2 = idx2(idx2 > 0);
        roi1 = fcmat(n).roi(idx1);
        roi2 = fcmat(n).roi(idx2);

        idx  = reshape([1:nroi*nroi], nroi, nroi);
        idx  = tril(idx, -1);
        idx  = idx(idx > 0);

        nfc  = length(idx);

        % --- write up
        for sid = 1:noksub
            if strcmp(options.fcmeasure, 'cv')            
                cv = fcset(n).subject(sid).cv(idx);
                for c = 1:nfc
                    fprintf(fout, '%s\t%s\t%s\t%s\t%s\t%.5f\n', lname, settitle, fcset(n).subject(sid).id, roi1{c}, roi2{c}, cv(c));
                end
            else
                r  = fcset(n).subject(sid).r(idx);
                fz = fcset(n).subject(sid).fz(idx);
                z  = fcset(n).subject(sid).z(idx);
                p  = fcset(n).subject(sid).p(idx);
                for c = 1:nfc
                    fprintf(fout, '%s\t%s\t%s\t%s\t%s\t%.5f\t%.5f\t%.5f\t%.7f\n', lname, settitle, fcset(n).subject(sid).id, roi1{c}, roi2{c}, r(c), fz(c), z(c), p(c));
                end
            end
        end
    end
    fclose(fout);
    if verbose; fprintf(' ... done\n'); end
end

if verbose; fprintf('DONE\n'); end



function [] = fc_compute_seedmaps_group(flist, roiinfo, frames, targetf, options)

%``function [] = fc_compute_seedmaps_group(flist, roiinfo, frames, targetf, options)``
%
%   Computes seed based correlations maps for individuals as well as group maps.
%
%   INPUTS
%   ======
%
%   --flist     A .list file listing the sessions and their files for which to compute seedmaps,
%               or a well strucutured string (see general_read_file_list).
%   --roiinfo   A names file for the ROI seeds.
%   --frames    The definition of which frames to use, it can be one of:
%                   -> a numeric array mask defining which frames to use (1) and which not (0) 
%                   -> a single number, specifying the number of frames to skip at start
%                   -> a string describing which events to extract timeseries for, and the frame offset from 
%                      the start and end of the event in format: ('title1:event1,event2:2:2|title2:event3,event4:1:2') 
%                   []
%   --tagetf    The folder to save images in ['.'].
%   --options   A string specifying additional analysis options formated as pipe separated pairs of colon separated
%               key, value pairs: "<key>:<value>|<key>:<value>"
%               It takes the following keys and values:
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
%                                    ['use,fidl']
%                   -> badevents ... what to do with events that have frames marked as bad, options are:
%                                    -> use      ... use any frames that are not marked as bad
%                                    -> <number> ... use the frames that are not marked as bad if at least <number> ok frames exist
%                                    -> ignore   ... if any frame is marked as bad, ignore the full event
%                                    ['use']
%                   -> fcmeasure ... which functional connectivity measure to compute, the options are:
%                                    -> r        ... pearson's r value
%                                    -> cv       ... covariance estimate
%                                    ['r']
%                   -> savegroup ... a comma separated list of files to save, options are:
%                                    -> groupr   ... mean group Pearson correlation coefficients (converted from Fz)
%                                    -> groupfz  ... mean group Fisher Z values
%                                    -> groupz   ... Z converted p values testing difference from 0
%                                    -> groupp   ... p values testing difference from 0
%                                    -> allfz    ... Fz values from all the sessions
%                                    -> groupcv  ... mean group covariance
%                                    -> allcv    ... covvariance values from all the participants
%                                    -> all      ... save all the relevant group level results
%                                    -> none     ... do not save any group level results
%                                    ['all']
%                   -> saveind   ... a comma separted list of individual session / session files to save:
%                                    -> r        ... save Pearson correlation coefficients (r only) separately for each roi
%                                    -> fz       ... save Fisher Z values (r only) separately for each roi
%                                    -> z        ... save Z statistic (r only) separately for each roi
%                                    -> p        ... save p value (r only) separately for each roi
%                                    -> cv       ... save covariances (cv only) separately for each roi
%                                    -> allbyroi ... save all relevant values by roi
%                                    -> jr       ... save Pearson correlation coefficients (r only) in a single file for all roi
%                                    -> jfz      ... save Fisher Z values (r only) in a single file for all roi
%                                    -> jz       ... save Z statistic (r only) in a single file for all roi
%                                    -> jp       ... save p value (r only) in a single file for all roi
%                                    -> jcv      ... save covariances (cv only) in a single file for all roi
%                                    -> alljoint ... save all relevant values in a joint file
%                                    -> none     ... do not save any individual level results
%                                    ['none']
%                   -> saveindname . whether to add the name of the session or subject to the individual output file, yes or no ['no']
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
%   `<targetf>/<root>[_<title>]_<roi>_group_r`
%       Mean group Pearson correlations (converted from Fz).
%
%   `<targetf>/<root>[_<title>]_<roi>_group_Fz`
%       Mean group Fisher Z values.
%
%   `<targetf>/<root>[_<title>]_<roi>_group_Z`
%       Z converted p values testing difference from 0.
%
%   `<targetf>/<root>[_<title>]_<roi>_all_Fz`
%       Fisher Z values for all participants.
%
%   `<targetf>/<root>[_<title>]_<roi>_group_cov`
%       Mean group covariance.
%
%   `<targetf>/<root>[_<title>]_<roi>_all_cov`
%       Covariances for all participants.
%
%   `<roi>` is the name of the ROI for which the seed map was computed for.
%   `<root>` is the root name of the flist.
%   `<title>` is the title of the extraction event(s), if event string was specified.
%
%   USE
%   ===
%
%   The function computes seed maps for the specified ROI. If an event string is
%   provided, it uses each session's .fidl file to extract only the specified
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
%   To compute resting state seed maps using first eigenvariate of each ROI::
%
%       fc_compute_seedmaps('scz.list', 'CCNet.names', 0, 'seed-maps', ...
%                           'roimethod:pca|ignore:udvarsme');
%
%   To compute resting state seed maps using mean of each region and covariances
%   instead of correlation::
%
%       fc_compute_seedmaps('scz.list', 'CCNet.names', 0, 'seed-maps', ...
%                           'roimethod:mean|igmore:udvarsme|fcmeasure:cv');
%
%   To compute seed maps for third and fourth frame of incongruent and congruent
%   trials (listed as inc and con events in fidl files with duration 1) using
%   mean of each region and exclude only frames marked for exclusion in fidl
%   files:
%
%       fc_compute_seedmaps('scz.list', 'CCNet.names', ...
%                           'incongruent:inc:2,3|congruent:con:2,3', 'seed-maps', ...
%                           'roimethod:mean|ignore:event');
%
%   To compute seed maps across all the tasks blocks, starting with the third
%   frame into the block and taking one additional frame after the end of the
%   block, use::
%
%       fc_compute_seedmaps('scz.list', 'CCNet.names', ...
%                           'task:easyblock,hardblock:2,1', 'seed-maps', ...
%                           'roimethod:mean|ignore:event');
%

if nargin < 5 || isempty(options), options = '';  end
if nargin < 4 || isempty(targetf), targetf = '.'; end
if nargin < 3 frames  = []; end
if nargin < 2 error('ERROR: At least boldlist and ROI .names file have to be specified!'); end

% ----- parse options

default = 'roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|savegroup=all|saveind=none|saveindname=no|itargetf=sfolder|verbose=false';
options = general_parse_options([], options, default);

general_print_struct(options, 'Options used');

if ~ismember(options.fcmeasure, {'r', 'cv'})
    error('ERROR: Invalid functional connectivity computation method: %s', options.fcmeasure);
end

cv = strcmp(options.fcmeasure, 'cv');

% ----- Check if the files are there!

go = true;

if options.verbose; fprintf('\n\nChecking ...\n'); end
go = go & general_check_file(flist, 'image file list', 'error');
go = go & general_check_file(roiinfo, 'ROI definition file', 'error');
general_check_folder(targetf, 'results folder');

if ~go
    error('ERROR: Some of the specified files were not found. Please check the paths and start again!\n\n');
end

% ----- What should be saved

options.savegroup = strtrim(regexp(options.savegroup, ',', 'split'));

if ismember({'none'}, options.savegroup)
    options.savegroup = {};
end

if ismember({'all'}, options.savegroup)
    if cv
        options.savegroup = {'groupz', 'groupp', 'groupcv', 'allcv'};
    else
        options.savegroup = {'groupz', 'groupp', 'groupr', 'groupfz', 'allfz'};
    end    
end

% ---- Start

fprintf('\n\nStarting ...\n');


%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf(' ... listing files to process');

[session, nsub, nfiles, listname] = general_read_file_list(flist, options.verbose);

lname = strrep(listname, '.list', '');
lname = strrep(lname, '.conc', '');
lname = strrep(lname, '.4dfp', '');
lname = strrep(lname, '.img', '');

fprintf(' ... done.\n');


%   ------------------------------------------------------------------------------------------
%                                                The main loop ... go through all the sessions

first_subject = true;
oksub         = zeros(1, length(session));

for n = 1:nsub

    go = true;

    if options.verbose; fprintf('\n---------------------------------\nProcessing session %s', session(n).id); end

    % ---> setting up roidef parameter

    if isfield(session(n), 'roi')
        go = go & general_check_file(session(n).roi, [session(n).id ' individual ROI file'], 'error');
        roidef = [roiinfo '|' session(n).roi];
    else
        roidef = [roiinfo];
    end

    % ---> setting up bolds parameter

    if isfield(session(n), 'conc')
        go = go & general_check_file(session(n).conc, 'conc file', 'error');
        bolds = [lname '|' session(n).conc];
        reference_file = general_read_concfile(session(n).conc);
        reference_file = reference_file{1};
    elseif isfield(session(n), 'file')
        for bold = session(n).files
            go = go & general_check_file(bold{1}, 'bold file', 'error');
        end
        bolds = [lname '|' strjoin(session(n).files, '|')];
        reference_file = session(n).files{1};
    end

    % ---> setting up frames parameter

    if isa(frames, 'char')
        if isfield(session(n), 'fidl')
            go = go & general_check_file(session(n).fidl, [session(n).id ' fidl file'], 'error');
            sframes = [session(n).fidl '|' frames];
        else
            go = false
            fprintf(' ... ERROR: %s missing fidl file specification!\n', session(n).id);
        end
    else
        sframes = frames;
    end

    if ~go, continue; end

    % ---> setting up target folder and name for individual data

    if strcmp(options.itargetf, 'sfolder')
        stargetf = fileparts(reference_file);
        options.subjectname = '';
    else
        stargetf = targetf;
        options.subjectname = session(n).id;
    end

    % ---> run individual session
    try
        fcmaps = fc_ComputeSeedMaps(bolds, roidef, sframes, stargetf, options);
    catch ME
        fprintf(' ... ERROR: Computation of seed maps for %s failed with error: %s\n', session(n).id, ME.message);
        continue
    end

    % ------> Reorganize results

    nroi = length(fcmaps(1).roi);
    nset = length(fcmaps);

    for s = 1:nset

        if n == 1
            fcset(s).name = fcmaps(s).title;
        end

        % ---> set up data if the first subject

        if first_subject
            fcset(s).roi = fcmaps(s).roi;
        end
        
        for r = 1:nroi

            % -------> Create data files if it is the first run

            if first_subject
                fcset(s).group(r).fc = fcmaps(s).fc.zeroframes(nsub);                
                fcset(s).group(r).roi = fcmaps(s).roi{r};                
            end

            % -------> Embed data
            
            fcset(s).group(r).fc.data(:,n) = fcmaps(s).fc.data(:,r);
       end
   end
   first_subject = false;
   oksub(n) = 1;
end


%   ------------------------------------------------------------------------------------------
%                                                                       Save the group results

if options.verbose; fprintf('\n---------------------------------\nComputing group results\n'); end

% --- filter data by successful sessions

oksub = oksub == 1;

if sum(oksub) < nsub
    session = session(oksub);
    nsub = sum(oksub);

    for s = 1:nset
        for r = 1:nroi
            fcset(s).group(r).fc = fcset(s).group(r).fc.sliceframes(oksub);
        end
    end
end

% --- add extra info for files

for s = 1:nsub
    extra(s).key = ['session ' int2str(s)];
    extra(s).value = session(s).id;
end

% --- save loop

for setid = 1:nset
    if options.verbose; fprintf(' -> %s\n', fcset(setid).name); end
    
    for r = 1:nroi

        if options.verbose; fprintf('    ... for region %s', fcset(setid).roi{r}); end

        M = [];

        % --- compute additional data

        if any(ismember(options.savegroup, {'groupfz', 'groupp', 'groupz', 'groupr', 'allfz'}))
            fz = fcset(setid).group(r).fc;
            fz.data = fc_fisher(fz.data);
        end

        if any(ismember(options.savegroup, {'groupp', 'groupz'}))
            if cv
                [p Z M] = fcset(setid).group(r).fc.img_ttest_zero();
            else
                [p Z M] = fz.img_ttest_zero();
                gr = M.img_FisherInv();
            end
        end

        if any(ismember(options.savegroup, {'groupr', 'groupcv'})) && isempty(M)
            M = fcset(setid).group(r).fc.zeroframes(1);
            if cv
                M.data = mean(fcset(setid).group(r).fc.data, 2);
            else
                M.data = mean(fz.data, 2);
                gr = M.img_FisherInv();
            end
        end

        if options.verbose; fprintf(' ... saving ...'); end
        if isempty(fcset(setid).name)
            tname = lname;
        else
            tname = [lname '_' fcset(setid).name];
        end

        % --- save requested data

        % -- save group r results
        if any(ismember(options.savegroup, {'groupr'}))
            gr.img_saveimage([targetf '/' tname '_' fcset(setid).roi{r} '_group_r'], extra);
            if options.verbose; fprintf(' r'); end
        end

        % -- save group cv results
        if any(ismember(options.savegroup, {'groupcv'}))
            M.img_saveimage([targetf '/' tname '_' fcset(setid).roi{r} '_group_cv'], extra);
            if options.verbose; fprintf(' cv'); end
        end

        % -- save all fz results
        if any(ismember(options.savegroup, {'allfz'}))
            fz.img_saveimage([targetf '/' tname '_' fcset(setid).roi{r} '_all_Fz'], extra);
            if options.verbose; fprintf(' all_fz'); end
        end
        
        % -- save all cv results
        if any(ismember(options.savegroup, {'allcv'}))
            fcset(setid).group(r).fc.img_saveimage([targetf '/' tname '_' fcset(setid).roi{r} '_all_Fz'], extra);
            if options.verbose; fprintf(' all_cv'); end
        end

        % -- save group Fz results
        if any(ismember(options.savegroup, {'groupfz'}))
            M.img_saveimage([targetf '/' tname '_' fcset(setid).roi{r} '_group_Fz'], extra);
            if options.verbose; fprintf(' fz'); end
        end

        % -- save group p results
        if any(ismember(options.savegroup, {'groupp'}))
            p.img_saveimage([targetf '/' tname '_' fcset(setid).roi{r} '_group_p'], extra);
            if options.verbose; fprintf(' p'); end
        end

        % -- save group Z results
        if any(ismember(options.savegroup, {'groupz'}))
            Z.img_saveimage([targetf '/' tname '_' fcset(setid).roi{r} '_group_Z'], extra);
            if options.verbose; fprintf(' Z'); end
        end

        if options.verbose; fprintf(' ... done.\n'); end
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




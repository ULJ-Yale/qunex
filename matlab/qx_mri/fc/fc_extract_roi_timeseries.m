function [tsset] = fc_extract_roi_timeseries(flist, roiinfo, frames, targetf, options)

%function [tsset] = fc_extract_roi_timeseries(flist, roiinfo, frames, targetf, options)
%
%   Extract ROI timeseries for group or individual subject / session.
%
%   Parameters:
%       --flist (str):
%           A .list file listing the subjects and their files for which to
%           compute seedmaps. 
%
%           Alternatively, a string that specifies the list, session id(s)
%           and files to be used for computing seedmaps. The string has to
%           have the following form:
%           
%               'listname:<name>|session id:<session id>|file:<path to bold file>|
%                roi:<path to individual roi mask>'
%
%           Note:
%           - 'roi' is optional, if individual roi masks are to be used, 
%           - 'file' can be replaced by 'conc' if a conc file is provied.
%
%           Example:
%
%               'listname:wmlist|session id:OP483|file:bold1.nii.gz|roi:aseg.nii.gz'
%
%       --roiinfo (str):
%           A path to the names file specifying group based ROI for which to
%           extract timeseries for. 
%
%       --frames (cell array | int | str, default ''):
%           The definition of which frames to extract, specifically
%
%           - a numeric array mask defining which frames to use (1) and
%             which not (0), or
%
%           - a single number, specifying the number of frames to skip at
%             the start of each bold, or
%
%           - a string describing which events to extract timeseries for,
%             and the frame offset from the start and end of the event in
%             format::
%
%               '<extraction name>:<event list>:<extraction start>:<extraction end>'
%
%           where:
%
%           - extraction name
%               is the name for the specific extraction definition
%           - event list
%               is a comma separated list of events for which data is to
%               be extracted
%           - extraction start
%               is a frame number relative to event start or end when the
%               extraction should start
%           - extraction end
%               is a frame number relative to event start or end when the
%               extraction should start the extraction start and end
%               should be given as '<s|e><frame number>'. E.g.:
%
%               - 's0'  ... the frame of the event onset
%               - 's2'  ... the second frame from the event onset
%               - 'e1'  ... the first frame from the event end
%               - 'e0'  ... the last frame of the event
%               - 'e-2' ... the two frames before the event end.
%
%           Example::
%
%               'encoding:e-color,e-shape:s2:s2|delay:d-color,d-shape:s2:e0'
%
%       --targetf (str, default '.'):
%           The group level folder to save results in. 
%
%       --options (str, default 'sessions=all|roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|savegroup=none|saveind=none|itargetf=gfolder|tsname=|verbose=false|debug=false'):
%           A string specifying additional analysis options formated as pipe
%           separated pairs of colon separated key, value pairs::
%
%               "<key>:<value>|<key>:<value>".
%
%           It takes the following keys and values:
%
%           - sessions
%               Which sessions to include in the analysis. The sessions should
%               be provided as a comma or space separated list. If all sessions
%               are to be processed this can be designated by 'all'. Defaults
%               to 'all'.
%
%           - roimethod
%               What method to use to compute ROI signal:
%
%               - mean
%                   compute mean values across the ROI
%               - median
%                   compute median value across the ROI
%               - max
%                   compute maximum value across the ROI
%               - min
%                   compute mimimum value across the ROI
%               - pca
%                   compute first eigenvariate of the ROI.
%
%               Defaults to 'mean'.
%
%           - eventdata
%               What data to use from each event:
%
%               - all
%                   use all identified frames of all events
%               - mean
%                   use the mean across frames of each identified event
%               - min
%                   use the minimum value across frames of each identified
%                   event
%               - max
%                   use the maximum value across frames of each identified
%                   event
%               - median
%                   use the median value across frames of each identified
%                   event.
%                   
%               Defaults to 'all'.
%
%           - ignore
%               A comma separated list of information to identify frames to
%               ignore, options are:
%
%               - use
%                   ignore frames as marked in the use field of the bold file
%               - fidl
%                   ignore frames as marked in .fidl file (only available
%                   with event extraction)
%               - <column>
%                   the column name in ∗_scrub.txt file that matches bold file
%                   to be used for ignore mask.
%
%               Defaults to 'use,fidl'.
%
%           - badevents
%               What to do with events that have frames marked as bad, options
%               are:
%
%               - use
%                   use any frames that are not marked as bad
%               - <number>
%                   use the frames that are not marked as bad if at least
%                   <number> ok frames exist
%               - ignore
%                   if any frame is marked as bad, ignore the full event.
%
%               Defaults to 'use'.
%
%           - savegroup
%               A comma separated list of formats to use to save the group 
%               level timeseries data. The options are:
%
%               - long
%                   save the resulting data in a long format .tsv file
%               - wide
%                   save the resulting data in a wide format .tsv file
%               - mat
%                   save the resulting data in a matlab .mat file
%               - none
%                   do not save any group level results.
%
%               Defaults to 'none'.
%
%           - saveind
%               a comma separted list of formats to use to save the 
%               individual level timeseries data ['']:
%
%               - long 
%                   save the resulting data in a long format .tsv file
%               - wide
%                   save the resulting data in a wide format .tsv file
%               - mat
%                   save the resulting data in a matlab .mat file
%               - ptseries
%                   save the resulting data as a ptseries image
%               - none
%                   do not save any individual level results.
%
%               Defaults to 'none'.
%
%           - itargetf
%               Where to save the individual data:
%
%               - gfolder
%                   in the group target folder
%               - sfolder
%                   in the individual session folder.
%
%               Defaults to 'gfolder'.
%
%           - savesessionid
%               whether to add the id of the session or subject to the
%               individual output file when saving to the individual session
%               images/functional folder:
%
%               - true
%               - false.
%
%               Defaults to 'false'.
%
%           - tsname
%               an optional name describing the extracted timeseries to add
%               to the output files. If empty, it won't be used. Defaults to [''].
%
%           - verbose
%               Whether to be verbose when running the analysis:
%
%               - true
%               - false.
%
%               Defaults to 'false'.
%
%           - debug
%               Whether to print debug when running the analysis:
%
%               - true
%               - false.
%
%               Defauts to 'false'.
%
%   Returns:
%       tsmat
%           A structure array with the following fields for each specified
%           data extraction:
%
%           - title
%               the title of the extraction as specifed in the frames string, empty 
%               if extraction was specified using a numeric value 
%           - roi
%               a cell array with the names of the ROI used in the order they were
%               used for timeseries extraction
%           - N
%               number of extracted frames
%           - ts
%               the extracted timeseries matrix in the format ROI x timepoint
%
%   Output files:
%       Based on saveind option specification a file may be saved with the extracted
%       timeseries saved in a matlab.mat file and/or in a .tsv format:
%
%       <targetf>/<name>[_<tsname>][_<subjectid>]_ts[_<long|wide>].<tsv|mat>
%
%       `<name>` is the provided name of the bold(s).
%       `<tsname>` is the optional name for the extracted timeseries if it was 
%       specified.
%       `<subjectid>` is the single session id. It is added in case of single 
%       session extraction if it was specified and if savesessionid was set to 'true'.
%       It is allways added in the context of group data extraction when the single
%       session data extraction is saved to the specified group target folder. 
%       `<long|wide>` is the provided text format, if it was specified.
%
%       The text .tsv file(s) will have the following columns:
%       
%       long format         wide format
%       - name              - name
%       - title             - title
%       - subject           - subject
%       - roi_name          - event
%       - roi_code          - event
%       - event             - frame
%       - frame             - [<roi_code>]_<roi_name>
%       - value
%   
%       - 'event' refers to the index of the extracted event.
%       - When all frames are extracted, 'frame' refers to the frame number within
%         the original BOLD timeseries. When a summary for each event is extracted
%         (e.g. mean across frames), then 'frame' refers to the number of frames
%         that were included in computation of the summary measure.
%
%   Notes:
%       The method returns a structure array named fcmaps with the fields lised
%       above for each specified data extraction.
%
%       Use:
%           The function extracts timeseries for the specified ROI. If an event string is 
%           provided, it has to start with a path to the .fidl file to be used to extract 
%           the events, following by a pipe separated list of event extraction definitions:
%
%               <title>:<eventlist>:<frame offset1>:<frame offset2>
%
%           multiple extractions can be specified by separating them using the pipe '|' 
%           separator. Specifically, for each extraction, all the events listed in a
%           comma-separated eventlist will be considered (e.g. 'congruent,incongruent'). 
%           For each event all the frames starting from the specified beginning and ending
%           offset will be extracted. If options eventdata is specified as 'all', all the
%           specified frames will be concatenated in a single timeseries, otherwise, each
%           event will be summarised by a single frame in a newly generated events series 
%           image.
%   
%           From the resulting timeseries, ROI series will be extracted for each specified 
%           ROI as specified by the roimethod option. 
%
%           The results will be returned in a tsmat structure and, if so specified, saved.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 5 || isempty(options), options = '';  end
if nargin < 4 || isempty(targetf), targetf = '.'; end
if nargin < 3 frames  = []; end
if nargin < 2 error('ERROR: At least file list and ROI .names file have to be specified!'); end

% --------------------------------------------------------------
%                                              parcel processing

parcels = {};
if starts_with(roiinfo, 'parcels:')
    parcels = strtrim(regexp(roiinfo(9:end), ',', 'split'));
end

% ----- parse options

default = 'sessions=all|roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|savegroup=none|itargetf=gfolder|saveind=none|tsname=|savesessionid=false|verbose=true|debug=false';
options = general_parse_options([], options, default);

verbose       = strcmp(options.verbose, 'true');
printdebug    = strcmp(options.debug, 'true');
savesessionid = strcmp(options.savesessionid, 'true') || strcmp(options.savesessionid, 'yes') || strcmp(options.itargetf, 'gfolder');
gem_options = sprintf('ignore:%s|badevents:%s|verbose:%s|debug:%s', options.ignore, options.badevents, options.verbose, options.debug);

if printdebug
    general_print_struct(options, 'fc_extract_roi_timeseries options used');
end

if verbose; fprintf('\nChecking ...\n'); end

options.flist = flist;
options.roiinfo = roiinfo;
options.targetf = targetf;

general_check_options(options, 'eventdata, roimethod, flist, roiinfo, targetf', 'stop');


% --- File saving related options

if options.tsname
    tsname = [options.tsname, '_'];
else
    tsname = '';
end

ftail = 'ts';
fout_glong = false;
fout_gwide = false;

% ----- What should be saved -- Group level

options.savegroup= strtrim(regexp(options.savegroup, ',', 'split'));
if ismember({'none'}, options.savegroup)
    options.savegroup = {};
end
sdiff = setdiff(options.savegroup, {'mat', 'long', 'wide', ''});
if ~isempty(sdiff)
    error('ERROR: Invalid group save format specified: %s', strjoin(sdiff,","));
end

% --- Individual level

options.saveind = strtrim(regexp(options.saveind, ',', 'split'));
if ismember({'none'}, options.saveind)
    options.saveind = {};
end
sdiff = setdiff(options.saveind, {'mat', 'long', 'wide', 'ptseries', ''});
if ~isempty(sdiff)
    error('ERROR: Invalid individual save format specified: %s', strjoin(sdiff,","));
end
saveptseries = ismember('ptseries', options.saveind);

%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf(' ... listing files to process');

list = general_read_file_list(flist, options.sessions, [], verbose);

lname = strrep(list.listname, '.list', '');
lname = strrep(lname, '.conc', '');
lname = strrep(lname, '.4dfp', '');
lname = strrep(lname, '.img', '');

if ~ verbose
    fprintf(' ... done.\n');
end

%   ------------------------------------------------------------------------------------------
%                                                The main loop ... go through all the sessions

first_subject = true;
oksub         = zeros(1, length(list.session));
embed_data    = nargout > 0 || ~isempty(options.savegroup);

if ~isempty(options.savegroup)
    groupbasefilename = fullfile(targetf, sprintf('%s_%s%s', lname, tsname, ftail));

    if ismember({'long'}, options.savegroup)
        if verbose; fprintf(' ... opening long group tsv file\n'); end
        fout_glong = fopen([groupbasefilename '_long.tsv'], 'w');
    end

    if ismember({'wide'}, options.savegroup)
        if verbose; fprintf(' ... opening wide tsv file\n'); end
        fout_gwide = fopen([groupbasefilename '_wide.tsv'], 'w');
    end
end

c = 0;
for s = 1:list.nsessions

    go = true;

    if verbose; fprintf('\n---------------------------------\nProcessing session %s', list.session(s).id); end
    
    % ---> check roi files

    if isfield(list.session(s), 'roi')
        go = go & general_check_file(list.session(s).roi, [list.session(s).id ' individual ROI file'], 'error');
        sroifile = list.session(s).roi;
    else
        sroifile = [];
    end

    % ---> check bold files

    if isfield(list.session(s), 'conc') && ~isempty(list.session(s).conc)
        go = go & general_check_file(list.session(s).conc, 'conc file', 'error');
        bolds = general_read_concfile(list.session(s).conc);
    elseif isfield(list.session(s), 'files') && ~isempty(list.session(s).files) 
        bolds = list.session(s).files;
    else
        fprintf(' ... ERROR: %s missing bold or conc file specification!\n', list.session(s).id);
        go = false;
    end    

    for bold = bolds
        go = go & general_check_file(bold{1}, 'bold file', 'error');
    end

    reference_file = bolds{1};

    % ---> setting up frames parameter

    if isempty(frames)
        frames = 0;
    elseif isa(frames, 'char')
        frames = str2num(frames);        
        if isempty(frames) 
            if isfield(list.session(s), 'fidl')
                go = go & general_check_file(list.session(s).fidl, [list.session(s).id ' fidl file'], 'error');
            else
                go = false;
                fprintf(' ... ERROR: %s missing fidl file specification!\n', list.session(s).id);
            end
        end
    end

    if ~go, continue; end

    % ---> setting up target folder and name for individual data

    if strcmp(options.itargetf, 'sfolder')
        stargetf = fileparts(reference_file);
        if ends_with(stargetf, '/concs')
            stargetf = strrep(stargetf, '/concs', '');
        end
    else
        stargetf = targetf;
    end
    subjectid = list.session(s).id;

    % ---> reading image files

    if verbose; fprintf('     ... reading image file(s)'); end
    y = nimage(strjoin(bolds, '|'));
    y.data = y.image2D;
    if verbose; fprintf(' ... %d frames read, done.\n', y.frames); end

    % ---> processing roi/parcels info

    if isempty(parcels)
        if verbose; fprintf('     ... creating ROI mask\n'); end
        roi = nimage.img_prep_roi(roiinfo, sroifile);
    else
        if ~isfield(y.cifti, 'parcels') || isempty(y.cifti.parcels)
            error('ERROR: The bold file lacks parcel specification! [%s]', list.session(s).id);
        end
        if length(parcels) == 1 && strcmp(parcels{1}, 'all')        
            parcels = y.cifti.parcels;
        end
        for r = 1:length(parcels)
            roi.roi(r).roiname = parcels{r};
            [~, roi.roi(r).roicode] = ismember(parcels{r}, y.cifti.parcels);
        end
    end

    roi_names = {roi.roi.roiname};
    roi_codes = [roi.roi.roicode];
    nroi = length(roi.roi);
    nparcels = length(parcels);

    % ---> create extraction sets

    if verbose; fprintf('     ... generating extraction sets\n'); end
    exsets = y.img_get_extraction_matrices(frames, gem_options);
    for n = 1:length(exsets)
        if verbose; fprintf('         -> %s: %d good events, %d good frames\n', exsets(n).title, size(exsets(n).exmat, 1), sum(exsets(n).estat)); end
    end

    % ---> loop through extraction sets

    if verbose; fprintf('     ... extracting timeseries\n'); end

    nsets = length(exsets);
    for n = 1:nsets        
        if verbose; fprintf('         ... set %s\n', exsets(n).title); end
        
        % ---> get the extracted timeseries
    
        tsimg = y.img_extract_timeseries(exsets(n).exmat, options.eventdata);
    
        if isempty(parcels)
            ts = tsimg.img_extract_roi(roi, [], options.roimethod, [], [], saveptseries);
        else
            ts = tsimg.img_extract_roi(roiinfo, [], options.roimethod, [], [], saveptseries); 
        end
        if saveptseries
            ptimage = ts;
            ts = ts.data;
        end

        if verbose; fprintf('         ... extracted ts\n'); end

        % ---> Embed results
        
        tsmat(n).title    = exsets(n).title;
        tsmat(n).roinames = {roi.roi.roiname};
        tsmat(n).roicodes = [roi.roi.roicode];
        tsmat(n).N        = size(ts, 2);
        tsmat(n).ts       = ts;
        tsmat(n).tevents  = tsimg.tevents;
        tsmat(n).tframes  = tsimg.tframes;

        if verbose; fprintf('         ... embedded ts\n'); end
    end
    c = c + 1;

    % ===================================================================================================
    %                                                                                        save results

    if any(ismember({'mat', 'long', 'wide'}, options.saveind)) || any(ismember({'mat', 'long', 'wide'}, options.savegroup))
        if verbose; fprintf('     ... saving timeseries\n'); end
    end

    % set subjectname

    if savesessionid && ~isempty(list.session(s).id)
        subjectname = [list.session(s).id, '_'];
    else
        subjectname = '';
    end

    indbasefilename = fullfile(targetf, sprintf('%s_%s%s%s', lname, tsname, subjectname, ftail));

    % ---------------------------------------------------------------------------------------------------
    %                                                                                              matlab

    if ismember({'mat'}, options.saveind)
        if verbose; fprintf('         ... saving mat file'); end
        try
            save(indbasefilename, 'tsmat', '-v7.3');
        catch
            if verbose; fprintf(' ... failed to save using -v7.3. Using default format instead.'); end
            save(indbasefilename, 'tsmat');
        end
        if verbose; fprintf(' ... done\n'); end
    end

    % ---------------------------------------------------------------------------------------------------
    %                                                                                            ptseries

    if ismember({'ptseries'}, options.saveind)
        if verbose; fprintf('         ... saving ptseries image'); end
        ptimage.img_saveimage([indbasefilename '.ptseries.nii']);
        if verbose; fprintf(' ... done\n'); end
    end


    % ---------------------------------------------------------------------------------------------------
    %                                                                                            long tsv

    if ismember({'long'}, options.saveind) || ismember({'long'}, options.savegroup)
        if verbose; fprintf('         ... saving long tsv file'); end
        
        if first_subject
            long_header = 'name\ttitle\tsubject\troi_name\troi_code\tevent\tframe\tvalue\n';
            if fout_glong; fprintf(fout_glong, long_header); end
        end

        if ismember({'long'}, options.saveind)
            fout_ilong = fopen([indbasefilename '_long.tsv'], 'w');
            fprintf(fout_ilong, long_header);
        else
            fout_ilong = false;
        end

        for n = 1:nsets
            if tsmat(n).title, settitle = tsmat(n).title; else settitle = 'timeseries'; end

            % --- write up
            nframes = tsmat(n).N;
            
            for r = 1:nroi
                for f = 1:nframes
                    long_line = sprintf('%s\t%s\t%s\t%s\t%d\t%d\t%d\t%.5f\n', lname, settitle, list.session(s).id, roi_names{r}, roi_codes(r), tsmat(n).tevents(f), tsmat(n).tframes(f), tsmat(n).ts(r, f));
                    if fout_ilong; fprintf(fout_ilong, long_line); end
                    if fout_glong; fprintf(fout_glong, long_line); end
                end
            end
        end
        if fout_ilong; fclose(fout_ilong); end
        if verbose; fprintf(' ... done\n'); end
    end

    % ---------------------------------------------------------------------------------------------------
    %                                                                                            wide tsv

    if ismember({'wide'}, options.saveind) || ismember({'wide'}, options.savegroup)
        if verbose; fprintf('         ... saving wide tsv file'); end
        
        if first_subject
            wide_header = sprintf('name\ttitle\tsubject\tevent\tframe');
            for r = 1:nroi
                wide_header = [wide_header sprintf('\t[%d]_%s', roi_codes(r), roi_names{r})];
            end
            if fout_gwide; fprintf(fout_gwide, wide_header); end
        end

        if ismember({'wide'}, options.saveind)
            fout_iwide = fopen([indbasefilename '_wide.tsv'], 'w');
            fprintf(fout_iwide, wide_header);
        else
            fout_iwide = false;
        end

        for n = 1:nsets
            if tsmat(n).title, settitle = tsmat(n).title; else settitle = 'timeseries'; end

            % --- write up
            nframes = tsmat(n).N;
            for f = 1:nframes
                wide_line = sprintf('\n%s\t%s\t%s\t%d\t%d', lname, settitle, list.session(s).id, tsmat(n).tevents(f), tsmat(n).tframes(f));
                wide_line = [wide_line sprintf('\t%.5f', tsmat(n).ts(:, f))];
                if fout_iwide; fprintf(fout_iwide, wide_line); end
                if fout_gwide; fprintf(fout_gwide, wide_line); end
            end
        end
        if fout_iwide; fclose(fout_iwide); end
        if verbose; fprintf(' ... done\n'); end
    end

    % ---------------------------------------------------------------------------------------------------
    %                                                                             compile group structure

    if ismember({'mat'}, options.savegroup) || nargout > 0
        nset = length(tsmat);

        for n = 1:nsets

            tsset(n).title    = tsmat(n).title;            
            tsset(n).roinames = tsmat(n).roinames;                
            tsset(n).roicodes = tsmat(n).roicodes;                

            % ---> Embed data
            tsset(n).subject(c).id      = list.session(c).id;
            tsset(n).subject(c).N       = tsmat(n).N;
            tsset(n).subject(c).ts      = tsmat(n).ts;
            tsset(n).subject(c).tevents = tsmat(n).tevents;
            tsset(n).subject(c).tframes = tsmat(n).tframes;
        end
    end

    first_subject = false;
end

if ~isempty(options.savegroup) && verbose, fprintf('\n----------------------------------\n'); end

if ismember({'mat'}, options.savegroup)
    if verbose; fprintf('... saving group mat file'); end
    try
        save(indbasefilename, 'tsset', '-v7.3');
    catch
        if verbose; fprintf(' ... failed to save using -v7.3. Using default format instead.'); end
        save(indbasefilename, 'tsset');
    end
    if verbose; fprintf(' ... done\n'); end
end

if fout_glong 
    fclose(fout_glong); 
    if verbose, fprintf('... closed group long tsv file\n'); end 
end

if fout_gwide 
    fclose(fout_gwide); 
    if verbose, fprintf('... closed group wide tsv file\n'); end 
end

if printdebug; fprintf('DONE\n'); end

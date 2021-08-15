% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function [tsset] = fc_extract_roi_timeseries(flist, roiinfo, frames, targetf, options)

%function [tsset] = fc_extract_roi_timeseries(flist, roiinfo, frames, targetf, options)
%
%   Extract ROI timeseries for group or individual subject / session.
%
%   INPUTS
%   ======
%
%   --flist     For individual subjects, a string with a pipe separated 
%               information including: 
%               '<timeseries name>|<subjid>|<path to file 1>[|<path to file 2>]'
%               The first element is the timeseries name to be used when saving 
%               the data. The second element is the session id. The following 
%               elements are paths to bold files to extract the data from.
%               E.g.: 'rest|s01|<path to rest file 1>|<path to rest file 2>'
%
%               For group of sessions a .list file listing the subjects and 
%               their files for which to compute extract ROI timeseries,
%               or a well strucutured file list string 
%               (see `general_read_file_list`).
%
%   --roiinfo   A path to the names file specifying group based ROI for which to
%               extract timeseries for. 
%               Optionally, in case of individual subjects or sessions, a path 
%               to an image file holding subject/session specific ROI definition.
%               separated by a pipe '|' symbol.
%
%   --frames    The definition of which frames to extract, specifically:
%
%               -  a numeric array mask defining which frames to use (1) and 
%                  which not (0), or 
%               -  a single number, specifying the number of frames to skip at 
%                  the start of each bold, or
%               -  a string describing which events to extract timeseries for, 
%                  and the frame offset from the start and end of the event in 
%                  format::
%                   
%                  individual session
%                      '<fidlfile>|<extraction name>:<event list>:<extraction start>:<extraction end>'
%
%                  group data
%                      '<extraction name>:<event list>:<extraction start>:<extraction end>'
%
%                  where:
%
%                  fidlfile        
%                      is a path to the fidle file that defines the events    
%                  extraction name 
%                      is the name for the specific extraction definition    
%                  event list      
%                      is a comma separated list of events for which data is to 
%                      be extracted    
%                  extraction start
%                      is a frame number relative to event start or end when the 
%                      extraction should start    
%                  extraction end  
%                      is a frame number relative to event start or end when the
%                      extraction should end. 
%
%                      The extraction start and end 
%                      should be given as '<s|e><frame number>'. E.g.:
%
%                      - s0  ... the frame of the event onset 
%                      - s2  ... the second frame from the event onset 
%                      - e1  ... the first frame from the event end 
%                      - e0  ... the last frame of the event 
%                      - e-2 ... the two frames before the event end
%                      
%                  Example::
%
%                      '<fidlfile>|encoding:e-color,e-shape:s2:s2|delay:d-color,d-shape:s2:e0'
%
%   --targetf   The folder to save images in ['.']. In case of group data it 
%               should point to the location to store qroup level data. In case
%               of individual extraction, the location of session functional 
%               images folder.
%
%   --options   A string specifying additional analysis options formated as pipe 
%               separated pairs of colon separated key, value pairs: 
%               "<key>:<value>|<key>:<value>".
%
%               It takes the following keys and values:
%
%               roimethod 
%                   What method to use to compute ROI signal ['mean']: 
%
%                   mean
%                       mean value across the ROI
%	                median
%                       median value across the ROI
%	                max
%                       maximum value across the ROI
%	                min
%                       mimimum value across the ROI
%                   pca
%                       first eigenvariate of the ROI
%
%               eventdata
%                   What data to use from each event ['all']:
%
%                   all    
%                       use all identified frames of all events
%                   mean   
%                       use the mean across frames of each identified event
%                   min    
%                       use the minimum value across frames of each identified 
%                       event
%                   max    
%                       use the maximum value across frames of each identified 
%                       event
%                   median 
%                       use the median value across frames of each identified 
%                       event
%
%               ignore
%                   A comma separated list of information to identify frames to 
%                   ignore, options are ['use,fidl']:
%
%                   use      
%                       ignore frames as marked in the use field of the bold file
%                   fidl     
%                       ignore frames as marked in .fidl file (only available 
%                       with event extraction)
%                   <column> 
%                       the column name in *_scrub.txt file that matches bold file 
%                       to be used for ignore mask
%
%               badevents
%                   What to do with events that have frames marked as bad, options 
%                   are ['use']:
%
%                   use      
%                       use any frames that are not marked as bad
%                   <number> 
%                       use the frames that are not marked as bad if at least 
%                       <number> ok frames exist
%                   ignore   
%                       if any frame is marked as bad, ignore the full event
%
%               savegroupts
%                   A comma separated list of formats to use to save the group 
%                   level timeseries data ['']:
%
%                   long
%                       save the resulting data in a long format .tsv file
%                   wide
%                       save the resulting data in a wide format .tsv file
%                   mat
%                       save the resulting data in a matlab .mat file
%
%               indtargetf 
%                   In case of group level extraction, where to save the 
%                   individual data ['gfolder']:
%
%                   gfolder
%                       in the group target folder
%                   sfolder
%                       in the individual session folder
%
%               saveindts
%                   a comma separted list of formats to use to save the 
%                   individual level timeseries data ['']:
%
%                   long 
%                       save the resulting data in a long format .tsv file
%                   wide
%                       save the resulting data in a wide format .tsv file
%                   mat
%                       save the resulting data in a matlab .mat file
%                                 
%               tsname
%                   an optional name describing the extracted timeseries to add
%                   to the output files, if empty, it won't be used ['']
%
%               addidtofile
%                   When running single session extraction or when saving to the
%                   individual session functional images folder, whether to add 
%                   subjectid to the single session filename, if one is provided 
%                   ['false'].
%
%               verbose
%                   Whether to be verbose 'true' or not 'false', when running the 
%                   analysis ['true']
%
%   RESULTS
%   =======
%
%   The function returns a structure array with the following fields for each specified
%   data extraction:
%
%   tsmat
%       title 
%           the title of the extraction as specifed in the frames string, empty 
%           if extraction was specified using a numeric value 
%       roi   
%           a cell array with the names of the ROI used in the order they were
%           used for timeseries extraction
%       N     
%           number of extracted frames 
%       ts     
%           the extracted timeseries matrix in the format ROI x timepoint
%
%   Based on saveind option specification a file may be saved with the extracted
%   timeseries saved in a matlab.mat file and/or in a .tsv format::
%
%       <targetf>/<name>[_<tsname>][_<subjectid>]_ts[_<long|wide>].<tsv|mat>
%
%   `<name>` is the provided name of the bold(s).
%   `<tsname>` is the optional name for the extracted timeseries if it was 
%   specified.
%   `<subjectid>` is the single session id. It is added in case of single 
%   session extraction if it was specified and if addidtofile was set to 'true'.
%   It is allways added in the context of group data extraction when the single
%   session data extraction is saved to the specified group target folder. 
%   `<long|wide>` is the provided text format, if it was specified.
%
%   The text .tsv file(s) will have the following columns:
%   
%   long format         wide format
%   - name              - name
%   - title             - title
%   - subject           - subject
%   - roi_name          - event
%   - roi_code          - event
%   - event             - frame
%   - frame             - [<roi_code>]_<roi_name>
%   - value
%   
%   Note:
%       - 'event' refers to the index of the extracted event.
%       - When all frames are extracted, 'frame' refers to the frame number within
%         the original BOLD timeseries. When a summary for each event is extracted
%         (e.g. mean across frames), then 'frame' refers to the number of frames
%         that were included in computation of the summary measure.
%
%   USE
%   ===
% 
%   The function extracts timeseries for the specified ROI. If an event string is 
%   provided, it has to start with a path to the .fidl file to be used to extract 
%   the events, following by a pipe separated list of event extraction definitions:
%
%   <title>:<eventlist>:<frame offset1>:<frame offset2>
%
%   multiple extractions can be specified by separating them using the pipe '|' 
%   separator. Specifically, for each extraction, all the events listed in a
%   comma-separated eventlist will be considered (e.g. 'congruent,incongruent'). 
%   For each event all the frames starting from the specified beginning and ending
%   offset will be extracted. If options eventdata is specified as 'all', all the
%   specified frames will be concatenated in a single timeseries, otherwise, each
%   event will be summarised by a single frame in a newly generated events series 
%   image.
%   
%   From the resulting timeseries, ROI series will be extracted for each specified 
%   ROI as specified by the roimethod option. 
%
%   The results will be returned in a tsmat structure and, if so specified, saved.
%

if nargin < 5 || isempty(options), options = '';  end
if nargin < 4 || isempty(targetf), targetf = '.'; end
if nargin < 3 frames  = []; end
if nargin < 2 error('ERROR: At least data and ROI .names file have to be specified!'); end

% ----- parse options

default = 'roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|savegroupts=none|indtargetf=gfolder|saveindts=none|tsname=|addidtofile=false|verbose=true|verboselevel=high';
options = general_parse_options([], options, default);

verbose     = strcmp(options.verbose, 'true');
detailed    = strcmp(options.verboselevel, 'high');
addidtofile = strcmp(options.addidtofile, 'true');

if verbose && detailed
    general_print_struct(options, 'Options used');
end

if ~ismember(options.eventdata, {'all', 'mean', 'min', 'max', 'median'})
    error('ERROR: Invalid eventdata option: %s', options.eventdata);
end

if ~ismember(options.roimethod, {'mean', 'pca', 'median', 'max', 'min'})
    error('ERROR: Invalid roi extraction method: %s', options.roimethod);
end


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

options.savegroupts= strtrim(regexp(options.savegroupts, ',', 'split'));
if ismember({'none'}, options.savegroupts)
    options.savegroupts = {};
end
sdiff = setdiff(options.savegroupts, {'mat', 'long', 'wide', ''});
if ~isempty(sdiff)
    error('ERROR: Invalid group save format specified: %s', strjoin(sdiff,","));
end

% --- Individual level

options.saveindts = strtrim(regexp(options.saveindts, ',', 'split'));
if ismember({'none'}, options.saveindts)
    options.saveindts = {};
end
sdiff = setdiff(options.saveindts, {'mat', 'long', 'wide', ''});
if ~isempty(sdiff)
    error('ERROR: Invalid individual save format specified: %s', strjoin(sdiff,","));
end

% --- Group level extraction

go = true;
if (startsWith(strtrim(flist), 'listname')) || (endsWith(strtrim(flist), '.list'))
    groupextraction = true;
    go = go & general_check_file(flist, 'image file list', 'error');

    if verbose && detailed; fprintf('\n\nStarting ...\n'); end

    %   ------------------------------------------------------------------------------------------
    %                                                      make a list of all the files to process

    if verbose && detailed; fprintf(' ... listing files to process'); end

    [subject, nsub, nfiles, listname] = general_read_file_list(flist, verbose);

    lname = strrep(listname, '.list', '');
    lname = strrep(lname, '.conc', '');
    lname = strrep(lname, '.4dfp', '');
    lname = strrep(lname, '.img', '');

    if strcmp(options.indtargetf, 'gfolder')
        addidtofile = true;
    end

    % -- check and set up group results folder and files
    go = go & general_check_file(roiinfo, 'ROI definition file', 'error');
    general_check_folder(targetf, 'results folder');

    if ~isempty(options.savegroupts)
        groupbasefilename = fullfile(targetf, sprintf('%s_%s%s', lname, tsname, ftail));
    
        if ismember({'long'}, options.savegroupts)
            if verbose; fprintf(' ... opening long group tsv file\n'); end
            fout_glong = fopen([groupbasefilename '_long.tsv'], 'w');
        end

        if ismember({'wide'}, options.savegroupts)
            if verbose; fprintf(' ... opening wide tsv file\n'); end
            fout_gwide = fopen([groupbasefilename '_wide.tsv'], 'w');
        end
    end

    if verbose && detailed; fprintf(' ... done.\n'); end

% --- Single session level extraction
else
    groupextraction = false;
    options.savegroupts = {};
    nsub = 1;
    % ----- get file information

    % -- name, subject, bold
    subjinfo = strtrim(regexp(flist, '\|', 'split'));
    if length(subjinfo) < 3
        error('ERROR: Missing information in flist parameter. Please provide full information on timeseries, subject id, and bold files!');
    end
    lname      = subjinfo{1};
    subject.id = subjinfo{2};
    boldlist   = subjinfo(3:end);

    % -- roi
    [roiinfo, sroifile] = strtok(roiinfo, '|');
    if sroifile
        sroifile = sroifile(2:end);
    else
        sroifile = [];
    end

    % -- fidl    
    if isa(frames, 'char')
        [fidlfile, frames] = strtok(frames, '|');
        if ~endsWith(fidlfile, '.fidl') || isempty(frames)
            error('ERROR: Missing information in frames parameter. Please provide fidl file and event extraction information!');
        end
        frames = frames(2:end);
    else
        fidlfile = [];
    end

    % -- pull together
    subject.files = boldlist;
    subject.roi   = sroifile;
    subject.fidl  = fidlfile; 
end

% --- general checks

if ~go
    error('ERROR: Some of the specified files were not found. Please check the paths and start again!');
end

% --- run the loop


c = 0;
for s = 1:nsub
    go = true;
    if verbose && detailed; fprintf('\n----------------------------------\nprocessing %s\n', subject(s).id); end
    
    % ----- Check if the files are there!
    if verbose && detailed; fprintf('\nChecking ...\n'); end
    
    % -- bold files
    if isfield(subject(s), 'files') && ~isempty(subject(s).files) 
        for bold = subject(s).files
            go = go & general_check_file(bold{1}, bold{1}, 'error');
        end
    end

    % -- conc files (map them to bold)
    if isfield(subject(s), 'conc') && ~isempty(subject(s).conc) 
        go = go & general_check_file(subject(s).conc, subject(s).conc, 'error');
        subject(s).files = [subject(s).conc];
    end

    % -- subject ROI file
    if isfield(subject(s), 'roi') && ~isempty(subject(s).roi)
        go = go & general_check_file(subject(s).roi, [subject(s).id ' individual ROI file'], 'error');
        sroiinfo = subject(s).roi;
    else
        sroiinfo = [];
    end

    % ---> setting up frames parameter

    if isa(frames, 'char')
        if isfield(subject(s), 'fidl')
            go = go & general_check_file(subject(s).fidl, [subject(s).id ' fidl file'], 'error');
            sframes = [subject(s).fidl '|' frames];
        else
            go = false
            fprintf(' ... ERROR: %s missing fidl file specification!\n', subject(s).id);
        end
    else
        sframes = frames;
    end

    if ~go, continue; end

    % ---> setting up and checking target folder for individual data

    if groupextraction 
        if strcmp(options.indtargetf, 'sfolder')
            reference = subject(s).files{1};
            if regexp(reference, '.conc$')
                reference = general_read_concfile(reference);
                reference = reference{1};
            end
            stargetf = fileparts(reference);
        else
            stargetf = targetf;
            options.addidtofile = 'true';
        end
    else
        stargetf = targetf;
    end

    if any(ismember({'long', 'wide', 'mat'}, options.saveindts))
        go = go & general_check_folder(stargetf, 'results folder', true, verbose & detailed);
    end

    if ~go, continue; end
    
    %   ------------------------------------------------------------------------------------------
    %                                                                            do the processing

    try 
        if verbose; fprintf('     ... creating ROI mask\n'); end

        roi  = nimage.img_read_roi(roiinfo, sroiinfo);
        nroi = length(roi.roi.roinames);
        roi_names = roi.roi.roinames;
        roi_codes = roi.roi.roicodes;

        % ---> reading image files

        if verbose; fprintf('     ... reading image file(s)'); end
        y = nimage(subject(s).files);
        if verbose; fprintf(' ... %d frames read, done.\n', y.frames); end

        % ---> create extraction sets

        if verbose; fprintf('     ... generating extraction sets\n'); end
        exsets = y.img_get_extraction_matrices(sframes, options);
        for n = 1:length(exsets)
            if verbose; fprintf('         -> %s: %d good events, %d good frames\n', exsets(n).title, size(exsets(n).exmat, 1), sum(exsets(n).estat)); end
        end
    catch ME
        fprintf(' ... ERROR: Preparing extraction of ROI timeseries for %s failed with error: %s\n', subject(s).id, ME.message);
        continue
    end

    % ---> loop through extraction sets

    c = c + 1;
    
    if verbose; fprintf('     ... extracting timeseries\n'); end
    nsets = length(exsets);
    for n = 1:nsets

        if verbose; fprintf('         -> %s:', exsets(n).title); end
        
        % --> get the extracted timeseries

        tsimg = y.img_extract_timeseries(exsets(n).exmat, options.eventdata);
        ts    = tsimg.img_extract_roi(roi, [], options.roimethod);

        if verbose; fprintf(' extracted'); end
        
        % ------> Embed results

        tsmat(n).title    = exsets(n).title;
        tsmat(n).roinames = roi.roi.roinames;
        tsmat(n).roicodes = roi.roi.roicodes;
        tsmat(n).N        = size(ts, 2);
        tsmat(n).ts       = ts;
        tsmat(n).tevents  = tsimg.tevents;
        tsmat(n).tframes  = tsimg.tframes;

        if verbose; fprintf(', embedded\n'); end
    end

    % ===================================================================================================
    %                                                                                        save results

    if any(ismember({'mat', 'long', 'wide'}, options.saveindts)) || any(ismember({'mat', 'long', 'wide'}, options.savegroupts))
        if verbose; fprintf('     ... saving timeseries\n'); end
    end

    % set subjectname

    if addidtofile && ~isempty(subject(s).id)
        subjectname = [subject(s).id, '_'];
    else
        subjectname = '';
    end

    indbasefilename = fullfile(targetf, sprintf('%s_%s%s%s', lname, tsname, subjectname, ftail));

    % ---------------------------------------------------------------------------------------------------
    %                                                                                              matlab

    if ismember({'mat'}, options.saveindts)
        if verbose; fprintf('         ... saving mat file'); end
        save(indbasefilename, 'tsmat', '-v7.3');
        if verbose; fprintf(' ... done\n'); end
    end


    % ---------------------------------------------------------------------------------------------------
    %                                                                                            long tsv

    if ismember({'long'}, options.saveindts) || ismember({'long'}, options.savegroupts)
        if verbose; fprintf('         ... saving long tsv file'); end
        
        if c == 1
            long_header = 'name\ttitle\tsubject\troi_name\troi_code\tevent\tframe\tvalue\n';
            if fout_glong; fprintf(fout_glong, long_header); end
        end

        if ismember({'long'}, options.saveindts)
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
                    long_line = sprintf('%s\t%s\t%s\t%s\t%d\t%d\t%d\t%.5f\n', lname, settitle, subject(s).id, roi_names{r}, roi_codes(r), tsmat(n).tevents(f), tsmat(n).tframes(f), tsmat(n).ts(r, f));
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

    if ismember({'wide'}, options.saveindts) || ismember({'wide'}, options.savegroupts)
        if verbose; fprintf('         ... saving wide tsv file'); end
        
        if c == 1
            wide_header = sprintf('name\ttitle\tsubject\tevent\tframe');
            for r = 1:nroi
                wide_header = [wide_header sprintf('\t[%d]_%s', roi_codes(r), roi_names{r})];
            end
            if fout_gwide; fprintf(fout_gwide, wide_header); end
        end

        if ismember({'wide'}, options.saveindts)
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
                wide_line = sprintf('\n%s\t%s\t%s\t%d\t%d', lname, settitle, subject(s).id, tsmat(n).tevents(f), tsmat(n).tframes(f));
                wide_line = [wide_line sprintf('\t%.5f', tsmat(n).ts(:, f))];
                if fout_iwide;   fprintf(fout_iwide,   wide_line); end
                if fout_gwide; fprintf(fout_gwide, wide_line); end
            end
        end
        if fout_iwide; fclose(fout_iwide); end
        if verbose; fprintf(' ... done\n'); end
    end

    % ---------------------------------------------------------------------------------------------------
    %                                                                             compile group structure

    if ismember({'wide'}, options.savegroupts) || nargout > 0
        nset = length(tsmat);

        for n = 1:nsets

            tsset(n).title    = tsmat(n).title;            
            tsset(n).roinames = tsmat(n).roinames;                
            tsset(n).roicodes = tsmat(n).roicodes;                

            % -------> Embed data
            tsset(n).subject(c).id      = subject(c).id;
            tsset(n).subject(c).N       = tsmat(n).N;
            tsset(n).subject(c).ts      = tsmat(n).ts;
            tsset(n).subject(c).tevents = tsmat(n).tevents;
            tsset(n).subject(c).tframes = tsmat(n).tframes;
        end
    end
end

if groupextraction && verbose, fprintf('\n----------------------------------\n'); end

if ismember({'mat'}, options.savegroupts)
    if verbose; fprintf('... saving group mat file'); end
    save([groupbasefilename '.mat'], 'tsset', '-v7.3');
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

if verbose && detailed; fprintf('DONE\n'); end

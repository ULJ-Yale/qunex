% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function [tsmat] = fc_extract_roi_timeseries(bolds, roiinfo, frames, targetf, options)

%function [tsmat] = fc_extract_roi_timeseries(bolds, roiinfo, frames, targetf, options)
%
%   Extract ROI timeseries for individual subject / session.
%
%   INPUTS
%   ======
%
%   --bolds     A string with a pipe separated list of paths to .conc or bold 
%               files. The first element has to be the name of the file or group  
%               to be used when saving the data. 
%               E.g.: 'rest|<path to rest file 1>|<path to rest file 2>'
%   --roiinfo   A path to the names file specifying group based ROI. Additionaly, 
%               separated by a pipe '|' symbol, a path to an image file holding 
%               subject/session specific ROI definition.
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
%                      '<fidlfile>|<extraction name>:<event list>:<extraction start>:<extraction end>'
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
%   --targetf   The folder to save images in ['.'].
%
%   --options   A string specifying additional analysis options formated as pipe 
%               separated pairs of colon separated key, value pairs: 
%               "<key>:<value>|<key>:<value>".
%
%               It takes the following keys and values:
%
%               roimethod 
%                   what method to use to compute ROI signal: 
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
%                   ['mean']
%
%               eventdata
%                   what data to use from each event:
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
%                   ['all']
%
%               ignore
%                   a comma separated list of information to identify frames to 
%                   ignore, options are:
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
%                   ['use,fidl']
%
%               badevents
%                   what to do with events that have frames marked as bad, options 
%                   are:
%
%                   use      
%                       use any frames that are not marked as bad
%                   <number> 
%                       use the frames that are not marked as bad if at least 
%                       <number> ok frames exist
%                   ignore   
%                       if any frame is marked as bad, ignore the full event
%
%                   ['use']
%
%               saveind
%                   a comma separted list of formats to use to save the data ['']:
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
%               subjectid
%                   an optional subject/session id to report in the results, 
%                   if empty, it won't be used ['']
%
%               addidtofile
%                   whether to add subjectid to the filename if a subject id, 
%                   is provided ['false']
%
%               verbose
%                   Whether to be verbose 'true' or not 'false', when running the 
%                   analysis ['false']
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
%   `<subjectid>` is the provided name of the subject, if it was specified and
%   if addidtofile was set to 'true'.
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
if nargin < 2 error('ERROR: At least boldlist and ROI .names file have to be specified!'); end

% ----- parse options

default = 'roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|saveind=none|verbose=false|debug=false|tsname=|subjectid=|addidtofile=false';
options = general_parse_options([], options, default);

verbose = strcmp(options.verbose, 'true');
printdebug = strcmp(options.debug, 'true');
addidtofile = strcmp(options.addidtofile, 'true');
issubjectid = ~isempty(options.subjectid);

if printdebug
    general_print_struct(options, 'Options used');
end

if ~ismember(options.eventdata, {'all', 'mean', 'min', 'max', 'median'})
    error('ERROR: Invalid eventdata option: %s', options.eventdata);
end

if ~ismember(options.roimethod, {'mean', 'pca', 'median', 'max', 'min'})
    error('ERROR: Invalid roi extraction method: %s', options.roimethod);
end

% ----- What should be saved

options.saveind = strtrim(regexp(options.saveind, ',', 'split'));
if ismember({'none'}, options.saveind)
    options.saveind = {};
end
sdiff = setdiff(options.saveind, {'mat', 'long', 'wide', ''});
if ~isempty(sdiff)
    error('ERROR: Invalid save format specified: %s', strjoin(sdiff,","));
end

% ----- Get the list of files

[name, bolds] = strtok(bolds, '|');
bolds = bolds(2:end);
boldlist = strtrim(regexp(bolds, '\|', 'split'));

[roideffile, sroifile] = strtok(roiinfo, '|');
if sroifile
    sroifile = sroifile(2:end);
else
    sroifile = [];
end


% ----- Check if the files are there!

go = true;
if verbose; fprintf('\nChecking ...\n'); end

for bold = boldlist
    go = go & general_check_file(bold{1}, bold{1}, 'error');
end
go = go & general_check_file(roideffile, 'ROI definition file', 'error');
if sroifile
    go = go & general_check_file(sroifile, 'individual ROI file', 'error');
end
if any(ismember({'long', 'wide', 'mat'}, options.saveind))
    general_check_folder(targetf, 'results folder', true, verbose);
end

if ~go
    error('ERROR: Some files were not found. Please check the paths and start again!\n\n');
end


%   ------------------------------------------------------------------------------------------
%                                                                            do the processing

if verbose; fprintf('     ... creating ROI mask\n'); end

roi  = nimage.img_read_roi(roideffile, sroifile);
nroi = length(roi.roi.roinames);
roi_names = roi.roi.roinames;
roi_codes = roi.roi.roicodes;

% ---> reading image files

if verbose; fprintf('     ... reading image file(s)'); end
y = nimage(bolds);
if verbose; fprintf(' ... %d frames read, done.\n', y.frames); end

% ---> create extraction sets

if verbose; fprintf('     ... generating extraction sets\n'); end
exsets = y.img_get_extraction_matrices(frames, options);
for n = 1:length(exsets)
    if verbose; fprintf('         -> %s: %d good events, %d good frames\n', exsets(n).title, size(exsets(n).exmat, 1), sum(exsets(n).estat)); end
end

% ---> loop through extraction sets

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

if ~any(ismember({'mat', 'long', 'wide'}, options.saveind))
    if verbose; fprintf(' ... done\n'); end
    return; 
end

if verbose; fprintf('     ... saving results\n'); end

% set tsname

if options.tsname
    tsname = [options.tsname, '_'];
else
    tsname = '';
end

% set subjectname

if addidtofile && issubjectid
    subjectname = [options.subjectid, '_'];
else
    subjectname = '';
end

ftail = 'ts';
basefilename = fullfile(targetf, sprintf('%s_%s%s%s', name, tsname, subjectname, ftail));

% ---------------------------------------------------------------------------------------------------
%                                                                                              matlab

if ismember({'mat'}, options.saveind)
    if verbose; fprintf('         ... saving mat file'); end
    save(basefilename, 'tsmat', '-v7.3');
    if verbose; fprintf(' ... done\n'); end
end


% ---------------------------------------------------------------------------------------------------
%                                                                                            long tsv

if ismember({'long'}, options.saveind)
    if verbose; fprintf('         ... saving long tsv file'); end

    fout = fopen([basefilename '_long.tsv'], 'w');
    fprintf(fout, 'name\ttitle\tsubject\troi_name\troi_code\tevent\tframe\tvalue\n');

    for n = 1:nsets
        if tsmat(n).title, settitle = tsmat(n).title; else settitle = 'timeseries'; end

        % --- write up
        nframes = tsmat(n).N;
        
        for r = 1:nroi
            for f = 1:nframes
                fprintf(fout, '%s\t%s\t%s\t%s\t%d\t%d\t%d\t%.5f\n', name, settitle, options.subjectid, roi_names{r}, roi_codes(r), tsmat(n).tevents(f), tsmat(n).tframes(f), tsmat(n).ts(r, f));
            end
        end
    end
    fclose(fout);
    if verbose; fprintf(' ... done\n'); end
end

% ---------------------------------------------------------------------------------------------------
%                                                                                            wide tsv

if ismember({'wide'}, options.saveind)
    if verbose; fprintf('         ... saving wide tsv file'); end
    
    fout = fopen([basefilename '_wide.tsv'], 'w');
    fprintf(fout, 'name\ttitle\tsubject\tevent\tframe');
    for r = 1:nroi
        fprintf(fout, '\t[%d]_%s', roi_codes(r), roi_names{r});
    end

    for n = 1:nsets
        if tsmat(n).title, settitle = tsmat(n).title; else settitle = 'timeseries'; end

        % --- write up
        nframes = tsmat(n).N;
        for f = 1:nframes
            fprintf(fout, '\n%s\t%s\t%s\t%d\t%d', name, settitle, options.subjectid, tsmat(n).tevents(f), tsmat(n).tframes(f));
            fprintf(fout, '\t%.5f', tsmat(n).ts(:, f));
        end
    end
    fclose(fout);
    if verbose; fprintf(' ... done\n'); end
end

if verbose; fprintf(' ... done\n'); end

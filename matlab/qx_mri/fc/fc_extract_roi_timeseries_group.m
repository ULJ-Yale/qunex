function [tsset] = fc_extract_roi_timeseries_group(flist, roiinfo, frames, targetf, options)

%function [tsset] = fc_extract_roi_timeseries_group(flist, roiinfo, frames, targetf, options)
%
%   Extracts ROI timeseries for a group of sujects/sessions.
%
%   INPUTS
%   ======
%
%   --flist     A .list file listing the subjects and their files for which 
%               to compute extract ROI timeseries,
%               or a well strucutured string (see general_read_file_list).
%   --roiinfo   A names file for definition of ROI to extract timeseries for.
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
%                   what data to use from the event:
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
%                       ignore frames as marked in .fidl file
%                   <column> 
%                       the column name in *_scrub.txt file that matches bold 
%                       file to be used for ignore mask
%
%                   ['use,fidl']
%
%               badevents
%                   what to do with events that have frames marked as bad, 
%                   options are:
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
%               savegroup
%                   a comma separated list of formats to use to save the group 
%                   data:
%
%                   - long ... save the resulting data in a long format .tsv file
%                   - wide ... save the resulting data in a wide format .tsv file
%                   - mat  ... save the resulting data in a matlab .mat file
%
%                   ['']
%
%               tsname   
%                   an optional name to add to the output files, if empty, it 
%                   won't be used ['']
%
%               saveind  
%                   a comma separated list of formats to use to save the 
%                   invidvidual data:
%                   - long ... save the resulting data in a long format .tsv file
%                   - wide ... save the resulting data in a wide format .tsv file
%                   - mat  ... save the resulting data in a matlab .mat file
%
%               ['']
%
%               itargetf 
%                   where to save the individual data:
%
%                   - gfolder ... in the group target folder
%                   - sfolder ... in the individual session folder
%                   
%                   ['gfolder']
%
%               verbose  
%                   whether to be verbose 'true' or not 'false', when running 
%                   the analysis ['false']
%
%   RESULTS
%   =======
%
%   The function returns a structure array with the following fields for each specified
%   data extraction:
%
%   tsset
%       title  
%           the title of the extraction as specifed in the frames string, empty
%           if extraction was specified using a numeric value 
%       roi    
%           a cell array with the names of the ROI used in the order of columns
%           and rows in the functional connectivity matrix
%       subject
%           a structure array with the following fields for each subject/session
%           included in the analysis:
%
%           id 
%               an id of the subject/session
%           ts  
%               timeseries matrix in ROI x timepoint format
%           N  
%               number of timepoints in the extracted timeseries
%
%   Based on saveind option specification a file may be saved with the extracted 
%   timeseries saved in a matlab.mat file and/or in a text long format:
%
%   <targetf>/<listname>[_<tsname>][_<long|wide>].<txt|mat>
%
%   `<listname>` is the filename of the provided <flist> w/o the extension.
%   `<tsname>` is the optional name for the extracted timeseries if it was 
%   specified.
%   `<long|wide>` is the provided text format, if it was specified.
%
%   The text .tsv file(s) will have the following columns:
%   
%   long format         wide format
%   - name              - name
%   - title             - title
%   - subject           - subject
%   - roi               - event
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
%   The function extracts timeseries for the specified ROI for each 
%   subject/session listed in the `flist` list file. If an event string is 
%   provided, it has to describe how to extract event related data using the
%   following specification::
%
%       <title>:<eventlist>:<frame offset1>:<frame offset2>
%
%   Multiple extractions can be specified by separating them using the pipe '|' 
%   separator. Specifically, for each extraction, all the events listed in a
%   comma-separated eventlist will be considered (e.g. 'congruent,incongruent'). 
%   For each event all the frames starting from the specified beginning and 
%   ending offset will be extracted. If options eventdata is specified as 'all', 
%   all the specified frames will be concatenated in a single timeseries, 
%   otherwise, each event will be summarised by a single frame in a newly 
%   generated events series image.
%   
%   From the resulting timeseries, ROI series will be extracted for each 
%   specified ROI as specified by the roimethod option. 
%
%   The results will be returned in a tsset structure and, if so specified, saved.
%

if nargin < 5 || isempty(options), options = '';  end
if nargin < 4 || isempty(targetf), targetf = '.'; end
if nargin < 3 frames  = []; end
if nargin < 2 error('ERROR: At least boldlist and ROI .names file have to be specified!'); end

% ----- parse options

default = 'roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|savegroup=|tsname=|saveind=|itargetf=gfolder|verbose=false';
options = general_parse_options([], options, default);

general_print_struct(options, 'Options used');

verbose = strcmp(options.verbose, 'true');

% ----- Check if the files are there!

go = true;

if options.verbose; fprintf('\n\nChecking ...\n'); end
go = go & general_check_file(flist, 'image file list', 'error');
go = go & general_check_file(roiinfo, 'ROI definition file', 'error');
general_check_folder(targetf, 'results folder');

if ~go
    error('ERROR: Some of the specified files were not found. Please check the paths and start again!\n\n');
end

% ---- Start

fprintf('\n\nStarting ...\n');


%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf(' ... listing files to process');

[subject, nsub, nfiles, listname] = general_read_file_list(flist, verbose);

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
        go = go & general_check_file(subject(n).roi, [subject(n).id ' individual ROI file'], 'error');
        roidef = [roiinfo '|' subject(n).roi];
    else
        roidef = [roiinfo];
    end

    % ---> setting up bolds parameter

    if isfield(subject(n), 'files') && ~isempty(subject(n).conc) 
        for bold = subject(n).files
            go = go & general_check_file(bold{1}, 'bold file', 'error');
        end
        bolds = [lname '|' strjoin(subject(n).files, '|')];        
    elseif isfield(subject(n), 'conc') && ~isempty(subject(n).conc) 
        go = go & general_check_file(subject(n).conc, 'conc file', 'error');
        bolds = [lname '|' subject(n).conc];
    else
        go = false
        fprintf(' ... ERROR: %s missing bold or conc file specification!\n', subject(n).id);
    end

    % ---> setting up frames parameter

    if isa(frames, 'char')
        if isfield(subject(n), 'fidl')
            go = go & general_check_file(subject(n).fidl, [subject(n).id ' fidl file'], 'error');
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
            reference = general_read_concfile(reference);
            reference = reference{1};
        end
        stargetf = fileparts(reference);
        options.addidtofile = 'false';
    else
        stargetf = targetf;
        options.addidtofile = 'true';            
    end

    % ---> run individual subject
    try
        options.subjectid = subject(n).id;
        tsmat = fc_extract_roi_timeseries(bolds, roidef, sframes, stargetf, options);
    catch ME
        fprintf(' ... ERROR: Extraction of ROI timeseries for %s failed with error: %s\n', subject(n).id, ME.message);
        continue
    end

    % ------> Reorganize results

    nset = length(tsmat);
    c = c + 1;

    for s = 1:nset

        tsset(s).title = tsmat(s).title;            
        tsset(s).roi   = tsmat(s).roi;                

        % -------> Embed data

        tsset(s).subject(c).id      = subject(n).id;
        tsset(s).subject(c).N       = tsmat(s).N;
        tsset(s).subject(c).ts      = tsmat(s).ts;
        tsset(s).subject(c).tevents = tsmat(s).tevents;
        tsset(s).subject(c).tframes = tsmat(s).tframes;
   end
end

noksub = c;

% ===================================================================================================
%                                                                                  save group results

% ---> save results

if isempty(options.savegroup)
    if verbose; fprintf(' ... done\n'); end
    return; 
else
    options.savegroup = strtrim(regexp(options.savegroup, ',', 'split'));
end

if verbose; fprintf('\n----------------------------------\nSaving group results\n'); end

% set tsname

if options.tsname
    tsname = [options.tsname, '_'];
else
    tsname = '';
end

ftail = 'ts';
basefilename = fullfile(targetf, sprintf('%s_%s%s', lname, tsname, ftail));

% ---------------------------------------------------------------------------------------------------
%                                                                                              matlab

if ismember({'mat'}, options.savegroup)
    if verbose; fprintf('... saving mat file'); end
    save([basefilename '.mat'], 'tsset', '-v7.3');
    if verbose; fprintf(' ... done\n'); end
end

% ---------------------------------------------------------------------------------------------------
%                                                                                            long tsv

if ismember({'long'}, options.savegroup)
    if verbose; fprintf('... saving long group tsv file'); end

    fout = fopen([basefilename '_long.tsv'], 'w');
    fprintf(fout, 'name\ttitle\tsubject\troi\tevent\tframe\tvalue\n');

    for n = 1:length(tsset)
        if tsset(n).title, settitle = tsset(n).title; else settitle = 'timeseries'; end

        nroi    = length(tsset(n).roi);
        % --- write up
        for sid = 1:noksub
            nframes = tsset(n).subject(sid).N;
            for r = 1:nroi
                for f = 1:nframes            
                    fprintf(fout, '%s\t%s\t%s\t%s\t%d\t%d\t%.5f\n', lname, settitle, tsset(n).subject(sid).id, tsset(n).roi{r}, tsset(n).subject(sid).tevents(f), tsset(n).subject(sid).tframes(f), tsset(n).subject(sid).ts(r,f));
                end
            end
        end
    end
    fclose(fout);
    if verbose; fprintf(' ... done\n'); end
end

% ---------------------------------------------------------------------------------------------------
%                                                                                            wide tsv

if ismember({'wide'}, options.savegroup)
    if verbose; fprintf('... saving wide tsv file'); end
    
    nroi = length(tsset(1).roi);
    fout = fopen([basefilename '_wide.tsv'], 'w');
    fprintf(fout, 'name\ttitle\tsubject\tevent\tframe');
    for r = 1:nroi
        fprintf(fout, '\t[%d]_%s', r, tsset(1).roi{r});
    end

    for n = 1:length(tsset)
        if tsset(n).title, settitle = tsset(n).title; else settitle = 'timeseries'; end

        % --- write up
        nframes = tsset(n).subject(sid).N;
        for f = 1:nframes
            fprintf(fout, '\n%s\t%s\t%s\t%d\t%d', lname, settitle, tsset(n).subject(sid).id, tsset(n).subject(sid).tevents(f), tsset(n).subject(sid).tframes(f));
            fprintf(fout, '\t%.5f', tsset(n).subject(sid).ts(:, f));
        end
    end
    fclose(fout);
    if verbose; fprintf(' ... done\n'); end
end


if verbose; fprintf('DONE\n'); end

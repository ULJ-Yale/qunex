function [fcset] = fc_compute_roifc_group(flist, roiinfo, frames, targetf, options)

%function [fcset] = fc_compute_roifc_group(flist, roiinfo, frames, targetf, options)
%
%   Computes ROI functional connectivity matrices for a group of sujects/sessions.
%
%   INPUTS
%   ======
%
%   --flist     Either a .list file or a string listing the subjects and their
%               files for which to compute ROI functional connectivity.
%               
%               For a .list file see list file format specification.
%               For a string see `general_read_file_list` inline help. Briefly,
%               The string should provide the same information separated by
%               a pipe character, with the first entry providing a list name:
%
%               'listname:<name of the list>|
%                  session id:<id>|
%                  file:<path to a bold or conc file>|
%                  roi:<path to an optional session specific ROI mask>|
%                  fidl:<path to a fidl file describing event structure>'
%
%               e.g.: 'listname:wmlist|session id:OP483|file:bold1.nii.gz|roi:aseg.nii.gz'
%
%   --roiinfo   A (group level) names file for definition of ROI to include in 
%               the analysis.
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
%                      '<extraction name>:<event list>:<extraction start>:<extraction end>'
%
%                  where:
%
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
%                      extraction should start the extraction start and end 
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
%               fcmeasure
%                   which functional connectivity measure to compute, the 
%                   options are ['r']:
%
%                   r
%                       pearson's r value
%                   cv
%                       covariance estimate
%
%               savegroup
%                   a comma separated list of formats to use to save the group 
%                   data ['']:
%
%                   long
%                       save the resulting data in a long format .tsv file
%                   wide-single
%                       save the resulting data in a single wide format .tsv file
%                   wide-separate
%                       save the resulting data in a wide format .tsv file, one
%                       file per each measure of interest
%                   mat
%                       save the resulting data in a matlab .mat file
%
%               fcname   
%                   an optional name to add to the output files, if empty, it 
%                   won't be used ['']
%
%               saveind  
%                   a comma separated list of formats to use to save the 
%                   invidvidual data ['']:
%
%                   long
%                       save the resulting data in a long format .tsv file
%                   wide-single
%                       save the resulting data in a single wide format .tsv file
%                   wide-separate
%                       save the resulting data in a wide format .tsv file, one
%                       file per each measure of interest
%                   mat
%                       save the resulting data in a matlab .mat file
%
%               itargetf 
%                   where to save the individual data ['gfolder']:
%
%                   gfolder
%                       in the group target folder
%                   sfolder
%                       in the individual session folder
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
%   fcset
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
%           r  
%               correlation matrix between all ROI for that subject/session
%           fz 
%               Fisher z transformed correlation matrix between all ROI for that 
%               subject/session
%           z  
%               z-scores for the correlations
%           p  
%               p-values for the correlations
%
%   Based on saveind option specification a file may be saved with the functional 
%   connectivity data saved in a matlab.mat file and/or in a text long format:
%
%   <targetf>/<listname>[_<fcname>]_<cor|cov>[_<long|[_<r|Fz|cv>]wide>].<tsv|mat>
%
%   `<listname>` is the filename of the provided <flist> w/o the extension.
%   `<fcname>` is the provided name of the functional connectivity computed,
%   if it was specified.
%   `long` and `wide` will be added for long and wide tsv files, respectively.
%   `r`, `Fz`, `cv` will be added when wide data is saved in separate wide 
%   format files.

%
%   The text file will have the following columns (depending on the fcmethod):
%   
%   long format         wide format
%   - name              - name
%   - title             - title
%   - subject           - subject
%   - roi1              - measure
%   - roi2              - [<roi1_code>]_<roi1_name>-[<roi_code>2]_<roi3_name>
%   - cv
%   - r
%   - Fz
%   - Z
%   - p
%   
%   Note:
%   In wide format only cv, r, and Fz data will be saved. 
%
%   USE
%   ===
%
%   The function computes functional connectivity matrices for the specified ROI
%   for each subject/session listed in the `flist` list file. If an event string 
%   is provided, it has to describe how to extract event related data using the
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
%   specified ROI as specified by the roimethod option. A functional connectivity 
%   matrix between ROI will be computed.
%
%   The results will be returned in a fcset structure and, if so specified, saved.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 5 || isempty(options), options = '';  end
if nargin < 4 || isempty(targetf), targetf = '.'; end
if nargin < 3 frames  = []; end
if nargin < 2 error('ERROR: At least file list and ROI information have to be specified!'); end

% ----- parse options

default = 'roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|savegroup=|fcname=|saveind=|itargetf=gfolder|verbose=false';
options = general_parse_options([], options, default);

general_print_struct(options, 'Options used');

if ~ismember(options.eventdata, {'all', 'mean', 'min', 'max', 'median'})
    error('ERROR: Invalid eventdata option: %s', options.eventdata);
end

if ~ismember(options.roimethod, {'mean', 'pca', 'median', 'min', 'max'})
    error('ERROR: Invalid roi extraction method: %s', options.roimethod);
end

if ~ismember(options.fcmeasure, {'r', 'cv'})
    error('ERROR: Invalid functional connectivity computation method: %s', options.fcmeasure);
end

cv = strcmp(options.fcmeasure, 'cv');
verbose = strcmp(options.verbose, 'true');

% ----- Check if the files are there!

go = true;

if verbose; fprintf('\n\nChecking ...\n'); end
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
        if strcmp(options.itargetf, 'sfolder')
            bolds = [lname '|' strjoin(subject(n).files, '|')];
        else
            bolds = [lname '_' subject(n).id '|' strjoin(subject(n).files, '|')];
        end
    elseif isfield(subject(n), 'conc') && ~isempty(subject(n).conc) 
        go = go & general_check_file(subject(n).conc, 'conc file', 'error');
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
    else
        stargetf = targetf;
    end

    % ---> run individual subject
    try
        fcmat = fc_compute_roifc(bolds, roidef, sframes, stargetf, options);
    catch ME
        fprintf(' ... ERROR: Computation of ROI FC for %s failed with error: %s\n', subject(n).id, ME.message);
        continue
    end

    % ------> Reorganize results

    nset = length(fcmat);
    c = c + 1;

    for s = 1:nset

        fcset(s).title    = fcmat(s).title;            
        fcset(s).roinames = fcmat(s).roinames;                

        % -------> Embed data

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

% set fcname

if options.fcname
    fcname = [options.fcname, '_'];
else
    fcname = '';
end

ftail = {'cor', 'cov'};
ftail = ftail{ismember({'r', 'cv'}, options.fcmeasure)};

basefilename = fullfile(targetf, sprintf('%s_%s%s', lname, fcname, ftail));

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
        if fcset(n).title, settitle = fcset(n).title; else settitle = 'ts'; end

        % --- set ROI names

        nroi = length(fcset(n).roinames);

        idx1 = repmat([1:nroi], nroi, 1);
        idx1 = tril(idx1, -1);
        idx1 = idx1(idx1 > 0);

        idx2 = repmat([1:nroi]', 1, nroi);
        idx2 = tril(idx2, -1);
        idx2 = idx2(idx2 > 0);

        roi1 = fcset(n).roinames(idx1);
        roi2 = fcset(n).roinames(idx2);

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



function [fcset] = fc_compute_roifc_group(flist, roiinfo, frames, targetf, options)

%``fc_compute_roifc_group(flist, roiinfo, frames, targetf, options)``
%
%   Computes ROI functional connectivity matrices for a group of sujects/sessions.
%
%   Parameters:
%       --flist (str):
%           A .list file listing the subjects and their files for which to
%           compute ROI functional connectivity, or a well strucutured string
%           (see general_read_file_list).
%
%       --roiinfo (str):
%           A names file for definition of ROI to include in the analysis.
%
%       --frames (str, default ''):
%           The definition of which frames to use, it can be one of:
%
%           - a numeric array mask defining which frames to use (1) and which
%             not (0)
%
%           - a single number, specifying the number of frames to skip at
%             start
%
%           - a string describing which events to extract timeseries for, and
%             the frame offset from the start and end of the event in format:
%             ('title1:event1,event2:2:2|title2:event3,event4:1:2').
%
%       --targetf (str, default '.'):
%           The folder to save images in.
%
%       --options (str, default 'roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|savegroup=|fcname=|saveind=|itargetf=gfolder|verbose=false'):
%           A string specifying additional analysis options formated as pipe
%           separated pairs of colon separated key, value pairs:
%           "<key>:<value>|<key>:<value>".
%
%           It takes the following keys and values:
%
%           - roimethod
%               What method to use to compute ROI signal:
%
%               - mean
%               - median
%               - pca.
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
%           - fcmeasure
%               Which functional connectivity measure to compute, the options
%               are:
%
%               - r
%                   Pearson's r value
%               - cv
%                   covariance estimate.
%
%               Defaults to 'r'.
%
%           - savegroup
%               A comma separted list of formats to use to save the group data:
%
%               - txt
%                   save the resulting data in a long format .txt file
%               - mat
%                   save the resulting data in a matlab .mat file.
%
%               - if format is not specified, data is not saved to a file.
%
%               Defaults to ''.
%
%           - fcname
%               An optional name to add to the output files, if empty, it
%               won't be used. Defaults to ''.
%
%           - saveind
%               A comma separated list of formats to use to save the
%               invidvidual data:
%
%               - txt
%                   save the resulting data in a long format txt file
%               - mat
%                   save the resulting data in a matlab .mat file
%
%               - if format is not specified, data is not saved to a file.
%
%               Defaults to ''.
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
%   Returns:
%       fcset
%           - title
%               The title of the extraction as specifed in the frames string,
%               empty if extraction was specified using a numeric value.
%           - roi
%               A cell array with the names of the ROI used in the order of
%               columns and rows in the functional connectivity matrix.
%           - subject
%               A structure array with the following fields for each
%               subject/session included in the analysis:
%
%               - id
%                   An id of the subject/session.
%               - r
%                   Correlation matrix between all ROI for that subject/session.
%               - fz
%                   Fisher z transformed correlation matrix between all ROI for
%                   that subject/session.
%               - z
%                   z-scores for the correlations.
%               - p
%                   p-values for the correlations.
%
%   Notes:
%       The function returns a structure array with the following fields for
%       each specified data extraction.
%
%       Based on saveind option specification a file may be saved with the
%       functional connectivity data saved in a matlab.mat file and/or in a text
%       long format::
%
%           <targetf>/<listname>[_<fcname>]_<cor|cov>.<txt|mat>
%
%       - `<listname>` is the filename of the provided <flist> w/o the
%         extension.
%
%       - `<fcname>` is the provided name of the functional connectivity
%         computed, if it was specified.
%
%       The text file will have the following columns (depending on the
%       fcmethod):
%   
%       - name
%       - title
%       - subject
%       - roi1
%       - roi2
%       - cv
%       - r
%       - Fz
%       - Z
%       - p
%
%       Use:
%           The function computes functional connectivity matrices for the
%           specified ROI for each subject/session listed in the `flist` list
%           file. If an event string is provided, it has to describe how to
%           extract event related data using the following specification::
%
%               <title>:<eventlist>:<frame offset1>:<frame offset2>
%
%           Multiple extractions can be specified by separating them using the
%           pipe '|' separator. Specifically, for each extraction, all the
%           events listed in a comma-separated eventlist will be considered
%           (e.g. 'congruent,incongruent'). For each event all the frames
%           starting from the specified beginning and ending offset will be
%           extracted. If options eventdata is specified as 'all', all the
%           specified frames will be concatenated in a single timeseries,
%           otherwise, each event will be summarised by a single frame in a
%           newly generated events series image.
%   
%           From the resulting timeseries, ROI series will be extracted for each
%           specified ROI as specified by the roimethod option. A functional
%           connectivity matrix between ROI will be computed.
%
%           The results will be returned in a fcset structure and, if so
%           specified, saved.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 5 || isempty(options), options = '';  end
if nargin < 4 || isempty(targetf), targetf = '.'; end
if nargin < 3 frames  = []; end
if nargin < 2 error('ERROR: At least boldlist and ROI .names file have to be specified!'); end

% ----- parse options

default = 'roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|savegroup=|fcname=|saveind=|itargetf=gfolder|verbose=false';
options = general_parse_options([], options, default);

general_print_struct(options, 'Options used');

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

        fcset(s).title = fcmat(s).title;            
        fcset(s).roi   = fcmat(s).roi;                

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

        nroi = length(fcset(n).roi);

        idx1 = repmat([1:nroi], nroi, 1);
        idx1 = tril(idx1, -1);
        idx1 = idx1(idx1 > 0);

        idx2 = repmat([1:nroi]', 1, nroi);
        idx2 = tril(idx2, -1);
        idx2 = idx2(idx2 > 0);

        roi1 = fcset(n).roi(idx1);
        roi2 = fcset(n).roi(idx2);

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



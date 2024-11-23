function [fcmats] = fc_compute_roifc(flist, roiinfo, frames, targetf, options)

%``fc_compute_roifc(flist, roiinfo, frames, targetf, options)``
%
%   Computes ROI functional connectivity matrices for group and/or 
%   individual subjects / sessions.
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
%       --options (str, default 'sessions=all|roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|saveind=none|savesessionid=false|fcname=|verbose=false|debug=false'):
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
%           - fcmeasure
%               Which functional connectivity measure to compute, the options
%               are:
%
%               - r
%                   Pearson's r value
%               - rho
%                   Spearman's rho value
%               - cv
%                   covariance estimate
%               - cc
%                   cross correlation
%               - icv
%                   inverse covariance
%               - coh
%                   coherence
%               - mi
%                   mutual information
%               - mar
%                   multivariate autoregressive model (coefficients)
%
%               Defaults to 'r'.
%
%               Additional parameters for specific measures can be added using
%               fcargs optional parameter (see below).
%
%           - fcargs
%               Additional arguments for computing functional connectivity, e.g.
%               k for computation of mutual information or standardize and
%               shrinkage for computation of inverse covariance. These parameters
%               need to be provided as subfields of fcargs, e.g.:
%               'fcargs>standardize:partialcorr,shrinkage:LW'
%
%           - savegroup
%               A comma separated list of formats to use to save the group 
%               data:
%
%               - all_long
%                   save the results from all sessions in a long format .tsv 
%                   file
%               - all_wide_single
%                   save the results from all sessions in a single wide format
%                   .tsv file
%               - all_wide_separate
%                   save the results from all sessions in a wide format .tsv
%                   file, one file per each measure of interest
%               - mean_long (not yet implemented)
%                   save the group mean results in a long format .tsv file
%               - mean_wide_single (not yet implemented)
%                   save the group mean results in a single wide format
%                   .tsv file
%               - mean_wide_separate (not yet implemented)
%                   save the group mean results in a wide format .tsv
%                   file, one file per each measure of interest
%               - mat
%                   save the resulting data in a matlab .mat file
%               - none
%                   do not save group results.c =
%
%               Defaults to 'none'.
%
%           - saveind
%               A comma separted list of formats to use to save the data:
%
%               - long
%                   save the resulting data in a long format .tsv file
%               - wide_single
%                   save the resulting data in a single wide format .tsv file
%               - wide_separate
%                   save the resulting data in a wide format .tsv file, one
%                   file per each measure of interest
%               - mat
%                   save the resulting data in a matlab .mat file.
%               - none
%                   do not save individual results.
%
%               Defaults to 'none'.
%
%           - savesessionid
%               whether to add the id of the session or subject to the
%               individual output file when saving to the individual session
%               images/functional folder:
%
%               - true
%               - false.
%
%               Defaults to 'true'.
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
%           - fcname
%               An optional name describing the functional connectivity
%               computed to add to the output files, if empty, it won't be
%               used. Defaults to ''.
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
%       fcset
%           - title
%               The title of the extraction as specifed in the frames string. It
%               defaults to 'timeseries' if not provided.
%           - roi
%               A cell array with the names of the ROI used in the order of
%               columns and rows in the functional connectivity matrix.
%           - subject
%               A structure array with the following fields for each
%               subject/session included in the analysis:
%
%               - id
%                   An id of the subject/session.
%               - <fcmeasure>
%                   A matrix of functional connectivity measure between all ROI 
%                   for that subject/session.
%               - fz
%                   Fisher z transformed connectivity matrix between all ROI for
%                   that subject/session.
%               - z
%                   z-scores for the correlations.
%               - p
%                   p-values for the correlations.
%
%           - group
%               A structure with group-level data:
%
%               - <fcmeasure>
%                   A matrix of mean functional connectivity measure between 
%                   all ROI averaged over the group.
%               - fz
%                   Fisher z transformed connectivity matrix between all ROI
%                   averaged over the group.
%               - z
%                   z-scores computed across the group connectivity matrices.
%               - p
%                   p-values computed across the group connectivity matrices.
%
%   Notes:
%       Please note, that only those results that are valid for the specific 
%       fcmeasure are saved. For example, `fz`, `p`, and `z` will not be
%       reported for `cv` at the individual level, and `fz` won't be reported
%       on the group level.
%
%       Based on savegroup option specification a file may be saved with the
%       functional connectivity data saved in a matlab.mat file and/or in a text
%       long format::
%
%           <targetf>/roifc_<listname>[_<fcname>]_<fcmeasure>_[long|[Fz_]wide>].<tsv|mat>
%
%       - `<targetf>` is the group target folder.
%
%       - `<listname>` is the name of the provided <flist>.
%
%       - `<fcname>` is the provided name of the functional connectivity
%         computed, if it was specified.
%
%       - `<fcmeasure>` is the measure of functional connectivity that was 
%         computed.
%
%       `long` and `wide` will be added for long and wide tsv files, respectively.
%       `Fz` will be added when wide data is saved in separate wide format files.
%
%       Based on saveind option specification a file may be saved with the
%       functional connectivity data saved in a matlab.mat and/or in a text
%       wide or long format::
%
%           <stargetf>/roifc_<listname>[_<fcname>][_<subjectid>]_<fcmeasure>_[long|[Fz_]wide>].<tsv|mat>
%
%       - `<stargetf>` is eitehr the group target folder or the individual's
%         functional images folder, depending on the `itargetf` option.
%
%       - `<listname>` is the name of the provided <flist>.
%
%       - `<fcname>` is the provided name of the functional connectivity computed,
%         if it was specified
%
%       - `<subjectid>` is the subject/session id, if it was requested by the
%         `savesessionid` or if the files are saved in the group target folder.
%
%       `long` and `wide` will be added for long and wide tsv files, respectively.
%       `Fz` will be added when wide data is saved in separate wide 
%       format files.
%
%       The text file will have the following columns (depending on the
%       fcmethod):
%
%       long format
%       - name
%       - title
%       - subject
%       - roi1
%       - roi2
%       - <fcmeasure>
%       - Fz
%       - Z
%       - p
%   
%       wide format
%       - name
%       - title
%       - subject
%       - <fcmeasure>
%       - [<roi1_code>]_<roi1_name>-[<roi_code>2]_<roi3_name>
%
%       Note:
%       In wide format only <fcmeasure> and Fz data will be saved. 
%
%       Use:
%           The function computes functional connectivity matrices for the
%           specified ROI. If an event string is provided, it has to start with
%           a path to the .fidl file to be used to extract the events, following
%           by a pipe separated list of event extraction definitions::
%
%               <title>:<eventlist>:<frame offset1>:<frame offset2>
%
%           multiple extractions can be specified by separating them using the
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
%           The results will be returned in a fcmat structure and, if so
%           specified, saved.
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

default = 'sessions=all|roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|fcargs=|savegroup=none|saveind=none|savesessionid=true|itargetf=gfolder|verbose=false|debug=false|fcname=|verbose=true|debug=false';
options = general_parse_options([], options, default);

verbose     = strcmp(options.verbose, 'true');
printdebug  = strcmp(options.debug, 'true');
addidtofile = strcmp(options.savesessionid, 'true') || strcmp(options.itargetf, 'gfolder');
gem_options = sprintf('ignore:%s|badevents:%s|verbose:%s|debug:%s', options.ignore, options.badevents, options.verbose, options.debug);
fcmeasure   = options.fcmeasure;

if options.fcname, fcname = [options.fcname, '_']; else fcname = ''; end

if printdebug
    general_print_struct(options, 'fc_compute_roifc options used');
end

% --> Check input

if verbose; fprintf('\nChecking ...\n'); end

options.flist = flist;
options.roiinfo = roiinfo;
options.targetf = targetf;

general_check_options(options, 'fc, eventdata, roimethod, flist, roiinfo, tfolder', 'stop');

% ----- What should be saved

% ---> individual data

options.saveind = strtrim(regexp(options.saveind, ',', 'split'));
if ismember({'none'}, options.saveind)
    options.saveind = {};
end
sdiff = setdiff(options.saveind, {'mat', 'long', 'wide_single', 'wide_separate', ''});
if ~isempty(sdiff)
    error('ERROR: Invalid individual save format specified: %s', strjoin(sdiff,","));
end

% ---> group data

options.savegroup = strtrim(regexp(options.savegroup, ',', 'split'));
if ismember({'none'}, options.savegroup)
    options.savegroup = {};
end
sdiff = setdiff(options.savegroup, {'mat', 'all_long', 'all_wide_single', 'all_wide_separate', 'mean_long', 'mean_wide_single', 'mean_wide_separate', ''});
if ~isempty(sdiff)
    error('ERROR: Invalid group save format specified: %s', strjoin(sdiff,","));
end

%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf(' ... listing files to process');

list = general_read_file_list(flist, options.sessions, [], verbose);

lname = strrep(list.listname, '.list', '');
lname = strrep(lname, '.conc', '');
lname = strrep(lname, '.4dfp', '');
lname = strrep(lname, '.img', '');

fprintf(' ... done.\n');


%   ------------------------------------------------------------------------------------------
%                                                The main loop ... go through all the sessions

first_subject = true;
oksub         = zeros(1, length(list.session));
embed_data    = nargout > 0 || ~isempty(options.savegroup);

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

    roinames = {roi.roi.roiname};
    roicodes = [roi.roi.roicode];
    nroi = length(roi.roi);
    nparcels = length(parcels);

    % ---> create extraction sets

    if verbose; fprintf('     ... generating extraction sets\n'); end
    exsets = y.img_get_extraction_matrices(frames, gem_options);
    for n = 1:length(exsets)
        if verbose; fprintf('         -> %s: %d good events, %d good frames\n', exsets(n).title, size(exsets(n).exmat, 1), sum(exsets(n).estat)); end
    end

    % ---> loop through extraction sets

    if verbose; fprintf('     ... computing fc matrices\n'); end

    nsets = length(exsets);
    for n = 1:nsets        
        if verbose; fprintf('         ... set %s\n', exsets(n).title); end
        
        % ---> get the extracted timeseries
    
        ts = y.img_extract_timeseries(exsets(n).exmat, options.eventdata);
    
        if verbose; fprintf('         ... extracted ts\n'); end
        
        % ---> generate fc matrice
        
        if isempty(parcels)
            rs = ts.img_extract_roi(roi, [], options.roimethod);
        else
            rs = ts.img_extract_roi(roiinfo, [], options.roimethod); 
        end
    
        fc = fc_compute(rs, [], fcmeasure, false, options);
        
        if verbose; fprintf('         ... computed fc matrix\n'); end
    
        % ---> store 
        
        if first_subject
            fcmat(n).title     = exsets(n).title;
            fcmat(n).roi       = {roi.roi.roiname};
            fcmat(n).subjects = {};
        end

        fcmat(n).subjects = {subjectid};
        fcmat(n).fc.(fcmeasure) = fc;
        fcmat(n).fc.N = ts.frames;

        if ismember(fcmeasure, {'r', 'rho', 'coh'})
            fcmat(n).fc.fz = fc_fisher(fc);
            fcmat(n).fc.z  = fcmat(n).fc.fz/(1/sqrt(fcmat(n).fc.N - 3));
            fcmat(n).fc.p  = (1 - normcdf(abs(fcmat(n).fc.z), 0, 1)) * 2 .* sign(fcmat(n).fc.fz);
        end

        if embed_data
            if first_subject
                fcmats(n).title     = exsets(n).title;
                fcmats(n).roi       = {roi.roi.roiname};
                fcmats(n).subjects = {};
            end
            fcmats(n).subjects(s) = {subjectid};
            fcmats(n).fc(s).(fcmeasure) = fc;
            fcmats(n).fc(s).N = ts.frames;
            if ismember(fcmeasure, {'r', 'rho', 'coh'})
                fcmats(n).fc(s).fz = fcmat(n).fc.fz;
                fcmats(n).fc(s).z  = fcmat(n).fc.z;
                fcmats(n).fc(s).p  = fcmat(n).fc.p;
            end
        end 
    end
    
    % ===================================================================================================
    %                                                                             save individual results

    if ~any(ismember({'mat', 'long', 'wide_single', 'wide_separate'}, options.saveind))
        if verbose; fprintf(' ... done\n'); end
        continue; 
    end

    if verbose; fprintf('     ... saving results\n'); end

    % set subjectname

    if addidtofile
        subjectname = [list.session(s).id, '_'];
    else
        subjectname = '';
    end

    basefilename = fullfile(stargetf, sprintf('roifc_%s_%s%s%s', lname, fcname, subjectname, fcmeasure));

    for save_format = options.saveind
        switch save_format{1}
            case 'mat'
                if verbose; fprintf('         ... saving mat file'); end
                save(basefilename, 'fcmat');
                if verbose; fprintf(' ... done\n'); end
            case 'long'
                save_long(fcmat, fcmeasure, lname, basefilename, verbose, printdebug);
            case 'wide_separate'
                save_wide(fcmat, fcmeasure, lname, basefilename, true, verbose, printdebug);
            case 'wide_single'
                save_wide(fcmat, fcmeasure, lname, basefilename, false, verbose, printdebug);
        end
    end        

    first_subject = false;
end


% ===================================================================================================
%                                                                                  save group results

% ---> save results

if ~isempty(options.savegroup)
    if verbose; fprintf('\n---------------------------------\nProcessing group data\n'); end
end

basefilename = fullfile(targetf, sprintf('roifc_%s_%s%s', lname, fcname, fcmeasure));

for save_format = options.savegroup
    switch save_format{1}
        case 'mat'
            if verbose; fprintf('         ... saving mat file'); end
            fcmat = fcmats;
            save(basefilename, 'fcmat');
            if verbose; fprintf(' ... done\n'); end
        case 'all_long'
            save_long(fcmats, fcmeasure, lname, basefilename, verbose, printdebug);
        case 'all_wide_separate'
            save_wide(fcmats, fcmeasure, lname, basefilename, true, verbose, printdebug);
        case 'all_wide_single'
            save_wide(fcmats, fcmeasure, lname, basefilename, false, verbose, printdebug);
    end
end  


% -------------------------------------------------------------------------------------------
%                                                  support function for saving in long format 

function [] = save_long(fcmat, fcmeasure, lname, basefilename, verbose, printdebug)

    if verbose; fprintf('         ... saving long tsv file'); end
    if printdebug; fprintf([' ' basefilename '_long.tsv']); end

    fout = fopen([basefilename '_long.tsv'], 'w');

    if ismember(fcmeasure, {'cv', 'icv', 'mi', 'mar', 'cc'})
        fprintf(fout, 'name\ttitle\tsubject\troi1_name\troi2_name\t%s\n', fcmeasure);
    else
        fprintf(fout, 'name\ttitle\tsubject\troi1_name\troi2_name\t%s\tFz\tZ\tp\n', fcmeasure);
    end

    for n = 1:length(fcmat)
        if fcmat(n).title, settitle = fcmat(n).title; else settitle = 'ts'; end

        % --- set ROI names

        nroi = length(fcmat(n).roi);

        idx1 = repmat([1:nroi], nroi, 1);
        idx1 = tril(idx1, -1);
        idx1 = idx1(idx1 > 0);

        idx2 = repmat([1:nroi]', 1, nroi);
        idx2 = tril(idx2, -1);
        idx2 = idx2(idx2 > 0);

        roi1name = fcmat(n).roi(idx1);
        roi2name = fcmat(n).roi(idx2);

        idx  = reshape([1:nroi*nroi], nroi, nroi);
        idx  = tril(idx, -1);
        idx  = idx(idx > 0);        

        nfc  = length(idx);

        % --- write up
        
        for s = 1:length(fcmat(n).subjects)
            if ismember(fcmeasure, {'cv', 'icv', 'mi', 'mar', 'cc'})
                fc = fcmat(n).fc(s).(fcmeasure)(idx);
                for c = 1:nfc
                    fprintf(fout, '%s\t%s\t%s\t%s\t%s\t%.5f\n', lname, settitle, fcmat(n).subjects{s}, roi1name{c}, roi2name{c}, fc(c));
                end
            elseif ismember(fcmeasure, {'r', 'rho', 'coh'})
                fc = fcmat(n).fc(s).(fcmeasure)(idx);
                fz = fcmat(n).fc(s).fz(idx);
                z  = fcmat(n).fc(s).z(idx);
                p  = fcmat(n).fc(s).p(idx);
                for c = 1:nfc
                    fprintf(fout, '%s\t%s\t%s\t%s\t%s\t%.5f\t%.5f\t%.5f\t%.7f\n', lname, settitle, fcmat(n).subjects{s}, roi1name{c}, roi2name{c}, fc(c), fz(c), z(c), p(c));
                end
            end
        end
    end
    fclose(fout);
    if verbose; fprintf(' ... done\n'); end

% -------------------------------------------------------------------------------------------
%                                                        support function for printing header 

function [] = printHeader(fout, roinames)
    fprintf(fout, 'name\ttitle\tsubject\tmeasure\troiname');
    nroi = length(roinames);
    for r = 1:nroi
        fprintf(fout, '\t%s', roinames{r});
    end


% -------------------------------------------------------------------------------------------
%                                                  support function for saving in wide format 
function [] = save_wide(fcmat, fcmeasure, lname, basefilename, separate, verbose, printdebug);

    if verbose; fprintf('         ... saving wide tsv file'); end

    nroi = length(fcmat(1).roi);
    roi  = fcmat(1).roi;
    
    if printdebug; fprintf([' ' basefilename '_wide.tsv']); end
    fout_fc = fopen([basefilename '_wide.tsv'], 'w');
    printHeader(fout_fc, roi);
    toclose = [fout_fc];

    if separate && ismember(fcmeasure, {'r', 'rho', 'coh'}) 
        if printdebug; fprintf([' ' basefilename '_Fz_wide.tsv']); end
        fout_Fz = fopen([basefilename '_Fz_wide.tsv'], 'w');
        printHeader(fout_Fz, roi);
        toclose = [toclose fout_Fz];
    else
        fout_Fz = fout_fc;
    end

    for n = 1:length(fcmat)
        if fcmat(n).title, settitle = fcmat(n).title; else settitle = 'ts'; end
        for s = 1:length(fcmat.subjects)
            for r = 1:nroi
                fprintf(fout_fc,'\n%s\t%s\t%s\t%s\t%s\t%d', lname, settitle, fcmat(n).subjects{s}, fcmeasure, roi{r});
                fprintf(fout_fc, '\t%.7f', fcmat(n).fc(s).(fcmeasure)(r, :));
            end
            if ismember(fcmeasure, {'r', 'rho', 'coh'})
                for r = 1:nroi
                    fprintf(fout_Fz, '\n%s\t%s\t%s\t%s\t%s\t%d', lname, settitle, fcmat(n).subjects{s}, 'fz', roi{r});
                    fprintf(fout_Fz, '\t%.7f', fcmat(n).fc(s).fz(r, :));
                end
            end
        end
    end

    for f = toclose
        fclose(f);
    end
    
    if verbose; fprintf(' ... done\n'); end        

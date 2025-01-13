function [gbcmaps] = fc_compute_gbc(flist, command, sroiinfo, troiinfo, frames, targetf, options)

%``fc_compute_gbc(flist, command, sroiinfo, troiinfo, frames, targetf, options)``
%
%   Computes seed based functional connectivity maps for group and/or
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
%       --command (str):
%           The type of gbc to run: mFz, aFz, pFz, nFz, aD, pD, nD, mFzp, aFzp ...
%
%           ``<type of gbc>:<parameter>|<type of gbc>:<parameter> ...``
%
%           There are a number of options available. They can be divided by
%           those that work on untransformed functional connectivity (Fc) values
%           e.g. covariance, and those that work on functional connectivity
%           estimates transformed to Fisher z (Fz) values. Note that the function
%           does not check the validity of using untransformed values or the
%           validity of their transform to Fz values.
%
%           The options that work on untransformed values are:
%
%           - mFc:t
%               computes mean Fc value across all voxels (over threshold t)
%           - aFc:t
%               computes mean absolute Fc value across all voxels (over
%               threshold t)
%           - pFc:t
%               computes mean positive Fc value across all voxels (over
%               threshold t)
%           - nFc:t
%               computes mean negative Fc value across all voxels (below
%               threshold t)
%
%           - aD:t
%               computes proportion of voxels with absolute Fc over t
%           - pD:t
%               computes proportion of voxels with positive Fc over t
%           - nD:t
%               computes proportion of voxels with negative Fc below t
%
%           - mFcp:n
%               computes mean Fc value across n proportional ranges
%           - aFcp:n
%               computes mean absolute Fc value across n proportional ranges
%           - mFcs:n
%               computes mean Fc value across n strength ranges
%           - pFcs:n
%               computes mean Fc value across n strength ranges for positive
%               correlations
%           - nFcs:n
%               computes mean Fc value across n strength ranges for negative
%               correlations
%           - aFcs:n
%               computes mean absolute Fc value across n strength ranges
%
%           - mDs:n
%               computes proportion of voxels within n strength ranges of Fc
%           - aDs:n
%               computes proportion of voxels within n strength ranges of
%               absolute Fc
%           - pDs:n
%               computes proportion of voxels within n strength ranges of
%               positive Fc
%           - nDs:n
%               computes proportion of voxels within n strength ranges of
%               negative Fc.
%
%           The options that first transform functional connectivity estimates
%           to Fisher z values are:
%
%           - mFz:t
%               computes mean Fz value across all voxels (over threshold t)
%           - aFz:t
%               computes mean absolute Fz value across all voxels (over
%               threshold t)
%           - pFz:t
%               computes mean positive Fz value across all voxels (over
%               threshold t)
%           - nFz:t
%               computes mean negative Fz value across all voxels (below
%               threshold t)
%
%           - mFzp:n
%               computes mean Fz value across n proportional ranges
%           - aFzp:n
%               computes mean absolute Fz value across n proportional ranges
%           - mFzs:n
%               computes mean Fz value across n strength ranges
%           - pFzs:n
%               computes mean Fz value across n strength ranges for positive
%               correlations
%           - nFzs:n
%               computes mean Fz value across n strength ranges for negative
%               correlations
%           - aFzs:n
%               computes mean absolute Fz value across n strength ranges
%
%       --sroiinfo (str):
%           A specification of the source voxels over which the GBC is to be
%           computed. This will be passed as the first parameter to the
%           img_prep_roi method. If individual roi files are listed in the
%           file list, they will be passed as the second parameter to the
%           img_prep_roi method. If empty GBC will be computed over all
%           grayordinates or voxels.
%
%       --troiinfo (str):
%           A specification of the target voxels for which the GBC is to be
%           computed. This will be passed as the first parameter to the
%           img_prep_roi method. If individual roi files are listed in the
%           file list, they will be passed as the second parameter to the
%           img_prep_roi method. If empty GBC will be computed over all
%           grayordinates or voxels.
%
%       --frames (matrix | int | str, default ''):
%           The definition of which frames to extract, specifically:
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
%                 '<extraction name>:<event list>:<extraction start>:<extraction end>'
%
%           where:
%
%           - extraction name
%               is the name for the specific extraction definition
%           - event list
%               is a comma separated list of events for which data is to
%               be extracted
%           - extraction start
%               is a frame number relative to event start or event end, that
%               specifies the frame at which the extraction should start
%           - extraction end
%               is a frame number relative to event start or event end, that
%               specifies the frame at which the extraction should end.
%
%               the extraction start and end should be given as
%               '<s|e><frame number>'. E.g.:
%
%               - 's0'  ... the frame of the event onset
%               - 's2'  ... the second frame from the event onset
%               - 'e1'  ... the first frame from the event end
%               - 'e0'  ... the last frame of the event
%               - 'e-2' ... the two frames before the event end.
%
%           Example::
%
%               'encoding:e-color,e-shape:s2:s4|delay:d-color,d-shape:s2:e0'
%
%       --targetf (str, '.'):
%           The group level folder to save images in.
%
%       --options (str, default 'sessions=all|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|savegroup=all|saveind=none|savesessionid=false|itargetf=gfolder|rsmooth=|rdilate=|verbose=false|debug=false'):
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
%           - eventdata
%               What data to use from each event:
%
%               - all
%                   use all identified frames of all events
%               - mean
%                   use the mean across frames of each identified event
%               - min
%                   use the minimum value across frames of each identified event
%               - max
%                   use the maximum value across frames of each identified event
%               - median
%                   use the median value across frames of each identified event.
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
%               A comma separated list of files to save, options are:
%
%               - mean
%                   mean group GBC estimates
%               - group_z
%                   Z converted p values testing difference from 0
%               - group_p
%                   p values testing difference from 0
%               - sessions
%                   GBC estimates for all the sessions
%               - all
%                   all the above files
%               - none
%                   do not save any group level results.
%
%               Defaults to 'all'. Any invalid options will be ignored without
%               a warning.
%
%           - saveind
%               A comma separted list of individual session / subject files
%               to save:
%
%               - fc
%                   save GBC estimates
%               - z
%                   save Z statistic (only valid for Pearson's r)
%               - p
%                   save p value (only valid for Pearson's r)
%               - all
%                   save all relevant files
%               - none
%                   do not save any individual level results
%
%               Default is 'none'. Any invalid options will be ignored without
%               a warning.
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
%           - rsmooth:
%               in case of volume images an optional radius (fwhm) for within
%               mask spatial smoothing (no smoothing if empty). Defaults to
%               ''.
%
%           - rdilate:
%               in case of volume images an optional radius in voxels by
%               which to dilate the masks before use. No dillation will be
%               performed if empty. Defaults to ''.
%
%           - step:
%               how many voxels/grayordinates/parcels to process in a single
%               step. Defaults to 12000.
%
%           - rmax
%               The Fc value above which the estimates are considered to be of
%               the same functional ROI. Set to 0 if it should not be used.
%               Defaults to 0.
%
%           - time
%               Whether to print timing information. [false]
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
%       gbcmaps
%           A structure array for all the computed GBC commands with the
%           following fields:
%
%           title
%               The title of the extraction as specifed in the frames string,
%               empty if extraction was specified using a numeric value.
%           commands
%               A cell array with the names of the commands used as they
%               were specified.
%           subjects
%               A cell array with the names of subjects for which the GBC maps
%               were computed.
%           gbc
%               An array of GBC images, each holding the results for a single
%               subject across all commands.
%           N
%               Number of frames over which the maps were computed for each
%               participant.
%
%
%   Output files:
%       Based on savegroup specification it saves the following group files:
%
%       `<targetf>/gbc_<listname>[_<title>]_<command>_<parameter>[_v<volume>]<fcmeasure>_group_mean`
%           Mean group GBC map.
%
%       `<targetf>/gbc_<listname>[_<title>]_<command>_<parameter>[_v<volume>]<fcmeasure>_group_p`
%           Group p values testing difference from 0.
%
%       `<targetf>/gbc_<listname>[_<title>]_<command>_<parameter>[_v<volume>]<fcmeasure>_group_Z`
%           Group Z converted p values testing difference from 0.
%
%       `<targetf>/gbc_<listname>[_<title>]_<command>_<parameter>[_v<volume>]<fcmeasure>_all_sessions`
%           GBC maps for all sessions.
%
%       Definitions:
%
%       - `<targetf>` is the group target folder.
%       - `<listname>` is the listname name of the flist.
%       - `<title>` is the title of the extraction event(s), if event string
%         was specified.
%       - `<command>` is the command specifying the type of the GBC to run (see
%           command parameter above).
%       - `<parameter>` is the additional parameter used with the specified type
%           of GBC run.
%       - `<volume>` is the volume number for those GBC results that return multiple
%           maps.
%       - `<fcmeasure>` is the functional connectivity measure used to compute
%           the GBC.
%
%       Based on saveind option specification the following files may be saved:
%
%       - `<targetf>/gbc[_<sessionid>]_<listname>[_<title>]_<command>_<parameter>_<fcmeasure>`
%           Correlation coefficients or covariances
%
%       - `<targetf>/gbc[_<sessionid>]_<listname>[_<title>]_<command>_<parameter>_<fcmeasure>_Fz`
%           Fisher Z values
%
%       - `<targetf>/gbc[_<sessionid>]_<listname>[_<title>]_<command>_<parameter>_<fcmeasure>_Z`
%           Z converted p values testing difference from 0
%
%       - `<targetf>/gbc[_<sessionid>]_<listname>[_<title>]_<command>_<parameter>_<fcmeasure>_p`
%           p values testing difference from 0
%
%   Notes:
%       The method returns a structure array named gbcmaps with the fields listed
%       above for each specified data extraction.
%
%       Use:
%           This function is a wrapper for  nimage.img_compute_gbc method. It
%           enables computing GBC for a list of sessions and saving group and/or
%           individual results for each specified GBC type.
%
%           Event based GBC
%           GBC can be computed either on the whole timeseries or across events
%           specified using the event string. If an event string is provided, it
%           has to start with a path to the .fidl file to be used to extract the
%           events, following  by a pipe separated list of event extraction
%           definitions::
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
%           otherwise, each event will be summarised by a single frame in a newly
%           generated events series image.
%
%           The GBC will be computed over the resulting time- or eventseries,
%           one map for each specified GBC command.
%
%           Reduced or regional GBC
%           GBC can be computed over the whole volume or cifti file, or limited
%           to a specific source and target mask. Source mask specifies for which
%           voxels, grayordinates or parcels to compute the GBC. Target mask
%           specifies across which voxels, grayordinates or parcels to compute
%           the GBC for each source voxel, grayordinate or parcel. If the image
%           is a volume, masks can be optionally smoothed and or dilated. As
%           sessions' gray matter masks differ and do not overlap precisely,
%           rdilate will dilate the borders with the provided number of voxels.
%           Here it is important to note that values from the expanded mask will
%           not be used, rather the values from the valid mask will be smeared
%           into the dilated area.
%
%           Computing GBC
%           A GBC map will be computed for each provided command. For details
%           regarding the commands, please, see help for the
%           nimage.img_compute_gbc method.
%
%           The results will be returned in a gbcmaps structure and, if so
%           specified, saved.
%
%   Examples:
%       To compute resting state seed maps using first eigenvariate of each ROI::
%
%           qunex fc_compute_seedmaps \
%               --flist='scz.list' \
%               --roiinfo='CCNet.names' \
%               --frames=0 \
%               --targetf='seed-maps' \
%               --options='roimethod:pca|ignore:udvarsme'
%
%       To compute resting state seed maps using mean of each region and
%       covariances instead of correlation::
%
%           qunex fc_compute_seedmaps \
%               --flist='scz.list' \
%               --roiinfo='CCNet.names' \
%               --frames=0 \
%               --targetf='seed-maps' \
%               --options='roimethod:mean|igmore:udvarsme|fcmeasure:cv'
%
%       To compute seed maps for third and fourth frame of incongruent and
%       congruent trials (listed as inc and con events in fidl files with
%       duration 1) using mean of each region and exclude only frames marked for
%       exclusion in fidl files::
%
%           qunex fc_compute_seedmaps \
%               --flist='scz.list' \
%               --roiinfo='CCNet.names' \
%               --frames='incongruent:inc:2,3|congruent:con:2,3' \
%               --targetf='seed-maps' \
%               --options='roimethod:mean|ignore:event'
%
%       To compute seed maps across all the tasks blocks, starting with the
%       third frame into the block and taking one additional frame after the end
%       of the block, use::
%
%           qunex fc_compute_seedmaps \
%               --flist='scz.list' \
%               --roiinfo='CCNet.names' \
%               --frames='task:easyblock,hardblock:2,1' \
%               --targetf='seed-maps' \
%               --options='roimethod:mean|ignore:event'


%   - lcgray  (left cortex gray matter)
%   - rcgray  (right cortex gray matter)
%   - cgray   (cortical gray matter)
%   - lsubc   (left subcortical gray matter)
%   - rsubc   (right subcortical gray matter)
%   - subc    (subcortical gray matter)
%   - lcerc   (left cerebellar gray matter)
%   - rcerc   (right cerelebbar gray matter)
%   - cerc    (cereberal gray matter)
%   - lgray   (left hemisphere gray matter)
%   - rgray   (right hemisphere gray matter)
%   - gray    (whole brain gray matter)


% SPDX-FileCopyrightText: 2024 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 7 || isempty(options), options = '';  end
if nargin < 6 || isempty(targetf), targetf = '.'; end
if nargin < 5 frames  = []; end
if nargin < 4 troiinfo = []; end
if nargin < 3 sroiinfo  = []; end
if nargin < 2 error('ERROR: At least list information and command have to be specified!'); end

% ----- parse options
default = 'sessions=all|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|savegroup=all|saveind=none|savesessionid=false|itargetf=gfolder|rsmooth=|rdilate=|vstep=12000|verbose=false|debug=false';
options = general_parse_options([], options, default);

verbose = strcmp(options.verbose, 'true');
printdebug = strcmp(options.debug, 'true');

gem_options = sprintf('ignore:%s|badevents:%s|verbose:%s|debug:%s', options.ignore, options.badevents, options.verbose, options.debug);
fcmeasure = options.fcmeasure;

if printdebug
    general_print_struct(options, 'fc_compute_gbc options used');
end

if verbose; fprintf('\n\nChecking ...\n'); end

options.flist    = flist;
options.sroiinfo = sroiinfo;
options.troiinfo = troiinfo;
options.targetf  = targetf;

check = 'fc, eventdata, flist, targetf';
if ~isempty(options.sroiinfo), check = [check, ', sroiinfo']; end
if ~isempty(options.troiinfo), check = [check, ', troiinfo']; end

general_check_options(options, check, 'stop');


%   ------------------------------------------------------------------------------------------
%                                                                 check what needs to be saved

% -> group files

options.savegroup = strtrim(regexp(options.savegroup, ',', 'split'));

if ismember({'none'}, options.savegroup)
    options.savegroup = {};
elseif ismember({'all'}, options.savegroup)
    options.savegroup = {'mean', 'sessions', 'group_p', 'group_z'};
else
    options.savegroup = intersect(options.savegroup, {'mean', 'sessions', 'group_p', 'group_z'});
end


% -> individual files

options.saveind = strtrim(regexp(options.saveind, ',', 'split'));

if ismember({'none'}, options.saveind)
    options.saveind = [];
elseif ismember({'all'}, options.saveind)
    options.saveind = {'fc', 'r', 'z', 'p'};
end

if ~isempty(options.saveind)
    if strcmp(options.fcmeasure, 'r')
        options.saveind = intersect(options.saveind, {'fc', 'r', 'z', 'p'});
    else
        options.saveind = intersect(options.saveind, {'fc'});
    end
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
oksub         = zeros(1, list.nsessions);
embed_data    = nargout > 0 || ~isempty(options.savegroup);

for s = 1:list.nsessions

    go = true;

    if verbose; fprintf('\n---------------------------------\nProcessing session %s\n', list.session(s).id); end

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

    % ---> run individual session

    if verbose; fprintf('     ... creating ROI masks\n'); end

    if isempty(sroiinfo)
        sroi = [];
    else
        sroi = nimage.img_prep_roi(sroiinfo, sroifile);
        nsroi = length(sroi.roi);
    end

    if isempty(troiinfo)
        troi = [];
    else
        troi = nimage.img_prep_roi(troiinfo, sroifile);
        ntroi = length(troi.roi);
    end

    if verbose; fprintf('     ... done\n'); end

    % ---> reading image files

    if verbose; fprintf('     ... reading image file(s)\n'); end
    y = nimage(strjoin(bolds, '|'));
    if verbose; fprintf('         -> %d frames read, done.\n', y.frames); end

    % --> get filetype
    switch y.filetype
        case 'dtseries'
            tfiletype = 'dscalar';
        case 'ptseries'
            tfiletype = 'pscalar';
        otherwise
            tfiletype = y.filetype;
    end

    % ---> create extraction sets

    if verbose; fprintf('     ... generating extraction sets ...'); end
    exsets = y.img_get_extraction_matrices(frames, gem_options);
    if verbose; fprintf(' done.\n'); end

    % ---> loop through extraction sets

    if verbose; fprintf('     ... computing gbc\n'); end

    nsets = length(exsets);
    for n = 1:nsets

        if verbose; fprintf('         ... set %s\n', exsets(n).title); end

        % ---> get the extracted timeseries

        ts = y.img_extract_timeseries(exsets(n).exmat, options.eventdata);

        if verbose; fprintf('         ... extracted ts\n'); end

        % --> generate gbc maps

        [gbc, commands] = ts.img_compute_gbc_fc(command, sroi, troi, options);
        ncomm = length(commands);

        if verbose; fprintf('         ... computed gbc maps\n'); end

        % ---> Embedd results (if group data is requested)
        if embed_data
            if first_subject
                gbcmaps(n).title    = exsets(n).title;
                gbcmaps(n).commands = command;
                gbcmaps(n).subjects = {};
                gbcmaps(n).gbc      = nimage();
            end
            gbcmaps(n).subjects{s}  = subjectid;
            gbcmaps(n).gbc(s) = gbc;
            gbcmaps(n).N(s) = ts.frames;

            if verbose; fprintf('         ... embedded\n'); end
        end

        % ---> save individual results

        if ~isempty(options.saveind)

            if verbose; fprintf('     ... saving gbc\n'); end

            % set subjectname
            if strcmp(options.savesessionid, 'true') || strcmp(options.savesessionid, 'yes') || strcmp(options.itargetf, 'gfolder')
                subjectname = [subjectid, '_'];
            else
                subjectname = '';
            end

            % set up extraction set title
            if exsets(n).title, settitle = ['_' exsets(n).title]; else settitle = ''; end

            % set up base filename
            basefilename = sprintf('gbc_%s%s%s', subjectname, lname, settitle);

            % save results of all commands
            sframe = 0;
            eframe = 0;
            for c = 1:ncomm

                % get start and end frames
                sframe = eframe + 1;
                eframe = sframe + commands(c).volumes - 1;
                frame_mask = zeros(1, gbc.frames);
                frame_mask(sframe:eframe) = 1;

                % extract and save data
                t = gbc.sliceframes(frame_mask == 1);
                t.filetype = tfiletype;

                tfilename = fullfile(stargetf, [basefilename '_' regexprep(commands(c).command_string, ':', '_') '_' fcmeasure]);
                t.filetype = tfiletype;
                % t.cifti.maps = cellfun(@(x) ['GBC ' fcmeasure ' ' commands(c).command_string ' parameter = ' x], arrayfun(@num2str, commands(c).parameter, 'UniformOutput', false), 'UniformOutput', false);
                t.cifti.maps = cellfun(@(x) ['GBC ' fcmeasure ' ' commands(c).command_string ' volume ' x], arrayfun(@num2str, 1:commands(c).volumes, 'UniformOutput', false), 'UniformOutput', false);
                t.img_saveimage(tfilename);
                if printdebug; fprintf(['\n             -> ' tfilename]); end

                if ismember('z', options.saveind)
                    % TODO: -> compute and save z image
                end

                if ismember('p', options.saveind)
                    % TODO: -> compute and save p image
                end

            end

            if verbose; fprintf(' done.\n'); end
        end
    end
    first_subject = false;
end

% -- save group data

if ~isempty(options.savegroup)
    if verbose; fprintf('Saving group data ... \n'); end

    for sid = 1:list.nsessions
        extra(sid).key = ['session ' int2str(sid)];
        extra(sid).value = list.session(sid).id;
    end

    session_names = {list.session.id};

    for setid = 1:nsets
        if verbose; fprintf(' -> %s\n', gbcmaps(setid).title); end
        if gbcmaps(setid).title, settitle = ['_' gbcmaps(setid).title]; else settitle = ''; end

        frame = 0;
        for cid = 1:ncomm
            comname = [commands(cid).command '_' regexprep(num2str(commands(cid).parameter), '\s+', 'x')];

            if verbose; fprintf('    ... for command %s', comname); end

            % -- prepare group gbc maps for the command
            for v = 1:commands(cid).volumes

                % -- setup
                frame = frame + 1;
                gbc = gbcmaps(setid).gbc(1).zeroframes(list.nsessions);

                % -- loop through subjects
                for sid = 1:list.nsessions
                    gbc.data(:,sid) = gbcmaps(setid).gbc(sid).data(:, frame);
                end

                % -- compute p-values
                if any(ismember(options.savegroup, {'group_p', 'group_z'}))
                    [p Z M] = gbc.img_ttest_zero();
                end

                % -- compute mean
                if any(ismember(options.savegroup, {'mean'})) && isempty(M)
                    M = gbc.zeroframes(1);
                    M.data = mean(gbc.data, 2);
                end

                % --- save requested data
                if verbose; fprintf(' ... saving ...'); end
                if commands(cid).volumes > 1 vol = ['_v' num2str(v)]; else vol = ''; end
                basefilename = sprintf('gbc_%s%s_%s%s_%s', lname, settitle, comname, vol, fcmeasure);
                basemap = sprintf('%s %s%s', fcmeasure, comname, vol);

                % -- save group mean results
                if any(ismember(options.savegroup, {'mean', 'all'}))
                    if printdebug; fprintf(['\n             -> ' fullfile(targetf, [basefilename '_group_mean'])]); end
                    M.filetype = tfiletype;
                    M.cifti.maps = {['GBC ' basemap ' [group mean]']};
                    M.img_saveimage(fullfile(targetf, [basefilename '_group_mean']), extra);
                    if verbose && ~printdebug; fprintf([' mean']); end
                end

                % -- save all results
                if any(ismember(options.savegroup, {'sessions', 'all'}))
                    if printdebug; fprintf(['\n             -> ' fullfile(targetf, [basefilename '_all_sessions'])]); end
                    gbc.filetype = tfiletype;
                    gbc.cifti.maps = cellfun(@(x) ['GBC ' x ' ' basemap], session_names, 'UniformOutput', false);
                    gbc.img_saveimage(fullfile(targetf, [basefilename '_all_sessions']), extra);
                    if verbose && ~printdebug; fprintf(' sessions'); end
                end

                % -- save group p results
                if any(ismember(options.savegroup, {'group_p', 'all'}))
                    if printdebug; fprintf(['\n             -> ' fullfile(targetf, [basefilename '_group_p'])]); end
                    p.filetype = tfiletype;
                    p.cifti.maps = {['GBC ' basemap ' [group p-values]']};
                    p.img_saveimage(fullfile(targetf, [basefilename '_group_p']), extra);
                    if verbose && ~printdebug; fprintf(' p'); end
                end

                % -- save group Z results
                if any(ismember(options.savegroup, {'group_z', 'all'}))
                    if printdebug; fprintf(['\n             -> ' fullfile(targetf, [basefilename '_group_Z'])]); end
                    Z.filetype = tfiletype;
                    Z.cifti.maps = {['GBC ' basemap ' [group Z-values]']};
                    Z.img_saveimage(fullfile(targetf, [basefilename '_group_Z']), extra);
                    if verbose && ~printdebug; fprintf(' Z'); end
                end

            if verbose; fprintf(' ... done.\n'); end

            end
        end
    end
end

if verbose; fprintf('\n\nCompleted\n'); end

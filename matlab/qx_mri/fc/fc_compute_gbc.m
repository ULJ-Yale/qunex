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
%           Following options are available:
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
%               computes mean positive Fz value across all voxels (below
%               threshold t)
%           - aD:t
%               computes proportion of voxels with absolute r over t
%           - pD:t
%               computes proportion of voxels with positive r over t
%           - nD:t
%               computes proportion of voxels with negative r below t
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
%           - mDs:n
%               computes proportion of voxels within n strength ranges of r
%           - aDs:n
%               computes proportion of voxels within n strength ranges of
%               absolute r
%           - pDs:n
%               computes proportion of voxels within n strength ranges of
%               positive r
%           - nDs:n
%               computes proportion of voxels within n strength ranges of
%               negative r.
%
%       --sroiinfo (str):
%           A path to the names file specifying group based ROI that defines
%           the source ROIs for which the GBC is to be computed. If empty
%           GBC will be computed for all grayordinates or voxels. 
%
%           Alternatively, for volume images, if subject specific roi files
%           are provided, a string specifying gray matter extent to be 
%           included (see Notes).
%
%       --troiinfo (str):
%           A path to the names file specifying group based ROI that defines
%           the target ROIs across which the GBC is to be computed. If empty
%           GBC will be computed across all grayordinates or voxels. 
%
%           Alternatively, for volume images, if subject specific roi files
%           are provided, a string specifying gray matter extent to be 
%           included (see Notes).
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
%               Which functional connectivity measure to use, the options
%               are:
%
%               - r
%                   Pearson's r coefficient of correlation
%               - rho
%                   Spearman's rho coefficient of correlation
%               - cv
%                   covariance estimate.               
%
%               Defaults to 'r'.
%
%           - savegroup
%               A comma separated list of files to save, options are:
%
%               - mean_r
%                   mean group functional connectivity estimates
%               - mean_fz
%                   mean group Fisher Z values
%               - group_z
%                   Z converted p values testing difference from 0
%               - group_p
%                   p values testing difference from 0
%               - all_r
%                   functional connectivity estimates for all the sessions
%               - all_fz
%                   Fz values for all the sessions
%               - all
%                   save all the relevant group level results
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
%               - r
%                   save functional connectivity estimates
%               - fz
%                   save Fisher Z values 
%               - z
%                   save Z statistic
%               - p
%                   save p value
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
%           - vstep:
%               how many voxels/grayordinates/parcels to process in a single 
%               step. Defaults to 12000.
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
%               A cell array with the names of the commands used in the they
%               were specified.
%           subjects
%               A cell array with the names of subjects for which the GBC maps
%               were computed.
%           gbc
%               A structure array with data per subject/session. With the 
%               following fields:
%
%               - fc
%                   The GBC maps, with one command per frame.
%               - fz
%                   The GBC maps converted to Fisher z-values.
%               - N
%                   Number of frames over which the maps were computed.
%
%
%   Output files:
%       Based on savegroup specification it saves the following group files:
%
%       `<targetf>/gbc_<listname>[_<title>]_<command>_<parameter>_mean_<fcmeasure>`
%           Mean group requested correlation coefficient or covariance.
%
%       `<targetf>/gbc_<listname>[_<title>]_<command>_<parameter>_mean_<fcmeasure>_Fz`
%           Mean group Fisher Z values.
%
%       `<targetf>/gbc_<listname>[_<title>]_<command>_<parameter>_group_<fcmeasure>_p`
%           Group p values testing difference from 0.
%
%       `<targetf>/gbc_<listname>[_<title>]_<command>_<parameter>_group_<fcmeasure>_Z`
%           Group Z converted p values testing difference from 0.
%
%       `<targetf>/gbc_<listname>[_<title>]_<command>_<parameter>_all_<fcmeasure>`
%           Correlation coefficients or covariance for all sessions.
%
%       `<targetf>/gbc_<listname>[_<title>]_<command>_<parameter>_all_<fcmeasure>_Fz`
%           Fisher Z values for all sessions.
%
%       Definitions:
%
%       - `<targetf>' is the group target folder.
%       - `<listname>` is the listname name of the flist.
%       - `<title>` is the title of the extraction event(s), if event string
%         was specified.
%       - `<command>` is the command specifying the type of the GBC to run (see
%           command parameter above).
%       - `<parameter>` is the additional parameter used with the specified type
%           of GBC run.
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
if nargin < 2 error('ERROR: At least list information and ROI .names file have to be specified!'); end

% ----- parse options
default = 'sessions=all|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|savegroup=all|saveind=none|savesessionid=false|itargetf=gfolder|rsmooth=|rdilate=|verbose=false|debug=false';
options = general_parse_options([], options, default);

verbose = strcmp(options.verbose, 'true');
printdebug = strcmp(options.debug, 'true');

gem_options = sprintf('ignore:%s|badevents:%s|verbose:%s|debug:%s', options.ignore, options.badevents, options.verbose, options.debug);
fcmeasure = options.fcmeasure;

if printdebug
    general_print_struct(options, 'fc_compute_seedmaps options used');
end

if ~ismember(options.eventdata, {'all', 'mean', 'min', 'max', 'median'})
    error('ERROR: Invalid eventdata option: %s', options.eventdata);
end

if ~ismember(options.roimethod, {'mean', 'pca', 'median'})
    error('ERROR: Invalid roi extraction method: %s', options.roimethod);
end

if ~ismember(options.fcmeasure, {'r', 'cv', 'rho', 'cc'})
    error('ERROR: Invalid functional connectivity computation method: %s', options.fcmeasure);
end

% ----- Check if the files are there!

go = true;

if verbose; fprintf('\n\nChecking ...\n'); end

% - check for presence of listfile unless the list is provided as a string
if ~strncmp(flist, 'listname:', 9)
    go = go & general_check_file(flist, 'image file list', 'error');
end
go = go & general_check_file(roiinfo, 'ROI definition file', 'error');
% - check for presence of target folder no data needs to be saved there
if ~strcmp(options.savegroup, 'none') || (~strcmp(options.saveind, 'none') && strcmp(options.itargetf, 'sfolder'))
    general_check_folder(targetf, 'results folder');
end

if ~go
    error('ERROR: Some of the specified files or folders were not found. Please check the paths and start again!\n\n');
end


% ----- What should be saved
% -> group files

options.savegroup = strtrim(regexp(options.savegroup, ',', 'split'));

if ismember({'none'}, options.savegroup)
    options.savegroup = {};
end

if ismember({'all'}, options.savegroup)
    if strcmp(options.fcmeasure, 'cv')
        options.savegroup = {'group_z', 'group_p', 'mean_r', 'all_r'};
    elseif ismember(options.fcmeasure, {'r', 'rho'})
        options.savegroup = {'group_z', 'group_p', 'mean_r', 'mean_fz', 'all_fz', 'all_r'};
    end    
end

% -> individual files

options.saveind = strtrim(regexp(options.saveind, ',', 'split'));

if ismember({'all_by_roi'}, options.saveind)    
    options.saveind = options.saveind(~ismember(options.saveind, {'all_by_roi', 'r', 'fz', 'z', 'p'}));
    options.saveind = [options.saveind, 'r', 'fz', 'z', 'p'];
end
if ismember({'all_joint'}, options.saveind)
    options.saveind = options.saveind(~ismember(options.saveind, {'all_joint', 'jr', 'jfz', 'jz', 'jp'}));
    options.saveind = [options.saveind, 'jr', 'jfz', 'jz', 'jp'];
end
if ismember({'none'}, options.saveind)
    options.saveind = [];
end

if length(options.saveind) 
    if strcmp(options.fcmeasure, 'r')
        options.saveind = intersect(options.saveind, {'r', 'fz', 'z', 'p', 'jr', 'jfz', 'jz', 'jp'});
    elseif strcmp(options.fcmeasure, 'rho')
        options.saveind = intersect(options.saveind, {'r', 'fz', 'jr', 'jfz'});
    else
        options.saveind = intersect(options.saveind, {'r', 'jr'});
    end
end

%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf(' ... listing files to process');

[session, nsub, nfiles, listname] = general_read_file_list(flist, options.sessions, [], verbose);

lname = strrep(listname, '.list', '');
lname = strrep(lname, '.conc', '');
lname = strrep(lname, '.4dfp', '');
lname = strrep(lname, '.img', '');

fprintf(' ... done.\n');

%   ------------------------------------------------------------------------------------------
%                                                The main loop ... go through all the sessions

first_subject = true;
oksub         = zeros(1, length(session));
embed_data    = nargout > 0 || ~isempty(options.savegroup);

for s = 1:nsub

    go = true;

    if verbose; fprintf('\n---------------------------------\nProcessing session %s', session(s).id); end

    % ---> check roi files

    if isfield(session(s), 'roi')
        go = go & general_check_file(session(s).roi, [session(s).id ' individual ROI file'], 'error');
        sroifile = session(s).roi;
    else
        sroifile = [];
    end

    % ---> check bold files

    if isfield(session(s), 'conc') && ~isempty(session(s).conc) 
        go = go & general_check_file(session(s).conc, 'conc file', 'error');
        bolds = general_read_concfile(session(s).conc);
    elseif isfield(session(s), 'files') && ~isempty(session(s).files) 
        bolds = session(s).files;
    else
        fprintf(' ... ERROR: %s missing bold or conc file specification!\n', session(s).id);
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
            if isfield(session(s), 'fidl')
                go = go & general_check_file(session(s).fidl, [session(s).id ' fidl file'], 'error');
            else
                go = false;
                fprintf(' ... ERROR: %s missing fidl file specification!\n', session(s).id);
            end
        end
    end

    if ~go, continue; end

    % ---> setting up target folder and name for individual data

    if strcmp(options.itargetf, 'sfolder')
        stargetf = fileparts(reference_file);
        if endsWith(stargetf, '/concs')
            stargetf = strrep(stargetf, '/concs', '');
        end
    else
        stargetf = targetf;
    end
    subjectid = session(s).id;

    % ---> run individual session

    if verbose; fprintf('     ... creating ROI mask'); end

    roi  = nimage.img_read_roi(roiinfo, sroifile);
    nroi = length(roi.roi.roinames);

    if verbose; fprintf(' ... read %d ROI\n', nroi); end

    % ---> reading image files

    if verbose; fprintf('     ... reading image file(s)'); end
    y = nimage(bolds);
    if verbose; fprintf(' ... %d frames read, done.\n', y.frames); end

    % ---> create extraction sets

    if verbose; fprintf('     ... generating extraction sets ...'); end
    exsets = y.img_get_extraction_matrices(frames, gem_options);
    if verbose; fprintf(' done.\n'); end

    % ---> loop through extraction sets

    if verbose; fprintf('     ... computing seedmaps\n'); end

    nsets = length(exsets);
    for n = 1:nsets

        if verbose; fprintf('         ... set %s', exsets(n).title); end
        
        % ---> get the extracted timeseries

        ts = y.img_extract_timeseries(exsets(n).exmat, options.eventdata);

        if verbose; fprintf(' ... extracted ts'); end
        
        % ---> generate seedmaps

        rs = ts.img_extract_roi(roi, [], options.roimethod);
        %fprintf('\n size(rs) is %s\n', mat2str(size(rs)));
        %fprintf('\n size(ts) is %s\n', mat2str(size(ts.data)));
        fc = ts.img_compute_correlations(rs', options.fcmeasure, false, strcmp(options.debug, 'true'));

        if verbose; fprintf(' ... computed seedmap'); end

        % ---> Embedd results (if group data is requested)
        
        if embed_data
            if first_subject
                fcmaps(n).title    = exsets(n).title;
                fcmaps(n).roi      = roi.roi.roinames;
                fcmaps(n).subjects = {};
            end
            fcmaps(n).subjects{s}  = subjectid;
            fcmaps(n).fc(s).(fcmeasure) = fc;
            fcmaps(n).fc(s).N = ts.frames;
                        
            if verbose; fprintf(' ... embedded\n'); end
        end
    end

    % ---> save individual results

    if ~isempty(options.saveind)

        if verbose; fprintf('     ... saving seedmaps\n'); end

        % set subjectname

        if strcmp(options.savesessionid, 'true') || strcmp(options.savesessionid, 'yes') || strcmp(options.itargetf, 'gfolder')
            subjectname = [subjectid, '_'];
        else
            subjectname = '';
        end

        % set up filetype for single images

        if strcmp(y.filetype, '.dtseries')
            tfiletype = '.dscalar';
        else
            tfiletype = y.filetype;
        end

        % --- loop through sets

        for n = 1:nsets
            if exsets(n).title, settitle = ['_' exsets(n).title]; else settitle = ''; end

            % --- prepare computed data

            if verbose; fprintf('         ... preparing data'); end

            if any(ismember(options.saveind, {'fz', 'p', 'z', 'jfz', 'jp', 'jz'}))
                fz = fc;
                fz.data = fc_fisher(fz.data);
            end

            if any(ismember(options.saveind, {'p', 'z', 'jp', 'jz'}))
                Z = fc;
                Z.data = fz.data/(1/sqrt(ts.frames-3));
            end

            if any(ismember(options.saveind, {'p', 'jp'}))
                p = fc;
                p.data = (1 - normcdf(abs(Z.data), 0, 1)) * 2 .* sign(fz.data);
            end

            if verbose; fprintf(' ... done\n'); end

            % --- loop through roi

            if verbose; fprintf('         ... saving set %s, roi:', exsets(n).title); end

            % --- print for each ROI separately
        
            if any(ismember(options.saveind, {'r', 'fz', 'z', 'p', 'rho', 'cv'}));

                for r = 1:nroi

                    if verbose; fprintf(' %s', roi.roi.roinames{r}); end

                    % --- prepare basename

                    basefilename = sprintf('seedmap_%s%s%s_%s', subjectname, lname, settitle, roi.roi.roinames{r});

                    % --- save images

                    for sn = 1:length(options.saveind)
                        switch options.saveind{sn}
                            case 'r'
                                t = fc.sliceframes([1:nroi] == r);                                              
                                t.filetype = tfiletype;
                                if printdebug; fprintf(['\n             -> ' fullfile(stargetf, [basefilename '_' fcmeasure])]); end
                                t.img_saveimage(fullfile(stargetf, [basefilename '_' fcmeasure]));
                            case 'fz'
                                t = fz.sliceframes([1:nroi] == r);
                                t.filetype = tfiletype;
                                if printdebug; fprintf(['\n             -> ' fullfile(stargetf, [basefilename '_' fcmeasure '_Fz'])]); end
                                t.img_saveimage(fullfile(stargetf, [basefilename '_' fcmeasure '_Fz']));
                            case 'z'
                                t = Z.sliceframes([1:nroi] == r);
                                t.filetype = tfiletype;
                                if printdebug; fprintf(['\n             -> ' fullfile(stargetf, [basefilename '_' fcmeasure '_Z'])]); end
                                t.img_saveimage(fullfile(stargetf, [basefilename '_' fcmeasure '_Z']));
                            case 'p'
                                t = p.sliceframes([1:nroi] == r);
                                t.filetype = tfiletype;
                                if printdebug; fprintf(['\n             -> ' fullfile(stargetf, [basefilename '_' fcmeasure '_p'])]); end
                                t.img_saveimage(fullfile(stargetf, [basefilename '_' fcmeasure '_p']));
                        end
                    end
                end
            end

            % --- print for all ROI jointly

            if any(ismember(options.saveind, {'jr', 'jfz', 'jz', 'jp', 'jrho', 'jcv'}));

                allroi = strjoin(roi.roi.roinames, '-');
                basefilename = sprintf('seedmap_%s%s%s_%s', subjectname, lname, settitle, allroi);

                if verbose; fprintf(' %s', allroi); end

                % --- save images

                for sn = 1:length(options.saveind)
                    switch options.saveind{sn}
                        case 'jr'
                            t = fc;  
                            t.filetype = tfiletype;
                            if printdebug; fprintf(['\n             -> ' fullfile(stargetf, [basefilename '_' fcmeasure])]); end
                            t.img_saveimage(fullfile(stargetf, [basefilename '_' fcmeasure]));
                        case 'jfz'
                            t = fz;
                            t.filetype = tfiletype;
                            if printdebug; fprintf(['\n             -> ' fullfile(stargetf, [basefilename '_' fcmeasure '_Fz'])]); end
                            t.img_saveimage(fullfile(stargetf, [basefilename '_' fcmeasure '_Fz']));
                        case 'jz'
                            t = Z;
                            t.filetype = tfiletype;
                            if printdebug; fprintf(['\n             -> ' fullfile(stargetf, [basefilename '_' fcmeasure '_Z'])]); end
                            t.img_saveimage(fullfile(stargetf, [basefilename '_' fcmeasure '_Z']));
                        case 'jp'
                            t = p;
                            t.filetype = tfiletype;
                            if printdebug; fprintf(['\n             -> ' fullfile(stargetf, [basefilename '_' fcmeasure '_p'])]); end
                            t.img_saveimage(fullfile(stargetf, [basefilename '_' fcmeasure '_p']));
                    end
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

    for sid = 1:nsub
        extra(sid).key = ['session ' int2str(sid)];
        extra(sid).value = session(sid).id;
    end

    for setid = 1:nsets
        if verbose; fprintf(' -> %s\n', fcmaps(setid).title); end
        if exsets(n).title, settitle = ['_' exsets(n).title]; else settitle = ''; end

        for roiid = 1:nroi
            roiname = fcmaps(setid).roi{roiid};
        
            if verbose; fprintf('    ... for region %s', roiname); end
            
            % -- prepare group fc maps for the ROI
            fc = fcmaps(setid).fc(1).(fcmeasure).zeroframes(nsub);
            for sid = 1:nsub
                fc.data(:, sid) = fcmaps(setid).fc(sid).(fcmeasure).data(:, roiid);
            end

            % -- compute Fisher-z values
            if any(ismember(options.savegroup, {'mean_fz', 'group_p', 'group_z', 'mean_r', 'all_fz'}))
                fz = fc;
                fz.data = fc_fisher(fz.data);
            end

            % -- compute p-values
            if any(ismember(options.savegroup, {'group_p', 'group_z'}))
                if ismember(fcmeasure, {'cv'})
                    [p Z M] = fc.img_ttest_zero();
                elseif ismember(fcmeasure, {'r', 'rho'})
                    [p Z MFz] = fz.img_ttest_zero();
                    M = MFz.img_FisherInv();
                end
            end

            % -- compute mean
            if any(ismember(options.savegroup, {'mean_r'})) && isempty(M)
                M = fc.zeroframes(1);
                if ismember(fcmeasure, {'cv'})
                    M.data = mean(fc.data, 2);
                elseif ismember(fcmeasure, {'r', 'rho'})
                    MFz = fc.zeroframes(1);
                    MFz.data = mean(fz.data, 2);
                    M = MFz.img_FisherInv();
                end
            end

            % --- save requested data
            if verbose; fprintf(' ... saving ...'); end
            basefilename = sprintf('seedmap_%s%s_%s', lname, settitle, roiname);

            % -- save group mean results
            if any(ismember(options.savegroup, {'mean_r'}))
                if printdebug; fprintf(['\n             -> ' fullfile(targetf, [basefilename '_mean_' fcmeasure])]); end
                M.img_saveimage(fullfile(targetf, [basefilename '_mean_' fcmeasure]), extra);
                if verbose && ~printdebug; fprintf([' ' fcmeasure]); end
            end

            % -- save group mean fz results
            if any(ismember(options.savegroup, {'mean_fz'}))
                if printdebug; fprintf(['\n             -> ' fullfile(targetf, [basefilename '_mean_' fcmeasure '_Fz'])]); end
                MFz.img_saveimage(fullfile(targetf, [basefilename '_mean_' fcmeasure '_Fz']), extra);
                if verbose && ~printdebug; fprintf(' fz'); end
            end

            % -- save all results
            if any(ismember(options.savegroup, {'all_r'}))
                if printdebug; fprintf(['\n             -> ' fullfile(targetf, [basefilename '_all_' fcmeasure])]); end
                fc.img_saveimage(fullfile(targetf, [basefilename '_all_' fcmeasure]), extra);
                if verbose && ~printdebug; fprintf(' all_r'); end
            end

            % -- save all fz results
            if any(ismember(options.savegroup, {'all_fz'}))
                if printdebug; fprintf(['\n             -> ' fullfile(targetf, [basefilename '_all_' fcmeasure '_Fz'])]); end
                fz.img_saveimage(fullfile(targetf, [basefilename '_all_' fcmeasure '_Fz']), extra);
                if verbose && ~printdebug; fprintf(' all_fz'); end
            end
            
            % -- save group p results
            if any(ismember(options.savegroup, {'group_p'}))
                if printdebug; fprintf(['\n             -> ' fullfile(targetf, [basefilename '_group_' fcmeasure '_p'])]); end
                p.img_saveimage(fullfile(targetf, [basefilename '_group_' fcmeasure '_p']), extra);
                if verbose && ~printdebug; fprintf(' p'); end
            end

            % -- save group Z results
            if any(ismember(options.savegroup, {'group_z'}))
                if printdebug; fprintf(['\n             -> ' fullfile(targetf, [basefilename '_group_' fcmeasure '_Z'])]); end
                Z.img_saveimage(fullfile(targetf, [basefilename '_group_' fcmeasure '_Z']), extra);
                if verbose && ~printdebug; fprintf(' Z'); end
            end

            if verbose; fprintf(' ... done.\n'); end
        end
    end
end            

if verbose; fprintf('\n\nCompleted\n'); end
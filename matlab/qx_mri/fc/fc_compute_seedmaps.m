function [fcmaps] = fc_compute_seedmaps(flist, roiinfo, frames, targetf, options)

%``fc_compute_seedmaps(flist, roiinfo, frames, targetf, options)``
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
%       --roiinfo (str):
%           A path to the names file specifying group based ROI for which to
%           extract timeseries for. 
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
%       --options (str, default 'roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|saveind=none|savesessionid=false|itargetf=gfolder|verbose=false|debug=false'):
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
%                   Pearson's r coefficient of correlation
%               - rho
%                   Spearman's rho coefficient of correlation
%               - cv
%                   covariance estimate 
%               - cc
%                  cross correlation
%               - coh
%                   coherence
%               - mi
%                   mutual information
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
%               - mean_r
%                   mean group correlation coefficients or covariances
%               - mean_fz
%                   mean group Fisher Z values
%               - group_z
%                   Z converted p values testing difference from 0
%               - group_p
%                   p values testing difference from 0
%               - all_r
%                   correlation coefficients or covariances for all the sessions
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
%                   save correlation coefficients or covariance separately 
%                   for each roi
%               - fz
%                   save Fisher Z values (r or rho) separately for each roi
%               - z
%                   save Z statistic (r only) separately for each roi
%               - p
%                   save p value (r only) separately for each roi
%               - all_by_roi
%                   save all relevant values by roi
%               - jr
%                   save correlation coefficients or covariances in a single
%                   file for all roi
%               - jfz
%                   save Fisher Z values (r or rho) in a single file for all roi
%               - jz
%                   save Z statistic (r only) in a single file for all roi
%               - jp
%                   save p value (r only) in a single file for all roi
%               - all_joint
%                   save all relevant values in a joint file
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
%       fcmaps
%           A structure array for all the extractions specified with the
%           following fields:
%
%           title
%               The title of the extraction as specifed in the frames string,
%               empty if extraction was specified using a numeric value.
%           roi
%               A cell array with the names of the ROI used in the order of
%               their seed-maps in the fc image.
%           subjects
%               A cell array with the names of subjects for which the fc maps
%               were computed.
%           fc
%               A structure array with data per subject/session. With the 
%               following fields:
%
%               - r/cv/rho/coh/mi/cc
%                   The functional connectivity map, with one seed-map per frame.
%               - fz
%                   The functional connectivity map converted to Fisher z-values.
%               - N
%                   Number of frames over which the map was computed.
%
%   Output files:
%       Based on savegroup specification it saves the following group files:
%
%       `<targetf>/seedmap_<listname>[_<title>]_<roi>_<fcmeasure>_group_mean`
%           Mean group requested correlation coefficient or covariance.
%
%       `<targetf>/seedmap_<listname>[_<title>]_<roi>_<fcmeasure>_Fz_group_mean`
%           Mean group Fisher Z values.
%
%       `<targetf>/seedmap_<listname>[_<title>]_<roi>_<fcmeasure>_group_p`
%           Group p values testing difference from 0.
%
%       `<targetf>/seedmap_<listname>[_<title>]_<roi>_<fcmeasure>_group_Z`
%           Group Z converted p values testing difference from 0.
%
%       `<targetf>/seedmap_<listname>[_<title>]_<roi>_<fcmeasure>_all_sessions`
%           Correlation coefficients or covariance for all sessions.
%
%       `<targetf>/seedmap_<listname>[_<title>]_<roi>_<fcmeasure>_Fz_all_sessions`
%           Fisher Z values for all sessions.
%
%       Definitions:
%
%       - `<targetf>` is the group target folder.
%       - `<roi>` is the name of the ROI for which the seed map was computed
%         for.
%       - `<listname>` is the listname name of the flist.
%       - `<title>` is the title of the extraction event(s), if event string
%         was specified.
%
%       Based on saveind option specification the following files may be saved:
%
%       - `<targetf>/seedmap[_<sessionid>]_<listname>[_<title>]_<roi>_<fcmeasure>`
%           Correlation coefficients or covariances
%
%       - `<targetf>/seedmap[_<sessionid>]_<listname>[_<title>]_<roi>_<fcmeasure>_Fz`
%           Fisher Z values
%
%       - `<targetf>/seedmap[_<sessionid>]_<listname>[_<title>]_<roi>_<fcmeasure>_Z`
%           Z converted p values testing difference from 0
%
%       - `<targetf>/seedmap[_<sessionid>]_<listname>[_<title>]_<roi>_<fcmeasure>_p`
%           p values testing difference from 0
%
%       Definitions:
%
%       - `<targetf>` is either the group target folder or the individual
%         image folder.
%       - `<listname>` is the provided name of the bold(s).
%       - `<sessionid>` is the id of the session/subject, if it was requested
%         or if files are saved to the group folder.
%       - `<title>` is the title of the extraction event(s), if event string
%         was specified.
%       - `<roi>` is the name of the ROI for which the seed map was computed
%         for.
%
%   Notes:
%       The method returns a structure array named fcmaps with the fields lised
%       above for each specified data extraction.
%
%       Use:
%           The function computes seed maps for the specified ROI. If an event
%           string is provided, it has to start with a path to the .fidl file to
%           be used to extract the events, following by a pipe separated list of
%           event extraction definitions::
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
%           otherwise, each event will be summrised by a single frame in a newly
%           generated events series image.
%   
%           From the resulting image, ROI series will be extracted for each
%           specified ROI as specified by the roimethod option. A seed-map will
%           be computed for each ROI where for each voxel or grayordinate, a
%           correlation or covariance of its dataseries with the ROI will be
%           entered.
%
%           The results will be returned in a fcmaps structure and, if so
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

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 5 || isempty(options), options = '';  end
if nargin < 4 || isempty(targetf), targetf = '.'; end
if nargin < 3 frames  = []; end
if nargin < 2 error('ERROR: At least list information and ROI .names file have to be specified!'); end

% ----- parse options
default = 'sessions=all|roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|savegroup=all|saveind=none|savesessionid=false|itargetf=sfolder|verbose=false|debug=false';
options = general_parse_options([], options, default);

verbose = strcmp(options.verbose, 'true');
printdebug = strcmp(options.debug, 'true');

gem_options = sprintf('ignore:%s|badevents:%s|verbose:%s|debug:%s', options.ignore, options.badevents, options.verbose, options.debug);
fcmeasure = options.fcmeasure;

if verbose
    general_print_struct(options, 'fc_compute_seedmaps options used');
end

if verbose; fprintf('\n\nChecking ...\n'); end

options.flist = flist;
options.roiinfo = roiinfo;
options.targetf = targetf;

general_check_options(options, 'fc, eventdata, roimethod, flist, roiinfo, targetf', 'stop');

%   ------------------------------------------------------------------------------------------
%                                                                          check files to save

% -> group files

options.savegroup = strtrim(regexp(options.savegroup, ',', 'split'));

if ismember({'none'}, options.savegroup)
    options.savegroup = {};

elseif ismember({'all'}, options.savegroup)

    if ismember(options.fcmeasure, {'cv', 'mi', 'cc'})
        options.savegroup = {'group_z', 'group_p', 'mean_r', 'all_r'};
    elseif ismember(options.fcmeasure, {'r', 'rho', 'coh'})
        options.savegroup = {'group_z', 'group_p', 'mean_r', 'mean_fz', 'all_fz', 'all_r'};
    end

else

    if ismember(options.fcmeasure, {'cv', 'mi', 'cc'})
        options.savegroup = intersect(options.savegroup, {'group_z', 'group_p', 'mean_r', 'all_r'});
    elseif ismember(options.fcmeasure, {'r', 'rho', 'coh'})
        options.savegroup = intersect(options.savegroup, {'group_z', 'group_p', 'mean_r', 'mean_fz', 'all_fz', 'all_r'});
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
    options.saveind = {};
end

if length(options.saveind) 
    if strcmp(options.fcmeasure, 'r')
        options.saveind = intersect(options.saveind, {'r', 'fz', 'z', 'p', 'jr', 'jfz', 'jz', 'jp'});
    elseif ismember(options.fcmeasure, {'rho', 'coh'}) 
        options.saveind = intersect(options.saveind, {'r', 'fz', 'jr', 'jfz'});
    else
        options.saveind = intersect(options.saveind, {'r', 'jr'});
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

    % ---> run individual session

    if verbose; fprintf('     ... creating ROI mask'); end

    roi  = nimage.img_prep_roi(roiinfo, sroifile);
    nroi = length(roi.roi);

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

        if verbose; fprintf('         ... set %s\n', exsets(n).title); end
        
        % ---> get the extracted timeseries

        ts = y.img_extract_timeseries(exsets(n).exmat, options.eventdata);

        if verbose; fprintf('         ... extracted ts\n'); end
        
        % ---> generate seedmaps

        rs = ts.img_extract_roi(roi, [], options.roimethod);
        fc = ts.zeroframes(size(rs, 1));
        fc.data = fc_compute(ts.data, rs, options.fcmeasure, false, options);
        % fc = ts.img_compute_correlations(rs', options.fcmeasure, false, strcmp(options.debug, 'true'), options);

        if verbose; fprintf('         ... computed seedmap\n'); end

        % ---> Embedd results (if group data is requested)
        
        if embed_data
            if first_subject
                fcmaps(n).title    = exsets(n).title;
                fcmaps(n).roi      = {roi.roi.roiname};
                fcmaps(n).subjects = {};
            end
            fcmaps(n).subjects{s}  = subjectid;
            fcmaps(n).fc(s).(fcmeasure) = fc;
            fcmaps(n).fc(s).N = ts.frames;
                        
            if verbose; fprintf('         ... embedded\n'); end
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
        end

        % set up filetype for single images

        if strcmp(y.filetype, 'dtseries') || strcmp(y.filetype, 'ptseries')
            tfiletype = [y.filetype(1) 'scalar'];
        else
            tfiletype = y.filetype;
        end

        % --- loop through sets

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
    
        if any(ismember(options.saveind, {'r', 'fz', 'z', 'p', 'rho', 'cv', 'cc', 'coh', 'mi'}));

            for r = 1:nroi

                if verbose; fprintf(' %s', roi.roi(r).roiname); end

                % --- prepare basename

                basefilename = sprintf('seedmap_%s%s%s_%s', subjectname, lname, settitle, roi.roi(r).roiname);

                % --- save images

                for sn = 1:length(options.saveind)
                    switch options.saveind{sn}
                        case 'r'
                            t = fc.sliceframes([1:nroi] == r);                                              
                            t.filetype = tfiletype;
                            if printdebug; fprintf(['\n             -> ' fullfile(stargetf, [basefilename '_' fcmeasure])]); end
                            t.cifti.maps = {['seedmap ' roi.roi(r).roiname ' ' fcmeasure]};
                            t.img_saveimage(fullfile(stargetf, [basefilename '_' fcmeasure]));
                        case 'fz'
                            t = fz.sliceframes([1:nroi] == r);
                            t.filetype = tfiletype;
                            if printdebug; fprintf(['\n             -> ' fullfile(stargetf, [basefilename '_' fcmeasure '_Fz'])]); end
                            t.cifti.maps = {['seedmap ' roi.roi(r).roiname ' ' fcmeasure ' [Fz]']};
                            t.img_saveimage(fullfile(stargetf, [basefilename '_' fcmeasure '_Fz']));
                        case 'z'
                            t = Z.sliceframes([1:nroi] == r);
                            t.filetype = tfiletype;
                            if printdebug; fprintf(['\n             -> ' fullfile(stargetf, [basefilename '_' fcmeasure '_Z'])]); end
                            t.cifti.maps = {['seedmap ' roi.roi(r).roiname ' ' fcmeasure ' [Z]']};
                            t.img_saveimage(fullfile(stargetf, [basefilename '_' fcmeasure '_Z']));
                        case 'p'
                            t = p.sliceframes([1:nroi] == r);
                            t.filetype = tfiletype;
                            if printdebug; fprintf(['\n             -> ' fullfile(stargetf, [basefilename '_' fcmeasure '_p'])]); end
                            t.cifti.maps = {['seedmap ' roi.roi(r).roiname ' ' fcmeasure ' [p]']};
                            t.img_saveimage(fullfile(stargetf, [basefilename '_' fcmeasure '_p']));
                    end
                end
            end
        end

        % --- print for all ROI jointly

        if any(ismember(options.saveind, {'jr', 'jfz', 'jz', 'jp', 'jrho', 'jcv', 'jcc', 'jmi', 'jcoh'}));

            allroi = strjoin({roi.roi.roiname}, '-');
            basefilename = sprintf('seedmap_%s%s%s_%s', subjectname, lname, settitle, allroi);
            roi_names = {roi.roi.roiname};

            if verbose; fprintf(' %s', allroi); end

            % --- save images

            for sn = 1:length(options.saveind)
                switch options.saveind{sn}
                    case 'jr'
                        t = fc;  
                        t.filetype = tfiletype;
                        if printdebug; fprintf(['\n             -> ' fullfile(stargetf, [basefilename '_' fcmeasure])]); end
                        t.cifti.maps = cellfun(@(x) ['seedmap ' x ' ' fcmeasure], roi_names, 'UniformOutput', false);
                        t.img_saveimage(fullfile(stargetf, [basefilename '_' fcmeasure]));
                    case 'jfz'
                        t = fz;
                        t.filetype = tfiletype;
                        if printdebug; fprintf(['\n             -> ' fullfile(stargetf, [basefilename '_' fcmeasure '_Fz'])]); end
                        t.cifti.maps = cellfun(@(x) ['seedmap ' x ' ' fcmeasure ' [Fz]'], roi_names, 'UniformOutput', false);
                        t.img_saveimage(fullfile(stargetf, [basefilename '_' fcmeasure '_Fz']));
                    case 'jz'
                        t = Z;
                        t.filetype = tfiletype;
                        if printdebug; fprintf(['\n             -> ' fullfile(stargetf, [basefilename '_' fcmeasure '_Z'])]); end
                        t.cifti.maps = cellfun(@(x) ['seedmap ' x ' ' fcmeasure ' [Z]'], roi_names, 'UniformOutput', false);
                        t.img_saveimage(fullfile(stargetf, [basefilename '_' fcmeasure '_Z']));
                    case 'jp'
                        t = p;
                        t.filetype = tfiletype;
                        if printdebug; fprintf(['\n             -> ' fullfile(stargetf, [basefilename '_' fcmeasure '_p'])]); end
                        t.cifti.maps = cellfun(@(x) ['seedmap ' x ' ' fcmeasure ' [p]'], roi_names, 'UniformOutput', false);
                        t.img_saveimage(fullfile(stargetf, [basefilename '_' fcmeasure '_p']));
                end
            end
        end
        if verbose; fprintf(' done.\n'); end
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
        if verbose; fprintf(' -> %s\n', fcmaps(setid).title); end
        if exsets(n).title, settitle = ['_' exsets(n).title]; else settitle = ''; end

        for roiid = 1:nroi
            roiname = fcmaps(setid).roi{roiid};
        
            if verbose; fprintf('    ... for region %s', roiname); end
            
            % -- prepare group fc maps for the ROI
            fc = fcmaps(setid).fc(1).(fcmeasure).zeroframes(list.nsessions);
            for sid = 1:list.nsessions
                fc.data(:, sid) = fcmaps(setid).fc(sid).(fcmeasure).data(:, roiid);
            end

            % -- compute Fisher-z values
            if any(ismember(options.savegroup, {'mean_fz', 'group_p', 'group_z', 'mean_r', 'all_fz'}))
                fz = fc;
                fz.data = fc_fisher(fz.data);
            end

            % -- compute p-values
            if any(ismember(options.savegroup, {'group_p', 'group_z'}))
                if ismember(fcmeasure, {'cv', 'mi', 'cc'})
                    [p Z M] = fc.img_ttest_zero();
                elseif ismember(fcmeasure, {'r', 'rho', 'coh'})
                    [p Z MFz] = fz.img_ttest_zero();
                    M = MFz.img_FisherInv();
                end
            end

            % -- compute mean
            if any(ismember(options.savegroup, {'mean_r'})) && isempty(M)
                M = fc.zeroframes(1);
                if ismember(fcmeasure, {'cv', 'mi', 'cc'})
                    M.data = mean(fc.data, 2);
                elseif ismember(fcmeasure, {'r', 'rho', 'coh'})
                    MFz = fc.zeroframes(1);
                    MFz.data = mean(fz.data, 2);
                    M = MFz.img_FisherInv();
                end
            end

            % --- save requested data
            if verbose; fprintf(' ... saving ...'); end
            basefilename = sprintf('seedmap_%s%s_%s_%s', lname, settitle, roiname, fcmeasure);

            % -- save group mean results
            if any(ismember(options.savegroup, {'mean_r'}))
                if printdebug; fprintf(['\n             -> ' fullfile(targetf, [basefilename '_group_mean'])]); end
                M.filetype = tfiletype;
                M.cifti.maps = {['seedmap ' roiname ' ' fcmeasure ' [group mean]']};
                M.img_saveimage(fullfile(targetf, [basefilename '_group_mean']), extra);                
                if verbose && ~printdebug; fprintf([' ' fcmeasure]); end
            end

            % -- save group mean fz results
            if any(ismember(options.savegroup, {'mean_fz'}))
                if printdebug; fprintf(['\n             -> ' fullfile(targetf, [basefilename '_Fz_group_mean'])]); end
                MFz.filetype = tfiletype;
                MFz.cifti.maps = {['seedmap ' roiname ' ' fcmeasure ' [Fz group mean]']};
                MFz.img_saveimage(fullfile(targetf, [basefilename '_Fz_group_mean']), extra);
                if verbose && ~printdebug; fprintf(' fz'); end
            end

            % -- save all results
            if any(ismember(options.savegroup, {'all_r'}))
                if printdebug; fprintf(['\n             -> ' fullfile(targetf, [basefilename '_all_sessions'])]); end
                fc.filetype = tfiletype;
                fc.cifti.maps = cellfun(@(x) ['seedmap ' x ' ' roiname ' ' fcmeasure], session_names, 'UniformOutput', false);
                fc.img_saveimage(fullfile(targetf, [basefilename '_all_sessions']), extra);
                if verbose && ~printdebug; fprintf(' all_r'); end
            end

            % -- save all fz results
            if any(ismember(options.savegroup, {'all_fz'}))
                if printdebug; fprintf(['\n             -> ' fullfile(targetf, [basefilename '_Fz_all_sessions'])]); end
                fz.filetype = tfiletype;
                fz.cifti.maps = cellfun(@(x) ['seedmap ' x ' ' roiname ' ' fcmeasure ' [Fz]'], session_names, 'UniformOutput', false);
                fz.img_saveimage(fullfile(targetf, [basefilename '_Fz_all_sessions']), extra);
                if verbose && ~printdebug; fprintf(' all_fz'); end
            end
            
            % -- save group p results
            if any(ismember(options.savegroup, {'group_p'}))
                if printdebug; fprintf(['\n             -> ' fullfile(targetf, [basefilename '_group_p'])]); end
                p.filetype = tfiletype;
                p.cifti.maps = {['seedmap ' roiname ' ' fcmeasure ' [group p]']};
                p.img_saveimage(fullfile(targetf, [basefilename '_group_p']), extra);
                if verbose && ~printdebug; fprintf(' p'); end
            end

            % -- save group Z results
            if any(ismember(options.savegroup, {'group_z'}))
                if printdebug; fprintf(['\n             -> ' fullfile(targetf, [basefilename '_group_Z'])]); end
                Z.filetype = tfiletype;
                Z.cifti.maps = {['seedmap ' roiname ' ' fcmeasure ' [group Z]']};
                Z.img_saveimage(fullfile(targetf, [basefilename '_group_Z']), extra);
                if verbose && ~printdebug; fprintf(' Z'); end
            end

            if verbose; fprintf(' ... done.\n'); end
        end
    end
end            

if verbose; fprintf('\n\nCompleted\n'); end
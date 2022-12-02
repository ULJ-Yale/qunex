function [fcmat] = fc_compute_roifc(bolds, roiinfo, frames, targetf, options)

%``fc_compute_roifc(bolds, roiinfo, frames, targetf, options)``
%
%   Computes ROI functional connectivity matrices for individual
%   subject / session.
%
%   Parameters:
%       --bolds (str):
%           A string with a pipe separated list of paths to .conc or bold files.
%           The first element has to be the name of the file or group to be used
%           when saving the data.
%           E.g.: 'rest|<path to rest file 1>|<path to rest file 2>'.
%
%       --roiinfo (str):
%           A path to the names file specifying group based ROI. Additionaly,
%           separated by a pipe '|' symbol, a path to an image file holding
%           subject/session specific ROI definition.
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
%               '<fidlfile>|<extraction name>:<event list>:<extraction start>:<extraction end>'
%
%           where:
%
%           - fidlfile
%               is a path to the fidle file that defines the events
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
%               '<fidlfile>|encoding:e-color,e-shape:s2:s2|delay:d-color,d-shape:s2:e0'
%
%       --targetf (str, default '.'):
%           The folder to save images in.
%
%       --options (str, default 'roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|saveind=none|verbose=false|debug=false|fcname=|addidtofile=false|subjectid='):
%           A string specifying additional analysis options formated as pipe
%           separated pairs of colon separated key, value pairs::
%
%               "<key>:<value>|<key>:<value>".
%
%           It takes the following keys and values:
%
%           - roimethod
%               What method to use to compute ROI signal:
%
%               - mean
%                   compute mean values across the ROI
%               - median
%                   compute median value across the ROI
%	            - max
%                   compute maximum value across the ROI
%	            - min
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
%                   covariance estimate.
%
%               Defaults to 'r'.
%
%           - saveind
%               A comma separted list of formats to use to save the data:
%
%               - long
%                   save the resulting data in a long format .tsv file
%               - wide-single
%                   save the resulting data in a single wide format .tsv file
%               - wide-separate
%                   save the resulting data in a wide format .tsv file, one
%                   file per each measure of interest
%               - mat
%                   save the resulting data in a matlab .mat file.
%               - none
%                   don't save the results in a file, same as ''.
%
%               Defaults to 'none'.
%
%           - fcname
%               An optional name describing the functional connectivity
%               computed to add to the output files, if empty, it won't be
%               used. Defaults to ''.
%
%           - subjectid
%               An optional subject/session id to report in the results, 
%               if empty, it won't be used. Defaults to ''.
%
%           -addidtofile
%               Whether to add subjectid to the filename if a subject id, 
%               is provided. Defaults to 'false'.
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
%       fcmat
%           - title
%               The title of the extraction as specifed in the frames string,
%               empty if extraction was specified using a numeric value.
%           - roi
%               A cell array with the names of the ROI used in the order of
%               columns and rows in the functional connectivity matrix.
%           - N
%               Number of frames over which the matrix was computed.
%           - r
%               Correlation matrix between all ROI for that subject/session.
%           - fz
%               Fisher z transformed correlation matrix between all ROI for that
%               subject/session.
%           - z
%               z-scores for the correlations.
%           - p
%               p-values for the correlations.
%           - cv
%               Covariance matrix between all ROI for that subject/session.
%
%   Notes:
%       Please note, that `cv` will only be present if it was specified as the
%       cmeasure. `r`, `fz`, `z`, `p` will only be present if `r` was specified
%       as the fcmeasure.
%
%       Based on saveind option specification a file may be saved with the
%       functional connectivity data saved in a matlab.mat file and/or in a text
%       long format::
%
%           <targetf>/<name>[_<fcname>][_<subjectid>]_<cor|cov>[_<long|[_<r|Fz|cv>]wide>].<tsv|mat>
%
%       - `<name>` is the provided name of the bold(s)
%       - `<fcname>` is the provided name of the functional connectivity computed,
%         if it was specified
%       - `<subjectid>` is the provided name of the subject, if it was
%         specified.
%
%       `long` and `wide` will be added for long and wide tsv files, respectively.
%       `r`, `Fz`, `cv` will be added when wide data is saved in separate wide 
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
%       - cv
%       - r
%       - Fz
%       - Z
%       - p
%   
%       wide format
%       - name
%       - title
%       - subject
%       - measure
%       - [<roi1_code>]_<roi1_name>-[<roi_code>2]_<roi3_name>
%
%       Note:
%       In wide format only cv, r, and Fz data will be saved. 
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
if nargin < 2 error('ERROR: At least boldlist and ROI .names file have to be specified!'); end

% --------------------------------------------------------------
%                                              parcel processing

parcels = {};

if startsWith(roiinfo, 'parcels:')
    parcels = strtrim(regexp(roiinfo(9:end), ',', 'split'));
end

% ----- parse options

default = 'roimethod=mean|eventdata=all|ignore=use,fidl|badevents=use|fcmeasure=r|saveind=none|verbose=false|debug=false|fcname=|addidtofile=false|subjectid=';
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

if ~ismember(options.roimethod, {'mean', 'pca', 'median', 'min', 'max'})
    error('ERROR: Invalid roi extraction method: %s', options.roimethod);
end

if ~ismember(options.fcmeasure, {'r', 'cv', 'rho'})
    error('ERROR: Invalid functional connectivity computation method: %s', options.fcmeasure);
end

% ----- What should be saved

options.saveind = strtrim(regexp(options.saveind, ',', 'split'));
if ismember({'none'}, options.saveind)
    options.saveind = {};
end
sdiff = setdiff(options.saveind, {'mat', 'long', 'wide-single', 'wide-separate', ''});
if ~isempty(sdiff)
    error('ERROR: Invalid save format specified: %s', strjoin(sdiff,","));
end

% ----- Get the list of files

[name, bolds] = strtok(bolds, '|');
bolds = bolds(2:end);
boldlist = strtrim(regexp(bolds, '\|', 'split'));

if isempty(parcels)
    [roideffile, sroifile] = strtok(roiinfo, '|');
    if sroifile
        sroifile = sroifile(2:end);
    else
        sroifile = [];
    end
end

% ----- Check if the files are there!

go = true;
if verbose; fprintf('\nChecking ...\n'); end

for bold = boldlist
    go = go & general_check_file(bold{1}, bold{1}, 'error');
end

if isempty(parcels)
    go = go & general_check_file(roideffile, 'ROI definition file', 'error');
    if sroifile
        go = go & general_check_file(sroifile, 'individual ROI file', 'error');
    end
end
if any(ismember({'txt', 'mat'}, options.saveind))
    general_check_folder(targetf, 'results folder', true, verbose);
end

if ~go
    error('ERROR: Some files were not found. Please check the paths and start again!\n\n');
end


%   ------------------------------------------------------------------------------------------
%                                                                            do the processing


% ---> reading image files

if verbose; fprintf('     ... reading image file(s)'); end
y = nimage(bolds);
if verbose; fprintf(' ... %d frames read, done.\n', y.frames); end


% ---> processing roi/parcels info

if isempty(parcels)
    if verbose; fprintf('     ... creating ROI mask\n'); end
    roi = nimage.img_read_roi(roideffile, sroifile);
    roi.data = roi.image2D;    
else
    if ~isfield(y.cifti, 'parcels') || isempty(y.cifti.parcels)
        error('ERROR: The bold file lacks parcel specification! [%s]', sessions(1).glm);
    end
    if length(parcels) == 1 && strcmp(parcels{1}, 'all')        
        parcels = y.cifti.parcels;
    end
    roi.roi.roinames = parcels;
    [x, roi.roi.roicodes] = ismember(parcels, y.cifti.parcels);
end

roinames = roi.roi.roinames;
roicodes = roi.roi.roicodes;
nroi = length(roi.roi.roinames);
nparcels = length(parcels);


% ---> create extraction sets

if verbose; fprintf('     ... generating extraction sets\n'); end
exsets = y.img_get_extraction_matrices(frames, options);
for n = 1:length(exsets)
    if verbose; fprintf('         -> %s: %d good events, %d good frames\n', exsets(n).title, size(exsets(n).exmat, 1), sum(exsets(n).estat)); end
end

% ---> loop through extraction sets

if verbose; fprintf('     ... computing fc matrices\n'); end

nsets = length(exsets);
for n = 1:nsets

    if verbose; fprintf('         ... set %s', exsets(n).title); end
    
    % --> get the extracted timeseries

    ts = y.img_extract_timeseries(exsets(n).exmat, options.eventdata);

    if verbose; fprintf(' ... extracted ts'); end
    
    % --> generate fc matrice
    
    if isempty(parcels)
        rs = ts.img_extract_roi(roi, [], options.roimethod);
    else
        rs = ts.img_extract_roi(roiinfo, [], options.roimethod); 
    end

    fc = fc_compute(rs, [], options.fcmeasure, false);
    
    if verbose; fprintf(' ... computed fc matrix'); end

    % ------> Embed results

    fcmat(n).title    = exsets(n).title;
    fcmat(n).roinames = roi.roi.roinames;
    fcmat(n).roicodes = roi.roi.roicodes;
    fcmat(n).N        = ts.frames;

    if strcmp(options.fcmeasure, 'cv')
        fcmat(n).cv = fc;
    else
        fcmat(n).r  = fc;
        fcmat(n).fz = fc_fisher(fc);
        fcmat(n).z  = fcmat(n).fz/(1/sqrt(fcmat(n).N-3));
        fcmat(n).p  = (1 - normcdf(abs(fcmat(n).z), 0, 1)) * 2 .* sign(fcmat(n).fz);
    end

    if verbose; fprintf(' ... embedded\n'); end
end


% ===================================================================================================
%                                                                                        save results

if ~any(ismember({'mat', 'long', 'wide-single', 'wide-separate'}, options.saveind))
    if verbose; fprintf(' ... done\n'); end
    return; 
end

if verbose; fprintf('     ... saving results\n'); end

% set fcname

if options.fcname
    fcname = [options.fcname, '_'];
else
    fcname = '';
end

% set subjectname

if addidtofile && issubjectid
    subjectname = [options.subjectid, '_'];
else
    subjectname = '';
end

ftail = {'cor', 'cov', 'rho'};
ftail = ftail{ismember({'r', 'cv', 'rho'}, options.fcmeasure)};

basefilename = fullfile(targetf, sprintf('%s_%s%s%s', name, fcname, subjectname, ftail));

% ---------------------------------------------------------------------------------------------------
%                                                                                              matlab

if ismember({'mat'}, options.saveind)
    if verbose; fprintf('         ... saving mat file'); end
    save(basefilename, 'fcmat');
    if verbose; fprintf(' ... done\n'); end
end

% ---------------------------------------------------------------------------------------------------
%                                                                                            long tsv

if ismember({'long'}, options.saveind)
    
    if verbose; fprintf('         ... saving long tsv file'); end

    fout = fopen([basefilename '_long.tsv'], 'w');

    if strcmp(options.fcmeasure, 'cv')
        fprintf(fout, 'name\ttitle\tsubject\troi1_name\troi2_name\troi1_code\troi2_code\tcv\n');
    else
        fprintf(fout, 'name\ttitle\tsubject\troi1_name\troi2_name\troi1_code\troi2_code\tr\tFz\tZ\tp\n');
    end

    for n = 1:nsets
        if fcmat(n).title, settitle = fcmat(n).title; else settitle = 'ts'; end

        % --- set ROI names

        nroi = length(fcmat(n).roinames);

        idx1 = repmat([1:nroi], nroi, 1);
        idx1 = tril(idx1, -1);
        idx1 = idx1(idx1 > 0);

        idx2 = repmat([1:nroi]', 1, nroi);
        idx2 = tril(idx2, -1);
        idx2 = idx2(idx2 > 0);

        roi1name = fcmat(n).roinames(idx1);
        roi2name = fcmat(n).roinames(idx2);
        roi1code = fcmat(n).roicodes(idx1);
        roi2code = fcmat(n).roicodes(idx2);

        idx  = reshape([1:nroi*nroi], nroi, nroi);
        idx  = tril(idx, -1);
        idx  = idx(idx > 0);        

        nfc  = length(idx);

        % --- write up

        if strcmp(options.fcmeasure, 'cv')
            cv = fcmat(n).cv(idx);
            for c = 1:nfc
                fprintf(fout, '%s\t%s\t%s\t%s\t%s\t%d\t%d\t%.5f\n', name, settitle, options.subjectid, roi1name{c}, roi2name{c}, roi1code(c), roi2code(c), cv(c));
            end
        else
            r  = fcmat(n).r(idx);
            fz = fcmat(n).fz(idx);
            z  = fcmat(n).z(idx);
            p  = fcmat(n).p(idx);
            for c = 1:nfc
                fprintf(fout, '%s\t%s\t%s\t%s\t%s\t%d\t%d\t%.5f\t%.5f\t%.5f\t%.7f\n', name, settitle, options.subjectid, roi1name{c}, roi2name{c}, roi1code(c), roi2code(c), r(c), fz(c), z(c), p(c));
            end
        end
    end
    fclose(fout);
    if verbose; fprintf(' ... done\n'); end
end

% ---------------------------------------------------------------------------------------------------
%                                                                                            wide tsv

if any(ismember({'wide-separate', 'wide-single'}, options.saveind))

    if verbose; fprintf('         ... saving wide tsv file'); end

    nroi = length(fcmat(1).roi);
    roi  = fcmat(1).roi;
    
    if ismember({'wide-separate'}, options.saveind)
        if strcmp(options.fcmeasure, 'cv') 
            fout_cv = fopen([basefilename '_cv_wide.tsv'], 'w');
            printHeader(fout_cv, roinames, roicodes);
            toclose = [fout_cv];
        else
            fout_r  = fopen([basefilename '_r_wide.tsv'], 'w');            
            fout_Fz = fopen([basefilename '_Fz_wide.tsv'], 'w');
            printHeader(fout_r, roinames, roicodes);
            printHeader(fout_Fz, roinames, roicodes);
            toclose = [fout_r, fout_Fz];
        end        
    else
        fout = fopen([basefilename '_wide.tsv'], 'w');
        fout_r  = fout;
        fout_Fz = fout;
        fout_cv = fout;
        printHeader(fout, roinames, roicodes)        
        toclose = [fout];
    end

    for n = 1:nsets
        if fcmat(n).title, settitle = fcmat(n).title; else settitle = 'ts'; end

        if strcmp(options.fcmeasure, 'cv')
            for r = 1:nroi
                fprintf(fout_cv,'\n%s\t%s\t%s\t%s\t%s\t%d', name, settitle, options.subjectid, 'cv', roinames{r}, roicodes(r));
                fprintf(fout_cv, '\t%.7f', fcmat(n).cv(r, :))
            end
        else
            for r = 1:nroi
                fprintf(fout_r,'\n%s\t%s\t%s\t%s\t%s\t%d', name, settitle, options.subjectid, 'cv', roinames{r}, roicodes(r));
                fprintf(fout_r, '\t%.7f', fcmat(n).r(r, :))
            end
            for r = 1:nroi
                fprintf(fout_Fz,'\n%s\t%s\t%s\t%s\t%s\t%d', name, settitle, options.subjectid, 'cv', roinames{r}, roicodes(r));
                fprintf(fout_Fz, '\t%.7f', fcmat(n).fz(r, :))
            end
        end
    end

    for f = toclose
        fclose(f);
    end
end

if verbose; fprintf(' ... done\n'); end


function [] = printHeader(fout, roinames, roicodes)
    fprintf(fout, 'name\ttitle\tsubject\tmeasure\troiname\troicode');
    nroi = length(roinames)
    for r = 1:nroi
        fprintf(fout, '\t[%d]_%s', roicodes(r), roinames{r})
    end
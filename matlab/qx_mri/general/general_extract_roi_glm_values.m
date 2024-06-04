function [data] = general_extract_roi_glm_values(flist, roif, outf, effects, frames, values, tformat, verbose)

%``general_extract_roi_glm_values(flist, roif, outf, effects, frames, values, tformat, verbose)``
%
%   Extracts per ROI estimates of specified effects from a volume or cifti GLM
%   files as specified in the file list.
%
%   Parameters:
%       --flist (str):
%           Path to the list file or a well structured string of files or
%           sessions to process.
%
%       --roif (str):
%           Path to a .names ROI file descriptor or a comma separated list of
%           parcels to be extracted, specified as 'parcels:<parcel1>,<parcel2>'.
%           'parcels:all' will export data for all parcels. Note that in this
%           case the list of parcels will be based on glm file from the first
%           session in the list.
%
%       --outf (str, default ''):
%           Name of the output file. If left empty the it is set to list root
%           with '.tsv' extension.
%
%       --effects (str, default ''):
%           A cell array or a comma separated list of effects of interest. If
%           none specified, all but trend and baseline are exported.
%
%       --frames (int, default ''):
%           List of frames to extract from all effects. All if empty or not
%           specified.
%
%       --values (str, default 'raw'):
%           In what form to extract the estimates. Possibilities are raw beta
%           values ('raw') or percent signal change ('psc') values.
%
%       --tformat (str, default 'wide,long,mat'):
%           A comma separated string specifying in what format the data is to be
%           extracted. It can be a combination of:
%
%           - 'mat'  ... a matlab file,
%           - 'wide' ... wide format txt file with one line per session
%             and each ROI and estimate in a separate column,
%           - 'long' ... long format txt file with one line per estimate
%             extracted with columns describing the session, ROI, effect
%             and frame that it belongs to. The minimum, maximum, median,
%             standard deviation, and standard error of the values within
%             the ROI are reported, as well as the number of effective
%             voxels within the ROI.
%
%       --verbose (bool, default false):
%           Whether to report on progress or not.
%
%   Returns:
%       data
%           The results are returned in a datastructure but also saved in the
%           specified file.
%
%   Notes:
%       The function is used to extract per ROI estimates of the effects of
%       interest for each of the ROI and sessions to enable second level
%       analysis and visualization of the data. In the background the function
%       first extracts the relevant volumes using the img_extract_glm_estimates.
%       It then defines the ROI and uses img_extract_roi_stats method to get per
%       ROI statistics.
%
%   Examples:
%       ::
%
%           qunex general_extract_roi_glm_values \
%               --flist='wm-glm.list' \
%               --roif='CCN.names' \
%               --outf='' \
%               --effects='encoding, delay' \
%               --frames='' \
%               --values='psc' \
%               --tformat='long'
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 8, verbose = false; end
if nargin < 7 || isempty(tformat), tformat = 'wide,long,mat'; end
if nargin < 6 || isempty(values), values = 'raw'; end
if nargin < 5, frames  = [];    end
if nargin < 4, effects = [];    end
if nargin < 3, outf    = [];    end
if nargin < 2, error('ERROR: No ROI file or parcel definition list provided!');  end
if nargin < 1, error('ERROR: No files to extract the values from provided!');  end

% --------------------------------------------------------------
%                                              parcel processing

parcels = {};
if starts_with(roif, 'parcels:')
    parcels = strtrim(regexp(roif(9:end), ',', 'split'));    
end

% --------------------------------------------------------------
%                                                    check files

general_check_file(flist, 'file list', 'errorstop');
if isempty(parcels)
    general_check_file(roif, 'ROI image', 'errorstop');
end

% --------------------------------------------------------------
%                                                  read filelist

list = general_read_file_list(flist);

% --------------------------------------------------------------
%                                                       read roi

if isempty(parcels)
    roi = nimage.img_prep_roi(roif);
elseif length(parcels) == 1 && strcmp(parcels{1}, 'all')
    t = nimage(list.session(1).glm);
    if ~isfield(t.cifti, 'parcels') || isempty(t.cifti.parcels)
        error('ERROR: The glm file lacks parcel specification! [%s]', list.session(1).glm);
    end
    parcels = t.cifti.parcels;
    for r = 1:length(parcels)
        roi.roi(r).roiname = parcels{r};
        [~, roi.roi(r).roicode] = ismember(parcels{r}, y.cifti.parcels);
    end
end
nroi = length(roi.roi);
nparcels = length(parcels);

% --------------------------------------------------------------
%                                             create output file

if isempty(outf)
    outf = [flist '_' values];
end

ltext = false;
wtext = false;

if ~isempty(strfind(tformat, 'long'))
    ltext = fopen([outf '_long.tsv'], 'w');
    fprintf(ltext, 'session\troi\troicode\tevent\tframe\tmin\tmax\tmean\tmedian\tsd\tse\tN');
end
if ~isempty(strfind(tformat, 'wide'))
    wtext = fopen([outf '_wide.tsv'], 'w');
    fprintf(wtext, 'session\tevent\tframe');
    for r = 1:nroi
        fprintf(wtext, '\t%s', roi.roi(r).roiname);
    end
end



% --------------------------------------------------------------
%                                          loop through sessions

for s = 1:list.nsessions

    % ---> read GLM

    if verbose, fprintf('\n---> processing session: %s', list.session(s).id); end

    % glm = nimage(sessions(s).glm, [], [], verbose);
    glm = nimage(list.session(s).glm);
    glm = glm.img_extract_glm_estimates(effects, frames);

    % ---> update ROI

    if isempty(parcels) && isfield(list.session(s), 'roi') && ~isempty(list.session(s).roi)
        sroi = nimage.img_prep_roi(roif, list.session(s).roi);
    else
        sroi = roi;
    end

    if strcmp(values, 'psc')
        glm.data = bsxfun(@rdivide, glm.data, glm.glm.gmean / 100);
    end

    if isempty(parcels)
        stats   = glm.img_extract_roi_stats(sroi);
    else
        if ~isfield(glm.cifti, 'parcels') || isempty(glm.cifti.parcels)
            fprintf('WARNING: The glm file [%s] lacks parcel specification! Skipping session [%s]', list.session(s).glm, list.session(s).id);
            continue
        end

        if all(ismember(parcels, glm.cifti.parcels))
            [~, parcel_index] = ismember(parcels, glm.cifti.parcels);
            for p = 1:nparcels
                stats(p).roiname = parcels{p};
                stats(p).roicode = p;
                stats(p).median  = glm.data(parcel_index(p),:);
                stats(p).max     = glm.data(parcel_index(p),:);
                stats(p).min     = glm.data(parcel_index(p),:);
                stats(p).mean    = glm.data(parcel_index(p),:);
                stats(p).N       = 1;
                stats(p).sd      = zeros(1, glm.frames);
                stats(p).se      = zeros(1, glm.frames);  
            end          
        else
            fprintf('WARNING: The glm file [%s] lacks some parcels (%s)! Skipping session [%s]', list.session(s).glm, strjoin(parcels(~ismember(parcels, glm.cifti.parcels)), ', '), list.session(s).id);
            continue
        end
    end

    data(s).stats = stats;
    data(s).effect = glm.glm.effects(glm.glm.effect);
    data(s).frame = glm.glm.eindex;

    nframes = length(stats(1).mean);

    if ltext
        for r = 1:nroi
            for f = 1:nframes
                fprintf(ltext, '\n%s\t%s\t%d\t%s\t%d\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%.3f\t%d', list.session(s).id, stats(r).roiname, stats(r).roicode, glm.glm.effects{glm.glm.effect(f)}, glm.glm.frame(f), stats(r).min(f), stats(r).max(f), stats(r).mean(f), stats(r).median(f), stats(r).sd(f), stats(r).se(f), stats(r).N);
            end
        end
    end
    if wtext
        for f = 1:nframes
            % fprintf(wtext, '\n%s\t%s\t%s', list.session(s).id, glm.glm.effects{glm.glm.effect(f)}, glm.glm.eindex(f));            
            fprintf(wtext, '\n%s\t%s\t%d', list.session(s).id, glm.glm.effects{glm.glm.effect(f)}, glm.glm.frame(f));            
            for r = 1:nroi
                fprintf(wtext, '\t%.3f', stats(r).mean(f));
            end
        end
    end
end

if ltext, fclose(ltext); end
if wtext, fclose(wtext); end

if ~isempty(strfind(tformat, 'mat'))
    save([outf '.mat'], 'data');
end

if verbose, fprintf('\n---> DONE\n'); end



% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function [] = general_glm_predict(flist, effects, targetf, options)

%``general_glm_predict(flist, effects, targetf, options)``
%
%   Computes predicted and residual signal based on GLM.
%
%   The function is based on the provided GLM file and (optionally) raw bold
%   data.
%
%   Parameters:
%       --flist (str):
%           Either a .list file listing the subjects and their files to use, or
%           a well structured file list string (see `general_read_file_list`).
%           The information should include at least `glm:` entries for each
%           session, as well as raw bold or conc files if residuals are
%           requested.
%
%       --effects (cell array | str):
%           Either a cell array or a comma separated string listing the names of
%           the effects that should be included in the prediction.
%
%       --targetf (str, default '.'):
%           The folder to save images in. It has to specify either a
%           target folder for all processed data or the location of session
%           functional images folder.
%
%       --options (str, 'default predicted_tail=|residual_tail=|sessions=all|save=|ignores>predict:mark,regress:mark|indtargetf=sfolder|bold_variant=|addidtofile=false|verbose=true|verboselevel=high'):
%           A string specifying additional analysis options formated as pipe
%           separated pairs of colon separated key, value pairs::
%
%               "<key>:<value>|<key>:<value>".
%
%           It takes the following keys and values:
%
%           predicted_tail
%               The tail to use for the predicted data. If no tail is provided,
%               a '_pred-<effects abbreviation> tail will be added to the glm
%               file name. <effects abbreviation> will be the first letters of
%               all the predicted regressors. ['']
%
%           residual_tail
%               The tail to use for the residual data. If no tail is provided, a
%               '_res-<effects abbreviation> tail will be added to each of the
%               source BOLD files. <effects abbreviation> will be the first
%               letters of all the predicted regressors. ['']
%
%           sessions
%               Which sessions to include in the analysis. The sessions should
%               be provided as a comma or space separated list. If all sessions
%               are to be processed this can be designated by 'all'. Defaults
%               to 'all'.
%
%           save
%               A comma separated string, listing the files to save ['']:
%
%               predicted
%                   save predicted bold timeseries
%               residual
%                   save residual bold timeseries
%           
%           ignores
%               How to deal with frames that were marked as bad and ignored when
%               GLM solution was completed. The information should be specified
%               separately for predicting timecourse and regressing signal:
%
%               'ignores>predict:[mark/linear/spline],regress:[keep/mark/linear/spline]'
%               
%               The options have the following meaning:
%       
%               keep
%                   keep the value in the original BOLD (only applicable to 
%                   regressed signal)
%               mark
%                   mark the bad frames by setting the value to "NaN" 
%               linear
%                   interpolate values for bad frames using linear interpolation
%               spline
%                   interpolate values for bad frames using spline interpolation
%
%               The default is 'ignores>predict:mark,regress:mark'
%
%           indtargetf
%               In case of group level extraction, where to save the individual
%               data ['sfolder']:
%
%               gfolder
%                   in the group target folder
%               sfolder
%                   in the individual session folder
%
%           img_suffix
%               An optional string that specifies the tail to be added to
%               the session 'image' subfolder if one is used. The target
%               location will then be:
%               <targetf>/<subjectid>/images<img_suffix>/functional<bold_variant>
%               ['']
%               
%           bold_variant
%               An optional string that specifies the tail be added to the
%               session specific 'functional' subfolder if one is used. The
%               target location will then be:
%               <targetf>/<subjectid>/images<img_suffix>/functional<bold_variant>
%               ['']
%
%           addidtofile
%               When running single session extraction or when saving to the
%               individual session functional images folder, whether to add
%               subjectid to the single session filename, if one is provided
%               ['false'].
%
%           verbose
%               Whether to be verbose 'true' or not 'false', when running the
%               analysis ['true']
%
%           verboselevel
%               Whether to be very detailed 'high' or not 'low', when reporting
%               progress ['high']
%
%   Output files:
%       If `indtargetf` is set to 'gfolder', all the resulting files will be
%       saved in the same folder, specified by `targetf` parameter. If
%       `indtargetf` is set to 'sfolder', then the results will be saved in
%       the subject specific sessions subfolders within the sessions folder
%       specified by the `targetf` parameter. If the files are in a variant
%       functional folder, then the 'bold_variant' option has to be
%       specified. In this case the location where the files will be saved
%       is specified by::
%
%           <targetf>/<session id>/images/functional<bold_variant>
%
%   Notes:
%       The functions computes predicted timeseries and (if requested) residual
%       after removal of the predicted signal, and saves the results.
%

if nargin < 4 || isempty(options), options = '';  end
if nargin < 3 || isempty(targetf), targetf = '.'; end
if nargin < 2 || isempty(effects), error('ERROR: At least data and effects to predict have to be specified!'); end
if nargin < 1 || isempty(flist), error('ERROR: At least data and effects to predict have to be specified!'); end

% -- support variables

filetypes = {'',         'nifti',    'dtseries',     'ptseries'};
extensions = {'.nii.gz', '.nii.gz', '.dtseries.nii', '.ptseries.nii'};

% ----- parse options

default = 'predicted_tail=|residual_tail=|sessions=all|save=|ignores>predict:mark,regress:mark|indtargetf=sfolder|img_suffix=|bold_variant=|addidtofile=false|verbose=true|verboselevel=high';
options = general_parse_options([], options, default);

effects  = strtrim(regexp(effects, ',', 'split'));
verbose  = strcmp(options.verbose, 'true');
detailed = strcmp(options.verboselevel, 'high');

if verbose; fprintf('\nRunning prediction for effects %s on list %s.\n', strjoin(effects, ', '), flist); end

if verbose && detailed
    general_print_struct(options, 'general_glm_predict options used');
end

options.save = strtrim(regexp(options.save, ',', 'split'));
if isempty(options.save)
    error('ERROR: No save option specified, nothing to do.');
end

if verbose && detailed; fprintf('\n\nStarting ...\n-> checking parameters\n'); end

if ~ismember({options.indtargetf}, {'gfolder', 'sfolder'})
    error('ERROR: No valid indtargetf specified [%s]. It has to be either gfolder or sfolder!', options.indtargetf);
end

if ismember({options.addidtofile}, {'true', 'false'})
    addidtofile = strcmp(options.addidtofile, 'true');
else
    error('ERROR: Invalid addidtofile option specified [%s]. It has to be either true or false!', options.addidtofile);
end

if isempty(options.predicted_tail)
    options.predicted_tail = sprintf('_pred-%s', get_firsts(effects));
end

if isempty(options.residual_tail)
    options.residual_tail = sprintf('_res-%s', get_firsts(effects));
end

% ------ Check file list

check = 'glm';

if verbose && detailed; fprintf('-> reading file list\n'); end

list = general_read_file_list(flist, options.sessions, check, verbose);

if sum(list.missing.sessions)
    fprintf('WARNING: Sessions with missing fields in file list will not be processed.\n');
    list.session = list.session(~list.missing.sessions);
    list.nsessions = length(list.session);
end

% ------ run prediction loop

if verbose; fprintf('-> processing sessions\n'); end

for s = 1:list.nsessions
    
    if verbose; fprintf('   ... session id: %s\n', list.session(s).id); end

    % -- root path to save results
    if strcmp(options.indtargetf, 'sfolder')
        targetpath = sprintf('%s/%s/images%s/functional%s/', targetf, list.session(s).id, options.img_suffix, options.bold_variant);
        targetconcpath = sprintf('%s/%s/images%s/functional%s/concs/', targetf, list.session(s).id, options.img_suffix, options.bold_variant);
        if addidtofile
            targetpath = sprintf('%s%s-', targetpath, list.session(s).id);
            targetconcpath = sprintf('%s%s-', targetconcpath, list.session(s).id);
        end
    else
        targetpath = sprintf('%s/%s-', targetf, list.session(s).id);
        targetconcpath = sprintf('%s/%s-', targetf, list.session(s).id);
    end

    % -- process files

    if verbose && detailed; fprintf('       - reading glm\n'); end

    glm = nimage(list.session(s).glm);

    % -- id extension

    extension = extensions{find(ismember(filetypes, glm.filetype))};    
    
    % -- do we have raw files
    if isfield(list.session(s), 'conc') && ~isempty(list.session(s).conc)
        if verbose && detailed; fprintf('       - reading conc file\n'); end
        raw = nimage(list.session(s).conc);
    elseif isfield(list.session(s), 'files') && ~isempty(list.session(s).files)
        if verbose && detailed; fprintf('       - reading raw files\n'); end
        raw = nimage(strjoin(list.session(s).files, '|'));
    else
        raw = [];
    end

    % -- temporary hack
    raw.use = ones(size(raw.use));

    % -- run requested computation
    if verbose && detailed; fprintf('       - computing predictions and/or residuals\n'); end
    if ismember({'residual'}, options.save)
        [predicted, residual] = img_glm_predict(glm, effects, raw, options);
    else
        [predicted] = img_glm_predict(glm, effects, raw, options);
    end

    % -- save residuals
    if ismember({'residual'}, options.save)
        if verbose && detailed; fprintf('       - saving residuals\n'); end
        savefiles = {};
        residual = residual.splitruns();
        for n = 1:length(residual)
            savefilename = [targetpath residual(n).img_basename() options.residual_tail extension];
            savefiles{end+1} = savefilename;
            if verbose && detailed; fprintf('         -> %s\n', savefilename); end
            residual(n).img_saveimage(savefilename);
        end
        if raw.rootconcname;
            [fp, fn, fe] = fileparts(raw.rootconcname);
            if verbose && detailed; fprintf('         -> %s\n', [targetconcpath fn fe options.residual_tail '.conc']); end
            nimage.img_save_concfile([targetconcpath fn fe options.residual_tail '.conc'], savefiles);
        end
    end

    % -- save predicted
    if ismember({'predicted'}, options.save)
        if verbose && detailed; fprintf('       - saving predictions\n'); end
        if ~isempty(raw)
            savefiles = {};
            predicted = predicted.splitruns();
            for n = 1:length(predicted)
                savefilename = [targetpath fpredicted(n).img_basename() options.predicted_tail extension];
                savefiles{end+1} = savefilename;
                if verbose && detailed; fprintf('         -> %s\n', savefilename); end
                predicted(n).img_saveimage(savefilename);
            end
            if raw.rootconcname;
                [fp, fn, fe] = fileparts(raw.rootconcname);
                if verbose && detailed; fprintf('         -> %s\n', [targetconcpath fn fe options.predicted_tail '.conc']); end
                nimage.img_save_concfile([targetconcpath fn fe options.predicted_tail '.conc'], savefiles);
            end
        else
            savefilename = [targetpath glm.img_basename() options.predicted_tail];
            if verbose && detailed; fprintf('         -> %s\n', savefilename); end
            predicted.img_saveimage(savefilename);
        end
    end
    if verbose && detailed; fprintf('       -> done\n'); end
end

if verbose; fprintf('-> finished\n'); end

% function [filenames, concname, nfiles] = get_filenames(session)
%     filenames = {};
%     concname = '';
%     for n = 1:length(session.files);
%         if regexp(session.files{n}, '.*\.conc$');
%             concname = session.files{n};
%             addfiles = img_read_concfile(session.files{n});
%             filenames = [filenames addfiles];
%         else
%             filenames{end+1} = session.files{n};
%         end
%     end
%     nfiles = length(filenames)

function [firsts] = get_firsts(effects)
    firsts = '';
    for e = effects
        firsts = [firsts e{1}(1)];
    end



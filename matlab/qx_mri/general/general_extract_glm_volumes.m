% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function [] = general_extract_glm_volumes(flist, outf, effects, frames, saveoption, values, verbose, txtf);

%``function [] = general_extract_glm_volumes(flist, outf, effects, frames, saveoption, values, verbose, txtf)``
%
%   For sessions specified in the session list it extracts the GLM estimates of
%   the effects of interests and saves them in the specified file.
%
%   INPUTS
%   ======
%
%   --flist       List of files / sessions to process. For each session id 
%                 in the list, there has to be a `glm:` file listed that 
%                 is a result of GLM analyses (a 'Bcoeff' file).
%   --outf        Root file name for the results. If empty, the flist name is 
%                 used. []
%   --efects      A cell array of strings or a comma separated list of effects 
%                 of interest. If empty all effects but Baseline and Trend are 
%                 extracted. []
%   --frames      Frame indeces to extract. If empty, all frames are extracted. []
%   --saveoption  Whether to save the extracted estimates in a single file
%                 organized 'by_session', 'by_effect', or in separate files for 
%                 each effect ('effect_files'). ['by_session']
%   --values      What kind of values to save: 'raw' or 'psc'. ['raw']
%   --verbose     Whether to report on the progress or not [false]
%   --txtf        An optional designator in what text file to also output the 
%                 data. Only saved if an option is provided and the input is 
%                 ptseries. Valid options are 'long' to save the data in long 
%                 format or empty to skip saving data in a text file. []
%
%   USE
%   ===
%
%   The function is used to extract GLM estimates for the effects of interest
%   for all the specified sessions and save them in a single file (or one
%   file per effect of interest). This files can then be used for more focused
%   analyses, such as second-level statistical testing using PALM.
%
%   To extract the effects of interest, the function calls the
%   img_extract_glm_estimates nimage method.
%
%   NOTICE
%   ======
%
%   The underlying method extracts the effects of interest by removing those
%   frames that relate to irrelevant effects. The order of the effects in the
%   resulting files will be the same as in the original GLM files when saved
%   organized 'by_session' and not as specified in the call to the function.
%   When the results are organized 'by_effect', the order of estimates will
%   be the same as in the effects variable. To be sure in what order the data
%   is present in the resulting file, please consult the 'list' structure
%   present in the extracted file, that for each frame specifies the session,
%   effect and frame the estimate belongs to.
%
%   Additionally, the code does not check for missing estimates. If an estimate
%   is not present in the file, no warning or error will be generated. So do
%   check the list structure that all the data is there.
%
%   EXAMPLE USE
%   ===========
%
%   ::
%   
%       general_extract_glm_volumes('wm-glm.list', 'wm-encoding-delay', ...
%       'encoding,delay', [], 'by_session');
%

if nargin < 8 || isempty(txtf),       txtf       = ''; end
if nargin < 7, verbose   = false; end
if nargin < 6 || isempty(values),     values     = 'raw'; end
if nargin < 5 || isempty(saveoption), saveoption = 'by_session'; end
if nargin < 4, frames    = [];    end
if nargin < 3, effects   = [];    end
if nargin < 2, outf      = [];    end

if nargin < 1, error('ERROR: No files to extract the volumes from provided!');  end

% --------------------------------------------------------------
%                                                    check files

general_check_file(flist, 'file list', 'errorstop');
if isempty(outf)
    outf = strrep(flist, '.list', '');
end

% --------------------------------------------------------------
%                                               check saveoption

reportmsg = strrep(saveoption, '_', ' ');
if ~ismember(saveoption, {'by_effect', 'by_session', 'effect_files'})
    error('ERROR: Invalid saveoption value [%s]! Valid options are: by_effect, by_session, effect_files.', saveoption);
end


% --------------------------------------------------------------
%                                                  read filelist

sessions = general_read_file_list(flist);
nsub = length(sessions);

% --------------------------------------------------------------
%                             check that glm entries are present

if verbose, fprintf('\n---> checking file list'); end
allok = true;
for s = 1:nsub
    if ~isfield(sessions(s), 'glm')
        fprintf('\n     WARNING: Session id: %s has no glm file specified!', sessions(s).id);
        allok = false;
    end
end
if ~allok
    fprintf('\n\nERROR: Some sessions do not have a glm file specified in the file list.\n       Please, check your list file!\n');
    exit(1);
end

% --------------------------------------------------------------
%                                      parse estimates parameter

if ischar(effects)
    if ~isempty(effects)
        effects = strtrim(regexp(effects, ',', 'split'));
    end
end


% --------------------------------------------------------------
%                                          loop through sessions

% --- setup data holder

if verbose, fprintf('\n---> processing session: %s', sessions(1).id); end

glm = nimage(sessions(1).glm);
sef = glm.glm.effects;
glm = glm.img_extract_glm_estimates(effects, frames, values);
effect = sef(glm.glm.effect);
frame  = glm.glm.frame;
event  = glm.glm.event;

[nvox nb]     = size(glm.image2D);
data          = zeros(nvox, nb * (nsub + 5));
data(:, 1:nb) = glm.image2D;
session       = repmat({sessions(1).id}, 1, nb);

pt = nb;

for s = 2:nsub

    % ---> read GLMs

    if verbose, fprintf('\n---> processing session: %s', sessions(s).id); end

    glm = nimage(sessions(s).glm);
    sef = glm.glm.effects;
    glm = glm.img_extract_glm_estimates(effects, frames, values);
    nb  = size(glm.image2D,2);
    effect  = [effect sef(glm.glm.effect)];
    frame   = [frame glm.glm.frame];
    event   = [event glm.glm.event];
    session = [session repmat({sessions(s).id}, 1, nb)];

    data(:, pt+1:pt+nb) = glm.image2D;
    pt = pt + nb;
end

data = data(:, 1:pt);

if isempty(effects)
    effects = unique(effect);
end

% --- do we need to reorder?

if strcmp(saveoption, 'by_effect')
    if verbose, fprintf('\n---> sorting data by effects'); end
    index = [];
    for e = effects(:)'
        index = [index find(ismember(effect, e))];
    end
    data    = data(:,index);
    effect  = effect(index);
    frame   = frame(index);
    event   = event(index);
    session = session(index);
end


% --- will we use parcel names?

if strcmp(glm.filetype, '.ptseries') & ~isempty(txtf)
    parcelnames = getParcelNames(glm);
end

% --- save

if ismember(saveoption, {'by_effect', 'by_session'})
    if verbose, fprintf('\n---> saving data in a single file, sorted %s', reportmsg); end

    out = glm.zeroframes(pt);
    out.data = data;
    out = setMeta(out, session, effect, frame, event, verbose);
    out.img_saveimage(outf);
    if strcmp(out.filetype, '.ptseries') & ~isempty(txtf)
        if verbose, fprintf('\n---> saving data in a text file, sorted %s', reportmsg); end
        tout = fopen([outf '_long.txt'], 'w');
        fprintf(tout, 'session\troi code\troi name\teffect\tframe\tvalue');
        [nroi, ndata] = size(out.data);
        for roi_index = 1:nroi
            for data_index = 1:ndata
                fprintf(tout, '\n%s\t%d\t%s\t%s\t%d\t%f', session{data_index}, roi_index, parcelnames{roi_index}, effect{data_index}, frame(data_index), out.data(roi_index, data_index));
            end
        end
        fclose(tout);
    end
else
    if verbose, fprintf('\n---> saving data in separate files for each effect'); end
    for e = effects(:)'
        if verbose, fprintf('\n     ... %s', e{1}); end
        mask = ismember(effect, e);
        out = glm.zeroframes(sum(mask));
        out.data = data(:, mask);
        out = setMeta(out, session(mask), effect(mask), frame(mask), event(mask), verbose);
        out.img_saveimage([outf '_' e{1}]);
        if strcmp(out.filetype, '.ptseries') & ~isempty(txtf)
            if verbose, fprintf('\n---> saving data in separate text files for each effect'); end
            tout = fopen([outf '_' e{1} '_long.txt'], 'w');
            fprintf(tout, 'session\troi code\troi name\teffect\tframe\tvalue');
            [nroi, ndata] = size(out.data);
            t_session = session(mask);
            t_effect  = effect(mask);
            t_frame   = frame(mask);
            for roi_index = 1:nroi
                for data_index = 1:ndata
                    fprintf(tout, '\n%s\t%d\t%s\t%s\t%d\t%f', t_session{data_index}, roi_index, parcelnames{roi_index}, t_effect{data_index}, t_frame(data_index), out.data(roi_index, data_index));
                end
            end
            fclose(tout);
        end
    end
end


if verbose, fprintf('\n===> DONE\n'); end


% --- Support function

function [img] = setMeta(img, session, effect, frame, event, verbose)
    s = '';
    s = [s sprintf('# session: %s\n', strjoin(session))];
    s = [s sprintf('# effect: %s\n', strjoin(effect))];
    s = [s sprintf('# frame:%s\n', sprintf(' %d', frame))];
    s = [s sprintf('# event: %s\n', strjoin(effect))];
    img = img.img_embed_meta(s, [], 'list', verbose);


function [parcelnames] = getParcelNames(img)

    % --> extract metadata from the input image

    xml  = cast(img.meta(find([img.meta.code] == 32)).data, 'char')';

    % --> load cifti brain model

    model = load('cifti_brainmodel');

    % --> process parcells

    parcels = regexp(xml, '<Parcel Name="(?<name>.*?)">.*?(?<parcelparts><.*?)\s*</Parcel>', 'names');
    parcelnames = {parcels.name};
function [] = g_ExtractGLMVolumes(flist, outf, effects, frames, saveoption, values, verbose);

%function [] = g_ExtractGLMVolumes(flist, outf, effects, frames, saveoption, values, verbose);
%
%	For subjects specified in the subject list it extracts the GLM estimates of
%   the effects of interests and saves them in the specified file.
%
%   INPUT
%       flist       - List of files / subjects to process.
%       outf        - Root file name for the results. If empty, the flist name
%                     is used. []
%       efects      - A cell array of strings or a comma separated list of
%                     effects of interest. If empty all effects but Baseline and
%                     Trend are extracted. []
%       frames      - Frame indeces to extract. If empty, all frames are
%                     extracted. []
%       saveoption  - Whether to save the extracted estimates in a single file
%                     organized 'by subject', 'by effect', or in separate
%                     files for each effect ('effect files'). ['by subject']
%       values      - What kind of values to save: 'raw' or 'psc'. ['raw']
%	    verbose		- Whether to report on the progress or not [false]
%
%   USE
%   The function is used to extract GLM estimates for the effects of interest
%   for all the specified subjects and save them in a single file (or one
%   file per effect of interest). This files can then be used for more focused
%   analyses, such as second-level statistical testing using PALM.
%
%   To extract the effects of interest, the function calls the
%   mri_ExtractGLMEstimates gmrimage method.
%
%   NOTICE
%   The underlying method extracts the effects of interest by removing those
%   frames that relate to irrelevant effects. The order of the effects in the
%   resulting files will be the same as in the original GLM files when saved
%   organized 'by subject' and not as specified in the call to the function.
%   When the results are organized 'by effect', the order of estimates will
%   be the same as in the effects variable. To be sure in what order the data
%   is present in the resulting file, please consult the 'list' structure
%   present in the extracted file, that for each frame specifies the subject,
%   effect and frame the estimate belongs to.
%
%   Additionally, the code does not check for missing estimates. If an estimate
%   is not present in the file, no warning or error will be generated. So do
%   check the list structure that all the data is there.
%
%   EXAMPLE USE
%   g_ExtractGLMVolumes('wm-glm.list', 'wm-encoding-delay', 'encoding,delay', [], 'by subject');
%
%   ---
% 	Written by Grega Repovš on 2016-08-26.
%
%   Changelog
%   2017-03-04 Grgega Repovs - updated documentation
%   2017-07-01 Grega Repovs - Added psc option.
%
%

if nargin < 7, verbose   = false; end
if nargin < 6 || isempty(values),     values     = 'raw'; end
if nargin < 5 || isempty(saveoption), saveoption = 'by subject'; end
if nargin < 4, frames    = [];    end
if nargin < 3, effects   = [];    end
if nargin < 2, outf      = [];    end

if nargin < 1, error('ERROR: No files to extract the volumes from provided!');  end

% --------------------------------------------------------------
%                                                    check files

g_CheckFile(flist, 'file list', 'errorstop');
if isempty(outf)
    outf = strrep(flist, '.list', '');
end

% --------------------------------------------------------------
%                                                  read filelist

subjects = g_ReadFileList(flist);
nsub = length(subjects);

% --------------------------------------------------------------
%                                      parse estimates parameter

if ischar(effects)
    effects = strtrim(regexp(effects, ',', 'split'));
end


% --------------------------------------------------------------
%                                          loop through subjects

% --- setup data holder

if verbose, fprintf('\n---> processing subject: %s', subjects(1).id); end

glm = gmrimage(subjects(1).glm);
sef = glm.glm.effects;
glm = glm.mri_ExtractGLMEstimates(effects, frames, values);
effect = sef(glm.glm.effect);
frame  = glm.glm.frame;
event  = glm.glm.event;

[nvox nb]     = size(glm.image2D);
data          = zeros(nvox, nb * (nsub + 5));
data(:, 1:nb) = glm.image2D;
subject       = repmat({subjects(1).id}, 1, nb);

pt = nb;

for s = 2:nsub

    % ---> read GLMs

    if verbose, fprintf('\n---> processing subject: %s', subjects(s).id); end

    glm = gmrimage(subjects(s).glm);
    sef = glm.glm.effects;
    glm = glm.mri_ExtractGLMEstimates(effects, frames, values);
    nb  = size(glm.image2D,2);
    effect  = [effect sef(glm.glm.effect)];
    frame   = [frame glm.glm.frame];
    event   = [event glm.glm.event];
    subject = [subject repmat({subjects(s).id}, 1, nb)];

    data(:, pt+1:pt+nb) = glm.image2D;
    pt = pt + nb;
end

data = data(:, 1:pt);

if isempty(effects)
    effects = unique(effect);
end

% --- do we need to reorder?

if strcmp(saveoption, 'by estimate')
    if verbose, fprintf('\n---> sorting data by estimate'); end
    index = [];
    for e = effects(:)'
        index = [index find(ismember(effect, e))];
    end
    data    = data(:,index);
    effect  = effect(index);
    frame   = frame(index);
    event   = event(index);
    subject = subject(index);
end


% --- save

if ismember(saveoption, {'by effect', 'by subject'})
    if verbose, fprintf('\n---> saving data in a single file, sorted %s', saveoption); end

    out = glm.zeroframes(pt);
    out.data = data;
    out = setMeta(out, subject, effect, frame, event, verbose);
    out.mri_saveimage(outf);
else
    if verbose, fprintf('\n---> saving data in separate files for each effect'); end
    for e = effects(:)'
        if verbose, fprintf('\n     ... %s', e{1}); end
        mask = ismember(effect, e);
        out = glm.zeroframes(sum(mask));
        out.data = data(:, mask);
        out = setMeta(out, subject(mask), effect(mask), frame(mask), event(mask), verbose);
        out.mri_saveimage([outf '_' e{1}]);
    end
end


if verbose, fprintf('\n===> DONE\n'); end


% --- Support function

function [img] = setMeta(img, subject, effect, frame, event, verbose)
    s = '';
    s = [s sprintf('# subject: %s\n', strjoin(subject))];
    s = [s sprintf('# effect: %s\n', strjoin(effect))];
    s = [s sprintf('# frame:%s\n', sprintf(' %d', frame))];
    s = [s sprintf('# event: %s\n', strjoin(effect))];
    img = img.mri_EmbedMeta(s, [], 'list', verbose);
function [] = g_ExtractGLMVolumes(flist, outf, estimates, frames, saveoption, verbose);

%function [] = g_ExtractGLMVolumes(flist, outf, estimates, frames, saveoption, verbose);
%
%	Extracts volumes from GLM files provided in a file list.
%
%   flist       - list of files
%   outf        - root file name [flist name]
%   estimates   - a cell array or a comma separated list of estimates of interest [all but Baseline and Trend]
%   frames      - frame indeces to extract [all]
%   saveoption  - whether to save in a single file organized 'by subject', 'by estimate', or in separate files for each estimate ('estimate files') ['by subject']
%	verbose		- to report on progress or not [false]
%
% 	Created by Grega Repovš on 2016-08-26.
%
% 	Copyright (c) 2016 Grega Repovs. All rights reserved.
%
%

if nargin < 6, verbose   = false; end
if nargin < 5 || isempty(saveoption), saveoption = 'by subject'; end
if nargin < 4, frames    = [];    end
if nargin < 3, estimates = [];    end
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

if ischar(estimates)
    estimates = strtrim(regexp(estimates, ',', 'split'));
end


% --------------------------------------------------------------
%                                          loop through subjects

% --- setup data holder

if verbose, fprintf('\n---> processing subject: %s', subjects(1).id); end

glm = gmrimage(subjects(1).glm);
sef = glm.glm.effects;
glm = glm.mri_ExtractGLMEstimates(estimates, frames);
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
    glm = glm.mri_ExtractGLMEstimates(estimates, frames);
    nb  = size(glm.image2D,2);
    effect  = [effect sef(glm.glm.effect)];
    frame   = [frame glm.glm.frame];
    event   = [event glm.glm.event];
    subject = [subject repmat({subjects(s).id}, 1, nb)];

    data(:, pt+1:pt+nb) = glm.image2D;
    pt = pt + nb;
end

data = data(:, 1:pt);

if isempty(estimates)
    estimates = unique(effect);
end

% --- do we need to reorder?

if strcmp(saveoption, 'by estimate')
    if verbose, fprintf('\n---> sorting data by estimate'); end
    index = [];
    for e = estimates(:)'
        index = [index find(ismember(effect, e))];
    end
    data    = data(:,index);
    effect  = effect(index);
    frame   = frame(index);
    event   = event(index);
    subject = subject(index);
end


% --- save

if ismember(saveoption, {'by estimate', 'by subject'})
    if verbose, fprintf('\n---> saving data in a single file, sorted %s', saveoption); end

    out = glm.zeroframes(pt);
    out.data = data;
    out = setMeta(out, subject, effect, frame, event, verbose);
    out.mri_saveimage(outf);
else
    if verbose, fprintf('\n---> saving data in separate files for each estimate'); end
    for e = estimates(:)'
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
function [obj] = img_extract_glm_estimates(obj, effects, frames, values)

%``img_extract_glm_estimates(obj, effects, frames, values)``
%
%   Extracts specified effects of interest from a GLM file.
%
%   Parameters:
%       --obj (nimage):
%           A nimage object with GLM results.
%       --effects (string, cellarray, []):
%           A cell array or a comma separated list of effects of interest
%           to be extracted. If empty all but Baseline and Trend will be
%           returned. 
%       --frames (array of indeces, []):    
%           Which frames (of the indicated effects of interest) to extract.
%           If empty all will be returned.
%       --values (string, 'raw'):
%           What kind of values to save: 'raw' or 'psc'. ['raw']
%
%   Returns:
%       obj
%           A nimage image object with GLM results trimmed to only the specified
%           effects of interest and frames.
%
%   Notes:
%       Used to extract the effects and frames of interest from GLM results for
%       further analysis. 'values' specify whether raw beta values ('raw') or
%       percent signal change ('psc') should be exported.
%
%       Please take note, that the order of estimates within the image will remain
%       unchanged. In other words, the estimates in the generated file will not be
%       in the order they were specified in the effects variable!
%
%   Example:
%
%    ::
%   
%        glme = glm.img_extract_glm_estimates('encoding, delay, response', 1);
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 4 || isempty(values); values = 'raw';  end
if nargin < 3; frames  = [];  end
if nargin < 2; effects = [];  end

% ---- check if we have a GLM image

if isempty(obj.glm)
    error('\nERROR: This is not a GLM image!\n');
end

if strcmp(values, 'psc')
    obj.data = bsxfun(@rdivide, obj.data, obj.glm.gmean / 100);
end

% ---- process input

if isempty(effects)
    effects = obj.glm.effects(~ismember(obj.glm.effects, {'Trend', 'Baseline'}));
elseif isa(effects, 'char')
    effects = strtrim(regexp(effects, ',', 'split'));
end

% ---- trim to selected effects and timepoints / frames

eoi = find(ismember(obj.glm.effects, effects));
msk = ismember(obj.glm.effect, eoi);
if ~isempty(frames)
    msk = msk & ismember(obj.glm.frame, frames);
end

obj = obj.sliceframes(msk);

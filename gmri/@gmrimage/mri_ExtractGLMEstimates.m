function [obj] = mri_ExtractGLMEstimates(obj, effects, frames, values)

%function [obj] = mri_ExtractGLMEstimates(obj, effects, frames, values)
%
%	Extracts specified effects of interest from a GLM file.
%
%   INPUT
%	      obj ... A gmrimage object with GLM results.
%     effects ... A cell array or a comma separated list of effects of interest
%                 To be extracted. If empty all but Baseline and Trend will be
%                 returned. []
%      frames ... Which frames (of the indicated effects of interest) to extract.
%                 If empty all will be returned. []
%      values ... What kind of values to save: 'raw' or 'psc'. ['raw']
%
%   OUTPUT
%         obj ... A gmrimage image object with GLM results trimmed to only the
%                 specified effects of interest and frames.
%
%   USE
%   Used to extract the effects and frames of interest from GLM results for
%   further analysis. 'values' specify whether raw beta values ('raw') or
%   percent signal change ('psc') should be exported.
%
%   NOTICE
%   Please take note, that the order of estimates within the image will remain
%   unchanged. In other words, the estimates in the generated file will not be
%   in the order they were specified in the effects variable!
%
%   EXAMPLE USE
%   glme = glm.mri_ExtractGLMEstimates('encoding, delay, response', 1);
%
%   ---
%   Written by Grega Repovš, 2015-12-09
%
%   Changelog
%   2017-03-03 Grega Repovs - Updated documentation.
%   2017-07-01 Grega Repovs - Added psc option.
%

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

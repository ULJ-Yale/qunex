function obj = mri_ExtractGLMEstimates(obj, estimates, frames)

%function obj = mri_ExtractGLMEstimates(obj, estimates, frames)
%
%	Extracts estimates of interest from a GLM file.
%
%	obj       - a GLM image
%   estimates - a cell array or a comma separated list of estimates of interest [all but Baseline and Trend]
%   frames    - frame indeces to extract [all]
%
%   Grega Repovš, 2015-12-09
%

if nargin < 3; frames    = [];  end
if nargin < 2; estimates = [];  end

% ---- check if we have a GLM file

if isempty(obj.glm)
    error('\nERROR: This is not a GLM file!\n');
end

% ---- process input

if isempty(estimates)
    estimates = obj.glm.effects(~ismember(obj.glm.effects, {'Trend', 'Baseline'}));
elseif isa(estimates, 'char')
    estimates = strtrim(regexp(estimates, ',', 'split'));
end

% ---- trim to selected estimates and timepoints

eoi = find(ismember(obj.glm.effects, estimates));
msk = ismember(obj.glm.effect, eoi);
if ~isempty(frames)
    msk = msk & ismember(obj.glm.eindex, frames);
end

obj = obj.sliceframes(msk);


function [predicted, residual] = img_glm_predict(glm, effects, raw)

%``img_glm_predict(glm, effects, raw)``.
%
%    Computes predicted and residual values based on the provided GLM object,
%   list of effects to predict and raw data.
%
%   INPUTS
%    ======
%
%    --glm       nimage glm object
%   --raw       nimage object with raw bold data
%   --effects   a comma separated string or a cell array with a list of effects
%               to model
%
%   OUTPUTS
%    =======
%
%   predicted
%        a nimage object with values predicted based on the beta values maps and
%       regressor matrix
%   residual
%        a nimage object with residuals remaining after the predicted values are
%       subtracted out
%
%   USE
%    ===
%
%   The method uses the data stored in the GLM nimage object to compute the 
%   predicted timecourse based on the beta image and regressor matrix. If raw
%   data is provided and residuals requested, it also returns the residuals
%   after the predicted signal has been regressed out.
%
%   EXAMPLE USE
%    ===========
%
%   ::
%
%        [predicted, residual] = glm_data.img_glm_predict(bold_data, 'Baseline,Trend,Incongruent,Congruent');
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

% ---- check input

if nargin < 3, raw = []; end
if nargin < 2, error('ERROR: Please provide a list of effects to model!'); end

if nargout == 2 
    if isempty(raw)
        error('ERROR: Residuals were requested but no bold data was provided!'); 
    end
    if sum(raw.use) ~= size(glm.glm.A, 1)
        error('ERROR: Regressor matrix and number of timepoints in BOLD do not match!'); 
    end
    if size(raw.data, 1) ~= size(glm.data, 1)
        error('ERROR: Beta maps and raw data do not match in voxel/grayordinate size!'); 
    end
end

% ---- identify and check regressors to predict

if ischar(effects)
    effects = strtrim(regexp(effects, ',', 'split'));
end

if ~all(ismember(effects, glm.glm.effects))
    missing = effects(~ismember(effects, glm.glm.effects));
    error('ERROR: The following effects are not present in the regressor matrix: %s!', strjoin(missing, ', ')); 
end

use_indeces = find(ismember(glm.glm.effects, effects));
use_columns = ismember(glm.glm.effect, use_indeces);

% ---- predict timeseries

if isempty(raw)
    predicted = glm.zeroframes(size(glm.glm.A, 1));
else
    predicted = raw;
end

X = glm.glm.A(:,use_columns);
Y = X*glm.data(:,use_columns)';
predicted.data(:, predicted.use == 1) = Y';
predicted.data(:, predicted.use ~= 1) = NaN;

% ---- compute residual

if nargout == 2
    residual = raw;
    residual.data = raw.data - predicted.data;
end

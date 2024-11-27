function [predicted, residual] = img_glm_predict(glm, effects, raw, options)

%``img_glm_predict(glm, effects, raw)``.
%
%   Computes predicted and residual values based on the provided GLM object,
%   list of effects to predict and raw data.
%   
%   INPUTS
%   ======
%
%   --glm       nimage glm object
%   --raw       nimage object with raw bold data
%   --effects   a comma separated string or a cell array with a list of effects
%               to model
%   --options   A string specifying additional analysis options formated as pipe
%               separated pairs of colon separated key, value pairs::
%
%                   "<key>:<value>|<key>:<value>".
%
%               It takes the following keys and values:
%
%              ignores
%                  How to deal with frames that were marked as bad and ignored when
%                  GLM solution was completed. The information should be specified
%                  separately for predicting timecourse and regressing signal:
%   
%                  'ignores>predict:[mark/linear/spline],regress:[keep/mark/linear/spline]'
%                  
%                  The options have the following meaning:
%          
%                  keep
%                      keep the value in the original BOLD (only applicable to 
%                      regressed signal)
%                  mark
%                      mark the bad frames by setting the value to "NaN" 
%                  linear
%                      interpolate values for bad frames using linear interpolation
%                  spline
%                      interpolate values for bad frames using spline interpolation
%   
%                  The default is 'ignores>predict:mark,regress:mark'
%
%   OUTPUTS
%   =======
%
%   predicted
%       a nimage object with values predicted based on the beta values maps and
%       regressor matrix
%   residual
%       a nimage object with residuals remaining after the predicted values are
%       subtracted out
%
%   USE
%   ===
%
%   The method uses the data stored in the GLM nimage object to compute the 
%   predicted timecourse based on the beta image and regressor matrix. If raw
%   data is provided and residuals requested, it also returns the residuals
%   after the predicted signal has been regressed out.
%
%   EXAMPLE USE
%   ===========
%
%   ::
%
%        [predicted, residual] = glm_data.img_glm_predict(bold_data, 'Baseline,Trend,Incongruent,Congruent');
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

% ---- check input

if nargin < 4, options = ''; end
if nargin < 3, raw = []; end
if nargin < 2, error('ERROR: Please provide a list of effects to model!'); end

if nargout == 2 
    if isempty(raw)
        error('ERROR: Residuals were requested but no bold data was provided!'); 
    end
    if size(raw.data, 1) ~= size(glm.data, 1)
        error('ERROR: Beta maps and raw data do not match in voxel/grayordinate size!'); 
    end
end

% ---- parse options

default = 'ignores>predict:mark,regress:mark';
options = general_parse_options([], options, default);

% ---- identify and check regressors to predict

if ischar(effects)
    effects = strtrim(regexp(effects, ',', 'split'));
end

if ~all(ismember(effects, glm.glm.effects))
    missing = effects(~ismember(effects, glm.glm.effects));
    error('ERROR: The following effects are not present in the regressor matrix: %s!', strjoin(missing, ', ')); 
end

if ~ismember({options.ignores.predict}, {'mark', 'linear', 'spline'})
    error('ERROR: Incorrect option for "ignores>predict": %s! Please use one of: mark, linear, spline.', options.ignores.predict); 
end

if ~ismember({options.ignores.regress}, {'keep', 'mark', 'linear', 'spline'})
    error('ERROR: Incorrect option for "ignores>regress": %s! Please use one of: keep, mark, linear, spline.', options.ignores.predict); 
end


use_indeces = find(ismember(glm.glm.effects, effects));
use_columns = ismember(glm.glm.effect, use_indeces);

% ---- predict timeseries

if isempty(raw)
    if isfield(glm.glm.use)
        nframes = length(glm.glm.use);
    else
        nframes = size(glm.glm.A, 1);
    end
    predicted = glm.zeroframes(nframes);
    if isfield(glm.glm.use)
        predicted.use = glm.glm.use;
    end
else
    predicted = raw;
    
    % --- check we have matching length of source and glm data
    
    raw_n_frames = predicted.frames;
    raw_use      = predicted.use;
    
    if isfield(glm.glm, 'use')
        glm_n_frames = length(glm.glm.use);
        if raw_n_frames ~= glm_n_frames
            error('ERROR: The length of the GLM (%d frames) and source (%d frames) data do not match!', glm_n_frames, raw_n_frames);
        end
        if sum(abs(predicted.use - glm.glm.use)) > 0
            fprintf('WARNING: When processing files, use information do not match! Using information provided in GLM. (glm file: %s, source file: %s)', fullfile(predicted.filepath, predicted.filename), fullfile(glm.filepath, glm.filename));
        end
        predicted.use = glm.glm.use;
    else
        if sum(predicted.use) ~= size(glm.glm.A, 1);
            if predicted.frames == size(glm.glm.A, 1);
                predicted.use = ones(1, predicted.frames);
            else
                error('ERROR: The length of the GLM frames (%d) and source good frames (%d) do not match!', size(glm.glm.A, 1), sum(predicted.use));
            end
        end
    end    
end


X = glm.glm.A(:,use_columns);
Y = X*glm.data(:,use_columns)';
predicted.data(:, predicted.use == 1) = Y';

if sum(predicted.use == 0) > 0
    if strcmp(options.ignores.predict, 'mark')
        predicted.data(:, predicted.use ~= 1) = NaN;
    else
        predicted.data = interpolate_data(predicted.data, predicted.use, options.ignores.predict);
    end
end

% ---- compute residual

if nargout == 2
    residual = raw;
    residual.data = raw.data - predicted.data;
    if sum(predicted.use == 0) > 0
        if strcmp(options.ignores.regress, 'keep')
            residual.data(:, predicted.use ~= 1) = raw.data(:, predicted.use ~= 1);
        elseif strcmp(options.ignores.regress, 'mark')
            residual.data(:, predicted.use ~= 1) = NaN;
        else
            residual.data = interpolate_data(residual.data, predicted.use, options.ignores.predict);
        end
    end
end


% ---- interpolation support function

function [ts] = interpolate_data(ts, mask, interp)

    x  = [1:length(mask)]';
    xi = x;
    x  = x(mask==1);
    ts = interp1(x, ts(:, mask==1)', xi, interp, 'extrap')';




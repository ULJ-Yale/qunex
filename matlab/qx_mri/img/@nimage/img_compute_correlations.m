function [correlations, zscores, pvalues] = img_compute_correlations(obj, bdata, verbose, cv)

%``function [correlations, zscores, pvalues] = img_compute_correlations(obj, bdata, verbose, cv)``
%
%   For each voxel, computes correlation with the provided (behavioral or other)
%   data.
%
%   INPUTS
%   ======
%
%	--obj       nimage object
%   --bdata     data matrix to compute correlations with
%   --verbose   should it talk a lot [no]
%   --cv        should it compute covariances instead of correlations
%
%   OUTPUTS
%   =======
%
%   correlations
%       A nimage object with computed correlations.
%
%   zscores
%       A nimage of z-scores reflecting significance of correlations.
%
%   pvalues
%       A nimage of uncorrected p-values.
%
%   USE
%   ===
%
%   The method computes correlations of each voxel with each column of the bdata
%   matrix. the bdata matrix can have any number of columns, but has to have the
%   same number of rows as there are frames in the original image. The first
%   frame of the resulting images will hold for each voxel the correlation /
%   p-value of its original dataseries across frames, with the first column of
%   the bdata. In a possible use scenario, each frame of the original image can
%   hold an activation or functional connectivity seed-map for one session while
%   each row of the bdata can hold that person's behavioral data, age,
%   diagnostic values etc. Each frame of the resulting image will hold a map of
%   correlations between activation maps and behavioral variables across
%   sessions.
%
%   If cv is set to true (or non-zero) the computed and reported values will be
%   covariances instead of correlations.
%
%   EXAMPLE USE
%   ===========
%
%   ::
%
%       [rimg, pimg] = img.img_compute_correlations(behdata);
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 4 || isempty(cv),      cv      = false; end
if nargin < 3 || isempty(verbose), verbose = false; end
if nargin < 2 error('ERROR: No data provided to compute correlations!'); end

if obj.frames ~= size(bdata,1)
    error('ERROR: data matrix file does not match number of image frames!')
end

ncorrelations = size(bdata, 2);
if verbose, fprintf('\n\nComputing %d correlations with %s', ncorrelations, obj.filename), end

% ---- prepare data

if verbose, fprintf('\n... setting up data'), end

if cv
    if verbose, fprintf('\n... setting up for covariances instead of correlations '), end
    obj.data = obj.data';
    obj.data = bsxfun(@minus, obj.data, mean(obj.data)) ./ sqrt(obj.voxels-1);
    obj.data = obj.data';
elseif ~obj.correlized && ~cv
    obj = obj.correlize;
end

if cv
    bdata = bdata';
    bdata = bsxfun(@minus, bdata, mean(bdata)) ./ sqrt(obj.voxels-1);
    bdata = bdata';
else
    bdata = zscore(bdata, 0, 1);
    bdata = bdata ./ sqrt(obj.frames -1);
end

correlations = zeroframes(obj, ncorrelations);

% ---- do the loop

voxels = obj.voxels;
data = obj.data;

if verbose, fprintf('\n... computing correlations'), end

for n = 1:ncorrelations
    x = data(n,:)';
    correlations.data(:,n) = data * bdata(:,n);
end

if nargout > 1
    if verbose, fprintf('\n... computing Z-scores'), end
    zscores = zeroframes(obj, ncorrelations);
    if cv
        zscores.data(:) = 1;
    else
        zscores.data = fc_fisher(correlations.data);
        zscores.data = zscores.data/(1/sqrt(obj.frames-3));
    end
end

if nargout > 2
    if verbose, fprintf('\n... computing p-values'), end
    pvalues = obj.zeroframes(1);
    pvalues.data = (1 - normcdf(abs(zscores.data), 0, 1)) * 2 .* sign(correlations.data);
end

if verbose, fprintf('\n... done!'), end

end


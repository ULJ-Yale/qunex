function [correlations, zscores, pvalues] = img_compute_correlations(obj, bdata, fcmeasure, optimized, verbose, options)

%``img_compute_correlations(obj, bdata, fcmeasure, verbose)``
%
%   For each voxel, computes correlation with the provided (behavioral or other)
%   data.
%
%   INPUTS
%   ======
%
%   --obj           nimage object
%   --bdata         data matrix to compute correlations with
%   --fcmeasure     functional connectivity measure to compute
%   --optimized     has the data been optimized for the computation
%   --verbose       should it talk a lot [no]
%   --options       additional options
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

if nargin < 6 || isempty(options),   options = struct([]); end
if nargin < 5 || isempty(verbose),   verbose   = false; end
if nargin < 4 || isempty(optimized), optimized = false; end
if nargin < 3 || isempty(fcmeasure), fcmeasure = false; end
if nargin < 2 error('ERROR: No data provided to compute correlations!'); end

if obj.frames ~= size(bdata,1)
    error('ERROR: data matrix file does not match number of image frames!')
end

ncorrelations = size(bdata, 2);
if optimized
    datatype = 'optimized';
else
    datatype = 'nonoptimized';
end
if verbose, fprintf('\n\nComputing %d correlations [%s] on %s data.', ncorrelations, fcmeasure, datatype), end

% ---- compute correlations

correlations = obj.zeroframes(ncorrelations);
correlations.data = fc_compute(obj.data, bdata', fcmeasure, optimized, options);

% ---- compute Z-scores if requested

if nargout > 1
    if verbose, fprintf('\n... computing Z-scores'), end
    zscores = obj.zeroframes(ncorrelations);
    if strcmp(fcmeasure, 'r')
        zscores.data = fc_fisher(correlations.data);
        zscores.data = zscores.data/(1/sqrt(obj.frames-3));
    else
        zscores.data(:) = 0;
    end
end

% ---- compute p-values if requested

if nargout > 2
    if verbose, fprintf('\n... computing p-values'), end
    pvalues = obj.zeroframes(ncorrelations);
    pvalues.data = (1 - normcdf(abs(zscores.data), 0, 1)) * 2 .* sign(correlations.data);
end

if verbose, fprintf('\n... done!'), end

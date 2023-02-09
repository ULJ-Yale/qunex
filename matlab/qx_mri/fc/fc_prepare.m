function [mat] = fc_prepare(mat, measure)

%``fc_prepare(mat, measure)``
%
%   Prepares data for efficient computation of functional connectivity measures.
%
%   Parameters:
%       --mat (numeric matrix):
%           A matrix of data on which functional connectivity will be computed.
%           The matrix should have variables in rows and datapoints in columns,
%           i.e., should be prepared to compute functional connectivity measures
%           on matrix rows.
%
%       --measure (str):
%           The name of the measure for which the data should be prepared for.
%           The possible options are:
%
%           - r
%               Pearson's r value
%           - rho
%               Spearman's rho value
%           - cv
%               covariance estimate.
%           - cc
%               cross correlation
%
%           Defaults to 'r'.
%
%   Returns:
%       --mat (numeric matrix)
%           A matrix of data prepared for optimized computation of functional
%           connectivity measures.
%
%   Notes:
%       The data is prepared so that minimal additional computation is needed
%       to calculate functional connectivity. The specific preparation steps
%       are:
%
%       - r
%           The data is converted to z-scores and divided by the square root
%           of number of datapoints - 1. For computing Pearson's r the rows
%           of interest only need to be cross multiplied.
%       - rho
%           The data is first converted to ranks and then prepared the same
%           as for Pearson's correlation. This prepares data for efficient
%           computation of Spearman's rho with simple cross multiplication.
%       - c
%           The data is demeaned and divided with the numnber of datapoints
%           - 1. For computing covariance the rows of interest only need to
%           be cross multiplied.

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 2 || isempty(measure), measure = 'r';  end
if nargin < 1 error('ERROR: A matrix with data needs to be provided!'); end

% --- transpose from rows to columns and compute number of points

mat = mat';
N = size(mat, 1);

% -- covert to rank

if ismember(measure, {'rho'})
    mat = tiedrank(mat);
end

% -- demean

if ismember(measure, {'cv', 'rho', 'r', 'cc'})
    mat = bsxfun(@minus, mat, mean(mat));
end

% -- standardize

if ismember(measure, {'rho', 'r', 'cc'})
    mat = bsxfun(@rdivide, mat, std(mat));
end

% -- divide by length

if ismember(measure, {'rho', 'r', 'cv', 'cc'})
    mat = mat ./ sqrt(N-1);
end

% -- transpose back

mat = mat';
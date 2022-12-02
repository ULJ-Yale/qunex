function [fcmat, fzmat] = fc_compute(A, B, measure, optimized)

%``fc_compute(A, B, measure, optimized)``
%
%   Computes functional connectivity matrix
%
%   Parameters:
%       --A (numeric matrix):
%           A matrix of data on which functional connectivity is to be computed.
%           The matrix should have variables in rows and datapoints in columns,
%           i.e., should be prepared to compute functional connectivity measures
%           on matrix rows. 
%
%       --B (numeric matrix):
%           A second, optional matrix of data for computing functional
%           connectivity with the same organization of data. 
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
%
%           Defaults to 'r'.
%
%       --optimized (boolean):
%           Whether the data have been optimized for computing the requested
%           measure. Defaults to false.
%
%   Returns:
%       --fcmat (numeric matrix)
%           A functional connectivity matrix.
%
%       --fzmat
%           If requested, fisher-z converted functional connectivity matrix.
%
%   Notes:
%       If only one matrix is provided, the function returns a matrix of 
%       functional connectivity estimates between each pair of rows of the 
%       input matrix. 
%       If two matrices are provided, the function returns a matrix of
%       functional connectivity of all pairs of rows of matrix A with 
%       all rows of matrix B.

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later
    
if nargin < 4 || isempty(optimized), optimized = false;  end
if nargin < 3 || isempty(measure),   measure   = 'r';  end
if nargin < 2,                       B         = [];  end
if nargin < 1 error('ERROR: A matrix with data needs to be provided!'); end

% --- check data and parameters

if ~isempty(B)
    if size(A, 2) ~= size(B, 2)
        error('ERROR: The lengths of matrix A (%d) and matrix B (%d) do not match! Check your data!', size(A, 2), size(B, 2)); 
    end
end

if ~ismember(measure, {'cv', 'rho', 'r'})
    error('ERROR: Invalid functional connectivity measure specified [%s]!', measure); 
end

% --- prepare data if needed

if ~optimized
    A = fc_prepare(A, measure);
    if ~isempty(B)
        B = fc_prepare(B, measure);
    end
end

% --- compute FC matrix

if ismember(measure, {'cv', 'rho', 'r'})
    if isempty(B)
        fcmat = A * A';
    else
        fcmat = A * B';
    end
end

% --- do we need to return Fz?

if nargin > 1
    fzmat = fc_fisher(fcmat);
end


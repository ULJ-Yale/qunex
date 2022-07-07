function [p Z M D SE t] = img_ttest_independent(A, B, vartype, verbose)

%``img_ttest_zero(A, B, vartype, verbose)``
%
%    Computes independent t-test comparing the called image object (A) to B.
%
%   INPUTS
%   ======
%
%    --A          the image object the method is called on
%    --B          the image object to compare to
%   --vartype    are the variances assumed to be equal ('equal') or not 
%                ('unequal') ['equal']
%   --verbose    should it talk a lot [false]
%
%   OUTPUTS
%   =======
%
%   p   
%       an image with p-values
%
%   t   
%       an image with t-values
%
%   Z   
%       an image with Z-scores converted from p-values
%
%   M   
%       on image with means of both groups
%
%   D   
%       an image with A - B difference in group means
%
%   SE  
%       an image with standard errors of both groups
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 4
    verbose = false;
    if nargin < 3
        vartype = []
        if nargin < 2
            error('ERROR: Not enought arguments provided - at least an image object to compare to must be specified');
        end
    end
end

if isempty(vartype)
    vartype = 'equal';
end


% ---- prepare data

if verbose, fprintf('\nSetting up data'), end

A.data = A.image2D;
B.data = B.image2D;
M = A.zeroframes(2);
D = A.zeroframes(1);
p = A.zeroframes(1);

% ---- compute t-test

if verbose, fprintf('\nComputing t-test'), end

if nargout > 5
    [h, p.data, c, s] = ttest2(A.data, B.data, 'Alpha', 0.05, 'Tail', 'both', 'Vartype', vartype, 'Dim', 2);
else
    [h, p.data] = ttest2(A.data, B.data, 'Alpha', 0.05, 'Tail', 'both', 'Vartype', vartype, 'Dim', 2);
end

M.data = [mean(A.data, 2) mean(B.data, 2)];
D.data = M.data(:,1) - M.data(:,2);

% ---- compute Z scores

if nargout > 1
    if verbose, fprintf('\nComputing Z-scores'), end
    Z = A.zeroframes(1);
    Z.data = norminv((1-(p.data ./2)), 0, 1) .* sign(D.data);
end

% ---- compute SE

if nargout > 4
    if verbose, fprintf('\nComputing standard error'), end
    SE = A.zeroframes(2);
    SE.data = [std(A.data, 0, 2) ./ sqrt(A.frames) std(B.data, 0, 2) ./ sqrt(B.frames)];
end

% ---- extract t-values

if nargout > 5
    if verbose, fprintf('\nExtracting t-values'), end
    t = A.zeroframes(1);
    t.data = s.tstat;
end

% ---- done

if verbose, fprintf('\n... done!\n'), end


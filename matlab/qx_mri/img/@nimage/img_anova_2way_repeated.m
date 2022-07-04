function [p F Z M SE] = img_anova_2way_repeated(obj, a, b, verbose)
%``img_anova_2way_repeated(obj, a, b, verbose)``
%
%    Computes ANOVA with two repeated measures factors with a and b levels.
%
%   INPUTS
%   ======
%
%    --obj       The images to work on. The images have to be organized as a
%               series of volumes with session, factor A, factor B in the order 
%               of faster to slowest varying variable. The data has to be fully 
%               balanced with no missing values.
%   --a         Number of levels for factor A
%   --b         Number of levels for factor B
%   --verbose   Should it talk a lot [no]
%
%   OUTPUTS
%   =======
%
%   p
%       an image with 3 frames for p-values related to factors A, B and their 
%       interaction
%
%   F
%       an image with 3 frames for F-values related to factors A, B and their 
%       interaction
%
%   Z
%       an image with 3 frames for Z-scores related to factors A, B and their 
%       interaction
%
%   M
%       an image with a*b frames for all cell means in a series with A as 
%       fastest varying factor
%
%   SE
%       an image with a*b frames for standard errors of all cell means in a 
%       series with A as fastest varying factor
%
%
%   The algorithm was created based on the rm_anova2 function created by 
%   Aron Schurger (2005-02-04).
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 4
    verbose = false;
    if nargin < 3;
        error('ERROR: number of levels for both factors need to be specified!');
    end
end


% ---- prepare data

if verbose, fprintf('\nSetting up data'), end

n = obj.frames / (a*b);
if n ~= ceil(n)
    error('ERROR: the number of volumes in the image (%d) is not divisible by number of possible level combinations (%d)! Please check your input data!', obj.frames, (a*b));
end
obj.data = reshape(obj.data, [obj.voxels, n, a, b]);

% ---- compute df

dfA   = a-1;
dfB   = b-1;
dfAB  = (a-1)*(b-1);
dfS   = n-1;
dfAS  = (a-1)*(n-1);
dfBS  = (b-1)*(n-1);
dfABS = (a-1)*(b-1)*(n-1);

% ---- compute sums I

if verbose, fprintf('\nComputing sums I'), end

AB = squeeze(sum(obj.data, 2));
AS = squeeze(sum(obj.data, 4));
BS = squeeze(sum(obj.data, 3));

% ---- compute sums II

if verbose, fprintf('\nComputing sums II'), end

A = squeeze(sum(AB, 3));
B = squeeze(sum(AB, 2));
S = squeeze(sum(AS, 3));
T = squeeze(sum(A, 2));

% ---- compute squares

if verbose, fprintf('\nComputing squares'), end

expA  = sum(A.^2, 2)./(b*n);
expB  = sum(B.^2, 2)./(a*n);
expS  = sum(S.^2, 2)./(a*b);

expAB = sum(sum(AB.^2, 3), 2)./n;
expAS = sum(sum(AS.^2, 3), 2)./b;
expBS = sum(sum(BS.^2, 3), 2)./a;

expY  = sum(sum(sum(obj.data.^2, 4), 3), 2);
expT  = T.^2 ./ (a*b*n);


% ---- compute mean sum of squares

if verbose, fprintf('\nComputing mean sum of squares'), end

msA = (expA - expT) ./ dfA;
msB = (expB - expT) ./ dfB;
msS = (expS - expT) ./ dfS;

msAB  = (expAB - expA - expB + expT) ./ dfAB;
msAS  = (expAS - expA - expS + expT) ./ dfAS;
msBS  = (expBS - expB - expS + expT) ./ dfBS;
msABS = (expY - expAB - expAS - expBS + expA + expB + expS - expT) ./ dfABS;

ssTot = expY - expT;

% ---- compute F values

if verbose, fprintf('\nComputing F values'), end

F = obj.zeroframes(3);
F.data(:,1) = msA ./ msAS;
F.data(:,2) = msB ./ msBS;
F.data(:,3) = msAB ./ msABS;

% ---- compute p values

if verbose, fprintf('\nComputing p values'), end

p = obj.zeroframes(3);
p.data(:,1) = 1-fcdf(F.data(:,1),dfA,dfAS);
p.data(:,2) = 1-fcdf(F.data(:,2),dfB,dfBS);
p.data(:,3) = 1-fcdf(F.data(:,3),dfAB,dfABS);


% ---- compute Z values

if nargout > 2
    if verbose, fprintf('\nComputing Z values'), end

    Z = obj.zeroframes(3);
    Z.data = norminv((1-(double(p.data)./2)), 0, 1);
end

% ---- compute means

if nargout > 3
    if verbose, fprintf('\nComputing cell means'), end

    M = obj.zeroframes(a*b);
    M.data = reshape(squeeze(mean(obj.data, 2)), M.voxels, (a*b));
end

% ---- compute stamdard error

if nargout > 4
    if verbose, fprintf('\nComputing cell standard errors'), end

    SE = obj.zeroframes(a*b);
    SE.data = reshape(squeeze(std(obj.data, 0, 2)./sqrt(n)), SE.voxels, (a*b));
end

% ---- The End!

if verbose, fprintf('\n... done!\n'), end


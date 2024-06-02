function [] = stats_anova_2way_repeated(dfile, a, b, output, verbose)

%``stats_anova_2way_repeated(dfile, a, b, output, verbose)``
%
%   Computes ANOVA with two repeated measures factors with a and b levels and
%   saves specified results.
%
%   INPUTS
%   ======
%
%    dfile     the data file to work on - either a single image or a conc file
%             The images have to be organized as a series of volumes with 
%             session, factor A, factor B in the order of faster to slowest 
%             varying variable. The data has to be fully balanced with no
%             missing values.
%   a         number of levels for factor A
%   b         number of levels for factor B
%   output    the type of results to save ['mefpz']
%
%             - m ... mean values for each cell
%             - e ... standard errors for each cell
%             - f ... F-values for all three effects
%             - p ... p-values for all three effects
%             - z ... Z-scores for all three effects
%
%   verbose   should report each step [false]
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 5
    verbose = false;
    if nargin < 4
        output = [];
        if verbose < 3
            error('ERROR: data and number of levels for both factors need to be provided as input!');
        end
    end
end

if isempty(output)
    output = 'mefpz';
end

root = strrep(dfile, '.img', '');
root = strrep(root, '.4dfp', '');
root = strrep(root, '.nii', '');
root = strrep(root, '.gz', '');
root = strrep(root, '.conc', '');


% ======================================================
%     ---> read file

if verbose, fprintf('--------------------------\nComputing 2-Way Repeated Measures anova with factors A (%d levels) and B (%d levels)\n ... reading data (%s) ', a, b, dfile), end
img = nimage(dfile);
img.data = img.image2D;


% ======================================================
%     ---> compute ANOVA

if verbose, fprintf('\n ... computing\n --- '), end
[p F Z M SE] = img.img_anova_2way_repeated(a, b, verbose);
if verbose, fprintf(' --- \n'), end


% ======================================================
%     ---> save results

if verbose, fprintf(' ... saving results'), end
if ismember('m', output)
    M.img_saveimage([root '_M']);
    if verbose, fprintf('\n ---> mean values [%s] ', [root '_M']),end
end
if ismember('e', output)
    SE.img_saveimage([root '_SE']);
    if verbose, fprintf('\n ---> standard errors [%s] ', [root '_SE']),end
end
if ismember('f', output)
    F.img_saveimage([root '_F']);
    if verbose, fprintf('\n ---> F-values [%s] ', [root '_F']),end
end
if ismember('p', output)
    p.img_saveimage([root '_p']);
    if verbose, fprintf('\n ---> p-values [%s] ', [root '_p']),end
end
if ismember('z', output)
    Z.img_saveimage([root '_Z']);
    if verbose, fprintf('\n ---> Z-scores [%s]', [root '_Z']),end
end

if verbose, fprintf('\nFinished!\n--------------------------\n'), end






function [] = stats_ttest_zero(dfile, output, exclude, verbose)

%``stats_ttest_zero(dfile, output, exclude, verbose)``
%
%   Computes t-test against zero and saves specified results.
%
%   Parameters:
%       --dfile (str):
%           The data file to work on - either a single image or a conc file.
%
%       --output (str, default 'metpz'):
%           The type of results to save:
%
%           - 'm' ... mean value for each voxel
%           - 'e' ... standard error for each voxel
%           - 't' ... t-value for each voxel
%           - 'p' ... p-value for each voxel
%           - 'z' ... Z-score for each voxel.
%
%       --exclude (int, default ''):
%           Values to be excluded from computation.
%
%       --verbose (bool, default false):
%           Whether to report each step.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 4
    verbose = false;
    if nargin < 3
        exclude = [];
        if nargin < 2
            output = [];
            if nargin < 1
                error('ERROR: file name needs to be provided as input!');
            end
        end
    end
end

if isempty(output)
    output = 'metpz';
end

root = strrep(dfile, '.img', '');
root = strrep(root, '.4dfp', '');
root = strrep(root, '.nii', '');
root = strrep(root, '.gz', '');
root = strrep(root, '.conc', '');

% ======================================================
%     ---> read file

if verbose, fprintf('--------------------------\nComputing t-test against zero\n ... reading data (%s) ', dfile), end
img = nimage(dfile);
img.data = img.image2D;

if ~isempty(exclude)
    img.data(ismember(img.data, exclude)) = NaN;
end


% ======================================================
%     ---> compute t-test

if verbose, fprintf('\n ... computing\n --- '), end
[p Z M SE t] = img.img_ttest_zero(verbose);
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
if ismember('t', output)
    t.img_saveimage([root '_t']);
    if verbose, fprintf('\n ---> t-values [%s] ', [root '_t']),end
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


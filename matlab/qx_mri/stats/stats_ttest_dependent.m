function [] = stats_ttest_dependent(filea, fileb, target, output, exclude, verbose)

%``stats_ttest_dependent(filea, fileb, target, output, exclude, verbose)``
%
%   Computes t-test of differences between two dependent groups.
%
%   Parameters:
%       --filea (str):
%           Either a single image or a conc file with data of the group to
%           compare to.
%
%       --fileb (str):
%           Either a single image or a conc file with data of the group to
%           compare with.
%
%       --target (str):
%           The base filename (and path) to be used when saving the results.
%
%       --output (str, default 'medtpz'):
%           The type of results to save:
% 
%           - 'm' ... mean values for each voxel of both groups (A and B)
%           - 'e' ... standard errors for each voxel of both groups (A and B)
%           - 'd' ... the A - B difference of means of the two groups
%           - 't' ... t-value for each voxel
%           - 'p' ... p-value for each voxel
%           - 'z' ... Z-score for each voxel.
%
%       --exclude (vector, default ''):
%           Values to be excluded from computation.
%
%       --verbose (bool, default false):
%           Should report each step.
% 

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 6
    verbose = false;
    if nargin < 5
        exclude = [];
        if nargin < 4
            output = [];
            if nargin < 3
                error('ERROR: two file names for the input images and a file name for storing the results need to be provided as input!');
            end
        end
    end
end

if isempty(output)
    output = 'metdpz';
end

root = strrep(target, '.img', '');
root = strrep(root, '.4dfp', '');
root = strrep(root, '.nii', '');
root = strrep(root, '.gz', '');
root = strrep(root, '.conc', '');

% ======================================================
%     ---> read file

if verbose, fprintf('--------------------------\nComputing dependent t-test\n ... reading data (%s and %s) ', filea, fileb), end
A = nimage(filea);
B = nimage(fileb);

if ~isempty(exclude)
    A.data(ismember(A.data, exclude)) = NaN;
    B.data(ismember(B.data, exclude)) = NaN;
end


% ======================================================
%     ---> compute t-test

if verbose, fprintf('\n ... computing\n --- '), end
[p Z M D SE t] = A.img_ttest_dependent(B, verbose);
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
if ismember('d', output)
    D.img_saveimage([root '_D']);
    if verbose, fprintf('\n ---> group differences [%s] ', [root '_D']),end
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


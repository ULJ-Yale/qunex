function [] = stats_compute_behavioral_correlations(imgfile, datafile, target)

%``stats_compute_behavioral_correlations(imgfile, datafile, target)``
%
%   Computes correlations between given images and provided data
%   and outputs resulting images per each behavioral variable.
%
%   Parameters:
%       --imgfile (str):
%           Path to data in either a single multi volume file or a conc file.

%       --datafile (str):
%           Path to a tab, space or comma delimited text file with a header line
%           and one column per variable.

%       --target (str, default 'r'):
%           A string specifying the results to compute separated by comma
%           or space:
%
%           - 'r'
%               compute independent correlations for each behavioral variable
%           - 't1'
%               compute multiple regression (GLM) and report Type I SS based
%               results
%           - 't3'
%               compute multiple regression (GLM) and report Type III SS based
%               results.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

% ------ check the parameters

if nargin < 3
    target = 'r';
    if nargin < 2
        error('ERROR: Not enough parameters specified in the function call! Please check the documentation!')
    end
end

% ------ check files

general_check_file(datafile, 'data table file', 'errorstop');
general_check_file(imgfile, 'image data', 'errorstop');

% ------ read behavioral data

bdata = importdata(datafile);

% ------ read image data

img = nimage(imgfile);

% ===================
% ------ process data

% ------ Correlations

if strfind(target, 'r')
    [r, Z] = img.img_compute_correlations(bdata.data, 'r', false, true);
    
    for n = 1:length(bdata.colheaders)
        r.img_saveimageframe(n, fullfile(r.filepath, [r.rootfilename '-' bdata.colheaders{n} '_r']));
        Z.img_saveimageframe(n, fullfile(r.filepath, [r.rootfilename '-' bdata.colheaders{n} '_Z']));
    end
    
end

if strfind(target, 't1')
    [B, Z] = img.img_compute_r_type1(bdata.data, true);
    
    for n = 1:length(bdata.colheaders)
        B.img_saveimageframe(n, fullfile(r.filepath, [r.rootfilename '-' bdata.colheaders{n} '_T-I_B']));
        Z.img_saveimageframe(n, fullfile(r.filepath, [r.rootfilename '-' bdata.colheaders{n} '_T-I_Z']));
    end
    
end

if strfind(target, 't3')
    [B, Z] = img.img_compute_r_type3(bdata.data, true);
    
    for n = 1:length(bdata.colheaders)
        B.img_saveimageframe(n, fullfile(r.filepath, [r.rootfilename '-' bdata.colheaders{n} '_T-III_B']));
        Z.img_saveimageframe(n, fullfile(r.filepath, [r.rootfilename '-' bdata.colheaders{n} '_T-III_Z']));
    end
    
end




function [] = img_save_concfile(file, files)

%``function [] = img_save_concfile(file, files)``
%
%    Saves a conc file.
%
%   INPUTS
%    ======
%
%     --file        path to conc file
%     --files       list of image files
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

file = strtrim(file);
[fout message] = fopen(file,'w');
if fout == -1
    error('\n\nERROR: Could not open %s for saving. Please check your paths!\n\nMatlab message: %s', file, message);
end

fprintf(fout, 'number_of_files: %d\n', length(files));
for n = 1:length(files)
    fprintf(fout, '    file:%s\n', files{n});
end
fclose(fout);

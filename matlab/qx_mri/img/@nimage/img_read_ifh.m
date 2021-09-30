function [ifh] = img_read_ifh(img, file)

%``function [ifh] = img_read_ifh(img, file)``
%
%	Reads .ifh header from a 4dfp file
%
%   INPUTS
%   ======
%
%   --img       nimage object
%   --file      filename
%
%   OUTPUT
%   ======
%
%   ifh
%
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

file = strtrim(file);
root = strrep(file, '.img', '');
root = strrep(root, '.4dfp', '');
root = strrep(root, '.ifh', '');
file = [root '.4dfp.ifh'];

[fin message]= fopen(file);
if fin == -1
    fprintf('\n\nERROR: Could not open %s for reading. Will assume it is a 333 file.\n', file);
    ifh.key{1} = 'INTERFILE';
    ifh.value{1} = '';
    ifh.key{2} = 'version of keys';
    ifh.value{2} = '3.3';
    ifh.key{3} = 'number format';
    ifh.value{3} = 'float';
    ifh.key{4} = 'number of bytes per pixel';
    ifh.value{4} = '4';
    ifh.key{5} = 'orientation';
    ifh.value{5} = '2';
    ifh.key{6} = 'number of dimensions';
    ifh.value{6} = '4';
    ifh.key{7} = 'matrix size [1]';
    ifh.value{7} = '48';
    ifh.key{8} = 'matrix size [2]';
    ifh.value{8} = '64';
    ifh.key{9} = 'matrix size [3]';
    ifh.value{9} = '48';
    ifh.key{10} = 'matrix size [4]';
    ifh.value{10} = '1';
    ifh.key{11} = 'scaling factor (mm/pixel) [1]';
    ifh.value{11} = '3.000000';
    ifh.key{12} = 'scaling factor (mm/pixel) [2]';
    ifh.value{12} = '3.000000';
    ifh.key{13} = 'scaling factor (mm/pixel) [3]';
    ifh.value{13} = '3.000000';
    ifh.key{14} = 'mmppix';
    ifh.value{14} = '3.000000 -3.000000 -3.000000';
    ifh.key{15} = 'center';
    ifh.value{15} = '73.5000  -87.0000  -84.0000';
else
    c = 1;
    while feof(fin) == 0
    	s = fgetl(fin);
    	[key, value] = strtok(s, ':=');
    	value = strtrim(strrep(value, ':=', ''));
    	key = strtrim(key);
    	ifh.key{c} = key;
    	ifh.value{c} = value;
    	c = c + 1;
    end
    fclose(fin);
end



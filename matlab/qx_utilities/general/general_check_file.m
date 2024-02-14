function [ok] = general_check_file(filename, description, v, prepend)

%``general_check_file(filename, description, v, prepend)``
%
%   Checks for existence of a file and prints error notices specified in v.
%
%   Parameters:
%       --filename (str):
%           The path to the file to check for.
%
%       --description (str, default 'a file'):
%           The description for a file.
%
%       --v (str, default 'errorstop'):
%           What should be reported:
%
%           'nothing'
%               just test and return true or false
%           'error'
%               report missing files only and continue
%           'errorstop'
%               report missing files only and stop execution on error
%           'full'
%               report both missing and found files and continue
%           'fullstop'
%               report both missing and found files and stop execution
%               on error.
%
%       --prepend (str, default '… '):
%           String to prepend before the reported line.
%
%   Returns:
%       ok
%           Whether the file was found (true or false).
%
%   Notes:
%       Use to check for presence of files and print warnings or stop
%       execution when the specified file is not present.
%
%   Examples:
%       ::
%
%           general_check_file('images/functional/movement/bold1.dat', ...
%           'movement file', 'full');
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 4 || isempty(prepend), prepend = '... '; end
if nargin < 3 || isempty(v), v = 'errorstop'; end
if nargin < 2 || isempty(description), description = 'a file'; end

if ~exist(filename, 'file')
    pause(3);
end

if exist(filename, 'file')

    if ismember(v, {'full', 'fullstop'})
        fprintf('%sfound %s (%s)\n', prepend, description, filename);
    end
    ok = true;
else
    ok = false;
    if ismember(v, {'errorstop', 'fullstop'})
        error('%scould not find %s (%s), please check your paths!\n', prepend, description, filename);
    elseif ismember(v, {'error', 'full'})
        fprintf('%scould not find %s (%s), please check your paths!\n', prepend, description, filename);
    end
end

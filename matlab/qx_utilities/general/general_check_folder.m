function [ok] = general_check_folder(filename, description, create, v)

%``general_check_folder(filename, description, create, v)``
%
%   Checks for existence of a folder, prints notices and creates folder if
%   specified.
%
%   Parameters:
%       --filename (str):
%           The path to the folder to check for.
%
%       --description (str, default 'a folder'):
%           The description for the folder.
%
%       --create (bool, default true):
%           Whether to create a folder if it does not exist.
%
%       --v (bool, default true):
%           Whether to notify of results.
%
%   Return:
%       ok
%           Whether the folder was found (true or false).
%
%   Notes:
%       Use this function to check for presence of a folder and to
%       (optionally) create one if it does not yet exist.
%
%   Examples:
%       ::
%
%           general_check_folder('images/functional/movement',
%           'movement folder', true, true);
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 4, v = true; end
if nargin < 3, create = true; end
if nargin < 2, description = 'a folder'; end


if ~exist(filename, 'file')
    pause(5);
end

if exist(filename, 'file')
	if v
		fprintf('... found %s (%s)\n', description, filename);
	end
	ok = true;
else	
	if create
		mkdir(filename);
		if v
			fprintf('... could not find %s (%s) a new folder was created!\n', description, filename);
		end
		ok = true;
	else
		if v
			fprintf('... could not find %s (%s), please check your paths!\n', description, filename);
		end
		ok = false;
	end
end

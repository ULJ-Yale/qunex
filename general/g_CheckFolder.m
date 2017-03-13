function [ok] = g_CheckFolder(filename, description, create, v)

%function [ok] = g_CheckFolder(filename, description, create, v)
%
%  Checks for existence of a folder, prints notices and creates folder if specified.
%
%  	INPUT
%    	filename    ... The path to the folder to check for.
%    	description ... The description for the folder ['a folder'].
%		create      ... Whether to create a folder if it does not exist [true].
%    	v           ... Whether to notify of results [true'].
%
%	OUTPUT
%	  	ok ... Whether the folder was found (true or false)
%
%   USE
%   Use to check for presence of a folder and to (optionally) create one if it
%	does not yet exist.
%
%   EXAMPLE USE
%
%   g_CheckFolder('images/functional/movement', 'movement folder', true, true);
%
%   ---
%   Written by Grega Repovs
%
%   Changelog
%   2017-03-12 Grega Repovs
%            - Updated documentation
%

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
	ok = false;
	if create
		mkdir(filename);
		if v
			fprintf('... could not find %s (%s) a new folder was created!\n', description, filename);
		end
	else
		if v & (~create)
			fprintf('... could not find %s (%s), please check your paths!\n', description, filename);
		end
	end
end

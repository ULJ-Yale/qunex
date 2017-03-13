function [ok] = g_CheckFile(filename, description, v)

%function [ok] = g_CheckFile(filename, description, v)
%
%  Checks for existence of a file and prints error notices specified in v.
%
%  INPUT
%    filename    ... The path to the file to check for.
%    description ... The description for a file ['a file'].
%    v           ... What should be reported ['error stop']:
%                    'nothing'     - just test and return true or false
%                    'error'       - report missing files only and continue
%                    'errorstop'   - report missing files only and stop execution on error
%                    'full'        - report both missing and found files and continue
%                    'fullstop'    - report both missing and found files and stop execution on error
%
%   OUTPUT
%     ok ... Whether the file was found (true or false).
%
%   USE
%   Use to check for presence of files and print warnings or stop execution when
%   the specified file is not present.
%
%   EXAMPLE USE
%
%   g_CheckFile('images/functional/movement/bold1.dat', 'movement file', 'full');
%
%   ---
%   Written by Grega Repovs
%
%   Changelog
%   2017-03-12 Grega Repovs
%            - Updated documentation
%

if nargin < 3
	v = 'error stop';
	if nargin < 2
	    description = 'a file';
    end
end

if ~exist(filename, 'file')
	pause(5);
end

if exist(filename, 'file')

    if ismember(v, {'full', 'fullstop'})
		fprintf('... found %s (%s)\n', description, filename);
	end
	ok = true;
else
	ok = false;
	if ismember(v, {'errorstop', 'fullstop'})
	    error('... could not find %s (%s), please check your paths!\n', description, filename);
    elseif ismember(v, {'error', 'full'})
        fprintf('... could not find %s (%s), please check your paths!\n', description, filename);
    end
end

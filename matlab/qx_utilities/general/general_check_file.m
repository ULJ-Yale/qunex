function [ok] = general_check_file(filename, description, v, prepend)

%``function [ok] = general_check_file(filename, description, v, prepend)``
%
%   Checks for existence of a file and prints error notices specified in v.
%
%   INPUTS
%   ======
%   --filename   	The path to the file to check for.
%   --description	The description for a file ['a file'].
%   --v          	What should be reported ['error stop']:
%
%   	           	'nothing'     
%						just test and return true or false
%   	           	'error'       
%						report missing files only and continue
%   	           	'errorstop'   
%						report missing files only and stop execution on error
%   	           	'full'        
%						report both missing and found files and continue
%   	           	'fullstop'    
%						report both missing and found files and stop execution 
%						on error
%
%   --prepend     	String to prepend before the reported line
%
%   OUTPUT
%   ======
%   
%	ok
%		Whether the file was found (true or false).
%
%   USE
%   ===
%
%   Use to check for presence of files and print warnings or stop execution when
%   the specified file is not present.
%
%   EXAMPLE USE
%   ===========
%
%	::
%
%   	general_check_file('images/functional/movement/bold1.dat', 'movement file', ...
%		'full');
%

if nargin < 4 || isempty(prepend), prepend = '... '; end
if nargin < 3 || isempty(v), v = 'error stop'; end
if nargin < 2 || isempty(description), description = 'a file'; end

if ~exist(filename, 'file')
	pause(5);
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

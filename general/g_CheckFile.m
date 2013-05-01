function [ok] = g_CheckFile(filename, description, v)

%  function [ok] = g_CheckFile(filename, description, v)
%  
%  Checks for existence of a file. It prints the notice based on choices.
%  
%  Input parameters:
%    : filename    - the filename to check
%    : description - description of the file to report
%    : v           - what should be reported
%                    'nothing'     - just test and return true or false
%                    'error'       - report error only and continue
%                    'errorstop'   - report error only and stop execution on error
%                    'full'        - report all and continue
%                    'fullstop'    - report all and stop execution on error
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

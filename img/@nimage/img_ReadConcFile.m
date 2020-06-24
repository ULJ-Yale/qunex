function [files, boldnum, sfolder] = img_ReadConcFile(file)

%function [files, boldnum, sfolder] = img_ReadConcFile(file)
%
%	Reads a .conc file and returns a list of files.
%
%   INPUT
%       file  ... a path to the conc file
%
%   OUTPUT
%       files   ... a cell array of file paths specified in the .conc file.
%       boldnum ... the number for the bold files if it can be extracted
%       sfolder ... the session folder where the files are located
%
%   USE
%   Use the method to get the list of files specified in the conc file.
%
%   EXAMPLE USE
%	>>> files = nimage.img_ReadConcFile('OP236-WM.conc');
%
%   ---
%	Written by Grega Repovs
%
%   Changelog
%   2017-03-11 Grega Repovs
%            - Updated documentation.
%   2017-03-21 Grega Repovs
%            - Added output of bold numbers and session folders in which the bolds are located.
%            - Can also process a cell array of file paths.
%

files = {};

if iscell(file)
    if length(file) == 1
        [fpath, fname, fext] = fileparts(file{1});
        if strcmp(fext, '.conc')
            file = file{1};
        else
            files = file;
        end
    else
        files = file;
    end
end

if isempty(files)
    file = strtrim(file);

    [fin message] = fopen(file);
    if fin == -1
        error('\n\nERROR: Could not open %s for reading. Please check your paths!\n\nMatlab message: %s', file, message);
    end
    s = fgetl(fin);

    files 	= {};
    c = 0;
    while feof(fin) == 0
    	s = fgetl(fin);
    	if findstr(s, 'file:')
            c = c + 1;
    		[f] = strread(s, '%s');
    		f = strtrim(strrep(f{1}, 'file:', ''));
    		files{c} = f;
    	end
    end

    fclose(fin);
end

% --- Extract BOLD numbers

if nargout > 1
    boldnum = zeros(1, c);
    for n = 1:c
        [fpath fname fext] = fileparts(files{n});
        boldn = regexp(fname, '^.*?([0-9]+)', 'tokens');
        if ~isempty(boldn)
            boldnum(n) = str2num(boldn{1}{1});
        end
    end
end

% --- Extract session folders

if nargout > 2
    sfolder = {};
    for n = 1:c
        tmp = regexp(files{n}, '^(.*?images)', 'tokens');
        if isempty(tmp)
            sfolder{n} = '';
        else
            sfolder{n} = tmp{1}{1};
        end
    end
end

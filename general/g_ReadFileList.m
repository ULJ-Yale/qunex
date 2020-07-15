function [session, nsessions, nfiles, listname] = g_ReadFileList(flist, verbose)

%function [session, nsessions, nfiles, listname] = g_ReadFileList(flist, verbose)
%
%	Reads a list of files and returns a structure with file information.
%
%   INPUTS
%       flist         : A path to the list file or a well structured string.
%       verbose       : Whether to report on progress [false]
%
%   OUTPUTS
%       - sessions    : a structure array with information
%           - id      : session id
%           - roi     : path to a session ROI file
%           - glm     : path to a session glm file
%           - fidl    : path to a session fidl file
%           - files   : cell array of file paths
%           - folder  : sessions root folder
%       - nsessions   : number of sessions in the list
%       - nfiles      : number of all files in the list
%
%   USE
%   The function reads the file list and returns a structure array with the
%   information on each session. It is also possible to pass the list in the
%   input string itself. In this case, it has to start with 'listname:<name>'
%   all the regular lines of the list file can then be passed with pipe ('|')
%   instead of newline. Example:
%
%   'listname:wmlist|session id:OP483|file:bold1.nii.gz|roi:aseg.nii.gz'
%
%   EXAMPLE USE
%   [sessions, nsessions] = g_ReadFileList('scz.list', true);
%
%   ---
% 	Written by Grega Repovš on 2010-11-23.
%
%   Changelog
%   2012-05-20 Grega Repovš - Changed to omit missing files
%   2013-07-26 Grega Repovš - Added folder to the list of things to list
%   2015-12-09 Grega Repovš - Added reading of fidl and glm files
%   2017-03-19 Grega Repovš - Updated documentation
%   2017-04-18 Grega Repovš - Added option of string parsing


if nargin < 2
    verbose = false;
end

if verbose, fprintf('\n ... reading file list: '); end
if verbose
    report = 'full';
else
    report = 'error';
end

if length(flist) >= 9 && strcmp(flist(1:9), 'listname:')
    files = regexp(flist, '\|', 'split');
    listname = strtrim(regexp(files{1}, ':', 'split'));
    listname = listname{2};
    files = files(2:end);
else
    [lpath, listname, lext] = fileparts(flist);
    files = {};
    infile = fopen(flist);
    while feof(infile) == 0
        files{end+1} = fgetl(infile);
    end
end

nsessions = 0;
nfiles    = 0;
nf        = -9;
prepend   = '       ... ';

for s = files(:)'
    s = strtrim(s{1});
    if length(s) > 0 && s(1) == '#'
        continue
    end
    if ~isempty(strfind(s, 'session id:'))
        nsessions = nsessions + 1;
        nf  = 0;
        [t, s] = strtok(s, ':');
        session(nsessions).id = strtrim(s(2:end));
        if verbose, fprintf('\n     - session id: %s\n', session(nsessions).id); end
        continue
    end
    if nf < 0
        continue
    elseif ~isempty(strfind(s, 'roi:'))
        [t, s] = strtok(s, ':');
        if g_CheckFile(strtrim(s(2:end)), 'ROI image', report, prepend);
            session(nsessions).roi = strtrim(s(2:end));
        end
    elseif ~isempty(strfind(s, 'file:'))
        [t, s] = strtok(s, ':');
        if g_CheckFile(strtrim(s(2:end)), 'image file', report, prepend)
            nf = nf + 1;
            nfiles = nfiles + 1;
            session(nsessions).files{nf} = strtrim(s(2:end));
        end
    elseif ~isempty(strfind(s, 'fidl:'))
        [t, s] = strtok(s, ':');
        if g_CheckFile(strtrim(s(2:end)), 'fidl file', report, prepend);
            session(nsessions).fidl = strtrim(s(2:end));
        end
    elseif ~isempty(strfind(s, 'glm:'))
        [t, s] = strtok(s, ':');
        if g_CheckFile(strtrim(s(2:end)), 'GLM file', report, prepend);
            session(nsessions).glm = strtrim(s(2:end));
        end
    elseif ~isempty(strfind(s, 'folder:'))
        [t, s] = strtok(s, ':');
        if g_CheckFile(strtrim(s(2:end)), 'folder', report, prepend)
            session(nsessions).folder = strtrim(s(2:end));
        end
    end
end

if nsessions == 0
    fprintf('\n\nERROR: No session id information present in file list: %s! Please check file format!\n\n', flist);
    error('ERROR: Could not read the provided filelist.');
end

if verbose, fprintf(' done.\n'); end



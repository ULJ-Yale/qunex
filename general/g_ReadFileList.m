function [subject, nsubjects, nfiles, listname] = g_ReadFileList(flist, verbose)

%function [subject, nsubjects, nfiles, listname] = g_ReadFileList(flist, verbose)
%
%	Reads a list of files and returns a structure with file information.
%
%   INPUTS
%       flist         : A path to the list file or a well structured string.
%       verbose       : Whether to report on progress [false]
%
%   OUTPUTS
%       - subjects    : a structure array with information
%           - id      : subject id
%           - roi     : path to a subject ROI file
%           - glm     : path to a subject glm file
%           - fidl    : path to a subject fidl file
%           - files   : cell array of file paths
%           - folder  : subjects root folder
%       - nsubjects   : number of subjects in the list
%       - nfiles      : number of all files in the list
%
%   USE
%   The function reads the file list and returns a structure array with the
%   information on each subject. It is also possible to pass the list in the
%   input string itself. In this case, it has to start with 'listname:<name>'
%   all the regular lines of the list file can then be passed with pipe ('|')
%   instead of newline. Example:
%
%   'listname:wmlist|subject id:OP483|file:bold1.nii.gz|roi:aseg.nii.gz'
%
%   EXAMPLE USE
%   [subjects, nsubjects] = g_ReadFileList('scz.list', true);
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

nsubjects = 0;
nfiles    = 0;
nf        = -9;
prepend   = '       ... ';

for s = files(:)'
    s = s{1};
    if ~isempty(strfind(s, 'subject id:'))
        nsubjects = nsubjects + 1;
        nf  = 0;
        [t, s] = strtok(s, ':');
        subject(nsubjects).id = strtrim(s(2:end));
        if verbose, fprintf('\n     - subject id: %s\n', subject(nsubjects).id); end
        continue
    end
    if nf < 0
        continue
    elseif ~isempty(strfind(s, 'roi:'))
        [t, s] = strtok(s, ':');
        if g_CheckFile(strtrim(s(2:end)), 'ROI image', report, prepend);
            subject(nsubjects).roi = strtrim(s(2:end));
        end
    elseif ~isempty(strfind(s, 'file:'))
        [t, s] = strtok(s, ':');
        if g_CheckFile(strtrim(s(2:end)), 'image file', report, prepend)
            nf = nf + 1;
            nfiles = nfiles + 1;
            subject(nsubjects).files{nf} = strtrim(s(2:end));
        end
    elseif ~isempty(strfind(s, 'fidl:'))
        [t, s] = strtok(s, ':');
        if g_CheckFile(strtrim(s(2:end)), 'fidl file', report, prepend);
            subject(nsubjects).fidl = strtrim(s(2:end));
        end
    elseif ~isempty(strfind(s, 'glm:'))
        [t, s] = strtok(s, ':');
        if g_CheckFile(strtrim(s(2:end)), 'GLM file', report, prepend);
            subject(nsubjects).glm = strtrim(s(2:end));
        end
    elseif ~isempty(strfind(s, 'folder:'))
        [t, s] = strtok(s, ':');
        if g_CheckFile(strtrim(s(2:end)), 'folder', report, prepend)
            subject(nsubjects).folder = strtrim(s(2:end));
        end
    end
end

if nsubjects == 0
    fprintf('\n\nERROR: No subject id information present in file list: %s! Please check file format!\n\n', flist);
    error('ERROR: Could not read the provided filelist.');
end

if verbose, fprintf(' done.\n'); end



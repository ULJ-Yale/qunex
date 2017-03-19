function [subject, nsubjects, nfiles] = g_ReadFileList(flist, verbose)

%function [subject, nsubjects, nfiles] = g_ReadFileList(flist, verbose)
%
%	Reads a list of files and returns a structure with file information.
%
%   INPUTS
%       flist         : A path to the list file.
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
%   information on each subject.
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


if nargin < 2
    verbose = false;
end

if verbose, fprintf('\n ... reading file list: '); end
if verbose
    report = 'full';
else
    report = 'error';
end

files     = fopen(flist);
nsubjects = 0;
nfiles    = 0;

while feof(files) == 0
    s = fgetl(files);
    if ~isempty(strfind(s, 'subject id:'))
        nsubjects = nsubjects + 1;
        nf  = 0;
        [t, s] = strtok(s, ':');
        subject(nsubjects).id = strtrim(s(2:end));
        if verbose, fprintf('%s \n', subject(nsubjects).id); end
    elseif ~isempty(strfind(s, 'roi:'))
        [t, s] = strtok(s, ':');
        if g_CheckFile(strtrim(s(2:end)), 'ROI image', report);
            subject(nsubjects).roi = strtrim(s(2:end));
        end
    elseif ~isempty(strfind(s, 'file:'))
        [t, s] = strtok(s, ':');
        if g_CheckFile(strtrim(s(2:end)), 'image file', report)
            nf = nf + 1;
            nfiles = nfiles + 1;
            subject(nsubjects).files{nf} = strtrim(s(2:end));
        end
    elseif ~isempty(strfind(s, 'fidl:'))
        [t, s] = strtok(s, ':');
        if g_CheckFile(strtrim(s(2:end)), 'fidl file', report);
            subject(nsubjects).fidl = strtrim(s(2:end));
        end
    elseif ~isempty(strfind(s, 'glm:'))
        [t, s] = strtok(s, ':');
        if g_CheckFile(strtrim(s(2:end)), 'GLM file', report);
            subject(nsubjects).glm = strtrim(s(2:end));
        end
    elseif ~isempty(strfind(s, 'folder:'))
        [t, s] = strtok(s, ':');
        if g_CheckFile(strtrim(s(2:end)), 'folder', report)
            subject(nsubjects).folder = strtrim(s(2:end));
        end
    end
end

fclose(files);

if verbose, fprintf(' done.\n'); end



function [subject, nsubjects, nfiles] = g_ReadFileList(flist, verbose)

%	
%	function [subjects, nsubjects, nfiles] = g_ReadFileList(flist, verbose)
%	
%	Reads a list of files and returns a structure with file information.
%
%   Outputs
%       - subjects  : a structure array with information
%           - id    : subject id
%           - roi   : path to a subject ROI file 
%           - files : cell array of file paths
%       - nsubjects : number of subjects in the list
%       - nfiles    : number of all files in the list (excluding roi)
%	
% 	Created by Grega Repovš on 2010-11-23.
%   2012-05-20 - Changed to omit missing files
%
% 	Copyright (c) 2010. All rights reserved.

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
        nf = 0;
        [t, s] = strtok(s, ':');        
        subject(nsubjects).id = strtrim(s(2:end));
        if verbose, fprintf(subject(nsubjects).id); end
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
    end
end

fclose(files);

if verbose, fprintf(' done.\n'); end



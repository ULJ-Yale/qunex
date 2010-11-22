function [subjects, nsubjects, nfiles] = g_ReadFileList(flist, verbose)

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
%
% 	Copyright (c) 2010. All rights reserved.

if nargin < 2
    verbose = false;
end

if verbose, fprintf('\n ... reading file list '); end

files     = fopen(flist);
nsubjects = 0;
nfiles    = 0;

while feof(files) == 0
    s = fgetl(files);
    if ~isempty(strfind(s, 'subject id:'))
        nsubjects = nsubjects + 1;
        nf = 0;
        [t, s] = strtok(s, ':');        
        subject(c).id = strtrim(s(2:end));
        if verbose, fprintf('S'); end
    elseif ~isempty(strfind(s, 'roi:'))
        [t, s] = strtok(s, ':');        
        subject(c).roi = strtrim(s(2:end));
        g_CheckFile(subject(c).roi);
        if verbose, fprintf('r'); end
    elseif ~isempty(strfind(s, 'file:'))
        nf = nf + 1;
        nfiles = nfiles + 1;
        [t, s] = strtok(s, ':');        
        subject(c).files{nf} = strtrim(s(2:end));
        g_CheckFile(s(2:end));      
        if verbose, fprintf('f'); end  
    end
end

fclose(files);

if verbose, fprintf(' done.\n'); end



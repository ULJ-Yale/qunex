function [subjects] = g_ReadSubjectsList(flist)

% function [subjects] = g_ReadSubjectsList(flist)
%	
%	Reads a subjects.list file and returns file paths for each subject.
%
%	Input:
%		flist 	        - a path to the subjects.list file
%
%	Output
%		subjects        - array of structures with data for each subject:
%			... id      - subject's id read from "subject id:" line
%           ... roi     - path to subject's roi file listed in "roi:" line
%           ... fidl    - path to subject's fidl file listed in "fidl:" line
%           ... files   - cell array of paths to files read from "file:" line
%           ... folder  - path to subject's folder read from "folder:" line
%
%   (c) Grega Repovš, 2011-02-11
%


files = fopen(flist);
c = 0;
while feof(files) == 0
    s = fgetl(files);
    if length(strfind(s, 'subject id:')>0)
        c = c + 1;
        [t, s] = strtok(s, ':');        
        subjects(c).id = s(2:end);
        nf = 0;
    elseif length(strfind(s, 'roi:')>0)
        [t, s] = strtok(s, ':');        
        subjects(c).roi = s(2:end);
    elseif length(strfind(s, 'folder:')>0)
        [t, s] = strtok(s, ':');        
        subjects(c).folder = s(2:end);
    elseif length(strfind(s, 'fidl:')>0)
        [t, s] = strtok(s, ':');        
        subjects(c).fidl = s(2:end);
    elseif length(strfind(s, 'file:')>0)
        nf = nf + 1;
        [t, s] = strtok(s, ':');        
        subjects(c).files{nf} = s(2:end);
    end
end


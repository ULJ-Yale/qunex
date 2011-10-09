function [obj] = mri_ReadStats(obj, filename, frames)

%function [obj] = mri_ReadStats(obj, filename, frames)
%
%	Reads in available files with information on movement, 
%	per frame image stats and scrubbing inf.
%
%   (c) Grega Repovs
%   2011-07-31 - Initial version
%

if nargin < 3
    frames = [];
end

% ---> check if movement folder exists


[fpath, fname] = fileparts(filename);
if isempty(fpath) || strcmp(fpath,'.') || strcmp(fpath, '~')
    fpath = pwd;
end
if exist(fullfile(fpath, 'movement'), 'dir')
    movfolder = fullfile(fpath, 'movement');
elseif exist(fullfile(fileparts(fpath),'movement'), 'dir')
    movfolder = fullfile(fileparts(fpath),'movement');
else
    return
end


% ---> check for movement data

tfile = FindMatchingFile(movfolder, fname, '.dat');
if tfile
    [data header] = ReadTextFile(tfile);
    data = CheckData(data, frames, obj.frames);
    if ~isempty(data)
        obj.mov     = data;
        obj.mov_hdr = header;
    end
end


% ---> check for per-frame stats data

tfile = FindMatchingFile(movfolder, fname, '_bstats.txt');
if tfile
    [data header] = ReadTextFile(tfile);
    data = CheckData(data, frames, obj.frames);
    if ~isempty(data)
        obj.fstats     = data;
        obj.fstats_hdr = header;
    end
end

% ---> check for scrubbing data

tfile = FindMatchingFile(movfolder, fname, '_scrub.txt');
if tfile
    [data header] = ReadTextFile(tfile);
    data = CheckData(data, frames, obj.frames);
    if ~isempty(data)
        obj.scrub     = data;
        obj.scrub_hdr = header;
    end
end


% ===============================================
%                                    ReadTextFile

function [x, header] = ReadTextFile(filename)

fin = fopen(filename, 'r');
c = 0;
s = fgetl(fin);
h = false;
while ischar(s)
    s = strtrim(s);
    if ~isempty(s)
        if ismember(s(1),'-.0123456789')
            c = c+1;
            x(c,:) = strread(s);
            h = true;
    	elseif ~h
    	    s = strrep(s, '#', '');
    	    header = textscan(s, '%s');
    	    header = header{1};
        end
    end
    s = fgetl(fin);
end
fclose(fin);





% ===============================================
%                                FindMatchingFile

function [mfile] = FindMatchingFile(movfolder, froot, tail)

mfile = false;

% ---> get the list of files
files = dir(fullfile(movfolder, ['*' tail]));
if isempty(files)
    return
end

% ---> get the one that matches best
li = length(froot);
nmatch = 0;
fmatch = 0;
for f = 1:length(files)
    ld     = length(files(f).name);
    c      = min(li, ld);
    tmatch = sum(froot(1:c) == files(f).name(1:c));
    if tmatch > nmatch
        nmatch = tmatch;
        fmatch = f;
    end
end

if fmatch > 0
    mfile = fullfile(movfolder, files(fmatch).name);
end


    



% ===============================================
%                                       CheckData

function [data] = CheckData(data, tframes, iframes)

l = size(data, 1);
if tframes
    if tframes > l
        data = [];
        return
    end
    data = data(1:tframes,:);
    l = tframes;
end
    
if l ~= iframes
    data = [];
end




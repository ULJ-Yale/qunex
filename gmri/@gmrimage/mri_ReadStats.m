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

% ---> check for movement data

tfile = FindMatchingFile(filename, '.dat')
[data header] = ReadTextFile(tfile);
data = CheckData(data, frames, obj.frames);
if data
    obj.mov     = data;
    obj.mov_hdr = header;
end


% ---> check for per-frame stats data

tfile = FindMatchingFile(filename, '_bstats.txt')
[data header] = ReadTextFile(tfile);
data = CheckData(data, frames, obj.frames);
if data
    obj.fstats     = data;
    obj.fstats_hdr = header;
end


% ---> check for scrubbing data

tfile = FindMatchingFile(filename, '_scrub.txt')
[data header] = ReadTextFile(tfile);
data = CheckData(data, frames, obj.frames);
if data
    obj.scrub     = data;
    obj.scrub_hdr = header;
end



% ===============================================
%                                    ReadTextFile

function [x, header] = ReadTextFile(filename)

fin = fopen(file, 'r');
c = 0;
s = fgetl(fin);
h = false;
while ischar(s)
    if ~ischar(s(1))
        c = c+1;
        x(c,:) = strread(s);
        h = true;
	elseif ~h
	    s = strrep(s, '#', '');
	    header = textscan(s, '%strrep');
	    header = header{1};
    end
    s = fgetl(fid);
end
fclose(fin)





% ===============================================
%                                FindMatchingFile

function [mfile] = FindMatchingFile(filename, tail)

% ---> get the list of files
[fpath, froot] = fileparts(filename);
files = dir([fpath filesep 'movement' filesep '*' tail]);
if length(files) == 0
    mfile = false;
    return
end

% ---> get the one that matches best
li = length(froot);
nmatch = 0;
fmatch = 0;
for f in 1:length(files)
    ld     = length(files(f).name);
    c      = min(li, ld);
    tmatch = sum(froot(1:c) == file(f).name(1:c));
    if tmatch > nmatch:
        nmatch = tmatch;
        fmatch = f;
    end
end

mfile = files(fmatch).name;



% ===============================================
%                                       CheckData

function [data] = CheckData(data, tframes, iframes)

l = size(data, 1);
if tframes
    if tframes > l
        data = false;
        return
    end
    data = data(1:tframes,:);
    l = tframes;
end
    
if l ~= iframes
    data = false;
end




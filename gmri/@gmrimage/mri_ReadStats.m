function [obj] = mri_ReadStats(obj, filename, frames)

%function [obj] = mri_ReadStats(obj, filename, frames)
%
%	Reads in available files with information on movement,
%	per frame image stats and scrubbing inf.
%
%   (c) Grega Repovs
%   2011-07-31 - Initial version
%   2013-10-19 - Added reading embedded data
%


if nargin < 3
    frames = [];
end

% ---> check for embedded data

obj.data = obj.image2D;
sel      = typecast(single(obj.data(1,:)), 'uint32');
ebstats  = sum(bitand(sel, 16) == 0) == 0;
esel     = sum(bitand(sel, 32) == 0) == 0;
emov     = sum(bitand(sel, 64) == 0) == 0;

if esel
    obj.scrub_hdr  = {'frame', 'mov', 'dvars', 'dvarsme', 'idvars', 'idvarsme', 'udvars', 'udvarsme'};
    obj.scrub      = zeros(obj.frames, 8);
    obj.scrub(:,1) = 1:obj.frames;
    obj.scrub(:,2) = bitand(sel,2) > 0;
    obj.scrub(:,3) = bitand(sel,4) > 0;
    obj.scrub(:,4) = bitand(sel,8) > 0;
    obj.scrub(:,5) = bitand(sel,6) == 6;
    obj.scrub(:,6) = bitand(sel,10) == 10;
    obj.scrub(:,7) = bitand(sel,6) > 0;
    obj.scrub(:,8) = bitand(sel,10) > 0;
    obj.use        = bitand(sel,1) > 0;
end

if ebstats
    obj.fstats_hdr  = {'frame', 'n', 'm', 'var', 'sd', 'dvars', 'dvarsm', 'dvarsme', 'fd'};
    obj.fstats      = zeros(obj.frames, 9);
    obj.fstats(:,1) = 1:obj.frames;
    obj.fstats(:,2) = obj.data(2,:);
    obj.fstats(:,3) = obj.data(3,:);
    obj.fstats(:,4) = obj.data(4,:)^2;
    obj.fstats(:,5) = obj.data(4,:);
    obj.fstats(:,6) = obj.data(5,:) .* obj.data(3,:) ./100;
    obj.fstats(:,7) = obj.data(5,:);
    obj.fstats(:,8) = obj.data(6,:);
    obj.fstats(:,9) = obj.data(7,:);
end

if emov
    obj.mov_hdr  = {'frame', 'dx(mm)', 'dy(mm)', 'dz(mm)', 'X(deg)', 'Y(deg)', 'Z(deg)', 'scale'};
    obj.mov      = zeros(obj.frames, 8);
    obj.mov(:,1) = 1:obj.frames;
    obj.mov(:,2:8) = obj.data(end-6:end,:)';
end


if ~ emov

    % ---> check if movement folder exists

    filename = strtrim(filename);
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
end


if ~ebstats

    % ---> check for per-frame stats data

    tfile = FindMatchingFile(movfolder, fname, '.bstats');
    if tfile
        [data header] = ReadTextFile(tfile);
        data = CheckData(data, frames, obj.frames);
        if ~isempty(data)
            obj.fstats     = data;
            obj.fstats_hdr = header;
        end
    end
end

if ~esel

    % ---> check for scrubbing data

    tfile = FindMatchingFile(movfolder, fname, '.scrub');
    if tfile
        [data header] = ReadTextFile(tfile);
        data = CheckData(data, frames, obj.frames);
        if ~isempty(data)
            obj.scrub     = data;
            obj.scrub_hdr = header;
        end
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




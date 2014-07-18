function [obj] = mri_ReadStats(obj, filename, frames, verbose)

%function [obj] = mri_ReadStats(obj, filename, frames, verbose)
%
%	Reads in available files with information on movement,
%	per frame image stats and scrubbing inf.
%
%   (c) Grega Repovs
%   2011-07-31 - Initial version
%   2013-10-19 - Added reading embedded data
%   2013-10-20 - Added verbose option
%   2014-07-19 - Switched to g_ReadTable
%

if nargin < 4
    verbose = false;
    if nargin < 3
        frames = [];
    end
end

obj.use = true(1, obj.frames);

% ---> check for embedded data

if verbose, fprintf('---> checking for embedded data ...'), end

obj.data = obj.image2D;
sel      = typecast(single(obj.data(1,:)), 'uint32');
embd     = sum(bitand(sel, 2147483520) > 0) == 0;
if embd
    ebstats  = sum(bitand(sel, 16) == 0) == 0;
    esel     = sum(bitand(sel, 32) == 0) == 0;
    emov     = sum(bitand(sel, 64) == 0) == 0;
else
    ebstats = false;
    esel    = false;
    emov    = false;
end

if verbose
    if ~embd, fprintf(' no embedded data'), end;
    if ebstats, fprintf(' stats'), end;
    if emov, fprintf(' movement'), end;
    if esel, fprintf(' scrub'), end;
    fprintf('\n')
end

% obj.data(1,1:10)
% sel(1:10)

if esel
    if verbose, fprintf('---> reading ebbedded scrub data\n'), end
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
    if verbose, fprintf('---> reading ebbedded stats data\n'), end
    obj.fstats_hdr  = {'frame', 'n', 'm', 'var', 'sd', 'dvars', 'dvarsm', 'dvarsme', 'fd'};
    obj.fstats      = zeros(obj.frames, 9);
    obj.fstats(:,1) = 1:obj.frames;
    obj.fstats(:,2) = obj.data(2,:);
    obj.fstats(:,3) = obj.data(3,:);
    obj.fstats(:,4) = obj.data(4,:).^2;
    obj.fstats(:,5) = obj.data(4,:);
    obj.fstats(:,6) = obj.data(5,:) .* obj.data(3,:) ./100;
    obj.fstats(:,7) = obj.data(5,:);
    obj.fstats(:,8) = obj.data(6,:);
    obj.fstats(:,9) = obj.data(7,:);
end

if emov
    if verbose, fprintf('---> reading ebbedded movement data\n'), end
    obj.mov_hdr  = {'frame', 'dx(mm)', 'dy(mm)', 'dz(mm)', 'X(deg)', 'Y(deg)', 'Z(deg)', 'scale'};
    obj.mov      = zeros(obj.frames, 8);
    obj.mov(:,1) = 1:obj.frames;
    obj.mov(:,2:8) = obj.data(end-6:end,:)';
end


if (~emov) | (~ebstats) | (~esel)

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

    if verbose, fprintf('---> found movement folder at %s\n', movfolder), end
end



if ~emov

    % ---> check for movement data

    tfile = FindMatchingFile(movfolder, fname, '.dat');
    if verbose, fprintf('---> reading movement data from %s\n', tfile), end
    if tfile
        [data header] = g_ReadTable(tfile);
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
    if verbose, fprintf('---> reading stats data from %s\n', tfile), end
    if tfile
        [data header] = g_ReadTable(tfile);
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
    if verbose, fprintf('---> reading scrub data from %s\n', tfile), end
    if tfile
        [data header] = g_ReadTable(tfile);
        data = CheckData(data, frames, obj.frames);
        if ~isempty(data)
            obj.scrub     = data;
            obj.scrub_hdr = header;
        end
    end
end




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




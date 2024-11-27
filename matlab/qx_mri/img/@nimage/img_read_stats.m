function [obj] = img_read_stats(obj, verbose)

%``img_read_stats(obj, verbose)``
%
%    Reads in available files with information on movement, per frame image stats
%   and scrubbing information.
%
%   INPUTS
%   ======
%
%   --obj       nimage object
%   --verbose   should it talk a lot [false]
%
%   OUTPUT
%   ======
%
%   obj
%       nimage with added data statistics
%
%   USE
%   ===
%
%   The method is used internaly to get the different statistical data about the
%   image. It first tries to see if the statistical data is embedded in the
%   image itself (as might be the case for volume images), otherwise it checks
%   for presence of external files and reads data from there.
%
%   EXAMPLE USE
%   ===========
%
%   ::
%   
%       img = img.img_read_stats();
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 2, verbose = false; end

frames   = obj.frames;

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

    fpath = obj.filepath;
    fname = obj.rootfilename;
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
    if tfile
        if verbose, fprintf('---> reading movement data from %s\n', tfile), end
        [data header] = general_read_table(tfile);
        data = CheckData(data, frames, obj.frames, verbose);
        if ~isempty(data)
            obj.mov     = data;
            obj.mov_hdr = header;
        elseif verbose
            fprintf('---> error reading movement data \n');
        end
    elseif verbose
        fprintf('---> could not find movement data\n');
    end

end


if ~ebstats

    % ---> check for per-frame stats data

    tfile = FindMatchingFile(movfolder, fname, '.bstats');
    if tfile
        if verbose, fprintf('---> reading stats data from %s\n', tfile), end
        [data header] = general_read_table(tfile);
        data = CheckData(data, frames, obj.frames, verbose);
        if ~isempty(data)
            obj.fstats     = data;
            obj.fstats_hdr = header;
        elseif verbose
            fprintf('---> error reading stats data \n');
        end
    else
        if verbose, fprintf('---> could not find stats data!\n'), end
    end
end

if ~esel

    % ---> check for scrubbing data

    tfile = FindMatchingFile(movfolder, fname, '.scrub');
    if tfile
        if verbose, fprintf('---> reading scrub data from %s\n', tfile), end
        [data header] = general_read_table(tfile);
        data = CheckData(data, frames, obj.frames, verbose);
        if ~isempty(data)
            obj.scrub     = data;
            obj.scrub_hdr = header;
            if ismember('use', header)
                obj.use = data(:,ismember(header, 'use'))';
            end
        elseif verbose
            fprintf('---> error reading scrub data \n');
        end
    elseif verbose
        fprintf('---> could not find scrub data \n');
    end
end




% ===============================================
%                                FindMatchingFile

function [mfile] = FindMatchingFile(movfolder, froot, tail, verbose)
if nargin < 4 || isempty(verbose), verbose = false; end

if verbose, fprintf('\n---> matching: %s %s', froot, tail); end

mfile = false;

% ---> split the source

ssplit = regexp(froot,'\.|-|_', 'split');
fbase = regexp(froot, '(^.*?[0-9]+).*', 'tokens');

% ---> abort if no tokens
if isempty(fbase)
    if verbose, fprintf('\n---> no match\n', froot, tail); end
    return
end

% ---> get the list of candidate files
files = dir(fullfile(movfolder, [ fbase{1}{1} '*' tail]));
if isempty(files)
    if verbose, fprintf('\n---> no match\n', froot, tail); end
    return
end

% ---> get the one that matches best
if length(files) > 1
    li = length(ssplit);
    nmatch = 0;
    fmatch = 0;
    for f = 1:length(files)
        tsplit = regexp(files(f).name,'\.|-|_', 'split');
        ld     = length(tsplit);
        c      = min(li, ld);
        tmatch = 0;
        for n = 1:c
            if strcmp(ssplit{n}, tsplit{n})
                tmatch = n;
            else
                break
            end
        end
        if tmatch > nmatch
            nmatch = tmatch;
            fmatch = f;
        end
    end
else
    fmatch = 1;
end

if fmatch > 0
    mfile = fullfile(movfolder, files(fmatch).name);
end

if verbose, fprintf('\n---> matched: %s\n', mfile); end






% ===============================================
%                                       CheckData

function [data] = CheckData(data, tframes, iframes, verbose)

l = size(data, 1);
if tframes
    if tframes > l
        data = [];
        if verbose, fprintf('     ... data check failed! (data length %d vs %d)!\n', l, tframes); end
        return
    end
    data = data(1:tframes,:);
    l = tframes;
end

if l ~= iframes
    data = [];
    if verbose, fprintf('     ... data check failed! (data length %d vs %d)!\n', l, iframes); end
end




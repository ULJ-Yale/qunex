function [img] = mri_ComputeScrub(img, comm)

%function [img] = mri_ComputeScrub(img, comm)
%
%   Scrubs image according to the command
%
%       input:
%           img   - mrimage object
%           comm  - the description of how to compute scrubbing - a string in 'param:value|param:value' format
%                   parameters:
%                   - radius   : head radius in mm [50]
%                   - fdt      : frame displacement threshold
%                   - dvarsmt  : dvarsm threshold
%                   - dvarsmet : dvarsme threshold
%                   - after    : how many frames after the bad one to reject
%                   - before   : how many frames before the bad one to reject
%                   - reject   : which criteria to use for rejection (mov, dvars, dvarsme, idvars, udvars ...)
%       output:
%           img  - image with scrubbing data included
%
%       Grega Repovs - 2013-10-20
%
%
%


param.before   = 0;
param.after    = 0;
param.radius   = 50;
param.fdt      = 0.5;
param.dvarsmt  = 3.0;
param.dvarsmet = 1.6;
param.reject   = 'udvarsme';

comm = regexp(comm, ',|;|:|\|', 'split');
if length(comm)>=2
    comm = reshape(comm, 2, [])';
    for p = size(comm, 1)
        val = str2num(comm{p,2});
        if isempty(val)
            setfield(param, comm{p,1}, comm{p,2});
        else
            setfield(param, comm{p,1}, val);
        end
    end
end

% ---- check for the relevant data

mov    = true;
fstats = true;

if isempty(img.fstats)
    fprintf('WARNING: mri_ComputeScrub(), missing image statistics data!');
    fstats = false;
    mov    = false;
end
if ismember('fd', img.fstats_hdr)
    fd = img.fstats(:,ismember(img.fstats_hdr, {'fd'}));
    if sum(fd > 0) == 0
        img.fstats = img.fstats(:,~ismember(img.fstats_hdr, {'fd'}));
        img.fstats_hdr = img.fstats_hdr(:,~ismember(img.fstats_hdr, {'fd'}));
        mov = false;
    end
else
    mov = false;
end
if ~mov
    if isempty(img.mov)
        fprintf('WARNING: mri_ComputeScrub(), missing movement data!');
    else
        rot = img.mov(:, ismember(img.mov_hdr, {'X(deg)', 'Y(deg)', 'Z(deg)'}));
        tra = img.mov(:, ismember(img.mov_hdr, {'dx(mm)', 'dy(mm)', 'dz(mm)'}));
        drot = [zeros(1,3); diff(rot)];
        dtra = [zeros(1,3); diff(tra)];
        fd = drot;
        fd = sind(fd./2) .* param.radius .* 2;
        fd = [fd dtra];
        fd = sum(abs(fd),2);

        img.fstats_hdr(end+1) = {'fd'};
        img.fstats = [img.fstats fd];
        mov = true;
    end
end


% ---- compute what to scrub

img.scrub_hdr  = {'frame', 'mov', 'dvars', 'dvarsme', 'idvars', 'idvarsme', 'udvars', 'udvarsme'};
img.scrub      = zeros(img.frames, 8);
img.scrub(:,1) = 1:img.frames;

if mov
    img.scrub(:,2) = fd > param.fdt;
end

if fstats
    img.scrub(:,3) = img.fstats(:,ismember(img.fstats_hdr, {'dvarsm'}))  > param.dvarsmt;
    img.scrub(:,4) = img.fstats(:,ismember(img.fstats_hdr, {'dvarsme'})) > param.dvarsmet;
end

img.scrub(:,5)   = img.scrub(:,2) & img.scrub(:,3);
img.scrub(:,6)   = img.scrub(:,2) & img.scrub(:,4);
img.scrub(:,7)   = img.scrub(:,2) | img.scrub(:,3);
img.scrub(:,8)   = img.scrub(:,2) | img.scrub(:,4);

img.scrub(:,2:8) = spreadTS(img.scrub(:,2:8)', -param.before, param.after)';
img.use          = ~img.scrub(:, ismember(img.scrub_hdr, param.reject))';





% -------------------------------------------------
%                                 support functions

function [ts] = shiftTS(ts, shift)

    if shift == 0, return, end
    if shift > 0
        ts = [zeros(1, shift) ts(1:end-shift)];
    else
        ts = [ts(1+shift:end) zeros(1, shift)];
    end


function [ts] = spreadTS(ts, s, e)

    nts = zeros(size(ts));
    for n = s:e
        if n == 0
            nts = nts + ts;
        elseif n > 0
            nts = nts + [zeros(1, n) ts(1:end-n)];
        else
            nts = nts + [ts(1+n:end) zeros(1, n)];
        end
    end
    ts = nts > 0;


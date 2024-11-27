function [img, param] = img_compute_scrub(img, comm)

%``img_compute_scrub(img, comm)``
%
%   Method that computes image scrubbing parameters.
%
%   INPUTS
%   ======
%
%   --img    nimage image object
%   --comm   the description of how to compute scrubbing - a string in 
%            'param:value|param:value' format
%            
%            Parameters:
%
%            - radius   ... head radius in mm [50]
%            - fdt      ... frame displacement threshold [0.5]
%            - dvarsmt  ... dvarsm threshold [3.0]
%            - dvarsmet ... dvarsme threshold [1.6]
%            - after    ... how many frames after the bad one to reject [0]
%            - before   ... how many frames before the bad one to reject [0]
%            - reject   ... which criteria to use for rejection [udvarsme]:
%
%               mov
%                  frame displacement threshold (fdt) is exceeded
%               dvars
%                  root mean squared error (RMSE) threshold (dvarsmt) is exceeded
%               dvarsme
%                  median normalised RMSE (dvarsmet) threshold is exceeded
%               idvars
%                  both fdt and dvarsmt are exceeded (i for intersection)
%               uvars
%                  either fdt or dvarsmt are exceeded (u for union)
%               idvarsme
%                  both fdt and dvarsmet are exceeded
%               udvarsme
%                  either fdt or udvarsmet are exceeded
%
%   OUTPUTS
%   =======
%
%   img
%       nimage image object with scrubbing data embedded:
%
%       img.scrub_hdr
%           a cell array of strings listing variables computed
%       img.scrub    
%           a nframes x nvariables matrix where 0 denotes threshold was not 
%           exceeded, 1 threshold was exceeded
%       img.use      
%           a vector denoting for each image frame whether it should be used (1) 
%           on not (0) based on whether the specified threshold / condition was 
%           exceeded or not
%
%   param
%       a structure holding the parameters used
%
%   USE
%   ===
%
%   The method is used on an nimage img object that has both movement parameters
%   data (img.mov) and per frame statistics data (img.fstats) already computed
%   and present. Movement data is read automatically when the image is loaded,
%   if the data is present in the relevant folder (images/functional/movement).
%   Frame statistics data is also read if present. It is computed and saved
%   using general_compute_bold_stats function that makes use of img_stats_time method.
%
%   The function is meant to identify frames with artefacts that should be
%   excluded in functional connectivity analyses. It makes use of three
%   statistics. fdt is mean frame displacement. It estimates the mean distance
%   that cortext has moved due to head movement. dvars is computed as root of
%   mean sqared differences (RMSD) between intensities of each voxel in the
%   current and previous frame. It is normalised by the mean frame intensity. As
%   dvars can differ significantly depending on the SNR, image geometry etc, a
%   median normalised dvars measure can be computed. This measure assumes that
%   artefacts are relatively rare and estimates the baseline dvars as median
%   across the timecourse. dvars at each time point is then divided by the
%   median resulting in a measure in which frames with baseline frame to frame
%   differences in intensities have a value round 1 and the rest are marked with
%   the multiple of baseline. This measure works well even with different base
%   SNR and with different image geometries.
%
%   In marking the bad frames any of the three methods can be used, as well as
%   their combination. For instance a frame can be marked bad if it exceeds the
%   threshold for either frame displacement or dvarsme (udvarsme). A more
%   conservative criterium would be a requirement that it exceeds both
%   (idvarsme).
%
%   If desired, a number of frames before or after the marked frame can also be
%   marked for exclusion.
%
%   The image is not scrubbed, only the scrubbing parameters are computed and
%   the chosen criterium is used to create the "img.use" mask that in other
%   functions and methods defines what frames to use or not.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

param.before   = 0;
param.after    = 0;
param.radius   = 50;
param.fdt      = 0.5;
param.dvarsmt  = 3.0;
param.dvarsmet = 1.6;
param.reject   = 'udvarsme';

param = general_parse_options(param, comm);

% ---- check for the relevant data

mov    = true;
fstats = true;

if isempty(img.fstats)
    fprintf('WARNING: img_compute_scrub(), missing image statistics data!');
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
        fprintf('WARNING: img_compute_scrub(), missing movement data!');
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
if strcmp(param.reject, 'none')
    img.use = [img.scrub(:,1) > 0]';
elseif ismember(param.reject, {'mov', 'dvars', 'dvarsme', 'idvars', 'idvarsme', 'udvars', 'udvarsme'})
    img.use = ~img.scrub(:, ismember(img.scrub_hdr, param.reject))';
else
    error('\nERROR: No valid column (or ''None'') specified as reject parameter!');
end






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

    tsl = size(ts,2);
    tsw = size(ts,1);
    nts = zeros(tsw, tsl);

    for n = s:e
        if n == 0
            nts = nts + ts;
        elseif n > 0
            nts = nts + [zeros(tsw, n) ts(:, 1:end-n)];
        else
            nts = nts + [ts(:,1-n:end) zeros(tsw, -n)];
        end
    end
    ts = nts > 0;

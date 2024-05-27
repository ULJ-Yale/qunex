function [img] = img_scrub(img, com)

%``img_scrub(img, com)``
%
%   Scrubs image according to the command
%
%   INPUTS
%   ======
%
%   --img     nimage object.
%   --com     The description of how to scrub. Format:
%
%             string only
%               use the relevant column from .scrub file
%             string:string
%               use the relevant columnd from .scrub and then either:
%                   - NA - set the bad frames to value NaN
%                   - RM - delete the bad frames from the image
%             string:string:number
%               use the number to threshold based on .bstats and .mov files
%
%   OUTPUT
%   ======
%   
%   img
%       scrubbed image
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 2
    fprintf('\n\nERROR in the use of nimage.img_scrub!')
    help('nimage.img_scrub');
    error();
end

r   = 50;
fdt = 0.5;

% ---- process the command

com = regexp(com, ',|;|:|\|', 'split');

if length(com) < 3
    if strcmp(com{1}, 'usevec')
        if isempty(img.use), error('ERROR: img_scrub(), missing .use data!'); end
        mask = img.use == 0;
    else
        if isempty(img.scrub), error('ERROR: img_scrub(), missing .scrub data file!'); end
        mask = img.scrub(:, ismember(img.scrub_hdr, com));
    end
    if length(com) == 2
        doIt = com{2};
    else
        doIt = 'RM';
    end
else
    stype = com{1};
    doIt    = com{2};
    if isempty(img.fstats), error('ERROR: img_scrub(), missing .bstats data file!'); end

    if stype(1) == 'i' or stype(1) == 'u'
        ui = stype(1);
        dv = stype(2:end);
    else
        ui = [];
        dv = stype;
    end

    if strcmp(dv, 'mov')
        if isempty(img.mov), error('ERROR: img_scrub(), missing .mov/.dat data file!'); end
        fdt = str2num(com{3});
        if length(com) > 3, r = str2num(com{4}); end
        mask = evaluateMov(img.mov, r, fdt);
    else
        dvt  = str2num(com{3});
        mask = img.fstats(:, ismember(img.fstats_hdr, dv)) >= dvt;
        if ~isempty(ui)
            if isempty(img.mov), error('ERROR: img_scrub(), missing .mov/.dat data file!'); end
            if length(com) > 3, fdt = str2num(com{4}); end
            if length(com) > 4, fdt = str2num(com{5}); end
            mov = evaluateMov(img.mov, r, fdt);
            if ui == 'i'
                mask = mask == 1 | mov == 1;
            else
                mask = mask == 1 & mov == 1;
            end
        end
    end
end

if strcmp(doIt, 'NA')
    img.data = img.image2D;
    img.data(:, mask==1) = NaN;
else
    img = img.sliceframes(mask<1);
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

    nts = [];
    for n = s:e
        if n == 0, nts = [nts; ts]; end
        if n > 0
            nts = [nts; zeros(1, t) ts(1:end-t)];
        else
            nts = [nts; ts(1+n:end) zeros(1, n)];
        end
    end
    ts = sum(nts) > 0;


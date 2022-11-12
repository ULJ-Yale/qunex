function [] = general_image_overlap(af, bf, tf, v)

%``general_image_overlap(af, bf, tf, v)``
%
%   Function that prints the overlap of two images, one in red, another in
%   green.
%
%   Parameters:
%       --af (nimage | str):
%           Either a nimage object or the path to the first image file.
%
%       --bf (nimage | str):
%           Either a nimage object or the path to the second image file.
%
%       --tf (str):
%           The path to the file to save the overlap to.
%
%       --v (int, default 3):
%           Which slice to show (1, 2 or 3).
%
%   Notes:
%       The function saves a picture that shows the overlap of two images, the
%       data from the first file is shown in red, from the second in green. The
%       images are normalized to values from 0 to 1, where 0.5 is the mean, and
%       0 and 1 are the -/+ 3 standard deviations from the mean. In the
%       resulting image the overlap will be yellow.
%
%   Examples:
%       ::
%
%           qunex general_image_overlap \
%               --af=imga \
%               --bf=imgb \
%               --tf='atlas_subject_overlap.png'
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 4 || isempty(v), v = 3; end
if nargin < 3
        help imgOverlap;
        error('ERROR: At least three parameters are required!');
end

if isobject(af)
    a =    af;
else
    a = nimage(af);
end

if isobject(bf)
    b =    bf;
else
    b = nimage(bf);
end

am = a.img_slice_matrix(v);
bm = b.img_slice_matrix(v);

am = normalize(am);
bm = normalize(bm);

rgb = zeros([size(am) 3]);
rgb(:,:,1) = am;
rgb(:,:,2) = bm;

imwrite(rgb, tf);


function [im] = normalize(im)

    os = size(im);
    im = reshape(im, [], 1);
    m  = mean(im);
    s  = std(im);
    mv = m+3*s;
    im(im > mv) = mv;
    im(im < 0) = 0;
    im = im./mv;
    im = reshape(im, os);

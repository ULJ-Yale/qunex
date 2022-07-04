function [frames] = general_get_image_length(file)

%``general_get_image_length(file)``
%
%    Reads a regular image or a conc file and returns the number of frames in
%   each of the files.
%
%   INPUT
%    =====
%
%   -- file      A filename, a list of files or a conc file (see documentation
%                 for nimage object constructor).
%
%   OUTPUT
%    ======
%   
%     frames
%        A column vector of frame lengths of the files specified.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

img = nimage(file);
frames = img.runframes;

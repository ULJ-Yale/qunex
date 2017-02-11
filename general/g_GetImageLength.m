function [frames] = g_GetImageLength(file)

%function [frames] = g_GetImageLength(file)
%
%	Reads a regular image or a conc file and returns the number of frames in
%   each of the files.
%
%   Input
%       - file ... it can be a filename, a list of files, a conc file (see
%                  documentation for gmrimage object constructor).
%
%   Output
%       - frames ... A column vector of frame lengths of the files specified.
%
%   ---
%   Written by Grega Repovš 2008-07-11
%
%	Changelog
%       2017-02-11 Grega Repovš - Updated to work with any files gmrimage can handle
%

img = gmrimage(file);
frames = img.runframes;


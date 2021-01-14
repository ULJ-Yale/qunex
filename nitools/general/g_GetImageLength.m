function [frames] = g_GetImageLength(file)

%``function [frames] = g_GetImageLength(file)``
%
%	Reads a regular image or a conc file and returns the number of frames in
%   each of the files.
%
%   INPUT
%	=====
%
%   -- file 	 A filename, a list of files or a conc file (see documentation 
%				 for nimage object constructor).
%
%   OUTPUT
%	======
%   
% 	frames
%		A column vector of frame lengths of the files specified.
%

%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%
%   2008-07-11 Grega Repovš
%			   Initial version.
%	2017-02-11 Grega Repovš
%			   Updated to work with any files nimage can handle
%

img = nimage(file);
frames = img.runframes;


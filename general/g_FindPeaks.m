function [] = g_FindPeaks(fin, fout, mins, maxs, val, t, verbose)

%function [] = g_FindPeaks(fin, fout, mins, maxs, val, t, verbose)
%
%		Uses mri_FindPeaks method to define peak ROI using a watershed algorithm to grow regions from peaks.
%
%       fin         - input image
%		fout        - output image
%       mins        - minimal size of the resulting ROI  [0]
%       maxi        - maximum size of the resulting ROI  [inf]
%       val         - whether to find positive, negative or both ('n', 'p', 'b') [b]
%       t           - threshold value [0]
%       verbose     - whether to report the peaks (1) and be verbose about it (2) [1]
%
%    (c) Grega Repovs, 2015-04-11
%

%  ---- initializing

if nargin < 7, verbose = []; end
if nargin < 6, t       = []; end
if nargin < 5, val     = []; end
if nargin < 4, maxs    = []; end
if nargin < 3, mins    = []; end
if nargin < 2, error('ERROR: Please specify input and output file names.'); end


%  ---- read image and call FindPeaks

img = gmrimage(fin);
[roi peak] = img.mri_FindPeaks(mins, maxs, val, t, verbose > 1);


%  ---- process results

if strcmp(img.imageformat, '4dfp')
	center = img.hdr4dfp.value(find(ismember([img.hdr4dfp.key], 'center')));
	mmppix = img.hdr4dfp.value(find(ismember([img.hdr4dfp.key], 'mmppix')));

	center = sscanf(center{1}, '%f')';
	mmppix = sscanf(mmppix{1}, '%f')';

	for p = 1:length(peak)
		peak(p).xyz 			 = center .* [1 -1 -1] - peak(p).xyz 			  .* mmppix .* [1 -1 1] - mmppix/2 .* [1 1 -1] + img.dim .* mmppix .* [0 0 1];
		peak(p).Centroid 		 = center .* [1 -1 -1] - peak(p).Centroid         .* mmppix .* [1 -1 1] - mmppix/2 .* [1 1 -1] + img.dim .* mmppix .* [0 0 1];
		peak(p).WeightedCentroid = center .* [1 -1 -1] - peak(p).WeightedCentroid .* mmppix .* [1 -1 1] - mmppix/2 .* [1 1 -1] + img.dim .* mmppix .* [0 0 1];

		roi.hdr4dfp.key{end+1}   = 'region names';
		roi.hdr4dfp.value{end+1} = sprintf('%3d   %14s  %4d', p-1, sprintf('%.1f_%.1f_%.1f', peak(p).xyz), peak(p).size);
	end
end

%  --- print report

if verbose
	fprintf('\n\n---=== Peak report ===---');
	fprintf('\nlabel\tvalue\tvoxels\tpeak\tcentroid\twcentroid');
	for p = 1:length(peak)
    	% fprintf('\n%d\t%.1f\t%d\t%.1f %.1f %.1f\t%.1f %.1f %.1f\t%.1f %.1f %.1f', peak(p).label, peak(p).value, peak(p).size, peak(p).xyz, peak(p).Centroid, peak(p).WeightedCentroid);
    	fprintf('\n%d\t%.1f\t%d\t%.1f %.1f %.1f', peak(p).label, peak(p).value, peak(p).size, peak(p).xyz);
	end
	fprintf('\n\n');
end

roi.mri_saveimage(fout);

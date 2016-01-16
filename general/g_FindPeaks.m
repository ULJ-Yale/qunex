function [] = g_FindPeaks(fin, fout, mins, maxs, val, t, presmooth, verbose)

%function [] = g_FindPeaks(fin, fout, mins, maxs, val, t, verbose)
%
%		Uses mri_FindPeaks method to define peak ROI using a watershed algorithm to grow regions from peaks.
%
%       fin         - input image
%		fout        - output image
%       mins        - minimal size of the resulting ROI  [0]
%       maxs        - maximum size of the resulting ROI  [inf]
%       val         - whether to find positive, negative or both ('n', 'p', 'b') [b]
%       t           - threshold value [0]
%		presmooth   - the amount of smoothing to do before finding peaks
%       verbose     - whether to report the peaks (1) and be verbose about it (2) [1]
%
%    (c) Grega Repovs, 2015-04-11
%
%	 2016-01-16 Grega Repovs
%        - Added presmoothing option.
%		 - Added printing of report file.
%

%  ---- initializing

if nargin < 8 || isempty(verbose),   verbose   = 1    ; end
if nargin < 7 || isempty(presmooth), presmooth = 0    ; end
if nargin < 6 || isempty(t),         t         = 0    ; end
if nargin < 5 || isempty(val),       val       = 'b'  ; end
if nargin < 4 || isempty(maxs),      maxs      = inf  ; end
if nargin < 3 || isempty(mins),      mins      = 0    ; end
if nargin < 2, error('ERROR: Please specify input and output file names.'); end

%  ---- read image and call FindPeaks

img = gmrimage(fin);

if ~isempty(presmooth) && presmooth > 0
	if verbose == 2, fprintf('\n---> Presmoothing image [%.1f vx]', presmooth); end
	img = img.mri_Smooth3D(presmooth);
end

[roi peak] = img.mri_FindPeaks(mins, maxs, val, t, verbose > 1);

% shift one up to start from 2 (to make fidl happy)
roi.data = roi.data + 1;
roi.data(roi.data == 1) = 0;

%  --- print report

if verbose == 2, fprintf('\n---> Saving image'); end

rep = strrep(fout, '.4dfp', '');
rep = strrep(rep, '.ifh', '');
rep = strrep(rep, '.img', '');
rep = strrep(rep, '.nii', '');
rep = strrep(rep, '.gz', '');

repf = fopen([rep '.txt'], 'w');
fprintf(repf, '#source: %s', fin);
fprintf(repf, '\n#mins: %d, maxs: %s, val: ''%s'', t: %.1f, presmooth: %.1f', mins, maxs, val, t, presmooth);
fprintf(repf, '\n#label\tvalue\tvoxels\tpeak_x\tpeak_y\tpeak_z\tcentroid_x\tcentroid_y\tcentroid_z\twcentroid_x\twcentroid_y\twcentroid_z');

for p = 1:length(peak)
   	fprintf(repf, '\n%d\t%.1f\t%d', peak(p).label+1, peak(p).value, peak(p).size);
   	fprintf(repf, '\t%5.1f', [peak(p).xyz, peak(p).Centroid, peak(p).WeightedCentroid]);
   	if strcmp(img.imageformat, '4dfp')
		roi.hdr4dfp.key{end+1}   = 'region names';
		roi.hdr4dfp.value{end+1} = sprintf('%3d   %14s  %4d', peak(p).label-1, sprintf('%.1f_%.1f_%.1f', peak(p).xyz), peak(p).size);
	end
end

fclose(repf);

roi.mri_saveimage(fout);
if verbose == 2, fprintf('\n---> Done\n'); end
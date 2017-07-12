function [] = g_FindPeaks(fin, fout, mins, maxs, val, t, presmooth, projection, frames, verbose)

%function [] = g_FindPeaks(fin, fout, mins, maxs, val, t, presmooth, verbose)
%
%	Performs smoothing using mri_Smooth() method and the uses mri_FindPeaks
%   method to define peak ROI using a watershed algorithm to grow regions from peaks.
%
%   INPUT
%       fin         - input image
%		fout        - output image
%       mins        - [minimal size, minimal area] of the resulting ROI  [0, 0]
%       maxs        - [maximum size, maximum area] of the resulting ROI  [inf, inf]
%       val         - whether to find positive, negative or both peaks ('n', 'p', 'b') [b]
%       t           - threshold value [0]
%		presmooth   - data structure containing presmoothing parameters:
%                     presmooth.fwhm     ... Full Width at Half Maximum in voxels (NIfTI)
%                     presmooth.ftype    ... Type of smoothing filter, 'gaussian' or 'box' (NIfTI). ['gaussian']
%                     presmooth.ksize    ... Size of the smoothing kernel:
%                                            a) for NIfTI: voxels [6]
%                                            b) for CIFTI-2: [voxels mm^2] [6 6]
%                     presmooth.wb_path  ... path to wb_command
%                     presmooth.hcpatlas ... path to HCPATLAS folder containing projection surf.gii files
%                     * the last two fields are not required if they are stored as
%                     environment variables (wb_command in $PATH and hcpatlas in $HCPATLAS
%
%       projection  - type of surface component projection ('midthickness', 'inflated',...) ['midthickness']
%       frames      - list of frames to perform ROI operation on
%       verbose     - whether to be verbose:
%                           a) on the first level    (1)
%                           b) on all the sub-levels (2) [false]
%
%   USE
%   The function is a wrapper to the gmrimage.mri_FindPeaks method and is used
%   to read the image file of interest, save the resulting ROI file and report
%   the peak statistics (if requested). Please see the method documentation for
%   algorithm and specifics about the parameters.
%
%   The function also allows presmoothing, the presmooth parameter specifying
%   the amount of gaussian smoothing in voxels.
%
%   RESULTS
%   The script saves the resulting ROI file under the specified filename. The report statistics
%
%   EXAMPLE USE 1 (CIFTI-2 image)
%   To get a roi image of both positive and negative peak regions with miminum z
%   value of (-)3 and 72 contiguous voxels in size, but no larger than 300
%   voxels, after applying 1 voxel gaussian smoothing and a smoothing kernel of
%   size 7 voxels for volume structures and 9 mm^2 for surfaces structures use:
%
%   presmooth.fwhm = 1;
%   presmooth.ksize = [7 9];
%   g_FindPeaks('zscores.nii.gz', 'zscores_peaks_3_72_300.nii.gz', [72 80], [300 350], 'b', 3, presmooth, 'midthickness', [], 1);
%
%   EXAMPLE USE 2 (CIFTI-2 image)
%   To get a roi image of both positive and negative peak regions with miminum z
%   value of (-)3 and 72 contiguous voxels in size, but no larger than 300
%   voxels, after applying 3 voxel gaussian smoothing and a smoothing kernel of
%   size 7 voxels for volume structures and 9 mm^2 for surfaces structures,
%   where only frames 1, 6 and 7 are to be analyzed use:
%
%   presmooth.fwhm = 3; 
%   g_FindPeaks('zscores.dtseries.nii', 'zscores_analyzed.dtseries.nii', [72 80], [300 350], 'b', 1, presmooth, 'inflated', [1 5 7], 1);
%
%   EXAMPLE USE 3 (NIfTI image)
%   To get a roi image of both positive and negative peak regions with miminum z
%   value of (-)1 and 50 contiguous voxels in size, but no larger than 250
%   voxels, after applying 3 voxel gaussian smoothing and a smoothing kernel of
%   size 6 voxels use:
%
%   presmooth.fwhm = 3;
%   presmooth.ksize = 7;
%   presmooth.ftype = 'gaussian'
%   g_FindPeaks('zscores.nii.gz', 'zscores_analyzed.nii.gz', 50, 250, 'b', 1, presmooth, [], [], 2);
%
%   ---
%   Written by Grega Repovs, 2015-04-11
%
%   Changelog
%	2016-01-16 Grega Repovs
%        - Added presmoothing option.
%		 - Added printing of report file.
%
%   2017-03-04 Grega Repovs
%        - Updated documentation.
%
%   2017-07-10 Aleksij Kraljic
%        - Added functionality for CIFTI-2 files
%

%  ---- read image and call FindPeaks
img = gmrimage(fin);

% --- load CIFTI brain model data
load('CIFTI_BrainModel.mat')

%  ---- initializing
presmooth.request = true;
if nargin < 10 || isempty(verbose),   verbose   = false    ;       end
if nargin < 9 || isempty(frames),     frames = 1:img.frames;       end
if nargin < 8 || isempty(projection), projection = 'midthickness'; end
if nargin < 7 || isempty(presmooth),  presmooth.request = false;   end
if nargin < 6 || isempty(t),          t         = 0    ;           end
if nargin < 5 || isempty(val),        val       = 'b'  ;           end
if nargin < 4 || isempty(maxs),       maxs      = inf  ;           end
if nargin < 3 || isempty(mins),       mins      = 0    ;           end
if nargin < 2, error('ERROR: Please specify input and output file names.'); end

if ~isfield(presmooth,'ftype'),  presmooth.ftype = []; end
if ~isfield(presmooth,'ksize'), presmooth.ksize =[]; end
if ~isfield(presmooth,'wb_path'),  presmooth.wb_path = []; end
if ~isfield(presmooth,'hcpatlas'), presmooth.hcpatlas =[]; end

% increment verbose for compatibility with the mri_FindPeaks method 
verbose = verbose + 1;

if ~isempty(presmooth) && presmooth.request
	if verbose >= 2, fprintf('\n---> Presmoothing image'); end
    img = img.mri_Smooth(presmooth.fwhm, verbose, presmooth.ftype,...
        presmooth.ksize, projection, presmooth.wb_path, presmooth.hcpatlas);
end

[roi vol_peak peak] = img.mri_FindPeaks(mins, maxs, val, t, projection, frames, verbose);

% shift one up to start from 2 (to make fidl happy)
roi.data = roi.data + 1;
roi.data(roi.data == 1) = 0;

%  --- print report

if verbose >= 2, fprintf('\n---> Saving image'); end

if img.frames == 1
    rep = strrep(fout, '.4dfp', '');
    rep = strrep(rep, '.ifh', '');
    rep = strrep(rep, '.img', '');
    rep = strrep(rep, '.nii', '');
    rep = strrep(rep, '.gz', '');
    
    repf = fopen([rep '.txt'], 'w');
    fprintf(repf, '#source: %s', fin);
    fprintf(repf, '\n#mins: %d, maxs: %d, val: ''%s'', t: %.1f', mins, maxs, val, t);
    if numel(presmooth.ksize) == 1
        fprintf(repf, '\npresmooth.fwhm: %.1f, presmooth.ftype: %s, presmooth.ksize(1): %.1f',...
            presmooth.fwhm, presmooth.ftype, presmooth.ksize(1));
    elseif numel(presmooth.ksize) == 2
        fprintf(repf, '\npresmooth.fwhm: %.1f, presmooth.ftype: %s, presmooth.ksize voxels: %.1f, presmooth.ksize mm^2: %.1f',...
            presmooth.fwhm, presmooth.ftype, presmooth.ksize(1), presmooth.ksize(2));
    end
    
    fprintf(repf, '\n\nVolume Structures ROI Report:\n');
    fprintf(repf, '\n#label\tvalue\tvoxels\tpeak_x\tpeak_y\tpeak_z\tcentroid_x\tcentroid_y\tcentroid_z\twcentroid_x\twcentroid_y\twcentroid_z');
    for p = 1:length(vol_peak)
        fprintf(repf, '\n%d\t%.1f\t%d', vol_peak(p).label+1, vol_peak(p).value, vol_peak(p).size);
        fprintf(repf, '\t%5.1f', [vol_peak(p).xyz, vol_peak(p).Centroid, vol_peak(p).WeightedCentroid]);
        if strcmp(img.imageformat, '4dfp')
            roi.hdr4dfp.key{end+1}   = 'region names';
            roi.hdr4dfp.value{end+1} = sprintf('%3d   %14s  %4d', vol_peak(p).label-1, sprintf('%.1f_%.1f_%.1f', vol_peak(p).xyz), vol_peak(p).size);
        end
    end
    
    if strcmp(img.imageformat, 'CIFTI-2')
        fprintf(repf, '\n\nSurface Structures ROI Report:');
        for c = 1:length(img.cifti.shortnames)
            if strcmp(cifti.(lower(img.cifti.shortnames{c})).type,'Surface')
                fprintf(repf, '\n\n%0.0f) %s\n', c, lower(img.cifti.shortnames{c}));
                fprintf(repf, '\n#index\tvalue\tsize\tarea');
                for p = 1:length(peak.(lower(img.cifti.shortnames{c})))
                    fprintf(repf, '\n%d\t%.1f\t%d\t%f', peak.(lower(img.cifti.shortnames{c}))(p).index,...
                        peak.(lower(img.cifti.shortnames{c}))(p).value, peak.(lower(img.cifti.shortnames{c}))(p).size, peak.(lower(img.cifti.shortnames{c}))(p).area);
                end
            end
        end
    end
    fclose(repf);
    
elseif img.frames > 1
    rep = strrep(fout, '.4dfp', '');
    rep = strrep(rep, '.ifh', '');
    rep = strrep(rep, '.img', '');
    rep = strrep(rep, '.nii', '');
    rep = strrep(rep, '.gz', '');
    
    repf = fopen([rep '.txt'], 'w');
    fprintf(repf, '#source: %s', fin);
    fprintf(repf, '\n#mins: %d, maxs: %d, val: ''%s'', t: %.1f', mins, maxs, val, t);
    if numel(presmooth.ksize) == 1
        fprintf(repf, '\npresmooth.fwhm: %.1f, presmooth.ftype: %s, presmooth.ksize(1): %.1f',...
            presmooth.fwhm, presmooth.ftype, presmooth.ksize(1));
    elseif numel(presmooth.ksize) == 2
        fprintf(repf, '\npresmooth.fwhm: %.1f, presmooth.ftype: %s, presmooth.ksize voxels: %.1f, presmooth.ksize mm^2: %.1f',...
            presmooth.fwhm, presmooth.ftype, presmooth.ksize(1), presmooth.ksize(2));
    end
    
    for j=1:img.frames
        if ~isempty(peak{j}) && ~isempty(vol_peak{j})
            fprintf(repf, '\n\nFrame #%d:\n', j);
            fprintf(repf, '\nVolume Structures ROI Report:\n');
            fprintf(repf, '\n#label\tvalue\tvoxels\tpeak_x\tpeak_y\tpeak_z\tcentroid_x\tcentroid_y\tcentroid_z\twcentroid_x\twcentroid_y\twcentroid_z');
            for p = 1:length(vol_peak{j})
                fprintf(repf, '\n%d\t%.1f\t%d', vol_peak{j}(p).label+1, vol_peak{j}(p).value, vol_peak{j}(p).size);
                fprintf(repf, '\t%5.1f', [vol_peak{j}(p).xyz, vol_peak{j}(p).Centroid, vol_peak{j}(p).WeightedCentroid]);
                if strcmp(img.imageformat, '4dfp')
                    roi.hdr4dfp.key{end+1}   = 'region names';
                    roi.hdr4dfp.value{end+1} = sprintf('%3d   %14s  %4d', vol_peak{j}(p).label-1, sprintf('%.1f_%.1f_%.1f', vol_peak{j}(p).xyz), vol_peak{j}(p).size);
                end
            end
            
            if strcmp(img.imageformat, 'CIFTI-2')
                fprintf(repf, '\n\nSurface Structures ROI Report:');
                for c = 1:length(img.cifti.shortnames)
                    if strcmp(cifti.(lower(img.cifti.shortnames{c})).type,'Surface')
                        fprintf(repf, '\n\n%0.0f) %s\n', c, lower(img.cifti.shortnames{c}));
                        fprintf(repf, '\n#index\tvalue\tsize\tarea');
                        for p = 1:length(peak{j}.(lower(img.cifti.shortnames{c})))
                            fprintf(repf, '\n%d\t%.1f\t%d\t%f', peak{j}.(lower(img.cifti.shortnames{c}))(p).index,...
                                peak{j}.(lower(img.cifti.shortnames{c}))(p).value, peak{j}.(lower(img.cifti.shortnames{c}))(p).size,...
                                peak{j}.(lower(img.cifti.shortnames{c}))(p).area);
                        end
                    end
                end
            end
        end
        
    end
    fclose(repf);
end

roi.mri_saveimage(fout);
if verbose >= 2, fprintf('\n---> Done\n'); end
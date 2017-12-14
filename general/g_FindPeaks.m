function [] = g_FindPeaks(fin, fout, mins, maxs, val, t, presmooth, projection, options, verbose)

%function [] = g_FindPeaks(fin, fout, mins, maxs, val, t, presmooth, projection, options, verbose)
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
%       presmooth   - string containing presmoothing parameters: []
%                     Format -> 'fwhm:[VAL1 VAL2]|ftype:TYPE_NAME|ksize:[]|wb_path:PATH|hcpatlas:PATH'
%                     fwhm        ... full Width at Half Maximum in mm formatted as:
%                                   a) [fwhm for volume structure] for NIfTI [2]
%                                   b) [fwhm for volume structure, fwhm for surface structures] for CIFTI [2]
%                                       *(if only 1 element is passed, it takes that value for both, volume and surface structures)
%                     ftype    ... type of smoothing filter:
%                                   a) 'gaussian' or 'box' for NIfTI files ['gaussian']
%                                   b) '' (empty argument) for CIFTI files, since geodesic gaussian smoothing is the only option
%                     ksize    ... size of the smoothing kernel in voxels for NIfTI files, [] (empty) for CIFTI files [6]
%                     mask     ... specify the cifti mask to select areas on which to perform smoothing
%                     wb_path  ... path to wb_command
%                     hcpatlas ... path to HCPATLAS folder containing projection surf.gii files
%                     * the last two fields are not required if they are stored as
%                     environment variables (wb_command in $PATH and hcpatlas in $HCPATLAS
%                     ****************************************************************************************************
%                     Smoothing time series images with thresholded data should be performed for each frame separatelly,
%                     otherwise the smoothing will use the first frame as a smoothing mask for all the frames.
%                     (this issue will be solved in the future)
%                     ****************************************************************************************************
%       projection  - type of surface component projection ('midthickness', 'inflated',...)
%                          or a string containing the path to the surface files (.surf.gii)
%                          for both, left and right cortex separated by a pipe:
%                                a) for a default projection: 'type: midthickness' ['type: midthickness']
%                                b) for a specific projection:
%                                        'cortex_left: CL_projection.surf.gii|cortex_right: CR_projection.surf.gii'
%       options          - list of options separated with a pipe symbol ("|"):
%                                a) for the number of frames to be analized:
%                                           - []                        ... analyze only the first frame
%                                           - 'frames:[LIST OF FRAMES]' ... analyze the list of frames
%                                           - 'frames:all'              ... analyze all the frames
%                                b) for the type of ROI boundary:
%                                           - []                        ... boundary left unmodified
%                                           - 'boundary:remove'         ... remove the boundary regions
%                                           - 'boundary:highlight'      ... highlight boundaries with a value of -100
%                                           - 'boundary:wire'           ... remove ROI data and return only ROI boundaries
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
%   voxels, after smoothing with a kernel of fwhm 2 and kernel size 7 voxels use:
%
%   g_FindPeaks('zscores.nii.gz', 'zscores_peaks_3_72_300.nii.gz', [72 80], [300 350], 'b', 3, 'fwhm:2|ksize:7', '', [], 1);
%
%   EXAMPLE USE 2 (CIFTI-2 image)
%   To get a roi image of both positive and negative peak regions with miminum z
%   value of (-)3 and 72 contiguous voxels in size, but no larger than 300
%   voxels, after smoothing with a kernel of fwhm 3 for volume and
%   surfaces structures,
%   where only frames 1, 6 and 7 are to be analyzed use:
%
%   g_FindPeaks('zscores.dtseries.nii', 'zscores_analyzed.dtseries.nii',...
%               [72 80], [300 350], 'b', 1, 'fwhm:3', 'inflated', 'frames:[1 5 7]', 1);
%
%   EXAMPLE USE 3 (NIfTI image)
%   To get a roi image of both positive and negative peak regions with miminum z
%   value of (-)1 and 50 contiguous voxels in size, but no larger than 250
%   voxels, after applying fwhm 3 gaussian smoothing and a smoothing kernel of
%   size 6 voxels use:
%
%   presmooth = ;
%   g_FindPeaks('zscores.nii.gz', 'zscores_analyzed.nii.gz', 50, 250, 'b', 1,...
%               'fwhm:3|ksize:6|ftype:gaussian', [], [], 2);
%
%   EXAMPLE USE 4 (CIFTI-2 image)
%   To get a roi image of both positive and negative peak regions with miminum z
%   value of (-)3 and 72 contiguous voxels in size, but no larger than 300
%   voxels, after smoothing with a kernel of
%   fwhm 1:
%
%   g_FindPeaks('zscores.nii.gz', 'zscores_peaks_3_72_300.nii.gz', [72 80], [300 350],...
%               'b', 3, 'fwhm:1', 'cortex_left:CL_projection.surf.gii|cortex_right:CR_projection.surf.gii', [], 1);
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
%   2017-08-02 Aleksij Kraljic
%        - Fixed mistakes in the help menu and set default values for smoothing to 0
%

% --- read image and call FindPeaks
img = gmrimage(fin);

% --- load CIFTI brain model data
load('CIFTI_BrainModel.mat')

% --- initializing
%presmooth_request = true;
if nargin < 10 || isempty(verbose),   verbose   = false    ;                end
if nargin < 9 || isempty(options),    options = '';                         end
if nargin < 8 || isempty(projection), projection = 'type: midthickness';    end
if nargin < 7 || isempty(presmooth),  presmooth = [];                       end
if nargin < 6 || isempty(t),          t         = 0    ;                    end
if nargin < 5 || isempty(val),        val       = 'b'  ;                    end
if nargin < 4 || isempty(maxs),       maxs      = inf  ;                    end
if nargin < 3 || isempty(mins),       mins      = 0    ;                    end
if nargin < 2, error('ERROR: Please specify input and output file names.'); end

% --- increment verbose for compatibility with the mri_FindPeaks method
verbose = verbose + 1;

%if ~isempty(presmooth) && presmooth_request
if ~isempty(presmooth)
    presmooth = g_ParseOptions([],presmooth);
    if ~isfield(presmooth,'fwhm'),     presmooth.fwhm = [];    end
    if ~isfield(presmooth,'ftype'),    presmooth.ftype = [];   end
    if ~isfield(presmooth,'ksize'),    presmooth.ksize =[];    end
    if ~isfield(presmooth,'mask'),     presmooth.mask =[];     end
    if ~isfield(presmooth,'wb_path'),  presmooth.wb_path = []; end
    if ~isfield(presmooth,'hcpatlas'), presmooth.hcpatlas =[]; end
    if verbose >= 2, fprintf('\n---> Presmoothing image'); end
    img = img.mri_Smooth(presmooth.fwhm, verbose, presmooth.ftype,...
        presmooth.ksize, projection, presmooth.mask, presmooth.wb_path, presmooth.hcpatlas);
end

[roi vol_peak peak] = img.mri_FindPeaks(mins, maxs, val, t, projection, options, verbose);

% --- shift one up to start from 2 (to make fidl happy)
% roi.data = roi.data + 1;
% roi.data(roi.data == 1) = 0;

% --- print report

if verbose >= 2, fprintf('\n---> Saving image'); end

if img.frames == 1
    rep = strrep(fout, '.4dfp', '');
    rep = strrep(rep, '.ifh', '');
    rep = strrep(rep, '.img', '');
    rep = strrep(rep, '.nii', '');
    rep = strrep(rep, '.gz', '');
    
    repf = fopen([rep '.txt'], 'w');
    fprintf(repf, '#source: %s', fin);
    if numel(mins) == 1 && numel(maxs) == 1
        fprintf(repf, '\n#mins: %d, maxs: %d, val: ''%s'', t: %.1f', mins, maxs, val, t);
    elseif numel(mins) == 2 && numel(maxs) == 2
        fprintf(repf, '\n#mins: [%d %d], maxs: [%d %d], val: ''%s'', t: %.1f', mins(1), mins(2), maxs(1), maxs(2), val, t);
    elseif numel(mins) == 1 && numel(maxs) == 2
        fprintf(repf, '\n#mins: %d, maxs: [%d %d], val: ''%s'', t: %.1f', mins, maxs(1), maxs(2), val, t);
    elseif numel(mins) == 2 && numel(maxs) == 1
        fprintf(repf, '\n#mins: [%d %d], maxs: %d, val: ''%s'', t: %.1f', mins(1), mins(2), maxs, val, t);
    end
    if ~isempty(presmooth) && numel(presmooth.fwhm) == 1
        fprintf(repf, '\npresmooth.fwhm: %.1f, presmooth.ftype: %s, presmooth.ksize: %.1f',...
            presmooth.fwhm, presmooth.ftype, presmooth.ksize);
    elseif ~isempty(presmooth) && numel(presmooth.fwhm) == 2
        fprintf(repf, '\npresmooth.fwhm: [%.1f, %.1f], presmooth.ftype: %s, presmooth.ksize voxels: %.1f',...
            presmooth.fwhm(1), presmooth.fwhm(2), presmooth.ftype, presmooth.ksize);
    end
    
    fprintf(repf, '\n\nVolume Structures ROI Report:\n');
    fprintf(repf, '\n#label\tpeak_value\tavg_value\tvoxels\tpeak_x\tpeak_y\tpeak_z\tcentroid_x\tcentroid_y\tcentroid_z\twcentroid_x\twcentroid_y\twcentroid_z');
    for p = 1:length(vol_peak)
        fprintf(repf, '\n%d\t%.1f\t%.1f\t%d', vol_peak(p).label, vol_peak(p).value, vol_peak(p).averageValue, vol_peak(p).size);
        fprintf(repf, '\t%5.1f', [vol_peak(p).xyz, vol_peak(p).Centroid, vol_peak(p).WeightedCentroid]);
        if strcmp(img.imageformat, '4dfp')
            roi.hdr4dfp.key{end+1}   = 'region names';
            roi.hdr4dfp.value{end+1} = sprintf('%3d   %14s  %4d', vol_peak(p).label, sprintf('%.1f_%.1f_%.1f', vol_peak(p).xyz), vol_peak(p).size);
        end
    end
    
    if strcmp(img.imageformat, 'CIFTI-2')
        fprintf(repf, '\n\nSurface Structures ROI Report:');
        for c = 1:length(img.cifti.shortnames)
            if strcmp(cifti.(lower(img.cifti.shortnames{c})).type,'Surface')
                fprintf(repf, '\n\n%0.0f) %s\n', c, lower(img.cifti.shortnames{c}));
                fprintf(repf, '\n#index\tpeak_value\tavg_value\tsize\tarea_mm^2\tpeak_x\tpeak_y\tpeak_z');
                for p = 1:length(peak.(lower(img.cifti.shortnames{c})))
                    fprintf(repf, '\n%d\t%.1f\t%.3f\t%d\t%.3f\t%.3f\t%.3f\t%.3f', peak.(lower(img.cifti.shortnames{c}))(p).index,...
                        peak.(lower(img.cifti.shortnames{c}))(p).value, peak.(lower(img.cifti.shortnames{c}))(p).averageValue,...
                        peak.(lower(img.cifti.shortnames{c}))(p).size,...
                        peak.(lower(img.cifti.shortnames{c}))(p).area, peak.(lower(img.cifti.shortnames{c}))(p).x,...
                        peak.(lower(img.cifti.shortnames{c}))(p).y, peak.(lower(img.cifti.shortnames{c}))(p).z);
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
    if numel(mins) == 1 && numel(maxs) == 1
        fprintf(repf, '\n#mins: %d, maxs: %d, val: ''%s'', t: %.1f', mins, maxs, val, t);
    elseif numel(mins) == 2 && numel(maxs) == 2
        fprintf(repf, '\n#mins: [%d %d], maxs: [%d %d], val: ''%s'', t: %.1f', mins(1), mins(2), maxs(1), maxs(2), val, t);
    elseif numel(mins) == 1 && numel(maxs) == 2
        fprintf(repf, '\n#mins: %d, maxs: [%d %d], val: ''%s'', t: %.1f', mins, maxs(1), maxs(2), val, t);
    elseif numel(mins) == 2 && numel(maxs) == 1
        fprintf(repf, '\n#mins: [%d %d], maxs: %d, val: ''%s'', t: %.1f', mins(1), mins(2), maxs, val, t);
    end
    if ~isempty(presmooth) && numel(presmooth.fwhm) == 1
        fprintf(repf, '\npresmooth.fwhm: %.1f, presmooth.ftype: %s, presmooth.ksize: %.1f',...
            presmooth.fwhm, presmooth.ftype, presmooth.ksize);
    elseif ~isempty(presmooth) && numel(presmooth.fwhm) == 2
        fprintf(repf, '\npresmooth.fwhm: [%.1f, %.1f], presmooth.ftype: %s, presmooth.ksize voxels: %.1f',...
            presmooth.fwhm(1), presmooth.fwhm(2), presmooth.ftype, presmooth.ksize);
    end
    
    for j=1:img.frames
        
        if ~isempty(peak{j}) || ~isempty(vol_peak{j})
            fprintf(repf, '\n\nFrame #%d:\n', j);
        end
        
        if ~isempty(vol_peak{j})
            fprintf(repf, '\nVolume Structures ROI Report:\n');
            fprintf(repf, '\n#label\tpeak_value\tavg_value\tvoxels\tpeak_x\tpeak_y\tpeak_z\tcentroid_x\tcentroid_y\tcentroid_z\twcentroid_x\twcentroid_y\twcentroid_z');
            for p = 1:length(vol_peak{j})
                fprintf(repf, '\n%d\t%.1f\t%.1f\t%d', vol_peak{j}(p).label, vol_peak{j}(p).value, vol_peak{j}(p).averageValue, vol_peak{j}(p).size);
                fprintf(repf, '\t%5.1f', [vol_peak{j}(p).xyz, vol_peak{j}(p).Centroid, vol_peak{j}(p).WeightedCentroid]);
                if strcmp(img.imageformat, '4dfp')
                    roi.hdr4dfp.key{end+1}   = 'region names';
                    roi.hdr4dfp.value{end+1} = sprintf('%3d   %14s  %4d', vol_peak{j}(p).label, sprintf('%.1f_%.1f_%.1f', vol_peak{j}(p).xyz), vol_peak{j}(p).size);
                end
            end
        end
        
        if ~isempty(peak{j})
            if strcmp(img.imageformat, 'CIFTI-2')
                fprintf(repf, '\n\nSurface Structures ROI Report:');
                for c = 1:length(img.cifti.shortnames)
                    if strcmp(cifti.(lower(img.cifti.shortnames{c})).type,'Surface')
                        fprintf(repf, '\n\n%0.0f) %s\n', c, lower(img.cifti.shortnames{c}));
                        fprintf(repf, '\n#index\tpeak_value\tavg_value\tsize\tarea_mm^2)\tpeak_x\tpeak_y\tpeak_z');
                        for p = 1:length(peak{j}.(lower(img.cifti.shortnames{c})))
                            fprintf(repf, '\n%d\t%.1f\t%.3f\t%d\t%.3f\t%.3f\t%.3f\t%.3f', peak{j}.(lower(img.cifti.shortnames{c}))(p).index,...
                                peak{j}.(lower(img.cifti.shortnames{c}))(p).value,peak{j}.(lower(img.cifti.shortnames{c}))(p).averageValue,...
                                peak{j}.(lower(img.cifti.shortnames{c}))(p).size,...
                                peak{j}.(lower(img.cifti.shortnames{c}))(p).area,peak{j}.(lower(img.cifti.shortnames{c}))(p).x,...
                                peak{j}.(lower(img.cifti.shortnames{c}))(p).y,peak{j}.(lower(img.cifti.shortnames{c}))(p).z);
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

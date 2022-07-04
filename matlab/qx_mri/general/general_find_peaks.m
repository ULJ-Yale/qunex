function [] = general_find_peaks(fin, fout, mins, maxs, val, t, presmooth, projection, options, verbose)

%``general_find_peaks(fin, fout, mins, maxs, val, t, presmooth, projection, options, verbose)``
%
%   Performs smoothing using img_smooth() method and uses img_find_peaks method
%   to define peak ROI using a watershed algorithm to grow regions from peaks.
%
%   Parameters:
%       --fin (str | matrix | cell array | nimage):
%           Input image.
%       --fout (str):
%           Output filename.
%       --mins (vector, default [0, 0]):
%           [minimal size, minimal area] of the resulting ROI.
%       --maxs (vector, default [inf, inf]):
%           [maximum size, maximum area] of the resulting ROI.
%       --val (str, default 'b'):
%           Whether to find positive, negative or both peaks ('n', 'p', 'b').
%       --t (int, default 0):
%           Threshold value.
%       --presmooth (str, default []):
%           String containing presmoothing parameters:
%
%           String format::
%                   
%               'fwhm:[VAL1 VAL2]|ftype:TYPE_NAME|ksize:[]|wb_path:PATH|hcpatlas:PATH'
%
%           - fwhm
%               full Width at Half Maximum in mm formatted as:
%
%               - [fwhm for volume structure] for NIfTI [2]
%               - [fwhm for volume structure, fwhm for surface structures]
%                 for CIFTI [2]
%                 
%                 If only 1 element is passed, it takes that value for both,
%                 volume and surface structures.
%
%           - ftype
%               type of smoothing filter:
%
%               - 'gaussian' or 'box' for NIfTI files ['gaussian']
%               - '' (empty argument) for CIFTI files, since geodesic
%                 gaussian smoothing is the only option
%
%           - ksize
%               size of the smoothing kernel in voxels for NIfTI files, []
%               (empty) for CIFTI files [6]
%
%           - mask
%               specify the cifti mask to select areas on which to perform
%               smoothing
%
%           - wb_path
%               path to wb_command
%
%           - hcpatlas
%               path to HCPATLAS folder containing projection surf.gii files
%
%           - timeSeries
%               boolean to indicate whether a thresholded timeseries image
%               should use each frame as a mask for the corresponding frame.
%               By default [false], the first frame is taken a mask for all
%               the frames
%
%           - frames
%               list of frames to perform smoothing on [default = options.frames]
%
%           `wb_path` and `hcpatlas` are not required if they are stored as
%           environment variables (`wb_command` in `$PATH` and `hcpatlas` in
%           `$HCPATLAS`).
%
%       --projection (str, default 'type꞉ midthickness'):
%           Type of surface component projection ('midthickness', 'inflated',
%           ...) or a string containing the path to the surface files
%           (.surf.gii) for both, left and right cortex separated by a pipe:
%
%           - for a default projection: 'type: midthickness'
%           - for a specific projection:
%             'cortex_left: CL_projection.surf.gii|cortex_right: CR_projection.surf.gii'.
%
%           NOTE
%
%           The colon symbols used above to denote::
%
%               'type꞉ midthickness'
%
%           are of the Unicode modifier colon variety (U+A789) and are not
%           equivalent to the usual colon (U+003A) that should be used when
%           running the command. Copying the above line containing modifier
%           colons will result in an error - use normal colons with the command
%           instead.
%
%       --options (str, default ''):
%           List of options separated with a pipe symbol ("|"):
%
%           - frames
%               for the number of frames to be analized:
%
%               - []                        ... analyze only the first frame
%               - 'frames:[LIST OF FRAMES]' ... analyze the list of frames
%               - 'frames:all'              ... analyze all the frames
%
%           - boundary
%               for the type of ROI boundary:
%
%               - []                    ... boundary left unmodified
%               - 'boundary:remove'     ... remove the boundary regions
%               - 'boundary:highlight'  ... highlight boundaries with a value
%                 of -100
%               - 'boundary:wire'       ... remove ROI data and return only
%                 ROI boundaries
%
%           - parcels
%               whether to generate a .txt file reporting ROI
%               composition across CIFTI-2 volume structures and/or an
%               input atlas (output file name: <fin>_parcels.txt):
%
%               - []  ... no file is generated
%               - 'parcels:volume'  ... ROI composition across CIFTI-2
%                 volume structures
%               - 'parcels:<path to atlas>'  ... ROI composition across CIFTI-2
%                 volume structures and parcels of the input atlas (output file
%                 name: <fin>_parcels.txt)
%
%           - limitvol
%               whether to limit the growth of regions to subcortical
%               structures as defined in CIFTI-2 format (applies to
%               volume structures only):
%
%               - []  ... growth of regions is not limited
%               - 'limitvol:1'  ... growth of regions is limited to
%                 subcortical structures as defined in CIFTI-2 format
%                 (applies to volume structures only)
%               - 'limitvol:0'... growth of regions is not limited.
%
%       --verbose (int | bool, default false):
%           Whether to be verbose:
%
%           - 1     ... on the first level
%           - 2     ... on all the sub-levels
%           - false ... don't be verbose.
%
%   Output files:
%       The script saves the resulting ROI file under the specified filename.
%
%   Notes:
%       The function is a wrapper to the `nimage.img_find_peaks` method and
%       is used to read the image file of interest, save the resulting ROI
%       file and report the peak statistics (if requested). Please see the
%       method documentation for algorithm and specifics about the
%       parameters.
%
%       The function also allows presmoothing, the presmooth parameter
%       specifying the amount of gaussian smoothing in voxels.
%
%   Examples:
%       CIFTI-2 images:
%           To get a roi image of both positive and negative peak regions with
%           miminum z value of (-)3 and 72 contiguous voxels in size, but no
%           larger than 300 voxels, after smoothing with a kernel of fwhm 2 and
%           kernel size 7 voxels use::
%
%               qunex general_find_peaks \
%                   --fin='zscores.nii.gz' \
%                   --fout='zscores_peaks_3_72_300.nii.gz' \
%                   --mins='[72 80]' \
%                   --maxs='[300 350]' \
%                   --val='b' \
%                   --t=3 \
%                   --presmooth='fwhm:2|ksize:7' \
%                   --projection='' \
%                   --options='' \
%                   --verbose=1
%
%           To get a roi image of both positive and negative peak regions with
%           miminum z value of (-)3 and 72 contiguous voxels in size, but no
%           larger than 300 voxels, after smoothing with a kernel of fwhm 3 for
%           volume and surfaces structures, where only frames 1, 6 and 7 are to
%           be analyzed use::
%
%               qunex general_find_peaks \
%                   --fin='zscores.dtseries.nii' \
%                   --fout='zscores_analyzed.dtseries.nii' \
%                   --mins='[72 80]' \
%                   --maxs='[300 350]' \
%                   --val='b' \
%                   --t=1 \
%                   --presmooth='fwhm:3' \
%                   --projection='inflated' \
%                   --options='frames:[1 5 7]' \
%                   --verbose=1
%
%           To get a roi image of both positive and negative peak regions with
%           miminum z value of (-)3 and 72 contiguous voxels in size, but no
%           larger than 300 voxels, after smoothing with a kernel of fwhm 1 use::
%
%               qunex general_find_peaks \
%                   --fin='zscores.nii.gz' \
%                   --fout='zscores_peaks_3_72_300.nii.gz' \
%                   --mins='[72 80]' \
%                   --maxs='[300 350]' \
%                   --val='b' \
%                   --t=3 \
%                   --presmooth='fwhm:1' \
%                   --projection='cortex_left:CL_projection.surf.gii|cortex_right:CR_projection.surf.gii' \
%                   --options='' \
%                   --verbose=1
%
%       NIfTI image:
%           To get a roi image of both positive and negative peak regions with
%           miminum z value of (-)1 and 50 contiguous voxels in size, but no
%           larger than 250 voxels, after applying fwhm 3 gaussian smoothing and
%           a smoothing kernel of size 6 voxels use ``presmooth=''``.
%
%           ::
%
%               qunex general_find_peaks \
%                   --fin='zscores.nii.gz' \
%                   --fout='zscores_analyzed.nii.gz' \
%                   --mins=50 \
%                   --maxs=250 \
%                   --val='b' \
%                   --t=1 \
%                   --presmooth='fwhm:3|ksize:6|ftype:gaussian' \
%                   --projection='' \
%                   --options='' \
%                   --verbose=2
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

% --- read image and call FindPeaks
img = nimage(fin);

% --- load CIFTI brain model data
load('cifti_brainmodel');

% --- initializing
if nargin < 10 || isempty(verbose),   verbose   = false    ;                end
if nargin < 9 || isempty(options),    options = '';                         end
if nargin < 8 || isempty(projection), projection = 'type: midthickness';    end
if nargin < 7 || isempty(presmooth),  presmooth = [];                       end
if nargin < 6 || isempty(t),          t         = 0    ;                    end
if nargin < 5 || isempty(val),        val       = 'b'  ;                    end
if nargin < 4 || isempty(maxs),       maxs      = inf  ;                    end
if nargin < 3 || isempty(mins),       mins      = 0    ;                    end
if nargin < 2, error('ERROR: Please specify input and output file names.'); end

% --- increment verbose for compatibility with the img_find_peaks method
verbose = verbose + 1;

frames = [];
parcels = [];
if ~isempty(options)
    opt = general_parse_options([],options);
    if isfield(opt,'frames')
        frames = opt.frames;
    end
    if isfield(opt,'parcels')
        parcels = opt.parcels;
    end
end
   
if ~isempty(presmooth)
    presmooth = general_parse_options([],presmooth);
    if ~isfield(presmooth,'fwhm'),       presmooth.fwhm = [];        end
    if ~isfield(presmooth,'ftype'),      presmooth.ftype = [];       end
    if ~isfield(presmooth,'ksize'),      presmooth.ksize =[];        end
    if ~isfield(presmooth,'mask'),       presmooth.mask =[];         end
    if ~isfield(presmooth,'wb_path'),    presmooth.wb_path = [];     end
    if ~isfield(presmooth,'hcpatlas'),   presmooth.hcpatlas =[];     end
    if ~isfield(presmooth,'timeSeries'), presmooth.timeSeries =[];   end
    if ~isfield(presmooth,'frames'),     presmooth.frames = frames;  end
    if verbose >= 2, fprintf('\n---> Presmoothing image'); end
    img = img.img_smooth(presmooth.fwhm, verbose, presmooth.ftype,...
        presmooth.ksize, projection, presmooth.mask, presmooth.wb_path,...
        presmooth.hcpatlas, presmooth.timeSeries, presmooth.frames);
end

[roi, vol_peak, peak] = img.img_find_peaks(mins, maxs, val, t, projection, options, verbose);

% input parameter data structure
fp_params.mins = mins;
fp_params.maxs = maxs;
fp_params.val = val;
fp_params.t = t;
fp_params.projections = projection;
fp_params.options = options;
fp_params.verbose = verbose;

% --- shift one up to start from 2 (to make fidl happy)
% roi.data = roi.data + 1;
% roi.data(roi.data == 1) = 0;

if verbose >= 2, fprintf('\n---> Saving image'); end

printReport(img, fin, fout, peak, vol_peak, fp_params, presmooth, cifti)

roi.img_saveimage(fout);

if ~isempty(parcels)
    if strcmpi(parcels,'volume')
        general_get_roi_parcels(fout, []);
    else
        general_get_roi_parcels(fout, [], parcels);
    end
end

if verbose >= 2, fprintf('\n---> Done\n'); end

end

function printReport(img, fin, fout, peak, vol_peak, fp_params, presmooth, cifti)
mins = fp_params.mins;
maxs = fp_params.maxs;
val = fp_params.val;
t = fp_params.t;
projection = fp_params.projections;
options = fp_params.options;
verbose = fp_params.verbose;

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

if ~isempty(presmooth) && isempty(presmooth.ftype)
    if ~isempty(presmooth) && numel(presmooth.fwhm) == 1
        fprintf(repf, '\npresmooth.fwhm: %.1f',...
            presmooth.fwhm);
    elseif ~isempty(presmooth) && numel(presmooth.fwhm) == 2
        fprintf(repf, '\npresmooth.fwhm: [%.1f, %.1f]',...
            presmooth.fwhm(1), presmooth.fwhm(2));
    end
elseif ~isempty(presmooth)
    if ~isempty(presmooth) && numel(presmooth.fwhm) == 1
        fprintf(repf, '\npresmooth.fwhm: %.1f, presmooth.ftype: %s, presmooth.ksize: %.1f',...
            presmooth.fwhm, presmooth.ftype, presmooth.ksize);
    elseif ~isempty(presmooth) && numel(presmooth.fwhm) == 2
        fprintf(repf, '\npresmooth.fwhm: [%.1f, %.1f], presmooth.ftype: %s, presmooth.ksize: %.1f',...
            presmooth.fwhm(1), presmooth.fwhm(2), presmooth.ftype, presmooth.ksize);
    end
end

if img.frames == 1
    peakCell{1} = peak;
    vol_peakCell{1} = vol_peak;
else
    peakCell = peak;
    vol_peakCell = vol_peak;
end

for j=1:img.frames
    
    if ~isempty(peakCell{j}) || ~isempty(vol_peakCell{j})
        if img.frames > 1
            fprintf(repf, '\n\nFrame #%d:\n', j);
        else
            fprintf(repf, '\n');
        end
        fprintf(repf,...
        ['\nComponent\tLabel\tPeak_value\tAvg_value\tSize\tArea_mm2\tGrayord\tPeak_x',...
        '\tPeak_y\tPeak_z\tCentroid_x\tCentroid_y\tCentroid_z\tWcentroid_x',...
        '\tWcentroid_y\tWcentroid_z']);
    end
    
    if ~isempty(vol_peakCell{j})
        for p = 1:length(vol_peakCell{j})
            if strcmpi(img.imageformat, 'CIFTI-2')
                fprintf(repf, '\n%s\t%d\t%.1f\t%.1f\t%d\tNA\t%d',...
                    vol_peakCell{j}(p).component, vol_peakCell{j}(p).label, vol_peakCell{j}(p).value, vol_peakCell{j}(p).averageValue, vol_peakCell{j}(p).size, vol_peakCell{j}(p).grayord);
            else
                fprintf(repf, '\n%s\t%d\t%.1f\t%.1f\t%d\tNA\tNA',...
                    vol_peakCell{j}(p).component, vol_peakCell{j}(p).label, vol_peakCell{j}(p).value, vol_peakCell{j}(p).averageValue, vol_peakCell{j}(p).size);
            end
            fprintf(repf, '\t%5.1f', [vol_peakCell{j}(p).xyz, vol_peakCell{j}(p).Centroid, vol_peakCell{j}(p).WeightedCentroid]);
            if strcmp(img.imageformat, '4dfp')
                roi.hdr4dfp.key{end+1}   = 'region names';
                roi.hdr4dfp.value{end+1} = sprintf('%3d   %14s  %4d',...
                    vol_peakCell{j}(p).label, sprintf('%.1f_%.1f_%.1f', vol_peakCell{j}(p).xyz), vol_peakCell{j}(p).size);
            end
        end
    end
    
    if ~isempty(peakCell{j})
        if strcmp(img.imageformat, 'CIFTI-2')
            for c = 1:length(img.cifti.shortnames)
                if strcmp(cifti.(lower(img.cifti.shortnames{c})).type,'Surface')
                    for p = 1:length(peakCell{j}.(lower(img.cifti.shortnames{c})))
                        fprintf(repf, '\n%s\t%d\t%.1f\t%.3f\t%d\t%.3f\t%d\t%.3f\t%.3f\t%.3f\tNA\tNA\tNA\tNA\tNA\tNA',...
                            lower(img.cifti.shortnames{c}), peakCell{j}.(lower(img.cifti.shortnames{c}))(p).index,...
                            peakCell{j}.(lower(img.cifti.shortnames{c}))(p).value,peakCell{j}.(lower(img.cifti.shortnames{c}))(p).averageValue,...
                            peakCell{j}.(lower(img.cifti.shortnames{c}))(p).size,...
                            peakCell{j}.(lower(img.cifti.shortnames{c}))(p).area,...
                            peakCell{j}.(lower(img.cifti.shortnames{c}))(p).grayord,...
                            peakCell{j}.(lower(img.cifti.shortnames{c}))(p).x,...
                            peakCell{j}.(lower(img.cifti.shortnames{c}))(p).y,peakCell{j}.(lower(img.cifti.shortnames{c}))(p).z);
                    end
                end
            end
        end
    end
end
fclose(repf);
end

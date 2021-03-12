function img = img_smooth(img, fwhm,  verbose, ftype, ksize, projection, mask, wb_path, hcpatlas, timeSeries, frames)

%``function img = img_smooth(img, fwhm,  verbose, ftype, ksize, projection, mask, wb_path, hcpatlas, timeSeries, frames)``
%
%   Does geodesic gaussian kernel smoothing of the gmri image.
%
%   INPUTS
%   ======
%
%   --img         a nimage object with data in volume representation.
%   --fwhm        Full Width at Half Maximum in mm formatted as:
%
%                 a) [fwhm for volume structure] for NIfTI [2]
%                 b) [fwhm for volume structure, fwhm for surface structures] 
%                    for CIFTI [2]
%
%                 If only 1 element is passed, it takes that value for both, 
%                 volume and surface structures.
%
%   --verbose     whether to report the progress. [false]
%   --ftype       type of smoothing filter:
%
%                 a) 'gaussian' or 'box' for NIfTI files ['gaussian']
%                 b) '' (empty argument) for CIFTI files, since geodesic 
%                    gaussian smoothing is the only option
%
%   --ksize       size of the smoothing kernel in voxels for NIfTI files, 
%                 [] (empty) for CIFTI files [6]
%   --projection  type of surface component projection ('midthickness', 
%                 'inflated', ...) or a string containing the path to the 
%                 surface files (.surf.gii) for both, left and right cortex 
%                 separated by a pipe:
%
%                 a) for a default projection: 'type: midthickness' 
%                    ['type:midthickness']
%                 b) for a specific projection:
%                    'cortex_left: CL_projection.surf.gii|cortex_right: CR_projection.surf.gii'
%
%   --mask        specify the cifti mask to select areas on which to perform 
%                 smoothing, if you don't want to use the mask set to 'no', 
%                 otherwise the default mask is the same as the input file
%   --wb_path     path to wb_command ['/Applications/workbench/bin_macosx64']
%   --hcpatlas    path to HCPATLAS folder containing projection surf.gii files
%   --timeSeries  boolean to indicate whether a thresholded timeseries image 
%                 should use each frame as a mask for the corresponding frame. 
%                 By default [false], the first frame is taken a mask for all 
%                 the frames.
%   --frames      list of frames to perform smoothing on [1]
%
%
%   OUTPUT
%   ======
%
%   img
%       image with data smoothed
%
%   NOTE
%   ====
%
%   Smoothing time series images with thresholded data should be performed for
%   each frame separatelly, otherwise the smoothing will use the first frame as
%   a smoothing mask for all the frames. (this issue will be solved in the
%   future)
%
%   USE
%   ===
%
%   The method enables smoothing of MR data (NIfTI or CIFTI). The smoothing is
%   specified in voxels for volume structures and mm^2 for surface structures
%   smoothing. The default smoothing kernel for volume structures is 'gaussian'
%   with kernel size 7. For surface structure it is required to specify the type
%   of the projection ('midthickness', 'inflated',...). If PATH environment
%   variable is not saved in the system, it is required to pass the path to the
%   wb_command with the wb_path input argument. The path to the directory
%   containing surface (surf.gii) files should be stored in the HCPATLAS
%   environment variable, otherwise, the path to surface files should be passed
%   with the hcpatlas input argument. In case the file contains multiple frames,
%   all of the frames undergo smoothing.
%
%   EXAMPLE (CIFTI image)
%   =====================
%
%   ::
%
%       img_smooth = img.img_smooth([7 9], false, [], [], 'midthickness');
%
%   EXAMPLE (NIfTI image)
%   =====================
%
%   ::
%
%       img_smooth = img.img_smooth(3, true, 'gaussian', 8);
%

% input checking
if nargin < 11 || isempty(frames),     frames = 1; warn = 1;             end
if nargin < 10 || isempty(timeSeries), timeSeries = false;               end
if nargin < 9  || isempty(hcpatlas),   hcpatlas = getenv('HCPATLAS');    end
if nargin < 8  || isempty(wb_path),    wb_path = '';                     end
if nargin < 7  || isempty(mask),       mask = '';                        end
if nargin < 6  || isempty(projection), projection = 'type:midthickness'; end
if nargin < 5  || isempty(ksize),      ksize = 6;                        end
if nargin < 4  || isempty(ftype),      ftype = 'gaussian';               end
if nargin < 3  || isempty(verbose),    verbose = false;                  end
if nargin < 2  || isempty(fwhm),       fwhm = 2;                         end
if numel(fwhm) == 1,                   fwhm = [fwhm, fwhm];              end

if img.frames > 1 && timeSeries == true
    if warn
        warning(['img_smooth(): image contains multiple frames and ',...
            'options->frames was not specified. As a result, only the ',...
            'first frame will be processed.']);
    end
    % if more than 1 frame, perform img_smooth() on each frame recursivelly
    fprintf('\nMore than 1 frame detected!\n');
    img_temp = img;
    img_temp.data = zeros(size(img_temp.data));
    img_smooth = img;
    for fr = frames
        img_temp.data(:,1) = img.data(:,fr);
        img_temp.data(:,fr) = img.data(:,fr);
        fprintf('-> Smoothing Frame #%d\n',fr);
        img_temp = ...
            img_temp.img_smooth(fwhm,  verbose, ftype, ksize, projection, mask, wb_path, hcpatlas, false);
        img_smooth.data(:,fr) = img_temp.data(:,fr);
    end
    img = img_smooth;
    return;
end

% take the absolute value of the mask, if it was passed
if  isempty(mask)
    mask_img = img;
    mask_img.data = abs(mask_img.data);
    img_save_nifti(mask_img,'mask_tmp.dscalar.nii');
    mask = 'mask_tmp.dscalar.nii';
elseif strcmp(lower(mask),'no')
    mask = '';
else
    mask_img = nimage(mask);
    mask_img.data = abs(mask_img.data);
    img_save_nifti(mask_img,'mask_tmp.dscalar.nii');
    mask = 'mask_tmp.dscalar.nii';
end

% check file type [NIfTI or CIFTI]
if strcmpi(img.imageformat, 'CIFTI-2')
    opt.fwhm = fwhm;
    opt.framework_path = [];
    opt.wb_command_path = wb_path;
    opt.omp_threads = [];
    
    
    projection = general_parse_options([],projection);
    % --- assign proper projection type format
    if isfield(projection,'cortex_left') && isfield(projection,'cortex_right')
        surfaceFile.lsurf = projection.cortex_left;
        surfaceFile.rsurf = projection.cortex_right;
    else
        % load surface files
        surfaceFile.lsurf = strcat(hcpatlas,'/Q1-Q6_R440.L.',projection.type,'.32k_fs_LR.surf.gii');
        surfaceFile.rsurf = strcat(hcpatlas,'/Q1-Q6_R440.R.',projection.type,'.32k_fs_LR.surf.gii');
    end
    
    % create temporary wb_command input file
    inFile = strcat('temp_',date,'_inFile.dscalar.nii');
    img_save_nifti(img, inFile);
    
    % create temporary wb_command output file
    outFile = strcat('temp_',date,'_outFile.dscalar.nii');
    
    % smooth the CIFTI model using wb_command
    wbSmooth(inFile, outFile, surfaceFile, mask, opt);
    if ~isempty(mask)
        delete('mask_tmp.dscalar.nii');
    end
    
    % save the temporary output file
    img = nimage(outFile);
    
    % delete both input and output temporary files
    delete '*File.dscalar.nii';
elseif strcmpi(img.imageformat, 'NIFTI')
    % smooth the entire volume structure with img_smooth_3d() method
    img = img.img_smooth_3d(fwhm(1), verbose, ftype, ksize);
end

end

% --- SUPPORT FUNCTIONS

function [] = wbSmooth(sfile, tfile, file, mask, options)

% --- convert FWHM to sd

options.surface_smooth  = options.fwhm(2) / (2*sqrt(2*log(2)));
options.volume_smooth  = options.fwhm(1) / (2*sqrt(2*log(2)));

fprintf('\n---> running wb_command -cifti-smoothing');

if ~isempty(options.framework_path)
    if strcmp(options.framework_path, 'NULL')
        setenv('LD_LIBRARY_PATH');
        setenv('DYLD_LIBRARY_PATH');
        setenv('DYLD_FRAMEWORK_PATH');
    else
        if isempty(strfind(s, options.framework_path))
            fprintf('\n     ... setting DYDL_FRAMEWORK_PATH to %s', options.framework_path);
            setenv('DYLD_FRAMEWORK_PATH');
        end
        if isempty(strfind(sl, options.framework_path))
            fprintf('\n     ... setting DYLD_LIBRARY_PATH to %s', options.framework_path);
            setenv('DYLD_LIBRARY_PATH', [options.framework_path ':' sl]);
        end
        if isempty(strfind(ll, options.framework_path))
            fprintf('\n     ... setting LD_LIBRARY_PATH to %s', options.framework_path);
            setenv('LD_LIBRARY_PATH', [options.framework_path ':' ll]);
        end
    end
end

if ~isempty(options.wb_command_path)
    s = getenv('PATH');
    if isempty(strfind(s, options.wb_command_path))
        fprintf('\n     ... setting PATH to %s', options.wb_command_path);
        setenv('PATH', [options.wb_command_path ':' s]);
    end
end

if options.omp_threads > 0
    setenv('OMP_NUM_THREADS', num2str(options.omp_threads));
end

roi_smooth = '';
if ~isempty(mask)
    roi_smooth = ['-cifti-roi ' mask];
end

fprintf('\n     ... smoothing');
comm = sprintf('wb_command -cifti-smoothing %s %f %f COLUMN %s -left-surface %s -right-surface %s %s', sfile, options.surface_smooth, options.volume_smooth, tfile, file.lsurf, file.rsurf, roi_smooth);
[status out] = system(comm);

if status
    fprintf('\nERROR: wb_command finished with error!\n       ran: %s\n', comm);
    fprintf('\n --- wb_command output ---\n%s\n --- end wb_command output ---\n', out);
    error('\nAborting processing!');
else
    fprintf(' ... done!\n');
end
end

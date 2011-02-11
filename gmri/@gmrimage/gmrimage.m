classdef gmrimage
% 
%  gmrimage class
%  
%  gmrimage class offers an object to store MR image data.
%  It provides basic methods for loading and saving image,
%  methods for returning different representations of the image,
%  methods for extracting data and manipulating image, and
%  methods for performing basic math with the images.
%
%  Methods:
%  
%  gmrimage           - constructor / loader
%  mri_readimage      - reads an image file
%  mri_saveimage      - saves an image file
%  mri_saveimageframe - saves only the specified frame(s) of an image file
%  image2D            - returns 2D (voxels by frames) representation of image data
%  image4D            - returns 4D (x by y by z by frames representation of image data)
%  maskimg            - trims data from all nonzero voxels of the mask
%  unmaskimg          - restores the full volume from masked image with zeros for missing voxels
%  standardize        - transforms values to z scores within each voxel's timeseries
%  correlize          - standardizes and divides by sqrt(N-1) to prepare for efficient correlation computation
%
%  mri_ComputeCorrelations - computes correlations with the provided data matrix
%
%  Created by Grega Repovš, 2009-10-04
%  Last modification by Grega Repovsš, 2010-03-18
%

    properties
        data
        imageformat
        mformat
        hdrnifti        = [];
        hdr4dfp         = [];
        dim
        voxels
        vsizes
        TR
        frames
        runframes       = [];
        filename        = [];
        rootfilename    = [];
        mask            = [];
        masked          = false;
        empty           = true;
        standardized    = false;
        correlized      = false;
        info            = [];
        roi             = [];
    end
    
    methods(Static = true)
        %ifh = mri_ReadIFH(file)
        files = mri_ReadConcFile(file)
        roi   = mri_ReadROI(roiinfo, roif2)
    end
    
    methods
        output = mri_Smooth3D(obj, fwhm, verbose)
        output = mri_Smooth3DMasked(obj, mask, fwhm, limit, verbose)
    end
    
    methods
        function obj = gmrimage(filename, dtype, frames)
        % 
        %  Class constructor, calls readimage function if a parameter is passed
        %
            if nargin < 4
                frames = [];
                if nargin < 3
                    dtype = 'single';
                end
            end
            
            % obj = gmrimage();
            if nargin > 0
               if isa(filename, 'char')
                    obj = obj.mri_readimage(filename, dtype, frames);
                end
            end        
        end
    
        function obj = mri_readimage(obj, filename, dtype, frames)
        %
        %  Checks what type the image is and calls the appropriate function
        %
            if nargin < 4
                frames = [];
                if nargin < 3
                    dtype = 'single';
                end
            end
        
            if strcmp(filename(length(filename)-8:end), '.4dfp.img') | strcmp(filename(length(filename)-4:end), '.conc')
                obj = obj.mri_Read4DFP(filename, dtype, frames);
                obj.empty = false;
            elseif strcmp(filename(length(filename)-3:end), '.nii') | strcmp(filename(length(filename)-6:end), '.nii.gz') | strcmp(filename(length(filename)-3:end), '.hdr')
                obj = obj.mri_ReadNIfTI(filename, dtype, frames);
                obj.empty = false;
            elseif strcmp(filename(length(filename)-4:end), '.conc')
                obj = obj.mri_ReadConcImage(filename, dtype, frames);
                obj.empty = false;
            else
                error('ERROR: Unknown file format!');
                obj = gmrimage();
            end
        end
        
        function mri_saveimage(obj, filename)
        %
        %  Save image based on the existing header data
        %
            if nargin < 2
                filename = obj.filename;
            end
        
            switch obj.imageformat
                case '4dfp'
                    obj.mri_Save4DFP(filename);
                case 'NIfTI'
                    obj.mri_SaveNIfTI(filename);
            end
        end
        
        function mri_saveimageframe(obj, frame, filename)
        %
        %  Save image based on the existing header data, it only saves the specified frames.
        %  
        %
            if nargin < 3
                filename = obj.filename;
            end
            
            obj.data   = obj.image2D;
            obj.data   = obj.data(:,frame);
            obj.frames = size(obj.data,2);
            
            mri_saveimage(obj, filename);
        end
        
        
        function image2D = image2D(obj)
        %
        %  Returns a 2D volume by frames representation of the image
        %
            image2D = reshape(obj.data, obj.voxels, []);
            
        end
        
        function image4D = image4D(obj)
        %
        %  Returns a 4D x by y by z by frames representation of the image
        %
            image4D = reshape(obj.data, [obj.dim obj.frames]);
            
        end
        
        function obj = maskimg(obj, mask)
        %
        %  Applies a mask so that all non 0 voxels are eliminated
        %
        
            if isa(mask, 'gmrimage')
                mask = mask.image2D;
            end
            if length(mask) ~= obj.voxels
                error('ERROR: mask is not the same size as target image!');
            end
            obj.data = obj.image2D;
            obj.mask = mask ~= 0;
            obj.data = obj.data(obj.mask,:);
            obj.masked = true;
            obj.voxels = size(obj.data,1);
        end
        
        function obj = unmaskimg(obj)
        %
        %  Puts image back into the original size by setting all the unmasked voxels to 0
        %
        
            if obj.masked
                unmasked = zeros([prod(obj.dim) obj.frames]);
                unmasked(obj.mask,:) = obj.data;
                obj.data = unmasked;
                obj.masked = false;
                obj.voxels = size(obj.data,1);
            else
                obj = obj;
            end
        end 
        
        function obj = standardize(obj)
        %
        %  Creates an standardized timeseries (usinh n-1)
        %        
            obj.data = zscore(obj.image2D, 0, 2);
            obj.standardized = true;
        end
        
        function obj = correlize(obj)
        %
        %  Creates a matrix ready for quick computation of correlations (standardized and divided by sqrt(n-1))
        %
            obj = obj.standardize ./ sqrt(obj.frames -1);
            obj.correlized = true;
        end
                
        function obj = times(obj, times)
            if isa(times, 'gmrimage')
                times = times.image2D;
            end
            obj.data = times(obj.image2D, times);
        end
        
        function obj = mtimes(obj, times)
            if isa(times, 'gmrimage')
                times = times.image2D;
            end
            obj.data = mtimes(obj.image2D, times);
        end
        
        function obj = mrdivide(obj, times)
            if isa(times, 'gmrimage')
                times = times.image2D;
            end
            obj.data = mrdivide(obj.image2D, times);
        end
        
        function obj = rdivide(obj, times)
            if isa(times, 'gmrimage')
                times = times.image2D;
            end
            obj.data = rdivide(obj.image2D, times);
        end
        
        function obj = plus(obj, B)
            if isa(B, 'gmrimage')
                B = B.image2D;
            end
            obj.data = plus(obj.image2D, B);
        end
        
        function obj = minus(obj, B)
            if isa(B, 'gmrimage')
                B = B.image2D;
            end
            obj.data = minus(obj.image2D, B);
        end
        
        function obj = eq(obj, B)
            if isa(B, 'gmrimage')
                B = B.image2D;
            end
            obj.data = eq(obj.image2D, B);
        end
        
        function obj = ismember(obj, B)
            obj.data = ismember(obj.image2D, B);
        end
        
        function obj = horzcat(obj, add)
            obj.data = [obj.image2D add.image2D];
            obj.frames = obj.frames + add.frames;
            obj.runframes = [obj.runframes add.frames];
        end
        
        function reply = isempty(obj)
            reply = obj.empty;
        end
        
        function reply = issize(obj, dim)
            if isa(dim, 'gmrimage')
                dim = dim.dim;
            end
            if obj.dim == dim
                reply = true;
            else
                reply = false;
            end
        end
        
        function obj = zeroframes(obj, frames)
            obj.data = zeros(obj.voxels, frames);
            obj.frames = frames;
            obj.runframes = frames;
        end
        
        function obj = sliceframes(obj, fmask, options)
            if nargin < 3
                options = [];
                if nargin < 2
                    fmask = [];
                end
            end
                        
            % --- if fmask is a scalar, remove passed number of frames from start of image or each run
            
            if length(fmask) == 1
                l = fmask;
                fmask = ones(1, obj.frames);
                if strcmp(options, 'perrun') && length(obj.runframes > 1)
                    off = 1;
                    for r = 1:length(obj.runframes)
                        fmask(off:off+l-1) = 0;
                        off = off + obj.runframes(r);
                        obj.runframes(r) = obj.runframes(r) - l;
                    end
                else
                    fmask(1:l) = 0;
                    obj.runframes(1) = obj.runframes(1) - l;
                end
                
            % --- if fmask is a vector, apply it as a mask for the whole image or at each run
                
            elseif length(fmask) > 1
                mask = zeros(1, obj.frames);
                if strcmp(options, 'perrun') && length(obj.runframes > 1)
                    off = 1;
                    for r = 1:length(obj.runframes)
                        mask(off:off+min([obj.runframes(r) length(fmask)])-1) = fmask(1:min([obj.runframes(r) length(fmask)]));
                        off = off + obj.runframes(r);
                        obj.runframes(r) = sum(fmask(1:min([obj.runframes(r) length(fmask)])) > 0);
                    end
                else
                    mask(1:min([length(fmask), length(mask)])) = fmask(1:min([length(fmask), length(mask)]));
                    obj.runframes(1) = sum(fmask > 0);
                end
                fmask = mask;
            end
            
            if ~isempty(fmask)
                obj.data = obj.image2D;
                obj.data = obj.data(:, fmask > 0);
                obj.frames = sum(fmask>0);
            end
        end
        
    end
    
end

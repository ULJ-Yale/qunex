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
%  Last modification by Grega Repovš, 2010-03-18
%  2011-07-31 - Added importing of existing movement, fstat and scrubbing data
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
        glm;
        xml             = [];
        meta            = [];

        % ---> various statistical data

        use             = [];
        mov             = [];
        mov_hdr         = [];
        fstats          = [];
        fstats_hdr      = [];
        scrub           = [];
        scrub_hdr       = [];
        nuisance        = [];
        nuisance_hdr    = [];

    end

    methods(Static = true)
        %ifh = mri_ReadIFH(file)
        files = mri_ReadConcFile(file)
        roi   = mri_ReadROI(roiinfo, roif2)
        mri_SaveConcFile(file, files)
        mri_SaveNIfTImx(filename, hdr, data, meta, doswap, verbose)
        [hdr, data, meta, doswap] = mri_ReadNIfTImx(filename, verbose)
    end

    methods
        output = mri_Smooth3D(obj, fwhm, verbose)
        output = mri_Smooth3DMasked(obj, mask, fwhm, limit, verbose)
        output = mri_Stats(obj, do, exclude)
        output = mri_Stats2(obj, obj2, do, exclude)
        output = mri_ComputeScrub(obj, do)
    end

    methods
        function obj = gmrimage(varone, dtype, frames, verbose)
        %
        %  Class constructor, calls readimage function if a parameter is passed
        %

            if nargin < 4
                verbose = false;
                if nargin < 3
                    frames = [];
                    if nargin < 2
                        dtype = 'single';
                    end
                end
            end

            % obj = gmrimage();
            if nargin > 0
               if isa(varone, 'char')
                    obj = obj.mri_readimage(varone, dtype, frames, verbose);
                elseif isa(varone, 'numeric')
                    obj         = gmrimage;
                    obj.data    = varone;
                    obj.dim     = ones(1,3);
                    obj.dim(1)  = size(varone,1);
                    obj.dim(2)  = size(varone,2);
                    obj.dim(3)  = size(varone,3);
                    obj.voxels  = prod(obj.dim(1:3));
                    obj.frames  = size(varone,4);
                    obj.empty   = false;
                end
            end
        end

        function obj = mri_readimage(obj, filename, dtype, frames, verbose)
        %
        %  Checks what type the image is and calls the appropriate function
        %

            if nargin < 5
                verbose = false;
                if nargin < 4
                    frames = [];
                    if nargin < 3
                        dtype = [];
                    end
                end
            end
            if isempty(dtype)
                dtype = 'single';
            end
            filename = strtrim(filename);
            if length(filename) > 8 && strcmp(filename(length(filename)-8:end), '.4dfp.img')
                obj = obj.mri_Read4DFP(filename, dtype, frames, verbose);
                obj = obj.mri_ReadStats(filename, frames, verbose);
                obj.empty = false;
            elseif length(filename) > 3 && strcmp(filename(length(filename)-3:end), '.nii') || strcmp(filename(length(filename)-6:end), '.nii.gz') || strcmp(filename(length(filename)-3:end), '.hdr')
                obj = obj.mri_ReadNIfTI(filename, dtype, frames, verbose);
                obj = obj.mri_ReadStats(filename, frames, verbose);
                obj.empty = false;
            elseif length(filename) > 4 && strcmp(filename(length(filename)-4:end), '.conc')
                obj = obj.mri_ReadConcImage(filename, dtype, frames, verbose);
                obj.empty = false;
            elseif length(filename) > 3 && strcmp(filename(length(filename)-3:end), '.glm')
                obj = obj.mri_ReadGLM(filename, dtype, verbose);
                obj.empty = false;
            else
                error('ERROR: Unknown file format! [%s]', filename);
                obj = gmrimage();
            end

        end

        function mri_saveimage(obj, filename, extra, verbose)
        %
        %  Save image based on the existing header data
        %
            if nargin < 4 verbose = [];            end
            if nargin < 3 extra = [];              end
            if nargin < 2 filename = obj.filename; end

            filename = strtrim(filename);

            switch obj.imageformat
                case '4dfp'
                    obj.mri_Save4DFP(filename, extra);
                case 'NIfTI'
                    obj.mri_SaveNIfTI(filename, verbose);
                case 'CIFTI'
                    obj.mri_SaveNIfTI(filename, verbose);
            end
        end

        function mri_saveimageframe(obj, frame, filename, verbose)
        %
        %  Save image based on the existing header data, it only saves the specified frames.
        %
        %
            if nargin < 4, verbose = []; end
            if nargin < 3, filename = obj.filename; end

            filename = strtrim(filename);

            obj.data   = obj.image2D;
            if max(max(frame)) > size(obj.data,2)
                fprintf('\nWARNING: The desired frame number (%d) exceeded the actual number of frames (%d). Image %s not saved! [mri_saveimageframe]', max(max(frame)), size(obj.data,2), filename);
                return
            end
            obj.data   = obj.data(:,frame);
            obj.frames = size(obj.data,2);

            mri_saveimage(obj, filename, [], verbose);
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

            % - unmask first if already masked!

            if obj.masked
                obj = obj.unmaskimg();
            end

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

        function obj = mri_p2z(obj, m)
        %
        %  Converts p values to Z scores
        %
            if nargin < 2
                obj.data = icdf('Normal', (1-(obj.data./2)), 0, 1);
            else
                obj.data = icdf('Normal', (1-(obj.data./2)), 0, 1) .* sign(m.data);
            end
        end

        function obj = mri_Fisher(obj)
        %
        %   Converts r to Fisher z values
        %
            obj.data = obj.data*0.999999;
            obj.data = atanh(obj.data);
        end

        function obj = mri_FisherInv(obj)
        %
        %   Converts r to Fisher z values
        %
            obj.data = exp(obj.data*2);
            obj.data = (obj.data-1)./(obj.data+1);
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


        % =================================================
        %                                           horzcat
        %
        %   method for concatenation of image volumes
        %

        function obj = horzcat(obj, add)
            obj.data = [obj.image2D add.image2D];
            obj.frames = obj.frames + add.frames;
            obj.runframes = [obj.runframes add.frames];
            obj.use  = [obj.use add.use];

            % --> combine movement data
            if ~isempty(obj.mov) && ~isempty(add.mov)
                obj.mov = [obj.mov; add.mov];
            else
                obj.mov     = [];
                obj.mov_hdr = [];
            end

            % --> combine fstats data
            if ~isempty(obj.fstats) && ~isempty(add.fstats)
                obj.fstats = [obj.fstats; add.fstats];
            else
                obj.fstats     = [];
                obj.fstats_hdr = [];
            end

            % --> combine scrub data
            if ~isempty(obj.scrub) & ~isempty(add.scrub)
                obj.scrub = [obj.scrub; add.scrub];
            else
                obj.scrub     = [];
                obj.scrub_hdr = [];
            end
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


        % =================================================
        %                                        zeroframes
        %
        %   method for creating image with empty frames
        %

        function obj = zeroframes(obj, frames)
            obj.data = zeros(obj.voxels, frames);
            obj.frames = frames;
            obj.runframes = frames;
            obj.use = true(1, frames);

            % ---> erase movement data

            if ~isempty(obj.mov)
                obj.mov     = [];
                obj.mov_hdr = [];
            end

            % ---> erase fstats data

            if ~isempty(obj.fstats)
                obj.fstats     = [];
                obj.fstats_hdr = [];
            end

            % ---> erase scrub data

            if ~isempty(obj.scrub)
                obj.scrub     = [];
                obj.scrub_hdr = [];
            end
        end




        % =================================================
        %                                       sliceframes
        %
        %   method for removing masked volumes from image
        %
        %   fmask is scalar or vector with 0 for frames to exclude
        %

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
                    obj.runframes = sum(fmask > 0);
                end
                fmask = mask;
            end

            if ~isempty(fmask)
                obj.data = obj.image2D;
                obj.data = obj.data(:, fmask > 0);
                obj.frames = sum(fmask>0);
                obj.use  = obj.use(:, fmask > 0);

                % ---> mask movement data

                if ~isempty(obj.mov)
                    obj.mov = obj.mov(fmask > 0, :);
                end

                % ---> mask fstats data

                if ~isempty(obj.fstats)
                    obj.fstats = obj.fstats(fmask > 0, :);
                end

                % ---> mask scrub data

                if ~isempty(obj.scrub)
                    obj.scrub = obj.scrub(fmask > 0, :);
                end
            end
        end

    end

end

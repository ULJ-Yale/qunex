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
%  ---
%  Written by Grega Repovs, 2009-10-04
%
%  2011-07-31 Grega Repovs
%           - Added importing of existing movement, fstat and scrubbing data
%  2016-01-16 Grega Repovs
%           - Added GetXY and specifying save format with file extension.
%  2017-03-21 Grega Repovs
%           - horzcat now supports concatenation of empty objects.
%           - mri_ReadConcFile returns more information
%  2017-07-02 Grega Repovs
%           - horzcat, zeroframes and sliceframe suport img.cifti.maps
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
        filetype        = [];
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
        metadata        = [];
        list            = [];

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
        cifti           = [];

    end

    methods(Static = true)
        %ifh = mri_ReadIFH(file)
        [files boldn sfolder] = mri_ReadConcFile(file)
        img   = mri_ReadConcImage(file, dtype, frames, verbose)
        roi   = mri_ReadROI(roiinfo, roif2)
        mri_SaveConcFile(file, files)
        mri_SaveNIfTImx(filename, hdr, data, meta, doswap, verbose)
        [hdr, data, meta, doswap] = mri_ReadNIfTImx(filename, verbose)
    end

    methods
        output = mri_Smooth3D(obj, fwhm, verbose, ftype, ksize)
        output = mri_Smooth3DMasked(obj, mask, fwhm, limit, verbose)
        output = mri_Smooth(obj, fwhm,  verbose, ftype, ksize, projection, mask, wb_path, hcpatlas)
        output = mri_Stats(obj, do, exclude)
        output = mri_StatsDiff(obj, obj2, do, exclude)
        output = mri_ComputeScrub(obj, do)
        output = mri_GetXYZ(obj, ijk)
        output = mri_GetIJK(obj, xyz)
        output = mri_CreateROIFrompeaksIn(obj, peaksIn)
    end

    methods
        function obj = gmrimage(varone, dtype, frames, verbose)

        %function obj = gmrimage(varone, dtype, frames, verbose)
        %
        %   Class constructor, calls readimage function if a parameter is passed otherwise it
        %   generates an empty image object.
        %
        %   Input
        %       - varone ... A number of possible argument types:
        %                    * string       ... File(s) will be read into a gmrimage object.
        %                    * data matrix  ... F gmrimage object will be generated with data
        %                                       from the data matrix.
        %                    * cell array   ... An array of grimage objects will be generated
        %                                       each item dependent on the type of the cell type.
        %                    * gmrimage     ... The image will be copied.
        %       - dtype  ... The datatype to store the data in. ['single']
        %       - frames ... The number of frames to read from the image.
        %       - verbose ... Whether to be talkative
        %
        %   Output
        %       - obj  ... A single gmrimage object or an array of gmrimage objects.
        %
        %   Strings
        %   -------
        %
        %   If varone is a string, reading of files will be attempted. The results depend on the
        %   Specifics of a string provided:
        %
        %   * a single filename
        %   A single filename will be read as a single file and will result in a single gmrimage object.
        %   If the filename is a .conc file, all the files listed in the .conc file will be concatenated
        %   together in one long file. The number of frames from each file will be stored in obj.runframes
        %   vector
        %
        %   * pipe separated list of files
        %   A pipe (|) separated list of files will result in reading and concatenating all of the listed
        %   files into a single long image object. The number of frames from each file will be stored
        %   in the obj.runframes vector.
        %
        %   * a semicolon separated list of files
        %   A semicolon (';') separated list of files will result in an array of gmrimage objects, each
        %   object can be a single image, .conc list of images or pipe separated list of images.
        %
        %   Examples
        %   --------
        %
        %   img1 = gmrimage();
        %   img2 = gmrimage('t1w.nii.gz');
        %   img3 = gmrimage('boldlist.conc');
        %   img4 = gmrimage('bold1.nii.gz|bold2.nii.gz|bold3.nii.gz');
        %   img5 = gmrimahe('boldlist.conc;bold1.nii.gz;bold2.nii.gz|bold3.nii.gz');
        %   img6 = gmrimage(randn(91,191,91));
        %
        %   The results will be:
        %   img1 ... An empty gmrimage object.
        %   img2 ... A gmrimage object with the content of a T1w image.
        %   img3 ... A gmrimage object with concatenated files listed in 'boldlist.conc'.
        %   img4 ... A gmrimage object with three bold files concatenated.
        %   img5 ... A vector of three image objects, img5(1) a concatenated set of images
        %            as specified in 'boldlist.conc', img5(2) a single bold run, and img5(3)
        %            a two concatenated bold images.
        %
        %   ---
        %   Written by Grega Repov??
        %
        %   Changelog
        %       2017-02-11 Grega Repov?? - Updated the documentation


            if nargin < 4, verbose = false;  end
            if nargin < 3, frames = [];      end
            if nargin < 2, dtype = 'single'; end

            if nargin > 0
               if isa(varone, 'char')
                    images = regexp(varone, ';', 'split');
                    iset = [];
                    for n = 1:length(images)
                        parts = regexp(images{n}, '\|', 'split');
                        for p = 1:length(parts)
                            if p == 1
                                t = obj.mri_readimage(parts{p}, dtype, frames, verbose);
                            else
                                t = [t gmrimage(parts{p}, dtype, frames, verbose)];
                            end
                        end
                        if n == 1
                            iset = t;
                        else
                            iset(end+1:end+length(t)) = t;
                        end
                    end
                    if length(images) > 1
                        obj = iset;
                    else
                        obj = iset(1);
                    end

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
                    if (obj.dim(1) == 91 && obj.dim(2) == 109 && obj.dim(3) == 91)
                        obj.imageformat='NIfTI';
                        obj.hdrnifti = struct('swap', 0,'swapped', 0, 'data_type', blanks(10),...
                            'db_name', blanks(18), 'extents', 0, 'session_error', 0,...
                            'regular', 'r', 'dim_info', ' ', 'dim', [3;91;109;91;1;1;1;1], 'intent_p1', 0,...
                            'intent_p2', 0, 'intent_p3', 0, 'intent_code', 0,'datatype', 16,...
                            'bitpix', 32, 'slice_start', 0, 'pixdim', [-1;2;2;2;0;0;0;0], 'vox_offset', 2736,...
                            'scl_slope', 0, 'scl_inter', 0, 'slice_end', 0, 'slice_code', ' ',...
                            'xyzt_units', '', 'cal_max', 0, 'cal_min', 0, 'slice_duration', 0,...
                            'toffset', 0, 'glmax', 0, 'glmin', 0, 'descrip', blanks(80),...
                            'aux_file', blanks(24), 'qform_code', 1, 'sform_code', 1, 'quatern_b', 0,...
                            'quatern_c', 1, 'quatern_d', 0, 'qoffset_x', 90, 'qoffset_y', -126,...
                            'qoffset_z', -72, 'srow_x', [-2;0;0;90], 'srow_y', [0;2;0;-126],...
                            'srow_z', [0;0;2;-72], 'intent_name', blanks(16), 'magic', 'n+1 ',...
                            'version', 1, 'unused_str', blanks(24));
                    end
                elseif iscell(varone)
                    for n = 1:length(varone);
                        if ischar(varone{n})
                            if n == 1
                                obj = gmrimage(varone{n}, dtype, frames, verbose);
                            else
                                t = gmrimage(varone{n}, dtype, frames, verbose);
                                obj(end+1:end+length(t)) = t;
                            end
                        elseif isa(varone{n}, 'gmrimage')
                            obj(n) = varone{n};
                        else
                            error('ERROR: Could not parse images!');
                        end
                    end
                elseif isa(varone, 'gmrimage')
                    obj = varone;
                else
                    error('ERROR: Could not parse images!');
                end
            end
        end

        function obj = mri_readimage(obj, filename, dtype, frames, verbose)
        %
        %  Checks what type the image is and calls the appropriate function
        %

            if nargin < 5                     verbose = false;   end
            if nargin < 4                     frames = [];       end
            if nargin < 3 || isempty(dtype),  dtype = 'single';  end

            filename = strtrim(filename);

            % --- check if file exists

            if ~exist(filename)
                error('\nERROR mri_readimage: File does not exist [%s]!\n', filename);
            end

            % --- load depending on filename extension

            if length(filename) > 8 && strcmp(filename(length(filename)-8:end), '.4dfp.img')
                obj = obj.mri_Read4DFP(filename, dtype, frames, verbose);
                obj = obj.mri_ReadStats(verbose);
                obj.empty = false;
            elseif length(filename) > 3 && strcmp(filename(length(filename)-3:end), '.nii') || strcmp(filename(length(filename)-6:end), '.nii.gz') || strcmp(filename(length(filename)-3:end), '.hdr')
                obj = obj.mri_ReadNIfTI(filename, dtype, frames, verbose);
                obj = obj.mri_ReadStats(verbose);
                obj.empty = false;
            elseif length(filename) > 4 && strcmp(filename(length(filename)-4:end), '.conc')
                obj = gmrimage.mri_ReadConcImage(filename, dtype, frames, verbose);
                obj.empty = false;
            elseif length(filename) > 3 && strcmp(filename(length(filename)-3:end), '.glm')
                obj = obj.mri_ReadGLM(filename, dtype, verbose);
                obj.empty = false;
            else
                error('ERROR: Unknown file format! [%s]', filename);
                obj = gmrimage();
            end

        end

        function mri_saveimage(obj, filename, extra, datatype, verbose)
        %
        %  Save image based on the existing header data
        %
            if nargin < 5 verbose = [];            end
            if nargin < 4 datatype = [];           end
            if nargin < 3 extra = [];              end
            if nargin < 2 filename = obj.filename; end

            filename = strtrim(filename);

            % --- Let's see if we have an explicit extension and take that into account

            if ~isempty(strfind(filename, '.4dfp.img'))
                obj.mri_Save4DFP(filename, extra);
            elseif ~isempty(strfind(filename, '.nii.gz'))
                obj.mri_SaveNIfTI(filename, datatype, verbose);

            % --- Otherwise save based on the set imageformat

            else
                switch obj.imageformat
                    case '4dfp'
                        obj.mri_Save4DFP(filename, extra);
                    case {'NIfTI', 'CIFTI', 'CIFTI-1', 'CIFTI-2'}
                        obj.mri_SaveNIfTI(filename, datatype, verbose);
                    otherwise
                        error('ERROR: Unknown file format, could not save image! [%s]', obj.imageformat);
                end
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

            if isempty(obj)
                obj = add;
                return
            elseif isempty(add)
                return
            end

            obj.data = [obj.image2D add.image2D];
            obj.frames = obj.frames + add.frames;
            obj.runframes = [obj.runframes add.frames];
            obj.use  = [obj.use add.use];
            if strcmp(obj.imageformat, 'CIFTI-2')
                obj.dim = size(obj.data);
            end

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

            % --> combine list data
            if ~isempty(obj.list) & ~isempty(add.list)
                for f = fields(obj.list)'
                    f = f{1};
                    if strcmp(f, 'meta')
                        continue
                    elseif isfield(add.list, f)
                        obj.list.(f) = [obj.list.(f) add.list.(f)];
                    else
                        obj.list = rmfield(obj.list, f);
                    end
                end
            else
                obj.list     = [];
            end

            % --> combine maps data
            if isfield(obj.cifti, 'maps') && ~isempty(obj.cifti.maps)
                if isfield(add.cifti, 'maps') && ~isempty(add.cifti.maps)
                    obj.cifti.maps = [obj.cifti.maps add.cifti.maps];
                else
                    for n = 1:add.frames
                        obj.cifti.maps{end+1} = sprintf('Map %d', n);
                    end
                end
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

            % ---> erase metadata

            for f = {'mov', 'mov_hdr', 'fstats', 'fstats_hdr', 'scrub', 'scrub_hdr', 'nuisance', 'nuisance_hdr', 'glm', 'list'}
                obj.(f{1}) = [];
            end

            % ---> erase metadata 2

            if length(obj.meta) > 0
                obj.meta = obj.meta([obj.meta.code] ~= 64);
            end

            % ---> erase maps info

            if isfield(obj.cifti, 'maps')
                obj.cifti.maps = {};
            end

        end




        % =================================================
        %                                       sliceframes
        %
        %   method for removing masked volumes from image
        %
        %   fmask can be:
        %   - a scalar specifying how many frames to exclude from the start
        %   - a boolean or 1/0 vector specifying which frames to keep
        %

        function obj = sliceframes(obj, fmask, options)
            if nargin < 3
                options = [];
                if nargin < 2
                    fmask = [];
                end
            end

            % --- if fmask is a scalar, remove passed number of frames from start of image or each run

            if length(fmask) == 1 && ~isa(fmask, 'logical')
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

            elseif ~isempty(fmask) && (length(fmask) > 1 || ~isa(fmask, 'logical'))
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
                fmask = fmask > 0;
                obj.data = obj.image2D;
                obj.data = obj.data(:, fmask);
                obj.frames = sum(fmask);

                % ---> mask use data

                if ~isempty(obj.use)
                    obj.use  = obj.use(:, fmask);
                end

                % ---> mask movement data

                if ~isempty(obj.mov)
                    obj.mov = obj.mov(fmask, :);
                end

                % ---> mask fstats data

                if ~isempty(obj.fstats)
                    obj.fstats = obj.fstats(fmask, :);
                end

                % ---> mask scrub data

                if ~isempty(obj.scrub)
                    obj.scrub = obj.scrub(fmask, :);
                end

                % ---> mask list data

                if ~isempty(obj.list)
                    lists     = fields(obj.list);
                    lists     = lists(~ismember(lists, 'meta'));
                    for l = lists(:)'
                        l = l{1};
                        obj.list.(l) = obj.list.(l)(fmask);
                    end
                end

                % ---> mask glm data

                if ~isempty(obj.glm)
                    if isfield(obj.glm, 'c'),      obj.glm.c      = obj.glm.c(:, fmask);    end
                    if isfield(obj.glm, 'ATAm1'),  obj.glm.ATAm1  = obj.glm.ATAm1(fmask, fmask); end
                    if isfield(obj.glm, 'event'),  obj.glm.event  = obj.glm.event(fmask);   end
                    if isfield(obj.glm, 'frame'),  obj.glm.frame  = obj.glm.frame(fmask);   end
                    if isfield(obj.glm, 'effect'), obj.glm.effect = obj.glm.effect(fmask);  end
                    if isfield(obj.glm, 'eindex'), obj.glm.eindex = obj.glm.eindex(fmask);  end
                    if isfield(obj.glm, 'hdr'),    obj.glm.hdr    = obj.glm.hdr(fmask);     end
                    if isfield(obj.glm, 'A'),      obj.glm.A      = obj.glm.A(:,fmask);     end
                end

                % ---> mask maps data

                if isfield(obj.cifti, 'maps') && (~isempty(obj.cifti.maps))
                    obj.cifti.maps = obj.cifti.maps(fmask);
                end
            end

        end

    end

end

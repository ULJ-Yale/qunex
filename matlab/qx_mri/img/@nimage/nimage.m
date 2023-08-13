classdef nimage
%
%   nimage class offers an object to store MR image data. It provides basic
%   methods for loading and saving image, methods for returning different
%   representations of the image, methods for extracting data and manipulating
%   image, and methods for performing basic math with the images.
%
%   METHODS
%   =======
%
%   nimage             
%       constructor / loader
%
%   img_readimage      
%       reads an image file
%
%   img_saveimage      
%       saves an image file
%
%   img_saveimageframe 
%       saves only the specified frame(s) of an image file
%
%   image2D            
%       returns 2D (voxels by frames) representation of image data
%
%   image4D            
%       returns 4D (x by y by z by frames representation of image data)
%
%   maskimg            
%       trims data from all nonzero voxels of the mask
%
%   unmaskimg          
%       restores the full volume from masked image with zeros for missing voxels
%
%   standardize        
%       transforms values to z scores within each voxel's timeseries
%
%   correlize
%       standardizes and divides by sqrt(N-1) to prepare for efficient 
%       correlation computation
%   
%   img_compute_correlations
%       computes correlations with the provided data matrix
%   
%   PROPERTIES
%   ==========
%
%   data          
%       [grayordinates, frames] or [x, y, z, frames] matrix of imaging data
%   imageformat   
%       The image format of the source file: 4dfp, NIfTI, CIFTI, CIFTI-1, CIFTI-2
%   mformat       
%       The number format of the source file: l - littleendian, b - bigendian
%   hdrnifti      
%       The structure with the NIfTI header
%   hdr4dfp       
%       The structure with the 4dfp header
%   dim           
%       The x, y, z dimensions or grayordinates dimensions of the original image
%   voxels        
%       The number of voxels / grayordinates in a single frame
%   vsizes        
%       The size of voxels in x, y, z direction
%   TR            
%       TR of the image
%   frames        
%       Number of frames in the image
%   runframes     
%       A vector with the number of frames from each run in the order the images were concatenated
%   filename      
%       The original image filename
%   filetype      
%       The type of the CIFTI file: .dtseries | .ptseries | .pconn | .pscalar | .dscalar
%   rootfilename  
%       Filename without the file type extension
%   mask          
%       Boolean vector specifying the spatial voxel / grayordinate mask used to mask the data
%   masked        
%       Has the data been spatially masked: true | false
%   empty         
%       Is the image data empty: true | false
%   standardized  
%       Has the timeseries been converted to z-scores: true / false
%   correlized    
%       Has the standardized values been deleted by sqrt(obj.frames -1) to allow easy computation of correlations: true | false
%   info          
%       Information on what operations were completed on the image
%   roi           
%       If the image is an ROI mask, a structure with the information about the ROI
%   glm           
%       If the image contains results of GLM, the structure with the GLM information
%   xml           
%       For CIFTI images, the content of the xml metadata
%   meta          
%       A structure that describes metadata
%   metadata      
%       uint8 encoded metadata
%   list          
%       S structure with list information
%   tevents        
%       A [2, frames] vector. The first row list index of the event from which the frame originates, the second row lists the frame number from the event.
%   use           
%       A row vector specifying which frame of the timeseries to use (1) and which not (0)
%   mov           
%       A [frame, parameter] matrix of movement parameters
%   mov_hdr       
%       A cell array providing header information for mov matrix
%   fstats        
%       A [frame, statistics] matrix of per frame statistics
%   fstats_hdr    
%       A cell array providing header information for fstats matrix
%   scrub         
%       A [frame, parameter] matrix of scrubbing parameters
%   scrub_hdr     
%       A cell array providing header information for scrub matrix
%   nuisance      
%       A [frame, signal] matrix of nuisance signals
%   nuisance_hdr  
%       A cell array providing header information for nuisance matrix
%   cifti         
%       A structure providing CIFTI information

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

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
        concname        = [];
        rootconcname    = [];
        filename        = [];
        filenames       = {};
        filetype        = [];
        rootfilename    = [];
        rootfilenames   = {};
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
        tevents         = [];
        tframes         = [];

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
        %ifh = img_read_ifh(file)
        [files boldn sfolder] = img_read_concfile(file)
        img   = img_read_concimage(file, dtype, frames, verbose)
        roi   = img_read_roi(roiinfo, roif2, checks)
        img_save_concfile(file, files)
        img_save_nifti_mx(filename, hdr, data, meta, doswap, verbose)
        [hdr, data, meta, doswap] = img_read_nifti_mx(filename, verbose)
    end

    methods
        output = img_smooth_3d(obj, fwhm, verbose, ftype, ksize)
        output = img_smooth_3d_masked(obj, mask, fwhm, limit, verbose)
        output = img_smooth(obj, fwhm,  verbose, ftype, ksize, projection, mask, wb_path, hcpatlas, timeSeries, frames)
        output = img_stats(obj, doIt, exclude)
        output = img_stats_diff(obj, obj2, doIt, exclude)
        [output param] = img_compute_scrub(obj, doIt)
        output = img_get_xyz(obj, ijk)
        output = img_get_ijk(obj, xyz)
        output = img_create_roi_from_peaks(obj, peaksIn)
    end

    methods
        function obj = nimage(varone, dtype, frames, verbose)

        %function obj = nimage(varone, dtype, frames, verbose)
        %
        %   Class constructor, calls readimage function if a parameter is passed otherwise it
        %   generates an empty image object.
        %
        %   Input
        %       - varone  ... A number of possible argument types:
        %                     * string       ... File(s) will be read into a nimage object.
        %                     * data matrix  ... F nimage object will be generated with data
        %                                        from the data matrix.
        %                     * cell array   ... An array of grimage objects will be generated
        %                                        each item dependent on the type of the cell type.
        %                     * nimage     ... The image will be copied.
        %       - dtype   ... The datatype to store the data in. ['single']
        %                     In case of numeric data that matches a standard CIFTI image, this
        %                     variable is interpreted as the type of CIFTI image, one of 'dtseries'
        %                     or 'dscalar' ['dtseries']
        %       - frames  ... The number of frames to read from the image, all by default.
        %                     In case of numeric data and 'dscalar' dtype, this variable is
        %                     interpreted as a list of map names, if not provided, maps will be
        %                     named 'Map 1', 'Map 2', ...
        %       - verbose ... Whether to be talkative
        %
        %   Output
        %       - obj  ... A single nimage object or an array of nimage objects.
        %
        %   Strings
        %   -------
        %
        %   If varone is a string, reading of files will be attempted. The results depend on the
        %   Specifics of a string provided:
        %
        %   * a single filename
        %   A single filename will be read as a single file and will result in a single nimage object.
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
        %   A semicolon (';') separated list of files will result in an array of nimage objects, each
        %   object can be a single image, .conc list of images or pipe separated list of images.
        %
        %   Examples
        %   --------
        %
        %   img1 = nimage();
        %   img2 = nimage('t1w.nii.gz');
        %   img3 = nimage('boldlist.conc');
        %   img4 = nimage('bold1.nii.gz|bold2.nii.gz|bold3.nii.gz');
        %   img5 = nimage('boldlist.conc;bold1.nii.gz;bold2.nii.gz|bold3.nii.gz');
        %   img6 = nimage(randn(91,191,91));
        %   img7 = nimage(randn(91282,5));
        %   img8 = nimage(randn(91282,5), 'dscalar', {'A', 'B', 'C', 'D', 'E'});
        %
        %   The results will be:
        %   img1 ... An empty nimage object.
        %   img2 ... A nimage object with the content of a T1w image.
        %   img3 ... A nimage object with concatenated files listed in 'boldlist.conc'.
        %   img4 ... A nimage object with three bold files concatenated.
        %   img5 ... A vector of three image objects, img5(1) a concatenated set of images
        %            as specified in 'boldlist.conc', img5(2) a single bold run, and img5(3)
        %            a two concatenated bold images.
        %   img6 ... A volume nifti image with a single frame, assuming standard 2mm MNI atlas.
        %   img7 ... A dense timeseries CIFTI image with 5 frames.
        %   img8 ... A dense scalar image with 5 maps named A to E.
        %

            if nargin < 4, verbose = false;  end
            if nargin < 3, frames = [];      end
            if nargin < 2, dtype = 'single'; end

            if nargin > 0
                if isa(varone, 'char')
                    images = regexp(varone, ';', 'split');
                    for n = 1:length(images)
                        parts = regexp(images{n}, '\|', 'split');
                        for p = 1:length(parts)
                            if p == 1
                                t = obj.img_readimage(parts{p}, dtype, frames, verbose);
                            else
                                t = [t nimage(parts{p}, dtype, frames, verbose)];
                            end
                        end
                        iset(n) = t;
                    end
                    if length(images) > 1
                        obj = iset;
                    else
                        obj = iset(1);
                    end

                elseif isa(varone, 'numeric')
                    obj         = nimage;
                    obj.data    = varone;
                    obj.dim     = ones(1,3);
                    obj.dim(1)  = size(varone,1);
                    obj.dim(2)  = size(varone,2);
                    obj.dim(3)  = size(varone,3);
                    if ndims(obj.data) >= 3
                        obj.voxels  = prod(obj.dim(1:3));
                        obj.frames  = size(varone,4);
                    else
                        obj.voxels = obj.dim(1);
                        obj.frames = obj.dim(2);
                    end
                    obj.empty   = false;
                    if (obj.dim(1) == 91 && obj.dim(2) == 109 && obj.dim(3) == 91)  % assuming it is a MNI Atlas NIfTI image
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
                            'srow_z', [0;0;2;-72], 'intent_name', blanks(16), 'magic', cast([110 43 49 0], 'char'),...
                            'version', 1, 'unused_str', blanks(24));
                    elseif (obj.dim(1) == 91282)  % assuming it is a CIFTI file
                        obj.filename = '';
                        obj.imageformat = 'CIFTI-2';
                        obj.hdrnifti = struct('swap', 0, 'swapped', 0, 'magic', cast([110   43   50    0   13   10   26   10], 'char'), 'datatype', 16, 'bitpix', 32, ...
                            'dim', [6 1 1 1 1 obj.dim(2) 91282 1]', 'intent_p1', 0, 'intent_p2', 0, 'intent_p3', 0, ...
                            'pixdim', [1 1 1 1 1 1 1 1]', ...
                            'vox_offset', 0, 'scl_slope', 1, 'scl_inter', 0, 'cal_max', 0, 'cal_min', 0, 'slice_duration', 0, ...
                            'toffset', 0, 'slice_start', 0, 'slice_end', 0, 'descrip', blanks(80), 'aux_file', blanks(24), ...
                            'qform_code', 0, 'sform_code', 0, 'quatern_b', 0, 'quatern_c', 0, 'quatern_d', 0, ...
                            'qoffset_x', 0, 'qoffset_y', 0, 'qoffset_z', 0, 'srow_x', [0;0;0;0], 'srow_y', [0;0;0;0], 'srow_z', [0;0;0;0], ...
                            'slice_code', 0, 'xyzt_units', 10, 'intent_code', 3006, 'intent_name', blanks(16), 'dim_info', ' ', ...
                            'unused_str', blanks(15), 'version', 2, 'data_type', blanks(10), 'db_name', blanks(18), 'extents', 0, ...
                            'session_error', 0, 'regular', ' ', 'glmax', 0, 'glmin', 0);
                        obj.cifti.longnames  = {'CIFTI_STRUCTURE_CORTEX_LEFT', 'CIFTI_STRUCTURE_CORTEX_RIGHT', 'CIFTI_STRUCTURE_ACCUMBENS_LEFT', 'CIFTI_STRUCTURE_ACCUMBENS_RIGHT', 'CIFTI_STRUCTURE_AMYGDALA_LEFT', 'CIFTI_STRUCTURE_AMYGDALA_RIGHT', 'CIFTI_STRUCTURE_BRAIN_STEM', 'CIFTI_STRUCTURE_CAUDATE_LEFT', 'CIFTI_STRUCTURE_CAUDATE_RIGHT', 'CIFTI_STRUCTURE_CEREBELLUM_LEFT', 'CIFTI_STRUCTURE_CEREBELLUM_RIGHT', 'CIFTI_STRUCTURE_DIENCEPHALON_VENTRAL_LEFT', 'CIFTI_STRUCTURE_DIENCEPHALON_VENTRAL_RIGHT', 'CIFTI_STRUCTURE_HIPPOCAMPUS_LEFT', 'CIFTI_STRUCTURE_HIPPOCAMPUS_RIGHT', 'CIFTI_STRUCTURE_PALLIDUM_LEFT', 'CIFTI_STRUCTURE_PALLIDUM_RIGHT', 'CIFTI_STRUCTURE_PUTAMEN_LEFT', 'CIFTI_STRUCTURE_PUTAMEN_RIGHT', 'CIFTI_STRUCTURE_THALAMUS_LEFT', 'CIFTI_STRUCTURE_THALAMUS_RIGHT'};
                        obj.cifti.shortnames = {'CORTEX_LEFT', 'CORTEX_RIGHT', 'ACCUMBENS_LEFT', 'ACCUMBENS_RIGHT', 'AMYGDALA_LEFT', 'AMYGDALA_RIGHT', 'BRAIN_STEM', 'CAUDATE_LEFT', 'CAUDATE_RIGHT', 'CEREBELLUM_LEFT', 'CEREBELLUM_RIGHT', 'DIENCEPHALON_VENTRAL_LEFT', 'DIENCEPHALON_VENTRAL_RIGHT', 'HIPPOCAMPUS_LEFT', 'HIPPOCAMPUS_RIGHT', 'PALLIDUM_LEFT', 'PALLIDUM_RIGHT', 'PUTAMEN_LEFT', 'PUTAMEN_RIGHT', 'THALAMUS_LEFT', 'THALAMUS_RIGHT'};
                        obj.cifti.start      = [1 29697 59413 59548 59688 60003 60335 63807 64535 65290 73999 83143 83849 84561 85325 86120 86417 86677 87737 88747 90035];
                        obj.cifti.end        = [29696 59412 59547 59687 60002 60334 63806 64534 65289 73998 83142 83848 84560 85324 86119 86416 86676 87736 88746 90034 91282];
                        obj.cifti.length     = [29696 29716 135 140 315 332 3472 728 755 8709 9144 706 712 764 795 297 260 1060 1010 1288 1248];
                        obj.cifti.maps       = {};
                        obj.frames = size(varone, 2);
                        obj.dim    = 91282;
                        obj.voxels = 91282;
                        switch dtype
                            case {'single', 'dtseries'}
                                obj.filetype = '.dtseries';
                                obj.TR = 1;
                                obj.hdrnifti.intent_code = 3002;
                                obj.hdrnifti.intent_name = 'ConnDenseSeries ';
                                obj.meta = obj.dtseriesXML();
                            case 'dscalar'
                                obj.filetype = '.dscalar';
                                obj.hdrnifti.intent_code = 3006;
                                obj.hdrnifti.intent_name = 'ConnDenseScalar ';
                                if isa(frames, 'cell')
                                    if length(frames) == obj.frames
                                        obj.cifti.maps = frames;
                                    end
                                end
                                obj.meta = obj.dscalarXML();
                            otherwise
                                error('ERROR: Unknown file type, could not generate nimage object! [%s]', dtype);
                        end
                    end
                elseif iscell(varone)
                    for n = 1:length(varone);
                        if ischar(varone{n})
                            if n == 1
                                obj = nimage(varone{n}, dtype, frames, verbose);
                            else
                                t = nimage(varone{n}, dtype, frames, verbose);
                                obj(end+1:end+length(t)) = t;
                            end
                        elseif isa(varone{n}, 'nimage')
                            obj(n) = varone{n};
                        else
                            error('ERROR: Could not parse images!');
                        end
                    end
                elseif isa(varone, 'nimage')
                    obj = varone;
                else
                    error('ERROR: Could not parse images!');
                end
            end
        end

        function [meta] = dtseriesXML(img)
        %
        %   Creates meta data for dtseries image
        %

            mpath = fileparts(mfilename('fullpath'));
            xml = fileread(fullfile(mpath, 'dtseries-32k.xml'));
            xml = strrep(xml,'{{ParentProvenance}}', img.filename);
            xml = strrep(xml,'{{ProgramProvenance}}', 'QuNex');
            xml = strrep(xml,'{{Provenance}}', 'QuNex');
            xml = strrep(xml,'{{WorkingDirectory}}', pwd);
            xml = strrep(xml,'{{Frames}}', num2str(img.frames));
            xml = strrep(xml,'{{TR}}', num2str(img.TR));
            xml = cast(xml', 'uint8');
            meta = nimage.string2meta(xml, 32);
        end

        function [meta] = dscalarXML(img)
        %
        %   Creates meta data for dscalar image
        %
            mpath = fileparts(mfilename('fullpath'));
            xml = fileread(fullfile(mpath, 'dscalar-32k.xml'));
            xml = strrep(xml, '{{ParentProvenance}}', img.filename);
            xml = strrep(xml, '{{ProgramProvenance}}', 'QuNex');
            xml = strrep(xml, '{{Provenance}}', 'QuNex');
            xml = strrep(xml, '{{WorkingDirectory}}', pwd);

            if ~isfield(img.cifti, 'maps') || isempty(img.cifti.maps)
                for n = 1:img.frames
                    img.cifti.maps{end+1} = sprintf('Map %d', n);
                end
            end
            mapString = '';
            first = true;
            for map = img.cifti.maps
                mapString = [mapString '            <NamedMap><MapName>' map{1} '</MapName></NamedMap>'];
                if ~first
                    mapString = [mapString '\n'];
                else
                    first = false;
                end
            end
            xml = strrep(xml, '{{NamedMaps}}', mapString);
            meta = nimage.string2meta(xml, 32);
        end

        function obj = img_readimage(obj, filename, dtype, frames, verbose)
        %
        %  Checks what type the image is and calls the appropriate function
        %

            if nargin < 5                     verbose = false;   end
            if nargin < 4                     frames = [];       end
            if nargin < 3 || isempty(dtype),  dtype = 'single';  end

            filename = strtrim(filename);

            % --- check if file exists

            if ~exist(filename)
                error('\nERROR img_readimage: File does not exist [%s]!\n', filename);
            end

            % --- load depending on filename extension

            if length(filename) > 8 && strcmp(filename(length(filename)-8:end), '.4dfp.img')
                obj = obj.img_read_4dfp(filename, dtype, frames, verbose);
                obj = obj.img_read_stats(verbose);
                obj.empty = false;
            elseif length(filename) > 3 && strcmp(filename(length(filename)-3:end), '.nii') || strcmp(filename(length(filename)-6:end), '.nii.gz') || strcmp(filename(length(filename)-3:end), '.hdr')
                obj = obj.img_read_nifti(filename, dtype, frames, verbose);
                obj = obj.img_read_stats(verbose);
                obj.empty = false;
            elseif length(filename) > 4 && strcmp(filename(length(filename)-4:end), '.conc')
                obj = nimage.img_read_concimage(filename, dtype, frames, verbose);
                obj.empty = false;
            elseif length(filename) > 3 && strcmp(filename(length(filename)-3:end), '.glm')
                obj = obj.img_read_glm(filename, dtype, verbose);
                obj.empty = false;
            else
                error('ERROR: Unknown file format! [%s]', filename);
                obj = nimage();
            end

        end

        function img_saveimage(obj, filename, extra, datatype, verbose)
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
                obj.img_save_4dfp(filename, extra);
            elseif ~isempty(strfind(filename, '.nii.gz'))
                obj.img_save_nifti(filename, datatype, verbose);

            % --- Otherwise save based on the set imageformat

            else
                switch obj.imageformat
                    case '4dfp'
                        obj.img_save_4dfp(filename, extra);
                    case {'NIfTI', 'CIFTI', 'CIFTI-1', 'CIFTI-2'}
                        obj.img_save_nifti(filename, datatype, verbose);
                    otherwise
                        error('ERROR: Unknown file format, could not save image! [%s]', obj.imageformat);
                end
            end
        end

        function img_saveimageframe(obj, frame, filename, verbose)
        %
        %  Save image based on the existing header data, it only saves the specified frames.
        %
        %
            if nargin < 4, verbose = []; end
            if nargin < 3, filename = obj.filename; end

            filename = strtrim(filename);

            obj.data   = obj.image2D;
            if max(max(frame)) > size(obj.data,2)
                fprintf('\nWARNING: The desired frame number (%d) exceeded the actual number of frames (%d). Image %s not saved! [img_saveimageframe]', max(max(frame)), size(obj.data,2), filename);
                return
            end
            obj.data   = obj.data(:,frame);
            obj.frames = size(obj.data,2);

            img_saveimage(obj, filename, [], verbose);
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

            if isa(mask, 'nimage')
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

        function obj = img_p2z(obj, m)
        %
        %  Converts p values to Z scores
        %
            if nargin < 2
                obj.data = icdf('Normal', (1-(obj.data./2)), 0, 1);
            else
                obj.data = icdf('Normal', (1-(obj.data./2)), 0, 1) .* sign(m.data);
            end
        end

        function obj = img_Fisher(obj)
        %
        %   Converts r to Fisher z values
        %
            obj.data = obj.data*0.999999;
            obj.data = atanh(obj.data);
        end

        function obj = img_FisherInv(obj)
        %
        %   Converts r to Fisher z values
        %
            obj.data = exp(obj.data*2);
            obj.data = (obj.data-1)./(obj.data+1);
        end


        function obj = times(obj, times)
            if isa(times, 'nimage')
                times = times.image2D;
            end
            obj.data = times(obj.image2D, times);
        end

        function obj = mtimes(obj, times)
            if isa(times, 'nimage')
                times = times.image2D;
            end
            obj.data = mtimes(obj.image2D, times);
        end

        function obj = mrdivide(obj, times)
            if isa(times, 'nimage')
                times = times.image2D;
            end
            obj.data = mrdivide(obj.image2D, times);
        end

        function obj = rdivide(obj, times)
            if isa(times, 'nimage')
                times = times.image2D;
            end
            obj.data = rdivide(obj.image2D, times);
        end

        function obj = plus(obj, B)
            if isa(B, 'nimage')
                B = B.image2D;
            end
            obj.data = plus(obj.image2D, B);
        end

        function obj = minus(obj, B)
            if isa(B, 'nimage')
                B = B.image2D;
            end
            obj.data = minus(obj.image2D, B);
        end

        function obj = eq(obj, B)
            if isa(B, 'nimage')
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

        % TODO: Add parcel matching check

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

            % --> dimensions for cifti files
            %     commented as the second dimension should not be used
            % if strcmp(obj.imageformat, 'CIFTI-2')
            %     obj.dim = size(obj.data);
            % end
            obj.filenames = [obj.filenames, add.filenames];
            obj.rootfilenames = [obj.rootfilenames, add.rootfilenames];

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

            % --> combine events data

            obj.tevents = [obj.tevents add.tevents];

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
            if isa(dim, 'nimage')
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
            obj.filename = '';
            obj.filenames = {};
            obj.rootfilename = '';
            obj.rootfilenames = {};
            obj.concname = '';
            obj.rootconcname = '';

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

                % ---> mask events data

                if ~isempty(obj.tevents)
                    obj.tevents = obj.tevents(:, fmask);
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


        % =================================================
        %                                         splitruns
        %
        %   method for splitting concatenated file back into
        %   constituent runs
        %
        
        function conc = splitruns(obj)
            startframe = 1;
            endframe = 0;
            obj.data = obj.image2D;
            for n = 1:length(obj.runframes)                
                endframe = endframe + obj.runframes(n);
               
                % -- data
                conc(n) = obj.zeroframes(obj.runframes(n));                
                conc(n).data = obj.data(:, startframe:endframe);

                % -- metadata
                conc(n).filename = obj.filenames{n};
                conc(n).filenames = obj.filenames(n);
                conc(n).rootfilename = obj.rootfilenames{n};
                conc(n).rootfilenames = obj.rootfilenames(n);

                conc(n).use = obj.use(startframe:endframe);
                if strcmp(obj.imageformat, 'CIFTI-2')
                    conc(n).dim = size(conc(n).data);
                end

                if ~isempty(obj.mov)
                    conc(n).mov = obj.mov(startframe:endframe, :);
                end

                if ~isempty(obj.fstats)
                    conc(n).fstats = obj.fstats(startframe:endframe, :);
                end

                if ~isempty(obj.scrub)
                    conc(n).scrub = obj.scrub(startframe:endframe, :);
                end

                if ~isempty(obj.list)
                    for f = fields(obj.list)'
                        f = f{1};
                        if strcmp(f, 'meta')
                            continue
                        else
                            conc(n).list.(f) = obj.list.(f)(startframe:endframe);
                        end
                    end
                end

                if ~isempty(obj.tevents)
                    conc(n).tevents = obj.tevents(:, startframe:endframe);
                end

                if isfield(obj.cifti, 'maps') && ~isempty(obj.cifti.maps)
                    conc(n).cifti.maps = obj.cifti.maps(startframe:endframe);
                end

                startframe = startframe + obj.runframes(n);
            end
        end
    end

    methods (Static)

        function [meta] = string2meta(string, code)
        %
        %   coverts string to proper meta structure
        %
            string = cast(string(:), 'uint8');
            meta.size = ceil((length(string)+8)/16)*16;
            meta.code = code;
            meta.data = zeros(1, meta.size-8, 'uint8');
            meta.data(1:length(string)) = string;
        end
    end

end

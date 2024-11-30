function [res] = img_save_nifti(img, filename, datatype, verbose)

%``img_save_nifti(obj, filename, datatype, verbose)``
%
%   Saves a NIfTI image based on the existing header information.
%
%   INPUTS
%   ======
%
%   --obj         nimage object
%   --filename    the filename to use
%   --datatype    []
%   --verbose     should it talk a lot [false]
%
%
%   OUTPUT
%   ======
%   
%   res
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 4, verbose = false; end
if nargin < 3, datatype = []; end

if verbose, fprintf('\n---> Saving image as %s', filename); end

cifti_filetypes = {'dtseries', 'dscalar', 'dlabel', 'ptseries', 'pscalar', 'plabel', 'pconn', 'dconn'};

% ---> embed extra data if available

if ~ismember(img.imageformat, {'CIFTI', 'CIFTI-1', 'CIFTI-2'}) && img.frames > 2
    img = img.img_embed_stats();
end


% ---> set up file to save

filename = strtrim(filename);
% unpack and set up

root = regexprep(filename, '\.hdr|\.nii|\.gz|\.img|\.dconn|\.dtseries|\.dscalar|\.dlabel|\.dpconn|\.pconnseries|\.pconnscalar|\.pconn|\.ptseries|\.pscalar|\.pdconn|\.dfan|\.fiberTemp', '');

ftype = regexp(filename, '(\.dconn|\.dtseries|\.dscalar|\.dlabel|\.dpconn|\.pconnseries|\.pconnscalar|\.pconn|\.ptseries|\.pscalar|\.pdconn|\.dfan|\.fiberTemp)', 'tokens');
if length(ftype) > 0
    ftype = char(ftype{1});
    img.filetype = ftype(2:end);
end

img = img.unmaskimg;

% ---> transform if necessary

if strcmp(img.imageformat, '4dfp')
    img.imageformat = 'NIfTI';
    img.data = flip(img.image4D, 2);
    img.hdrnifti.srow_y = [0; -img.hdrnifti.srow_y(2); 0; (img.dim(2) - img.hdrnifti.srow_y(4) / -img.hdrnifti.srow_y(2)) * img.hdrnifti.srow_y(2)];
end

% ---> save dimension information

switch img.imageformat
    case 'NIfTI'
        img.hdrnifti.dim(5) = img.frames;
        if img.frames > 1
            img.hdrnifti.dim(1) = 4;
        end
        file = [root '.nii.gz'];

    case 'CIFTI-1'
        if strcmp(img.filetype, 'pconn')
            img.hdrnifti.dim(6:7) = img.dim;
        else
            img.hdrnifti.dim(7) = img.frames;
        end
        file = [root '.' img.filetype '.nii'];

    case 'CIFTI-2'
        if isempty(img.TR)
            img.TR = 1;
        end

        % check filename
        if any(ismember(cifti_filetypes, strsplit(filename, '.')))
            img.filetype = cifti_filetypes{find(ismember(cifti_filetypes, strsplit(filename, '.')))};
        end
            
        % --- if series create series information
        if strfind(img.filetype, 'tseries') 
            try series_unit = img.cifti.metadata.diminfo{2}.seriesUnit; catch series_unit = 'SECOND'; end
            try series_start = img.cifti.metadata.diminfo{2}.seriesStart; catch series_start = 0; end
            img.cifti.metadata.diminfo{2} = cifti_diminfo_make_series(img.frames, series_start, img.TR, series_unit);
            
        % --- if scalar or label create scalar information
        elseif any(strfind(img.filetype, 'scalar')) || any(strfind(img.filetype, 'label'))
            if length(img.cifti.maps) == img.frames
                img.cifti.metadata.diminfo{2} = cifti_diminfo_make_scalars(img.frames, img.cifti.maps);
            else
                map_names = {};
                for imap = 1:img.frames
                    map_names{imap} = sprintf('Map %d', imap);
                end
                img.cifti.metadata.diminfo{2} = cifti_diminfo_make_scalars(img.frames, map_names);
            end        
        end

        if strfind(img.filetype, 'label') 
            img.cifti.metadata.diminfo{2}.type = 'labels';
            for imap = 1:img.frames
                img.cifti.metadata.diminfo{2}.maps(imap).table = img.cifti.labels{imap};
            end
        end

        % --- get correct dimensions (not needed - set by cifi-matlab)
        % if strfind(img.filetype, 'conn')
        %     img.hdrnifti.dim(6:7) = img.dim;
        % else
        %     img.hdrnifti.dim(6) = img.frames;
        %     img.hdrnifti.dim(7) = img.voxels;
        % end

        tcifti = img.cifti.metadata;
        tcifti.cdata = img.data;
        file = [root '.' img.filetype '.nii'];
        [metaxml, hdrnifti] = cifti_encode_metadata(tcifti, file);

        % -> update hdrnifti
        for fieldname = fieldnames(hdrnifti)'
            img.hdrnifti.(fieldname{1}) = hdrnifti.(fieldname{1});
        end

        % -> for some reason intent returned is too short
        img.hdrnifti.intent_name = [img.hdrnifti.intent_name '                 '];
        img.hdrnifti.intent_name = img.hdrnifti.intent_name(1:16);

        % -> add xml to metadata

        cmeta = length(img.meta) + 1;
        if length(img.meta) > 0
            cmeta = find([img.meta.code] == 32);
        end
        if cmeta > 1
            img.meta(cmeta) = string2meta(metaxml, 32);
        else
            img.meta = string2meta(metaxml, 32);
        end
        % img.hdrnifti = hdrnifti; -> leave as is for the time (need to update rather than replace)

    otherwise
        fprintf('\nWARNING: Imageformat info not recognized [%s], using .nii.gz\n', img.imageformat);
        file = [root '.nii.gz'];

end

% ---> flip before saving if needed

if ismember(img.imageformat, {'CIFTI', 'CIFTI-1', 'CIFTI-2'})
    if verbose, fprintf('\n---> Switching data [%s] to single (4byte float) for CIFTI data.', class(img.data)); end
    img.data = single(img.data');
    % img.data = img.data';
else
    if ~isempty(datatype)
        if verbose, fprintf('\n---> Switching data from %s to %s.', class(img.data), datatype); end
        img.data = cast(img.data, datatype);
    else
        if strcmp(class(img.data), 'double')
            if verbose, fprintf('\n---> Switching data from double to single.'); end
            img.data = single(img.data);
        end
    end
end

% ---> setup datatype

switch class(img.data)
    case 'bitN'
        img.hdrnifti.datatype = 1;
        img.hdrnifti.bitpix   = 1;
    case 'uchar'
        img.hdrnifti.datatype = 2;
        img.hdrnifti.bitpix   = 8;
    case 'int16';
        img.hdrnifti.datatype = 4;
        img.hdrnifti.bitpix   = 16;
    case 'int32'
        img.hdrnifti.datatype = 8;
        img.hdrnifti.bitpix   = 32;
    case {'float32', 'single'};
        img.hdrnifti.datatype = 16;
        img.hdrnifti.bitpix   = 32;
    case {'float64', 'double'};
        img.hdrnifti.datatype = 64;
        img.hdrnifti.bitpix   = 64;
    case 'schar';
        img.hdrnifti.datatype = 256;
        img.hdrnifti.bitpix   = 8;
    case 'uint16';
        img.hdrnifti.datatype = 512;
        img.hdrnifti.bitpix   = 16;
    case 'uint32';
        img.hdrnifti.datatype = 768;
        img.hdrnifti.bitpix   = 32;
    case 'int64';
        img.hdrnifti.datatype = 1024;
        img.hdrnifti.bitpix   = 64;
    case 'uint64';
        img.hdrnifti.datatype = 1280;
        img.hdrnifti.bitpix   = 64;
    otherwise
        error('\nERROR: Uknown datatype or datatype I can not handle! [%s]', class(img.data));
end


% ---> prepare metadata

if isstruct(img.list)
    lists = fields(img.list)';
    s = '';
    for fname = lists
        fname = fname{1};
        if strcmp(fname, 'meta')
            metaname = img.list.meta;
        else
            if length(img.list.(fname)) ~= img.frames
                error('\nERROR: list %s length (%d) does not match number of image frames (%d)! Aborting img_saveimage!', fname, length(img.list.(fname)), img.frames);
            end
            if isnumeric(img.list.(fname))
                s = [s sprintf('# %s: %s\n', fname, num2str(img.list.(fname)))];
            elseif iscell(img.list.(fname))
                s = [s sprintf('# %s: %s\n', fname, strjoin(img.list.(fname)))];
            end
        end
    end
    img = img.img_embed_meta(s, [], metaname);
end


% ---> pack metadata

if img.hdrnifti.swap
    sw = @(x, c) typecast(swapbytes(cast(x, c)), 'uint8');
else
    sw = @(x, c) typecast(cast(x, c), 'uint8');
end

pt = 4;
if length(img.meta) > 0
    metadata = zeros(4 + sum([img.meta.size]), 1, 'uint8');
    metadata(1:4) = sw([1 0 0 0], 'uint8');
    for n = 1:length(img.meta)
        if verbose, fprintf('\n ---> preparing meta %d [%d bytes]', img.meta(n).code, img.meta(n).size); end
        metadata(pt+1:pt+4) = sw(img.meta(n).size, 'int32');
        metadata(pt+5:pt+8) = sw(img.meta(n).code, 'int32');
        metadata(pt+9:pt+img.meta(n).size) = img.meta(n).data;
        pt = pt + img.meta(n).size;
    end
else
    metadata = sw([0 0 0 0], 'uint8');
end


% ---> pack header

if img.hdrnifti.version == 1
    img.hdrnifti.vox_offset = 348 + pt;
    fhdr = packHeader_nifti1(img.hdrnifti);
elseif img.hdrnifti.version == 2
    img.hdrnifti.vox_offset = 540 + pt;
    fhdr = packHeader_nifti2(img.hdrnifti);
    if verbose, fprintf('\n ---> data at offset %d', img.hdrnifti.vox_offset); end
else
    error('\nERROR: Unknown NIfTI version!');
end



% ---> save it

nimage.img_save_nifti_mx(file, fhdr, img.data, metadata, img.hdrnifti.swapped == 1, verbose);



% ----- Pack NIfTI-1 Header


function [s] = packHeader_nifti1(hdrnifti)

    if hdrnifti.swap
        sw = @(x, c) typecast(swapbytes(cast(x, c)), 'uint8');
    else
        sw = @(x, c) typecast(cast(x, c), 'uint8');
    end

    s = zeros(348, 1, 'uint8');

    s(1:4)     =   sw(348                          , 'int32');
    s(5:14)    =   sw(hdrnifti.data_type           , 'uint8');
    s(15:32)   =   sw(hdrnifti.db_name             , 'uint8');
    s(33:36)   =   sw(hdrnifti.extents             , 'int32');
    s(37:38)   =   sw(hdrnifti.session_error       , 'int16');
    s(39)      =   sw(hdrnifti.regular             , 'uint8');
    s(40)      =   sw(hdrnifti.dim_info            , 'uint8');
    s(41:56)   =   sw(hdrnifti.dim                 , 'int16');
    s(57:60)   =   sw(hdrnifti.intent_p1           , 'single');
    s(61:64)   =   sw(hdrnifti.intent_p2           , 'single');
    s(65:68)   =   sw(hdrnifti.intent_p3           , 'single');
    s(69:70)   =   sw(hdrnifti.intent_code         , 'int16');
    s(71:72)   =   sw(hdrnifti.datatype            , 'int16');
    s(73:74)   =   sw(hdrnifti.bitpix              , 'int16');
    s(75:76)   =   sw(hdrnifti.slice_start         , 'int16');
    s(77:108)  =   sw(hdrnifti.pixdim              , 'single');
    s(109:112) =   sw(hdrnifti.vox_offset          , 'single');
    s(113:116) =   sw(hdrnifti.scl_slope           , 'single');
    s(117:120) =   sw(hdrnifti.scl_inter           , 'single');
    s(121:122) =   sw(hdrnifti.slice_end           , 'int16');
    s(123)     =   sw(hdrnifti.slice_code          , 'uint8');
    s(124)     =   sw(hdrnifti.xyzt_units          , 'uint8');
    s(125:128) =   sw(hdrnifti.cal_max             , 'single');
    s(129:132) =   sw(hdrnifti.cal_min             , 'single');
    s(133:136) =   sw(hdrnifti.slice_duration      , 'single');
    s(137:140) =   sw(hdrnifti.toffset             , 'single');
    s(141:144) =   sw(hdrnifti.glmax               , 'int32');
    s(145:148) =   sw(hdrnifti.glmin               , 'int32');
    s(149:228) =   sw(hdrnifti.descrip             , 'uint8');
    s(229:252) =   sw(hdrnifti.aux_file            , 'uint8');
    s(253:254) =   sw(hdrnifti.qform_code          , 'int16');
    s(255:256) =   sw(hdrnifti.sform_code          , 'int16');
    s(257:260) =   sw(hdrnifti.quatern_b           , 'single');
    s(261:264) =   sw(hdrnifti.quatern_c           , 'single');
    s(265:268) =   sw(hdrnifti.quatern_d           , 'single');
    s(269:272) =   sw(hdrnifti.qoffset_x           , 'single');
    s(273:276) =   sw(hdrnifti.qoffset_y           , 'single');
    s(277:280) =   sw(hdrnifti.qoffset_z           , 'single');
    s(281:296) =   sw(hdrnifti.srow_x              , 'single');
    s(297:312) =   sw(hdrnifti.srow_y              , 'single');
    s(313:328) =   sw(hdrnifti.srow_z              , 'single');
    s(329:344) =   sw(hdrnifti.intent_name(1:16)   , 'uint8');
    s(345:348) =   sw([hdrnifti.magic(1:3) char(0)], 'uint8');



% ----- Pack NIfTI-2 Header


function [s] = packHeader_nifti2(hdrnifti)

    if hdrnifti.swap
        sw = @(x, c) typecast(swapbytes(cast(x, c)), 'uint8');
    else
        sw = @(x, c) typecast(cast(x, c), 'uint8');
    end

    s = zeros(540, 1, 'uint8');

    s(1:4)     = sw(540,                     'int32');
    s(5:12)    = sw([hdrnifti.magic(1:3) char([0 13 10 26 10])],          'uint8');
    s(13:14)   = sw(hdrnifti.datatype,       'int16');
    s(15:16)   = sw(hdrnifti.bitpix,         'int16');
    s(17:80)   = sw(hdrnifti.dim,            'int64');
    s(81:88)   = sw(hdrnifti.intent_p1,      'double');
    s(89:96)   = sw(hdrnifti.intent_p2,      'double');
    s(97:104)  = sw(hdrnifti.intent_p3,      'double');
    s(105:168) = sw(hdrnifti.pixdim,         'double');
    s(169:176) = sw(hdrnifti.vox_offset,     'int64');
    s(177:184) = sw(hdrnifti.scl_slope,      'double');
    s(185:192) = sw(hdrnifti.scl_inter,      'double');
    s(193:200) = sw(hdrnifti.cal_max,        'double');
    s(201:208) = sw(hdrnifti.cal_min,        'double');
    s(209:216) = sw(hdrnifti.slice_duration, 'double');
    s(217:224) = sw(hdrnifti.toffset,        'double');
    s(225:232) = sw(hdrnifti.slice_start,    'int64');
    s(233:240) = sw(hdrnifti.slice_end,      'int64');
    s(241:320) = sw(hdrnifti.descrip,        'uint8');
    s(321:344) = sw(hdrnifti.aux_file,       'uint8');
    s(345:348) = sw(hdrnifti.qform_code,     'int32');
    s(349:352) = sw(hdrnifti.sform_code,     'int32');
    s(353:360) = sw(hdrnifti.quatern_b,      'double');
    s(361:368) = sw(hdrnifti.quatern_c,      'double');
    s(369:376) = sw(hdrnifti.quatern_d,      'double');
    s(377:384) = sw(hdrnifti.qoffset_x,      'double');
    s(385:392) = sw(hdrnifti.qoffset_y,      'double');
    s(393:400) = sw(hdrnifti.qoffset_z,      'double');
    s(401:432) = sw(hdrnifti.srow_x,         'double');
    s(433:464) = sw(hdrnifti.srow_y,         'double');
    s(465:496) = sw(hdrnifti.srow_z,         'double');
    s(497:500) = sw(hdrnifti.slice_code,     'int32');
    s(501:504) = sw(hdrnifti.xyzt_units,     'int32');
    s(505:508) = sw(hdrnifti.intent_code,    'int32');
    s(509:524) = sw(hdrnifti.intent_name,    'uint8');
    s(525)     = sw(hdrnifti.dim_info,       'uint8');
    s(526:540) = sw(hdrnifti.unused_str,     'uint8');


function [meta] = dtseriesXML(img)

    mpath = fileparts(mfilename('fullpath'));
    xml = fileread(fullfile(mpath, 'dtseries-32k.xml'));
    xml = strrep(xml,'{{ParentProvenance}}', img.filenamepath);
    xml = strrep(xml,'{{ProgramProvenance}}', 'QuNex');
    xml = strrep(xml,'{{Provenance}}', 'QuNex');
    xml = strrep(xml,'{{WorkingDirectory}}', pwd);
    xml = strrep(xml,'{{Frames}}', num2str(img.frames));
    xml = strrep(xml,'{{TR}}', num2str(img.TR));
    xml = cast(xml', 'uint8');
    meta = string2meta(xml, 32);


function [meta] = dscalarXML(img)

    mpath = fileparts(mfilename('fullpath'));
    xml = fileread(fullfile(mpath, 'dscalar-32k.xml'));
    xml = strrep(xml, '{{ParentProvenance}}', img.filenamepath);
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
    meta = string2meta(xml, 32);


function [meta] = string2meta(string, code)
    string = cast(string(:), 'uint8');
    meta.size = ceil((length(string)+8)/16)*16;
    meta.code = code;
    meta.data = zeros(1, meta.size-8, 'uint8');
    meta.data(1:length(string)) = string;

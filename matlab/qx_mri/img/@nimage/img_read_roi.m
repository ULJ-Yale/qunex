function [img] = img_read_roi(roiinfo, roi2, check)

%``img_read_roi(roiinfo, roi2, check)``
%
%   Reads in an ROI file, if a second file is provided, it uses it to mask the
%   first one.
%
%   Parameters
%       --roiinfo (str):
%           A path to a .names ROI information file.
%       --roi2 (str):
%           A path to the second ROI image file matching ROI codes
%           specified in the third column of the .names file. []
%       --check  (str):   
%           How to handle unknown integer codes from the .names file. Options
%           are: 
%
%           - 'ignore' (don't do anything)
%           - 'warning' (throw a warning)
%           - 'error' (throw an error)
%
%           Default is 'warning'.
%
%   Returns:
%       img
%           A nimage object with ROI coded using integer values and additional 
%           data structure 'roi' describing the ROI:
%
%           .roinames  - a cell array of ROI names
%           .roicodes  - a cell array of codes specifying the ROI
%           .roicodes1 - a cell array of group level codes specifying the ROI
%           .roicodes2 - a cell array of subject level codes specifying the ROI
%           .nvox      - an array specifying the number of voxels for each ROI
%           .roifile1  - path to the file providing group level specification
%           .roifile2  - path to the file providing subject level specification
%
%   Notes:
%       This method is being deprecated in favor of using img_prep_roi method
%       which provides a more robust and optimized representation of ROI and
%       enables using wider range of input sources for specifying ROI. Use
%       img_roi_old_2_new to transform old ROI objects to new ones.
%
%       The method is used to generate an ROI object. It also supports masking 
%       the original image (usually a group ROI fle) with the second ROI image 
%       (usually) a subject specific segmentation file.
%
%       If no file is specified as the second ROI, then no masking is performed. 
%       If a second file exists, it will be used to mask the original data based 
%       on the specified values in the third column of the .names file. 
%
%       The function supports the specification of region codes in the .names 
%       file using either numeric vaues (e.g. 3,8,9) or names. The names are 
%       based on FreeSurfer aseg+aparc segmentation. They are:
%
%       - lcgray  (left cortex gray matter)
%       - rcgray  (right cortex gray matter)
%       - cgray   (cortical gray matter)
%       - lsubc   (left subcortical gray matter)
%       - rsubc   (right subcortical gray matter)
%       - subc    (subcortical gray matter)
%       - lcerc   (left cerebellar gray matter)
%       - rcerc   (right cerelebbar gray matter)
%       - cerc    (cereberal gray matter)
%       - lgray   (left hemisphere gray matter)
%       - rgray   (right hemisphere gray matter)
%       - gray    (whole brain gray matter)
%
%   Names file specification:
%       Names file is a regular text file with .names extension. It specifies 
%       how to generate a ROI file. It has the following example form::
%
%           /path-to-resources/CCN_ROI.nii.gz
%           RDLPFC|1|rcgray
%           LDLPFC|2|lcgray
%           ACC|3,4|cgray
%
%       The above example file specifies three cognitive cotrol regions. The 
%       original ROI file is referenced by the first line of the .names file. If 
%       the path starts with a forward slash ('/'), it is assumed to be an 
%       absolute path, otherwise it is assumed to be a path relative to the 
%       location of the roiinfo '.names' file. If the line is empty or 
%       references "none", it is assumed that all the ROI are defined by the 
%       roi2 codes only.
%
%       The lines that follow specify the ROI to be generated with a pipe (|)
%       separated columns. The first column specifies the name of the ROI. The
%       second column specifies the integer codes that represent the desired 
%       region. There can be more than one code used and the ROI will be a union 
%       of all the specified, comma separated codes. The third column specifies 
%       the codes to be used to mask the ROI generated from the original file. 
%       If either the third or the second column is empty, the specified ROI 
%       from the original or secondary image file will be used. Again, If the 
%       first line is empty or set to none, only the third column will be used 
%       to generate ROI.
%
%       In the case when the generated ROI would overlap, a multivolume file is
%       generated with each volume specifying one ROI.
%
%   Examples:
%       To create a group level roi file::
%
%           roi = nimage.img_read_roi('resources/CCN.names')
%
%       To create a subject specific file::
%
%           roi = nimage.img_read_roi('resources/CCN.names', 'AP3345.aseg+aparc.nii.gz')
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

%   ---- Named region codes
rcodes.lcgray = [3 415 417 419 421:422 424 427 429 431 433 435 438 1000:1035 1100:1104 1200:1202 1205:1207 1210:1212 1105:1181 9000:9006 11100:11175];
rcodes.rcgray = [42 416 418 420 423 425:426 428 430 432 434 436 439 2000:2035 2100:2104 2105:2181 2200:2202 2205:2207 2210:2212 9500:9506 12100:12175 ];
rcodes.cgray  = [rcodes.lcgray rcodes.rcgray 220 222 225 226 400:414 437 ];

rcodes.lsubc  = [9:13 17:20 26:28 96 136 163 169 193:196 550 552:557];
rcodes.rsubc  = [48:56 58:60 97 137 164 176 197:200 500 502:507];
rcodes.subc   = [rcodes.lsubc rcodes.rsubc 16 170:175 203:209 212 214:218 226 7001:7020 7100:7101 8001:8014 ];

rcodes.lcerc  = [8 601 603 605 608 611 614 617 620 623 626 660:679];
rcodes.rcerc  = [47 602 604 607 610 613 616 619 622 625 628 640:659];
rcodes.cerc   = [rcodes.lcerc rcodes.rcerc 606 609 612 615 618 621 624 627];

rcodes.lgray  = [rcodes.lcgray rcodes.lsubc rcodes.lcerc];
rcodes.rgray  = [rcodes.rcgray rcodes.rsubc rcodes.rcerc];
rcodes.gray   = [rcodes.cgray rcodes.subc rcodes.cerc 702];

% rcodes.lcgray = [3 415 417 419 421:422 424 427 429 431 433 435 438 11100:11175 1000:1035 1100:1104 1200:1202 1205:1207 1210:1212 1105:1181];
% rcodes.rcgray = [42 416 418 420 423 425:426 428 430 432 434 436 439 12100:12175 2000:2035 2100:2104 2105:2181 2200:2202 2205:2207 2210:2212];
% rcodes.cgray  = [rcodes.lcgray rcodes.rcgray 220 222 225 400:414 437];
%
% rcodes.lsubc  = [9:13 17:20 26 27 96 193 195:196 9000:9006 550 552:557];
% rcodes.rsubc  = [48:56 58:59 97 197 199:200 9500:9506 500 502:507];
% rcodes.subc   = [rcodes.lsubc rcodes.rsubc 16 170:175 203:209 212 214:218 226 7001:7020 7100:7101 8001:8014];
%
% rcodes.lcerc  = [8 601 603 605 608 611 614 617 620 623 626 660:679];
% rcodes.rcerc  = [47 602 604 607 610 613 616 619 622 625 628 640:659];
% rcodes.cerc   = [rcodes.lcerc rcodes.rcerc 606 609 612 615 618 621 624 627];
%
% rcodes.lgray  = [rcodes.lcgray rcodes.lsubc rcodes.lcerc];
% rcodes.rgray  = [rcodes.rcgray rcodes.rsubc rcodes.rcerc];
% rcodes.gray   = [rcodes.cgray rcodes.subc rcodes.cerc];


%   ---- Go on ...

if nargin < 2 || isempty(roi2),     roi2 = 'none';    end
if nargin < 3 || isempty(check),   check = 'warning'; end

if ~any(strcmpi({'ignore','warning','error'}, check))
    error('\nERROR: Option [%s] for check argument is invalid! Valid options are ''ignore'', ''warning'' and ''error''.\n', check);
end

% ---> Read the ROI info

if isempty(strfind(roiinfo, '.names'))
    img = nimage(roiinfo);
    img.data = img.image2D;
    rcodes = unique(img.data);
    rcodes = sort(rcodes(rcodes > 0));
    for r = 1:length(rcodes)
        img.data(img.data == rcodes(r)) = r;
        img.roi.roinames{r} = ['ROI' num2str(r)];
        img.roi.roicodes(r) = r;
        img.roi.roicodes1{r} = rcodes(r);
        img.roi.roicodes2{r} = [];
        img.roi.nvox(r) = sum(img.data == r);
    end
    img.roi.roifile1  = roiinfo;
    img.roi.roifile2  = [];
    return
end

roiinfo = strtrim(roiinfo);
rois    = fopen(roiinfo);
roif1   = fgetl(rois);

if ~isa(roi2, 'nimage')
    roi2 = strtrim(roi2);
    if strcmp(roi2, 'none')
        roi2 = [];
    end
end

c = 0;
while feof(rois) == 0
    s = fgetl(rois);
    if length(s) < 3 || s(1) == '#'
        continue
    end
    c = c + 1;
    
    relements   = regexp(s, '\|', 'split');
    if length(relements) == 3
        roinames{c}  = relements{1};
        roicodes1{c} = getCodes(relements{2}, rcodes);
        roicodes2{c} = getCodes(relements{3}, rcodes);
    else
        fprintf('\n WARNING: Not all fields present in ROI definition: ''%s'' ??? skipping ROI.', s);
    end
end
nroi = c;
fclose(rois);

% ---> Read the first ROI file

if strcmp('none', roif1) || isempty(roif1)
    roi1 = [];
else
    if roif1(1) ~= '/';
        roif1 = fullfile(fileparts(roiinfo), roif1);
    end
    roi1 = nimage(roif1);
    roi1.data = roi1.image2D;
end

% ---> Read the second ROI file if needed

if ~isa(roi2, 'nimage') & ~isempty(roi2)
    roi2 = nimage(roi2);
    roi2.data = roi2.image2D;
    roif2 = roi2.filenamepath;
else
    if isa(roi2, 'nimage')
        roif2 = roi2.filenamepath;
        roi2.data = roi2.image2D;
    else
        roif2 = roi2;
    end
end


% ---> Set up final ROI image

if isempty(roi2)
    img = roi1.zeroframes(nroi);
else
    img = roi2.zeroframes(nroi);
end

% ---> Check whether ROI codes from .names file exist in images

if isa(roi1, 'nimage')
    for i=1:length(roicodes1)
        for j=1:length(roicodes1{i})
            if ~any(roi1.data == roicodes1{i}(j))
                switch lower(check)
                    case 'warning'
                        warning('\nimg_read_roi: Code [%d] does not exist in %s!\n',roicodes1{i}(j), roif1);
                    case 'error'
                        error('\nERROR: Code [%d] does not exist in %s!\n',roicodes1{i}(j), roif1);
                end
            end
        end
    end
end

if isa(roi2, 'nimage')
    for i=1:length(roicodes2)
        for j=1:length(roicodes2{i})
            if ~any(roi2.data == roicodes2{i}(j))
                switch lower(check)
                    case 'warning'
                        warning('\nimg_read_roi: Code [%d] does not exist in %s!\n',roicodes2{i}(j), roif2);
                    case 'error'
                        error('\nERROR: Code [%d] does not exist in %s!\n',roicodes2{i}(j), roif2);
                end
            end
        end
    end
end

% ---> Process ROI

for n = 1:nroi
    
    if ((length(roicodes1{n}) == 0 || isempty(roi1)) & (~isempty(roi2)))
        rmask = roi2.img_roi_mask(roicodes2{n});
    elseif ((length(roicodes2{n}) == 0 || isempty(roi2)) & (~isempty(roi1)))
        rmask = roi1.img_roi_mask(roicodes1{n});
    elseif ((~isempty(roi2)) & (~isempty(roi1)));
        rmask = roi1.img_roi_mask(roicodes1{n}) & roi2.img_roi_mask(roicodes2{n});
    else
        rmask = [];
    end
    
    img.data(rmask==1, n) = n;
    img.roi.nvox(n) = sum(rmask==1);
    
end

% ---> Collapse to a single volume when there is no overlap between ROI

if max(sum(img.data > 0, 2)) == 1
    img.data   = sum(img.data, 2);
    img.frames = 1;
end

% ---> Encode metadata

img.roi.roinames  = roinames;
img.roi.roicodes  = [1:nroi];
img.roi.roicodes1 = roicodes1;
img.roi.roicodes2 = roicodes2;
img.roi.roifile1  = roif1;
img.roi.roifile2  = roif2;


function [codes] = getCodes(s, rcodes)

    codes = [];
    s = strtrim(regexp(s, ',', 'split'));
    for n = 1:length(s)
        if ~isempty(s{n})
            if min(isstrprop(s{n}, 'digit'))
                codes = [codes str2num(s{n})];
            elseif isfield(rcodes, s{n})
                codes = [codes rcodes.(s{n})];
            else
                fprintf('\n WARNING: Ignoring unknown region code name: ''%s''!', s{n});
            end
        end
    end


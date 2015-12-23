function [img] = mri_ReadROI(roiinfo, roi2)

%function [img] = mri_ReadROI(roiinfo, roifile)
%
%		Reads in an ROI file, if a second file is provided, it uses it to mask the first one.
%
%       roiinfo - a names formated ROI information file
%       roifile - a path to the second roifile
%
%
%    (c) Grega Repovs, 2010-05-10
%
%   ---- Changelog ----
%   2013-07-24 Grega Repovs - adjusted to create either single or multiple volume ROI
%   2015-12-08 Grega Repovs - added option for named region codes

%   ---- Named region codes

rcodes.lcgray = [3 415 417 419 421:422 424 427 429 431 433 435 438 11100:11175 1000:1035 1100:1104 1200:1202 1205:1207 1210:1212 1105:1181];
rcodes.rcgray = [42 416 418 420 423 425:426 428 430 432 434 436 439 12100:12175 2000:2035 2100:2104 2105:2181 2200:2202 2205:2207 2210:2212];
rcodes.cgray  = [rcodes.lcgray rcodes.rcgray 220 222 225 400:414 437];

rcodes.lsubc  = [9:13 17:20 26 27 96 193 195:196 9000:9006 550 552:557];
rcodes.rsubc  = [48:56 58:59 97 197 199:200 9500:9506 500 502:507];
rcodes.subc   = [rcodes.lsubc rcodes.rsubc 16 170:175 203:209 212 214:218 226 7001:7020 7100:7101 8001:8014];

rcodes.lcerc  = [8 601 603 605 608 611 614 617 620 623 626 660:679];
rcodes.rcerc  = [47 602 604 607 610 613 616 619 622 625 628 640:659];
rcodes.cerc   = [rcodes.lcerc rcodes.rcerc 606 609 612 615 618 621 624 627];

rcodes.lgray  = [rcodes.lcgray rcodes.lsubc rcodes.lcerc];
rcodes.rgray  = [rcodes.rcgray rcodes.rsubc rcodes.rcerc];
rcodes.gray   = [rcodes.cgray rcodes.subc rcodes.cerc];


%   ---- Go on ...

if nargin < 2
    roi2 = 'none';
end

% ----> Read the ROI info

if isempty(strfind(roiinfo, '.names'))
    img = gmrimage(roiinfo);
    img.data = img.image2D;
    rcodes = unique(img.data);
    rcodes = sort(rcodes(rcodes > 0));
    for r = 1:length(rcodes)
        img.data(img.data == rcodes(r)) = r;
        img.roi.roinames{r} = ['ROI' num2str(r)];
        img.roi.roicodes(r) = r;
        img.roi.roicodes1{r} = rcodes(r);
        img.roi.roicodes2{r} = [];
    end
    img.roi.roifile1  = roiinfo;
    img.roi.roifile2  = [];
    return
end

roiinfo = strtrim(roiinfo);
roi2    = strtrim(roi2);
rois    = fopen(roiinfo);
roif1   = fgetl(rois);

if strcmp(roi2, 'none')
    roi2 = [];
end

c = 0;
while feof(rois) == 0
	s = fgetl(rois);
    if length(s) < 3
        continue
    end
	c = c + 1;

    relements   = regexp(s, '\|', 'split');
    if length(relements) == 3
        roinames{c}  = relements{1};
        roicodes1{c} = getCodes(relements{2}, rcodes);
        roicodes2{c} = getCodes(relements{3}, rcodes);
    else
        fprintf('\n WARNING: Not all fields present in ROI definition: ''%s'' — skipping ROI.', s);
    end
end
nroi = c;
fclose(rois);

% ----> Read the first ROI file

if strcmp('none',roif1)
    roi1 = [];
else
    roi1 = gmrimage(roif1);
    roi1.data = roi1.image2D;
end

% ----> Read the second ROI file if needed

if ~isa(roi2, 'gmrimage') & ~isempty(roi2)
    roi2 = gmrimage(roi2);
    roi2.data = roi2.image2D;
    roif2 = roi2.filename;
else
    if isa(roi2, 'gmrimage')
        roif2 = roi2.filename;
        roi2.data = roi2.image2D;
    else
        roif2 = roi2;
    end
end


% ----> Set up final ROI image

if isempty(roi2)
    img = roi1.zeroframes(nroi);
else
    img = roi2.zeroframes(nroi);
end




% ----> Process ROI

for n = 1:nroi

    if ((length(roicodes1{n}) == 0 | isempty(roi1)) & (~isempty(roi2)))
	    rmask = roi2.mri_ROIMask(roicodes2{n});
	elseif ((length(roicodes2{n}) == 0 | isempty(roi2)) & (~isempty(roi1)))
        rmask = roi1.mri_ROIMask(roicodes1{n});
    elseif ((~isempty(roi2)) & (~isempty(roi1)));
	    rmask = roi1.mri_ROIMask(roicodes1{n}) & roi2.mri_ROIMask(roicodes2{n});
	else
	    rmask = [];
	end

    img.data(rmask==1, n) = n;
    img.roi.nvox(n) = sum(rmask==1);

end

% ----> Collapse to a single volume when there is no overlap between ROI

if max(sum(img.data > 0, 2)) == 1
    img.data   = sum(img.data, 2);
    img.frames = 1;
end


% ----> Encode metadata

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


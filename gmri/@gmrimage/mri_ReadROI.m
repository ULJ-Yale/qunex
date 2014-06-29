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
%

if nargin < 2
    roi2 = 'none';
end

% ----> Read the ROI info

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
	c = c + 1;
	[roinames{c},s] = strtok(s, '|');
    [t, s] = strtok(s, '|');
    roicodes1{c} = sscanf(t,'%d,');
    [t] = strtok(s, '|');
	roicodes2{c} = sscanf(t,'%d,');
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


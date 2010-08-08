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

if nargin < 2
    roi2 = [];
end

% ----> Read the ROI info

rois = fopen(roiinfo);
roif1 = fgetl(rois);

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
end

% ----> Read the second ROI file if needed

if ~isa(roi2, 'gmrimage') & ~isempty(roi2)
    roi2 = gmrimage(roi2);
end

% ----> Set up final ROI image

if isempty(roif2)
    img = roi1.zeroframes(1);
else
    img = roi2.zeroframes(1);
end

% ----> Process ROI

for n = 1:nroi
    
    if ((length(roicodes1{n}) == 0 | isempty(roi1)) & (~isempty(roi2)))
	    rmask = ismember(roi2.data,roicodes2{n});
	elseif ((length(roicodes2{n}) == 0 | isempty(roi2)) & (~isempty(roi1)))
	    rmask = ismember(roi1.data,roicodes1{n});
    elseif ((~isempty(roi2)) & (~isempty(roi1)))		    
	    rmask = ismember(roi1.data,roicodes1{n}) & ismember(roi2.data,roicodes2{n});
	else
	    rmask = [];
	end
    
    img.data(rmask==1) = n;

end

img.roi.roinames  = roinames;
img.roi.roicodes1 = roicodes1;
img.roi.roicodes2 = roicodes2;
img.roi.roifile1  = roif1;
img.roi.roifile2  = roif2;


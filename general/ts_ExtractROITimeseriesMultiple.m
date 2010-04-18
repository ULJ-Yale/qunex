function [] = ts_ExtractROITimeseriesMultiple(flist, roiinfo, inmask, targetf)

%	
%	ts_ExtractROITimeseries
%
%	Extracts and saves ROI timeseries.
%	
%	flist   	- a list of bolds to extract, one per line: "subject number|subject id|bold file path"
%	roiinfo		- a file listing ROI files and regions to use
%	roinfile	- file with region names, one region per line in format: "value\tname"
%	inmask		- an array mask defining which frames to use (1) and which not (0)
%               - if scalar it signifies how many frames to skip at the beginning of each run
%	tagetf		- a filename for the extracted timeseries
%
% 	Created by Grega Repovš on 2008-07-02.
%   Adjusted format for multiple subjects and ROI files on 2009-01-22
%
% 	Copyright (c) 2008. All rights reserved.


fprintf('\n\nStarting ...');

startframe = 1;
if length(inmask) == 1
    startframe = inmask + 1;
    inmask = [];
end


%   ------------------------------------------------------------------------------------------
%   ------------------------------------------------ get list of region codes and region names

fprintf('\n ... reading ROI info');

roiname = {};

rois = fopen(roiinfo);
roif1 = fgetl(rois);

c = 0;
while feof(rois) == 0
	s = fgetl(rois);
	c = c + 1;
	[roiname{c},s] = strtok(s, '|');
    [t, s] = strtok(s, '|');
    roicode1{c} = sscanf(t,'%d,');
    [t] = strtok(s, '|');
	roicode2{c} = sscanf(t,'%d,');
	fprintf('\nroi1 %d', roicode1{c});
	fprintf('\nroi2 %d', roicode2{c});
end
nroi = c;
fclose(rois);

fprintf(' ... done.');


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------------- make a list of all the files to process

fprintf('\n ... listing files to process');

files = fopen(flist);
c = 0;
while feof(files) == 0
    s = fgetl(files);
    if length(strfind(s, 'subject id:')>0)
        c = c + 1;
        [t, s] = strtok(s, ':');        
        subject(c).id = s(2:end);
        nf = 0;
    elseif length(strfind(s, 'roi:')>0)
        [t, s] = strtok(s, ':');        
        subject(c).roi = s(2:end);
    elseif length(strfind(s, 'file:')>0)
        nf = nf + 1;
        [t, s] = strtok(s, ':');        
        subject(c).files{nf} = s(2:end);
    end
end

fprintf(' ... done.');


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------- The main loop ... go through all the subjects

%   --- Get variables ready first

fprintf('\n ... reading ROI image');
if strcmp('none',roif1)
    roi1 = ones(48*48*64,1);
else
    roi1 = g_Read4DFP(roif1, 'int8');
end
fprintf('... done.');

nsub = length(subject);
for n = 1:nsub

    y = [];
    
	%   --- reading in image files

	fprintf('\n ... processing %s', subject(n).id);
	fprintf('\n     ... reading image file(s)');
	
	nfiles = length(subject(n).files);
    
    sumframes = 0;
	if nfiles > 1
		for m = 1:nfiles
			in = g_Read4DFP(subject(n).files{m}, 'single');
			nframes = size(in,1)/(48*48*64);
			in = reshape(in, 48*48*64, nframes);
			y = [y in(:,startframe:end)];
			fprintf(' %d ', m);
			sumframes = sumframes + nframes;
		end
		in = [];
	else
		fim = fopen(subject(n).files{1}, 'r', 'b');
		y = fread(fim, 'float32=>single');
		fclose(fim);
		nframes = size(y,1)/(48*48*64);
		y = reshape(y, 48*48*64, nframes);
		y = y(:,startframe:end);
		sumframes = nframes;
	end

	fprintf(' ... %d frames read, done.', sumframes);
	
	if (isempty(inmask))
		mask = ones(1, nframes);
	else
		mask = inmask;
		if (size(mask,2) ~= nframes)
			fprintf('\n\nERROR: Length of img files (%d frames) does not match length of mask (%d frames).', nframes, size(mask,2));
		end
	end
	
	if (min(mask) == 0)
		fprintf(' ... masking.');
		y = y(:,mask==1);
	end
	N = size(y, 2);
	y = y'; 
	
	% --- extracting timeseries for each region
	
	fprintf('\n     ... extracting timeseries from region ');
	
	if strcmp('none',subject(n).roi)
        roi2 = ones(48*48*64,1);
    else
        roi2 = g_Read4DFP(subject(n).roi, 'int8');
    end
	
	for m = 1:nroi
	
		fprintf(' %s', roiname{m});
		
		if (length(roicode1{m}) == 0)
		    rmask = ismember(roi2,roicode2{m});
		elseif (length(roicode2{m}) == 0)
		    rmask = ismember(roi1,roicode1{m});
	    else		    
		    rmask = ismember(roi1,roicode1{m}) & ismember(roi2,roicode2{m});
		end
		
		roits = mean(y(:, rmask),2);
		
		ts{n}(:,m) = roits;
	
	end

end


%   ---------------------------------------------
%   --- Save it all


fprintf('\n\n... saving timeseries');

data.ts = ts;
data.regions = roiname;
data.subject = subject;
data.subjects = {subject.id}

save(targetf, 'data')

fprintf('\n\n FINISHED!\n\n');



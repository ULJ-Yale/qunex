function [] = ts_ExtractROITimeseries(flist, roif, roinfile, inmask, targetf)

%	
%	ts_ExtractROITimeseries
%
%	Extracts and saves ROI timeseries.
%	
%	flist   	- conc style list of subject image files or conc files, header row, one subject per line
%	roif		- 4dfp image file with ROI
%	roinfile	- file with region names, one region per line in format: "value\tname"
%	mask		- an array mask defining which frames to use (1) and which not (0)
%               - if scalar it signifies how many frames to skip at the beginning of each run
%	tagetf		- a filename for the extracted timeseries
%
% 	Created by Grega Repovš on 2008-07-02.
% 	Copyright (c) 2008. All rights reserved.


fprintf('\n\nStarting ...');

startframe = 1;
if length(inmask) == 1
    startframe = inmask + 1;
    inmask = [];
end


%   ------------------------------------------------------------------------------------------
%   ------------------------------------------------ get list of region codes and region names

fprintf('\n ... reading ROI names');

roicode = [];
roiname = {};

rois = fopen(roinfile);
c = 0;
while feof(rois) == 0
	s = fgetl(rois);

	c = c + 1;
	[roistr, roiname{c}] = strtok(s, '|');
	roiname{c} = strrep(roiname{c}, '|', '');
	roicode(c) = str2num(roistr);
end
nroi = c;
fclose(rois);

fprintf(' ... done.');

%   ------------------------------------------------------------------------------------------
%   -------------------------------------------------- make a list of all the files to process

fprintf('\n ... listing files to process');

sfiles = g_ReadConcFile(flist);
nsub = length(sfiles);

% --- check if files are concs and read them if so

for n = 1:nsub

	cfile = sfiles{n};
	if (findstr(char(cfile), '.conc'))
%	if (cfile(length(cfile)-5:end) == '.conc')
		subject(n).files = g_ReadConcFile(cfile);
	else
		subject(n).files{1} = cfile;
	end

end

fprintf(' ... done.');


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------- The main loop ... go through all the subjects

%   --- Get variables ready first

fprintf('\n ... reading ROI image');
roi		 = g_Read4DFP(roif, 'int8');
fprintf('... done.');

for n = 1:nsub

    y = [];
    
	%   --- reading in image files

	fprintf('\n ... processing %s', char(sfiles{n}));
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
	
	for m = 1:nroi
	
		fprintf(' %s', roiname{m});
		
		rmask = roi == roicode(m);
		roits = mean(y(:, rmask),2);
		
		ts{n}(:,m) = roits;
	
	end

end


%   ---------------------------------------------
%   --- Save it all


fprintf('\n\n... saving timeseries');

data.ts = ts;
data.regions = roiname;
data.files = sfiles;

save(targetf, 'data')

fprintf('\n\n FINISHED!\n\n');



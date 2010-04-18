function [] = fc_ExtractROITimeseriesMasked(flist, roiinfo, inmask, targetf, options)

%	
%	fc_ExtractROITimeseriesMasked
%
%	Extracts and saves region timeseries defined by provided roiinfo file
%	
%	flist   	- conc style list of subject image files or conc files, header row, one subject per line
%   inmask      - per run mask information, number of frames to skip or a vector of frames to keep (1) and reject (0)
%	roiinfo	    - file with region names, one region per line in format: "value|group roi values|subject roi values"
%	tagetf		- the matlab file to save timeseries in
%   options     - options for alternative output: t - create a tab delimited text file, m - create a matlab file (default)
%
%	
% 	Created by Grega Repovš on 2009-06-25.
%   Adjusted for a different file list format and an additional ROI mask - 2008-01-23
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
	%fprintf('\nroi1 %d', roicode1{c});
	%fprintf('\nroi2 %d', roicode2{c});
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
nsub = length(subject);

fprintf(' ... done.');

%   ---------------------------------------------
%   --- set up datastructure to save results

for n = 1:nsub
    data.subjects{n} = subject(n).id;
end

data.roinames = roiname;
data.roicodes1 = roicode1;
data.roicodes2 = roicode1;


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------- The main loop ... go through all the subjects

%   --- Get variables ready first

fprintf('\n ... reading ROI image');

if strcmp('none',roif1)
    roi1 = ones(48*48*64,1);
else
    roi1 = g_Read4DFP(roif1);
end

fprintf('\n ... done.');
book = [786 147456];
y = zeros(book, 'single');


data.timeseries = {};                % ---> cell array to store subjects' timeseries

for n = 1:nsub

	%   --- reading in image files

	fprintf('\n ... processing %s', subject(n).id);
	fprintf('\n     ... reading image file(s)');

	y = [];

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
	nframes = size(y,2); 
			
	%   --- extracting timeseries for each region
	
    roi2 = g_Read4DFP(subject(n).roi);
    roits = zeros(nframes, nroi);
    
    fprintf('\n     ... extracting timeseries for:');
    
	n_roi_vox = zeros(nroi,1);
	for m = 1:nroi
	
		fprintf(' %s', roiname{m});
		
		if (length(roicode1{m}) == 0)
		    rmask = ismember(roi2,roicode2{m});
		elseif (length(roicode2{m}) == 0)
		    rmask = ismember(roi1,roicode1{m});
	    else		    
		    rmask = ismember(roi1,roicode1{m}) & ismember(roi2,roicode2{m});
		end
		
		n_roi_vox(m) = sum(rmask);	
		roits(:,m) = mean(y(rmask, :),1)';
			
	end
    
    data.n_roi_vox{n} = n_roi_vox;
    data.timeseries{n} = roits;
    
end


%   ---------------------------------------------
%   --- save data


fprintf('... saving ...');

if ismember('m', options)
    save(targetf, 'data');
end

if ismember('t', options)
    
    % -- open file and print header
    
    [fout message] = fopen([targetf '.txt'],'w');
    fprintf(fout, 'subject');
    for ir = 1:nroi
        fprintf(fout, '\t%s', roiname{ir});
    end
    
    % -- print data
    
    for is = 1:nsub
        ts = data.timeseries{is};
        tslen = size(ts,1);
        for it = 1:tslen
            fprintf(fout, '\n%s', data.subjects{is});
            fprintf(fout, '\t%.5f', ts(it,:));
        end
    end
    
    % -- close file
    
    fclose(fout);
end

fprintf('\n\n FINISHED!\n\n');



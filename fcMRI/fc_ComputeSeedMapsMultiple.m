function [] = fc_ComputeSeedMapsMultiple(flist, roiinfo, inmask, options, targetf)

%	
%	fc_ComputeSeedMaps
%
%	A memory optimised version of the script.
%	
%	Computes seed based correlations maps for individuals as well as group maps.
%	
%	flist   	- conc style list of subject image files or conc files, header row, one subject per line
%	roif		- 4dfp image file with ROI
%	roinfile	- file with region names, one region per line in format: "value\tname"
%	mask		- an array mask defining which frames to use (1) and which not (0)
%	options		- a string defining which subject files to save
%		r		- save map of correlations
%		f		- save map of Fisher z values
%		z		- save map of Z scores
%	tagetf		- the folder to save images in
%
%	It saves group files:
%		_group_Fz	- average Fz over all the subjects
%		_group_r	- average Fz converted back to Pearson r
%		_group_Z	- p values converted to Z scores based on t-test testing if Fz over subject differ significantly from 0 (two-tailed)
%	
% 	Created by Grega Repovš on 2008-02-07.
%   Adjusted for a different file list format and an additional ROI mask - 2008-01-23
% 	Copyright (c) 2008. All rights reserved.

go = true;

fprintf('\n\nChecking ...\n');
go = go & g_CheckFile(flist, 'image file list','error');
go = go & g_CheckFile(roiinfo, 'ROI definition file','error');
g_CheckFolder(targetf, 'results folder');

if ~go
	fprintf('ERROR: Some files were not found. Please check the paths and start again!\n\n');
	return
end


% ---- list name

[fpathstr, fname, fext, fversn] = fileparts(flist);

lname = strrep(fname, '.list', '');
lname = strrep(lname, '.conc', '');
lname = strrep(lname, '.4dfp', '');
lname = strrep(lname, '.img', '');


% ---- starts


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
nsub = length(subject);

fprintf(' ... done.');


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------- The main loop ... go through all the subjects

%   --- Get variables ready first

fprintf('\n ... reading ROI image');

g_fz_img = zeros(48*48*64,nsub,nroi);
if strcmp('none',roif1)
    roi1 = ones(48*48*64,1);
else
    roi1 = g_Read4DFP(roif1, 'int8');
    if ~roi1
    	return
    end
end

fprintf('\n ... done.');
book = [786 147456];

x = zeros(book, 'single');
y = zeros(book, 'single');

for n = 1:nsub

	%   --- reading in image files

	fprintf('\n ... processing %s', subject(n).id);
	fprintf('\n     ... reading image file(s)');

	y = [];

	nfiles = length(subject(n).files);
	
	sumframes = 0;
	if nfiles > 1
		for m = 1:nfiles
		    fprintf('\n     ... %s', subject(n).files{m});
			in = g_Read4DFP(subject(n).files{m}, 'single');
			nframes = size(in,1)/(48*48*64);
			in = reshape(in, 48*48*64, nframes);
			y = [y in(:,startframe:end)];
			fprintf(' %d ', m);
			sumframes = sumframes + nframes;
		end
		in = [];
	else
	    fprintf('\n     ... %s', subject(n).files{1});
		fim = fopen(subject(n).files{1}, 'r', 'b');
		y = fread(fim, 'float32=>single');
		fclose(fim);
		nframes = size(y,1)/(48*48*64);
		y = reshape(y, 48*48*64, nframes);
		y = y(:,startframe:end);
		sumframes = nframes;
	end

	fprintf('\n     ... %d frames read, done.', sumframes);
	
	if (isempty(inmask))
		mask = ones(1, nframes);
	else
		mask = inmask;
		mask = reshape(mask, 1, []);
		if (size(mask,2) ~= sumframes)
			fprintf('\n\nERROR: Length of img files (%d frames) does not match length of mask (%d frames).', sumframes, size(mask,2));
		end
	end
	
	if (min(mask) == 0)
		fprintf(' ... masking.');
		y = y(:,mask==1);
	end
	N = size(y, 2);
	Nr = N-1;
	y = y; 
	y = zscore(y,0,2);
    y = y./sqrt(Nr);
	
	%   --- creating base filename
	
	[fpathstr, fname, fext, fversn] = fileparts(subject(n).id);
	
	bname = strrep(fname, '.conc', '');
	bname = strrep(bname, '.4dfp', '');
	bname = strrep(bname, '.img', '');
		
	%   --- doing correlations for each region
	
	if strcmp('none',subject(n).roi)
        roi2 = ones(48*48*64,1);
    else
        roi2 = g_Read4DFP(subject(n).roi);
    end
	
	for m = 1:nroi
	
		fprintf('\n     ... computing correlation map for seed region %s ', roiname{m});
		
		if (length(roicode1{m}) == 0)
		    rmask = ismember(roi2,roicode2{m});
		elseif (length(roicode2{m}) == 0)
		    rmask = ismember(roi1,roicode1{m});
	    else		    
		    rmask = ismember(roi1,roicode1{m}) & ismember(roi2,roicode2{m});
		end
		
		x = mean(y(rmask,:),1)';

		% ------------------------> compute correlation
    
		% r = (N*sum(x.*y, 1) - sum(x,1).*sum(y,1))./sqrt((N*sum(x.^2, 1) - sum(x,1).^2).*(N*sum(y.^2, 1) - sum(y,1).^2));		fprintf('.');
		r = y * x;
			
		% ------------------------> compute Fz and significance

		Fz = fc_Fisher(r);			fprintf('.');
		
		if strfind(options, 'z')
			Z = Fz/(1/sqrt(N-3));			fprintf('.');
		end
		
		fprintf(' done.');
		
		% ------------------------> saving images
		
		if (length(options)>0)
			fprintf('\n     ... saving images');
			
			ifhextra.key = 'number of samples';
			ifhextra.value = int2str(N);
			
			if strfind(options, 'r')
				g_Save4DFP([targetf '/' bname '_' lname '_' roiname{m} '_r.4dfp.img'], r, ifhextra); 		fprintf(' r');
			end
			if strfind(options, 'f')
				g_Save4DFP([targetf '/' bname '_' lname '_' roiname{m} '_Fz.4dfp.img'], Fz, ifhextra); 	fprintf(' Fz');
			end
			if strfind(options, 'z')
				g_Save4DFP([targetf '/' bname '_' lname '_' roiname{m} '_Z.4dfp.img'], Z, ifhextra); 		fprintf(' Z');
			end
			
			fprintf(' ... done.');

		end
		
		g_fz_img(:,n,m) = reshape(Fz, 48*48*64, 1);

		r = []; Fz = []; Z = [];
	
	end

end


%   ---------------------------------------------
%   --- And now group results


fprintf('\n\n... computing group results');


%   --- setting up file details

ifhextra.key = 'number of subjects';
ifhextra.value = int2str(nsub);

for n = 1:nsub
    ifhextra_all(n).key = ['subject ' int2str(n)];
    ifhextra_all(n).value = subject(n).id;
end

%   --- running ROI loop

for m = 1:nroi

	fprintf('\n    ... for region %s', roiname{m});

	Fz = g_fz_img(:,:,m)';
	p  = fc_ttest(Fz);
	Fz = mean(Fz,1);
%	Z = fc_ptoz(1-(p),0,1) .* sign(Fz);
	Z = icdf('Normal', (1-(p/2)), 0, 1) .* sign(Fz);
	r = fc_FisherInv(Fz);
	
	fprintf('... saving ...');

	g_Save4DFP([targetf '/' lname '_' roiname{m} '_group_r.4dfp.img'], r, ifhextra); 		fprintf(' r');
	g_Save4DFP([targetf '/' lname '_' roiname{m} '_group_Fz.4dfp.img'], Fz, ifhextra); 	    fprintf(' Fz');
	g_Save4DFP([targetf '/' lname '_' roiname{m} '_group_Z.4dfp.img'], Z, ifhextra); 		fprintf(' Z');
	g_Save4DFP([targetf '/' lname '_' roiname{m} '_all_Fz.4dfp.img'], g_fz_img(:,:,m), ifhextra_all); 	fprintf(' all Fz');
	
	fprintf(' ... done.');

end

fprintf('\n\n FINISHED!\n\n');



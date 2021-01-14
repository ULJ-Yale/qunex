function [] = fc_ComputeSeedMaps(flist, roif, roinfile, inmask, options, targetf)

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

g_fz_img = zeros(48*48*64,nsub,nroi);
roi		 = g_Read4DFP(roif, 'int8');

fprintf('\n ... done.');
book = [786 147456];

x = zeros(book, 'single');
y = zeros(book, 'single');
%sx = zeros(book);
%sy = zeros(book);
%sx2 = zeros(book);
%sy2 =zeros(book);
%sxy = zeros(book);
%r = zeros(book);
%Fz = zeros(book);
%Z = zeros(book);

for n = 1:nsub

	%   --- reading in image files

	fprintf('\n ... processing %s', char(sfiles{n}));
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
	N = size(y, 2);
	y = y'; 
	
	%   --- creating base filename
	
	[fpathstr, fname, fext, fversn] = fileparts(sfiles{n});
	
	bname = strrep(fname, '.conc', '');
	bname = strrep(bname, '.4dfp', '');
	bname = strrep(bname, '.img', '');
		
	%   --- doing correlations for each region
	
	% --- get memory
	
	%book = size(y);
	%x = [];
	%x = zeros(book, 'single');
		
	
	for m = 1:nroi
	
		fprintf('\n     ... computing correlation map for seed region %s ', roiname{m});
		
		rmask = roi == roicode(m);
		roits = mean(y(:, rmask),2);
		
		% ------------------------> setting up
	 			
		x = [];
		x = repmat(roits,1,147456);
		fprintf('.');

		% ------------------------> compute correlation

   % 	sx = sum(x,1);			fprintf('.');
   % 	sy = sum(y,1);			fprintf('.');
   % 	sx2 = sum(x.*x, 1);		fprintf('.');
   % 	sy2 = sum(y.*y, 1);		fprintf('.');
   % 	sxy = sum(x.*y, 1);		fprintf('.');
   % 
   % 	r = (N*sxy - sx.*sy)./sqrt((N*sx2 - sx.*sx).*(N*sy2 - sy.*sy));		fprintf('.');
   % 	
   % 	sx = []; sy = []; sx2 = []; sy2 =[]; sxy = []; 
		
		
	
		% ------------------------> alternate computation of correlation

	%	sx = sum(x,1);			fprintf('.');
	%	sy = sum(y,1);			fprintf('.');
	%	sx2 = sum(x.*x, 1);		fprintf('.');
	%	sy2 = sum(y.*y, 1);		fprintf('.');
	%	sxy = sum(x.*y, 1);		fprintf('.');
    
		r = (N*sum(x.*y, 1) - sum(x,1).*sum(y,1))./sqrt((N*sum(x.^2, 1) - sum(x,1).^2).*(N*sum(y.^2, 1) - sum(y,1).^2));		fprintf('.');
		
	%	sx = []; sy = []; sx2 = []; sy2 =[]; sxy = []; 
	
	
	
	
	
	% ---- alternative
	
  %	 y = img';
  %	 x = roits';
  %	 [r, p] = corr(y, x);
	
		% ------------------------> compute Fz and significance

		Fz = fc_Fisher(r);			fprintf('.');
		
		if strfind(options, 'z')
			Z = Fz/(1/sqrt(N-3));			fprintf('.');
		end
		
	% Z = icdf('Normal', (1-p), 0, 1);	
		
		fprintf(' done.');
		
		% ------------------------> saving images
		
		if (length(options)>0)
			fprintf('\n     ... saving images');
			
			ifhextra.key = 'number of samples';
			ifhextra.value = int2str(N);
			
			if strfind(options, 'r')
				g_Save4DFP([targetf '/' bname '_' roiname{m} '_r.4dfp.img'], r, ifhextra); 		fprintf(' r');
			end
			if strfind(options, 'f')
				g_Save4DFP([targetf '/' bname '_' roiname{m} '_Fz.4dfp.img'], Fz, ifhextra); 		fprintf(' Fz');
			end
			if strfind(options, 'z')
				g_Save4DFP([targetf '/' bname '_' roiname{m} '_Z.4dfp.img'], Z, ifhextra); 		fprintf(' Z');
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

[fpathstr, fname, fext, fversn] = fileparts(flist);

bname = strrep(fname, '.list', '');
bname = strrep(fname, '.conc', '');
bname = strrep(bname, '.4dfp', '');
bname = strrep(bname, '.img', '');

ifhextra.key = 'number of subjects';
ifhextra.value = int2str(nsub);


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

	g_Save4DFP([targetf '/' bname '_' roiname{m} '_group_r.4dfp.img'], r, ifhextra); 		fprintf(' r');
	g_Save4DFP([targetf '/' bname '_' roiname{m} '_group_Fz.4dfp.img'], Fz, ifhextra); 	fprintf(' Fz');
	g_Save4DFP([targetf '/' bname '_' roiname{m} '_group_Z.4dfp.img'], Z, ifhextra); 		fprintf(' Z');
	g_Save4DFP([targetf '/' bname '_' roiname{m} '_all_Fz.4dfp.img'], g_fz_img(:,:,m)); 		fprintf(' all Fz');
	
	fprintf(' ... done.');

end

fprintf('\n\n FINISHED!\n\n');



function [] = fc_ComputeGBC(flist, inmask, options, targetf)

%	
%	fc_ComputeGBC
%	
%	Computes GBC maps for individuals as well as group maps.
%	
%	flist   	- conc style list of subject image files or conc files, header row, one subject per line
%	mask		- an array mask defining which frames to use (1) and which not (0)
%	options		- a string defining which subject files to save
%       - undefined
%	tagetf		- the folder to save images in
%
%	It saves group files:
%		-unspecified
%	
% 	Created by Grega Repovš on 2009-11-04.
%
% 	Copyright (c) 2009. All rights reserved.

target = [3 8 9 10 11 12 13 16 17 18 19 20 26 27 28 42 47 48 49 50 51 52 53 54 55 56 58 59 60 96 97];
thr = 0.17;
fprintf('\n\nStarting ...');

startframe = 1;
if length(inmask) == 1
    startframe = inmask + 1;
    inmask = [];
end


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------------- make a list of all the files to process

fprintf('\n ... listing files to process');

files = fopen(flist);
c = 0;
while feof(files) == 0
    s = fgetl(files);
    if ~isempty(strfind(s, 'subject id:'))
        c = c + 1;
        [t, s] = strtok(s, ':');        
        subject(c).id = s(2:end);
        nf = 0;
    elseif ~isempty(strfind(s, 'roi:'))
        [t, s] = strtok(s, ':');        
        subject(c).roi = s(2:end);
    elseif ~isempty(strfind(s, 'file:'))
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

book = [786 147456];

x = zeros(book, 'single');
y = zeros(book, 'single');

gmFz = zeros(147456,nsub);
gaFz = zeros(147456,nsub);
gpD  = zeros(147456,nsub);
gnD  = zeros(147456,nsub);


for n = 1:nsub

    tic;
    
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
	N = size(y, 2);
	Nr = N-1;
	y = y; 
	
	%   --- creating base filename
	
	[fpathstr, fname, fext, fversn] = fileparts(subject(n).id);
	
	bname = strrep(fname, '.conc', '');
	bname = strrep(bname, '.4dfp', '');
	bname = strrep(bname, '.img', '');
		
	%   --- setting up image data
	
    roi2 = g_Read4DFP(subject(n).roi);
    roi2 = ismember(roi2, target);
    vmask = roi2 == 1;
    y = y(vmask,:);
    ntvox = size(y,1);
    
    y = zscore(y,0,2);
    y = y./sqrt(Nr);    % to remove delete by Nr in computing r
    
    %   --- setting up results data
    
    mFz = zeros(ntvox,1);
    aFz = zeros(ntvox,1);
    pD  = zeros(ntvox,1);
    nD  = zeros(ntvox,1);
    
    
    %   --- doing correlations for each voxel
    
    fprintf('\n     ... %d voxels to process', ntvox);
    fprintf('\n     ... computing GBC for voxel:        '); 
	
	for m = 1:ntvox
	    
	    if mod(m,20) == 0
		    fprintf('\b\b\b\b\b\b\b\b%8d', m);
	    end
		
		% ------------------------> setting up
	 			
		% x = [];
		% x = repmat(y(:,m),1,ntvox);
		x = y(m,:)';

		% ------------------------> compute correlation
        
        % r = sum(y.*x,1);            % see above --- ./Nr;
        r = y * x;
			
		% ------------------------> compute Fz and significance

		Fz = fc_Fisher(r);			
		
		mFz(m) = mean(Fz);
		aFz(m) = mean(abs(Fz));
		pD(m)  = sum(r > thr);
		nD(m)  = sum(r < -thr);
		
		% r = []; Fz = []; Z = [];
	
	end
	
	gmFz(vmask, n) = mFz;
    gaFz(vmask, n) = aFz;
    gpD(vmask, n) = pD;
    gnD(vmask, n) = nD;
    
	if strfind(options, 'mFz')
		g_Save4DFP([targetf '/' bname '_mFz.4dfp.img'], gmFz(:,n));
	end
	if strfind(options, 'aFz')
		g_Save4DFP([targetf '/' bname '_aFz.4dfp.img'], gaFz(:,n));
	end
	if strfind(options, 'pD')
		g_Save4DFP([targetf '/' bname '_pD.4dfp.img'], gpD(:,n));
	end
	if strfind(options, 'nD')
		g_Save4DFP([targetf '/' bname '_nD.4dfp.img'], gnD(:,n));
	end
    
    toc
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

for n = 1:nsub
    ifhextra_all(n).key = ['subject ' int2str(n)];
    ifhextra_all(n).value = subject(n).id;
end

%	Fz = g_fz_img(:,:,m)';
%	p  = fc_ttest(Fz);
%	Fz = mean(Fz,1);
%%	Z = fc_ptoz(1-(p),0,1) .* sign(Fz);
%	Z = icdf('Normal', (1-(p/2)), 0, 1) .* sign(Fz);
%	r = fc_FisherInv(Fz);

fprintf('... saving ...');

g_Save4DFP([targetf '/' bname '_group_mFz.4dfp.img'], gmFz, ifhextra); 		fprintf(' mFz');
g_Save4DFP([targetf '/' bname '_group_aFz.4dfp.img'], gaFz, ifhextra); 	    fprintf(' aFz');
g_Save4DFP([targetf '/' bname '_group_pD.4dfp.img'], gpD, ifhextra); 		fprintf(' pD');
g_Save4DFP([targetf '/' bname '_group_nD.4dfp.img'], gnD, ifhextra); 	fprintf(' nD');
	
fprintf(' ... done.');

fprintf('\n\n FINISHED!\n\n');



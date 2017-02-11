function [out] = fc_ComputeSeedCorrelationMapsMT(eventf, concf, roif, ass)

%
%	Written by Grega Repovš, 29.10.2006
%	
%	17.12.2007
%	A "multiple timepoints" version of the script 
%	- instead of computing the correlation for each timepoint individually, 
%	  it enables concatenating datapoints for the timeseries with optional separate  
%	  standardization
%	
%	eventf - fidl event file for the bold runs
%	concf - conc file for the bold runs
%	roif - region image file
%
%	ass - datastructure defining analyses to run
%		roic 	- region to use as seed
%		events 	- events to include in the analysis
%		sframes - seed frames to include in the analysis
%		vframes - volume frames to include in the analysis   !!! - here vframes = sframes!
%		bframes - frames to use for baseline computation
%		targetf	- target folder for results
%		targete - extension to use for results
%	
%		mode - mode of combining datapoints within event
%			none 	- same as m
%			m		- compute mean of within-even timepoints, N = number of events
%			c		- concatenate within-event timepoints, N = number of events * number of frames within event
%			s		- concatenate within-event timepoints and standardize within each within-event timepoints set separately
%	
%	---------------------
%
%	fevents: datastructure for coding events from fidl events file
%		frame 	- array with event start times in frames
%		elength - array with event duration in frames
%		event 	- array with event codes
%		events	- list of event names
%		TR		- TR in s 
%

% ======================================================
% 	----> set up the variables

nass = length(ass);
[t1, fbase, t2, t3] = fileparts(concf);

% ======================================================
% 	----> filter out the events to include in the analysis

fprintf('\nStarting analysis (%s)\n... reading event data\n', fbase);

fevents = fc_ReadEventFile(eventf);
temp = fevents.frame(:,1) + 1;
bframes = int16([temp; 999999]);
for n = 1:nass
	do = ismember(fevents.event, ass(n).events);
	ass(n).fevents.event = fevents.event(do);
	ass(n).fevents.elength = fevents.elength(do);
	ass(n).fevents.frame = fevents.frame(do) + 1;
	ass(n).fevents.events = fevents.events(ass(n).events+1);
	ass(n).nevents = length(ass(n).fevents.event);
	ass(n).frames = int16([ass(n).fevents.frame; 999999]);	
	ass(n).sframes = int16(ass(n).sframes);
	ass(n).vframes = int16(ass(n).vframes);
	ass(n).bframes = int16(ass(n).bframes);
	
	ass(n).tss = length(ass(n).vframes);
	if ass(n).mode == 'm'
		ass(n).seed = zeros(1, ass(n).nevents);
		ass(n).volumes = zeros(147456, ass(n).nevents);
	else
		ass(n).seed = zeros(1, ass(n).nevents*ass(n).tss);
		ass(n).volumes = zeros(147456, ass(n).nevents*ass(n).tss);
	end
	
	ass(n).N  = 0;
	ass(n).c  = 1;
	ass(n).cb = 1;
	ass(n).max = max([ass(n).sframes ass(n).vframes ass(n).bframes]);	
end


% ======================================================
% 	----> read in region file and create masks

fprintf('... reading roi definition image\n');

roi = fc_Read4DFP(roif);

for n = 1:nass
	ass(n).roi = ismember(roi, ass(n).roic);
end

% ======================================================
% 	----> read in bold runs

fprintf('... extracting data\n');

files = fc_ReadConcFile(concf);
for ni = 1:length(files)

	fprintf('    ... run %d', ni);
	
	ifh = fc_ReadIFH(strrep(char(files{ni}), '.img', '.ifh'));
	img = fc_Read4DFPn(char(files{ni}),ifh.frames);     			fprintf(' read, computing baseline ');
	
	%------- compute baseline for this run if defined, else set it to 0
	
	for n = 1:nass
		if isempty(ass(n).bframes)
			ass(n).bseed = 0;
			ass(n).bimg = zeros(147456,1);
		else
			ass(n).bseed = 0;
			ass(n).bimg = zeros(147456, 1);
			c = 1;
			while bframes(ass(n).cb)  < ifh.frames
				if (bframes(ass(n).cb) + ass(n).max) < ifh.frames
					tb = ass(n).bframes + bframes(ass(n).cb);
					ass(n).bseed = ass(n).bseed + mean(mean(img(ass(n).roi,tb)));
					ass(n).bimg = ass(n).bimg + mean(img(:,tb),2);
					c = c + 1;
				end				
				ass(n).cb = ass(n).cb + 1;
			end
			ass(n).bseed = ass(n).bseed ./ c;
			ass(n).bimg = ass(n).bimg ./ c;
		end
		if ass(n).mode ~= 'm'
			ass(n).bseed = repmat(ass(n).bseed, 1, ass(n).tss);
			ass(n).bimg = repmat(ass(n).bimg, 1, ass(n).tss);
		end
		fprintf('.');
	end
	bframes = bframes - ifh.frames;

	fprintf(' done, extracting data ');
	
	%------- extract datapoints for this run
	
	for n = 1:nass
		while ass(n).frames(ass(n).c) < ifh.frames
			if (ass(n).frames(ass(n).c) + ass(n).max) < ifh.frames
				ts = ass(n).sframes + ass(n).frames(ass(n).c);
				tv = ass(n).vframes + ass(n).frames(ass(n).c);
				try
					if ass(n).mode ~= 'm'
						ass(n).seed(1, 1+ass(n).tss*(ass(n).c-1):ass(n).c*ass(n).tss) = mean(img(ass(n).roi,ts),1) - ass(n).bseed;
					else
						ass(n).seed(1, ass(n).c) = mean(mean(img(ass(n).roi,ts))) - ass(n).bseed;
					end
				catch
					ts
					% ass(n).sframes
					% ass(n).frames
					% ass(n).frames(ass(n).c)
					% ass(n).c
					rethrow(lasterror)
				end
				if ass(n).mode ~= 'm'
					ass(n).volumes(:,1+ass(n).tss*(ass(n).c-1):ass(n).c*ass(n).tss) = img(:,tv) - ass(n).bimg;			
				else
					ass(n).volumes(:,ass(n).c) = mean(img(:,tv),2) - ass(n).bimg;
				end
				ass(n).N = ass(n).N + 1;
			end
			ass(n).c = ass(n).c + 1;
		end
		ass(n).frames = ass(n).frames - ifh.frames;
		fprintf('.');
	end
	fprintf(' done\n');
end


% ======================================================
% 	----> computing correlations

fprintf('... computing correlations\n');


for n = 1:nass

	fprintf('    analysis %d: ', n);

	% ------------------------> set up matrices

	N = ass(n).N;
	if ass(n).mode ~= 'm'
		N = N * ass(n).tss;
	end
	
	
	y = ass(n).volumes(:,1:N); 
	x = ass(n).seed(1,1:N); 					

	%fprintf('.[size1 x: %d, %d, y: %d, %d]\n', size(x,1), size(x,2), size(y,1), size(1,2));

	% ------------------------> compute sd
	
	if ass(n).mode == 's'
		eventv = repmat(1:ass(n).tss, 1, N/ass(n).tss);
		grps = ass(n).tss;
	else
		eventv = ones(1,N);
		grps = 1;
	end

	for i = grps
		mask = eventv == i;
		ns = sum(mask);
		ssx = sum(x(:,mask).*x(:,mask),2);										fprintf('.');
		ssy = sum(y(:,mask).*y(:,mask),2);										fprintf('.');
		mx = mean(x(:,mask),2);													fprintf('.');	
		my = mean(y(:,mask),2);													fprintf('.');
		stdx = sqrt((ssx-mx*ns)/ns);											fprintf('.');
		stdy = sqrt((ssy-my*ns)/ns);											fprintf('.');
		x(:,mask) = (x(:,mask)-repmat(mx,1,ns))./repmat(stdx,1,ns);				fprintf('.');
		y(:,mask) = (y(:,mask)-repmat(my,1,ns))./repmat(stdy,1,ns);				fprintf('.');
	end

	% fprintf('.[size2 x: %d, %d, y: %d, %d]\n', size(x,1), size(x,2), size(y,1), size(1,2));
	
	% ------------------------> compute correlation

	x = repmat(x,147456,1);														fprintf('.');
	r = sum(x.*y,2)./(N-1);														fprintf('.');

	% ------------------------> compute Fz and significance

	Fz = 0.5*log((1+r)./(1-r));			fprintf('.');
	Z  = Fz/(1/sqrt(N-3));				fprintf('. saving ');

	% fprintf('.[size1 Fz: %d, %d, Z: %d, %d]\n', size(Fz,1), size(Fz,2), size(Z,1), size(Z,2));

	% ======================================================
	% 	----> writing images
	ifhextra.key   = 'number of samples';
	ifhextra.value = int2str(N);

	fc_Save4DFP(strcat(ass(n).targetf, '/', fbase, ass(n).targete, '_r.4dfp.img'),r, ifhextra);		fprintf('.');
	fc_Save4DFP(strcat(ass(n).targetf, '/', fbase, ass(n).targete, '_Fz.4dfp.img'),Fz, ifhextra);	fprintf('.');
	fc_Save4DFP(strcat(ass(n).targetf, '/', fbase, ass(n).targete, '_Z.4dfp.img'),Z, ifhextra);		fprintf('.');
	
	fprintf(' saved\n');
end

fprintf('Done!\n');


function [out] = fc_ComputeSeedMapsEvent(eventf, concf, roif, ass)

%
%	Written by Grega Repovš, 29.10.2006
%	
%	eventf - fidl event file for the bold runs
%	concf - conc file for the bold runs
%	roif - region image file
%
%	ass - datastructure defining analyses to run
%		roic 	- region to use as seed
%		events 	- events to include in the analysis
%		sframes - seed frames to include in the analysis
%		vframes - volume frames to include in the analysis
%		bframes - frames to use for baseline computation
%		targetf	- target folder for results
%		targete - extension to use for results
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

fevents = g_ReadEventFile(eventf);
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
	ass(n).vframes = int16(ass(n).vframes);
	ass(n).sframes = int16(ass(n).sframes);
	ass(n).bframes = int16(ass(n).bframes);
	ass(n).seed = zeros(ass(n).nevents, 1);
	ass(n).volumes = zeros(147456, ass(n).nevents);
	ass(n).c = 1;
	ass(n).N = 0;
	ass(n).max = max([ass(n).sframes ass(n).vframes ass(n).bframes]);
end


% ======================================================
% 	----> read in region file and create masks

fprintf('... reading roi definition image\n');

roi = g_Read4DFP(roif);

for n = 1:nass
	ass(n).roi = ismember(roi, ass(n).roic);
end

% ======================================================
% 	----> read in bold runs

fprintf('... extracting data\n');

files = g_ReadConcFile(concf);
for ni = 1:length(files)

	fprintf('    ... run %d', ni);
	
	ifh = g_ReadIFH(strrep(char(files{ni}), '.img', '.ifh'));
	img = g_Read4DFPn(char(files{ni}),ifh.frames);     			fprintf(' read, computing baseline ');
	
	%------- compute baseline for this run if defined, else set it to 0
	
	for n = 1:nass
		if isempty(ass(n).bframes)
			ass(n).bseed = 0;
			ass(n).bimg = 0;
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
					ass(n).seed(ass(n).c) = mean(mean(img(ass(n).roi,ts))) - ass(n).bseed;
				catch
					ass(n).sframes
					ass(n).frames
					ass(n).frames(ass(n).c)
					ass(n).c
					rethrow(lasterror)
				end
				ass(n).volumes(:,ass(n).c) = mean(img(:,tv),2) - ass(n).bimg;	
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
	y = ass(n).volumes(:,1:N)';  				
	x = repmat(ass(n).seed(1:N),1,147456);
	fprintf('.');

	% ------------------------> compute correlation

	sx = sum(x,1);			fprintf('.');
	sy = sum(y,1);			fprintf('.');
	sx2 = sum(x.*x, 1);		fprintf('.');
	sy2 = sum(y.*y, 1);		fprintf('.');
	sxy = sum(x.*y, 1);		fprintf('.');

	r = (N*sxy - sx.*sy)./sqrt((N*sx2 - sx.*sx).*(N*sy2 - sy.*sy));		fprintf('.');

	% ------------------------> compute Fz and significance

	Fz = 0.5*log((1+r)./(1-r));			fprintf('.');
	Z = Fz/(1/sqrt(N-3));				fprintf('. saving ');


	% ======================================================
	% 	----> writing images
	ifhextra.key = 'number of samples';
	ifhextra.value = int2str(N);

	g_Save4DFP(strcat(ass(n).targetf, '/', fbase, ass(n).targete, '_r.4dfp.img'),r, ifhextra);		fprintf('.');
	g_Save4DFP(strcat(ass(n).targetf, '/', fbase, ass(n).targete, '_Fz.4dfp.img'),Fz, ifhextra);	fprintf('.');
	g_Save4DFP(strcat(ass(n).targetf, '/', fbase, ass(n).targete, '_Z.4dfp.img'),Z, ifhextra);		fprintf('.');
	
	fprintf(' saved\n');
end

fprintf('Done!\n');


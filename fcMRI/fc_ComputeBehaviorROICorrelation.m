function [out] = fc_ComputeBehaviorROICorrelation(eventf, concf, roif, ass)

%
%	Notes
%	- has to take beh for event instead of img and return a correlation for each of the ass!
%
%


%
%	Written by Grega Repovš, 2008.07.2
%	
%	eventf - fidl event file for the bold runs
%	concf - conc file for the bold runs
%	roif - region image file
%
%	ass - datastructure defining analyses to run
%		col 	- column from which to take behavioral data
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
%		beh 	- matrix with behavioral data
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
bframes = [temp; 999999];
for n = 1:nass
	do = ismember(fevents.event, ass(n).events);
	ass(n).fevents.event = fevents.event(do);
	ass(n).fevents.elength = fevents.elength(do);
	ass(n).fevents.beh = fevents.beh(do,:);
	ass(n).fevents.frame = fevents.frame(do) + 1;
	ass(n).fevents.events = fevents.events(ass(n).events+1);
	
	ass(n).nevents = length(ass(n).fevents.event);
	ass(n).frames = [ass(n).fevents.frame; 999999];
%	ass(n).vframes = ass(n).vframes;
	ass(n).sframes = ass(n).sframes;
	ass(n).bframes = ass(n).bframes;
	ass(n).seed = zeros(ass(n).nevents, 1);
	ass(n).volumes = zeros(ass(n).nevents, 1); % zeros(147456, ass(n).nevents);
	ass(n).c = 1;
	ass(n).N = 0;
	ass(n).max = max([ass(n).sframes  ass(n).bframes]); %ass(n).vframes
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
%			ass(n).bimg = 0;
		else
			ass(n).bseed = 0;
%			ass(n).bimg = zeros(147456, 1);
			c = 1;
			while bframes(ass(n).cb)  < ifh.frames
				if (bframes(ass(n).cb) + ass(n).max) < ifh.frames
					tb = ass(n).bframes + bframes(ass(n).cb);
					ass(n).bseed = ass(n).bseed + mean(mean(img(ass(n).roi,tb)));
%					ass(n).bimg = ass(n).bimg + mean(img(:,tb),2);
					c = c + 1;
				end				
				ass(n).cb = ass(n).cb + 1;
			end
			ass(n).bseed = ass(n).bseed ./ c;
%			ass(n).bimg = ass(n).bimg ./ c;
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
%				tv = ass(n).vframes + ass(n).frames(ass(n).c);
				try
					ass(n).seed(ass(n).c) = mean(mean(img(ass(n).roi,floor(ts)))) - ass(n).bseed;
				catch
					ass(n).sframes
					ass(n).frames
					ass(n).frames(ass(n).c)
					ass(n).c
					rethrow(lasterror)
				end
				ass(n).volumes(ass(n).c) = ass(n).fevents.beh(ass(n).c, ass(n).col);	
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

fprintf('... computing correlations ');


for n = 1:nass

	fprintf('.');

	% ------------------------> set up 
	
	N = ass(n).N;
	y = ass(n).volumes(1:N);  				
	x = ass(n).seed(1:N);
	
	[r, p] = corr(x, y);
	Fz = 0.5*log((1+r)./(1-r));			fprintf('.');
	
	out(n).r = r;
	out(n).Fz = Fz;
	out(n).p = p;

end

fprintf('Done!\n');


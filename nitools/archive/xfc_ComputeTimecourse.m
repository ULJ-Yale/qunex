function [out] = fc_ComputeTimecourse(concf, eventf, frames, measure, baseline, bframes, omit, regress)

%
%	Written by Grega Repovš, 15.11.2007
%		
%	Outputs average timeseries for events of frames length
%	
%	
%	concf - conc file for the bold runs
%	eventf - fidl event file for the bold runs
%	frames - the length of timecourse to estimate
%	measure - what should the measure be
%		raw - just raw values
%		dif - difference to baseline
%		pch - percent change from baseline
%
%	baseline - what should be used as baseline
%		na - nothing, 0 (combined with raw in measure)
%		ra - run average value for that voxel
%		ta - run average of timepoints specified in bframes
%		te - average of timepoints specified in bframes for that event
%
%	omit - number of frames at the start to omit from analysis
%
%	regress - type of regression to do before analysis
%
% ======================================================
% 	----> set up the variables

nass = length(ass);
[t1, fbase, t2, t3] = fileparts(concf);

% ======================================================
% 	----> filter out the events to include in the analysis

fprintf('\nStarting analysis (%s)\n... reading event data\n', fbase);

fevents = fc_ReadEventFile(eventf);
for n = 1:nass
	doIt = ismember(fevents.event, ass(n).events);
	ass(n).fevents.event = fevents.event(doIt);
	ass(n).fevents.elength = fevents.elength(doIt);
	ass(n).fevents.frame = fevents.frame(doIt) + 1;
	ass(n).fevents.events = fevents.events(ass(n).events+1);
	
	ass(n).nevents = length(ass(n).fevents.event);
	ass(n).frames = int16([ass(n).fevents.frame; 999999]);
	ass(n).vframes = int16(ass(n).vframes);
	ass(n).sframes = int16(ass(n).sframes);
	ass(n).bframes = int16(ass(n).bframes);
	ass(n).seed = zeros(ass(n).nevents, 1);
	ass(n).volumes = zeros(147456, ass(n).nevents);
	ass(n).c = 1;
	ass(n).cb = 1;
end
bframes = int16([fevents.frame + 1; 999999]);

% ======================================================
% 	----> read in region file and create masks

fprintf('... reading roi definition image\n');

roi = fc_Read4DFPn(roif,1);

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
			ass(n).bimg = 0;
		else
			ass(n).bseed = 0;
			ass(n).bimg = zeros(147456, 1);
			c = 1;
			while bframes(ass(n).cb) < ifh.frames
				tb = ass(n).bframes + bframes(ass(n).cb);
				ass(n).bseed = ass(n).bseed + mean(mean(img(ass(n).roi,tb)));
				ass(n).bimg = ass(n).bimg + mean(img(:,tb),2);
				c = c + 1;
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
			ts = ass(n).sframes + ass(n).frames(ass(n).c);
			tv = ass(n).vframes + ass(n).frames(ass(n).c);
			ass(n).seed(ass(n).c) = mean(mean(img(ass(n).roi,ts))) - ass(n).bseed;
			ass(n).volumes(:,ass(n).c) = mean(img(:,tv),2) - ass(n).bimg;
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

	y = ass(n).volumes';  				
	x = repmat(ass(n).seed,1,147456);
	N = size(x, 1);
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

	fc_Save4DFP(strcat(ass(n).targetf, '/', fbase, ass(n).targete, '_r.4dfp.img'),r);		fprintf('.');
	fc_Save4DFP(strcat(ass(n).targetf, '/', fbase, ass(n).targete, '_Fz.4dfp.img'),Fz);		fprintf('.');
	fc_Save4DFP(strcat(ass(n).targetf, '/', fbase, ass(n).targete, '_Z.4dfp.img'),Z);		fprintf('.');
	
	fprintf(' saved\n');
end

fprintf('Done!\n');


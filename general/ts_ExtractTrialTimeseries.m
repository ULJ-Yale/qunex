function [out] = fc_ExtractTrialTimeseries(ofile, eventf, concf, roif, events, frames)

%
%	Written by Grega Repovš, 22.1.2008
%	
%	ofile 	- file to save into
%	eventf 	- fidl event file for the bold runs
%	concf 	- conc file for the bold runs
%	roif 	- region image file
%	events 	- the events for which to extract timeseries, can be a cell array of combinations
%	frames 	- limits of frames to include in the extracted timeseries
%
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

nniz = length(events);							%--- number of separate sets we will be extracting
[t1, fbase, t2, t3] = fileparts(concf);			%--- details about the filename
tlength = frames(2) - frames(1) + 1;			%--- number of timepoints in the timeseries
f.max = frames(2);
f.min = frames(1);
frames = int16(frames); 

files = fc_ReadConcFile(concf);
nruns = length(files);

fprintf('\nStarting analysis (%s)', fbase);

% ======================================================
% 	----> read in region file and create masks

fprintf('\n... reading roi definition image');

roiimg = fc_Read4DFP(roif);
regions = unique(roiimg); 
nregions = length(regions);

for n = 1:nregions
	roi(n).mask = ismember(roiimg, regions(n));
end


% ======================================================
% 	----> filter out the events to include in the analysis

fprintf('\n... reading event data');

fevents = fc_ReadEventFile(eventf);
temp = fevents.frame(:,1) + 1;
bframes = int16([temp; 999999]);
for n = 1:nniz
	do = ismember(fevents.event, events{n});					%--- get a mask of events to process
	niz(n).fevents.event = fevents.event(do);					%--- get a list of events we are processing
	niz(n).fevents.frame = fevents.frame(do) + 1;				%--- get the start frames of events we are processing
	niz(n).fevents.events = fevents.events(events{n}+1);		%--- get list of events names we included
	
	niz(n).nevents = length(niz(n).fevents.event);				%--- get a number of events we are processing
	niz(n).frames = int16([niz(n).fevents.frame; 999999]);		%--- get a list of frames we are processing plus an extra large nonexistent frame
	niz(n).timeseries = zeros(niz(n).nevents, tlength, nregions);			%--- prepare a matrix to hold all the timeseries
	niz(n).baseline = zeros(nruns, nregions);					%--- a matrix to store baseline data for each region in each run
	niz(n).eventbaseline = zeros(niz(n).nevents, nregions);		%--- run baseline recorded for each event
	niz(n).run = zeros(1, niz(n).nevents);						%--- a list to record which run the trial comes from
	niz(n).c = 1;
	niz(n).N = 0;
end

% ======================================================
% 	----> read in bold runs

fprintf('\n... extracting data');

for ni = 1:nruns

	fprintf('\n    ... run %d', ni);
	
	ifh = fc_ReadIFH(strrep(char(files{ni}), '.img', '.ifh'));
	img = fc_Read4DFPn(char(files{ni}),ifh.frames);     			fprintf(' read');
	
	
	%------- extract baseline for this run
	
	fprintf(' baseline ...');
	
	for r = 1:nregions
		m = mean(mean(img(roi(r).mask, 6:end)));
		for n = 1:nniz
			niz(n).baseline(ni,r) = m;
		end	
	end	
	
	fprintf(' computed');
	
	%------- extract datapoints for this run
	
	fprintf(', extracting data ');
	
	for n = 1:nniz
		while niz(n).frames(niz(n).c) < ifh.frames
			if (niz(n).frames(niz(n).c) + f.max) < ifh.frames
				ts = frames + niz(n).frames(niz(n).c);
				if ts(1) > 0
					niz(n).N = niz(n).N + 1;
                    for r = 1:nregions
                        try
                        	niz(n).timeseries(niz(n).N, :, r) = mean(img(roi(r).mask, ts(1):ts(2)),1);
							niz(n).run(1, niz(n).N) = ni;
							niz(n).eventbaseline(niz(n).N, :) = niz(n).baseline(ni,:);
                        catch
                    		niz(n).frames
                        	niz(n).frames(niz(n).c)
                            niz(n).c
                            rethrow(lasterror)
                        end	
                    end
                end
			end
			niz(n).c = niz(n).c + 1;
		end
		niz(n).frames = niz(n).frames - ifh.frames;
		fprintf('.');
	end
	fprintf(' done');
end

% ======================================================
% 	----> save

fprintf('\nSaving ...');

save(ofile, 'niz');

fprintf('Done!\n');


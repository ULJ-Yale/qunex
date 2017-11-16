function [out] = fc_ExtractTrialTimeseriesWB(ofile, eventf, concf, events, frames, smooth)

%
%	Written by Grega Repovš, 22.1.2008
%	
%	ofile 	- file to save into (a cell array of names, one for each event combination)
%	eventf 	- fidl event file for the bold runs
%	concf 	- conc file for the bold runs
%	events 	- the events for which to extract timeseries, can be a cell array of combinations
%	frames 	- limits of frames to include in the extracted timeseries (2 x n array with n = number of event combinations)
%   smooth  - optional smoothing FWHM in voxels
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

if nargin < 6 
    smooth = [];
end

nniz = length(events);							%--- number of separate sets we will be extracting
[t1, fbase, t2, t3] = fileparts(concf);			%--- details about the filename

files = fc_ReadConcFile(concf);
nruns = length(files);

fprintf('\nStarting analysis (%s)', fbase);


% ======================================================
% 	----> filter out the events to include in the analysis

fprintf('\n... reading event data');

fevents = fc_ReadEventFile2(eventf);
temp = fevents.frame(:,1) + 1;
bframes = [temp; 999999];
for n = 1:nniz
	doIt = ismember(fevents.event, events{n});					%--- get a mask of events to process
	niz(n).fevents.event = fevents.event(doIt);					%--- get a list of events we are processing
	niz(n).fevents.frame = fevents.frame(doIt) + 1;				%--- get the start frames of events we are processing
	niz(n).fevents.events = fevents.events(events{n}+1);		%--- get list of events names we included
	
	niz(n).nevents = length(niz(n).fevents.event);				%--- get a number of events we are processing
	niz(n).frames = [niz(n).fevents.frame; 999999];		        %--- get a list of frames we are processing plus an extra large nonexistent frame
	niz(n).s = [];			                                    %--- prepare a matrix to hold sums
	niz(n).ss = [];			                                    %--- prepare a matrix to hold sums of squares

	niz(n).c = 1;
	niz(n).N = 0;
	
	niz(n).tlength = frames(n,2) - frames(n,1) + 1;			    %--- number of timepoints in the timeseries
    niz(n).f.max = frames(n,2);
    niz(n).f.min = frames(n,1);
    
	
end

% ======================================================
% 	----> read in bold runs

fprintf('\n... extracting data');

imask = fevents.mask';

for ni = 1:nruns

	fprintf('\n    ... run %d ', ni);
	
	ifh = fc_ReadIFH(strrep(char(files{ni}), '.img', '.ifh'));
	img = fc_Read4DFPn(char(files{ni}),ifh.frames);     			fprintf(' read');
    if ~isempty(smooth)
	    img = g_Smooth3D(img,smooth);
    end
	
    %------- we're creating a base mask that takes all but first 6 voxels 
    mask = ones(1, ifh.frames);
    mask(1,1:6) = 0;
    
    %------- if a mask is present in the event file, we need to translate it for this run
    if ~isempty(imask)                                    
        if length(imask) > ifh.frames
            mask(imask(1:ifh.frames)==0) = 0;
            imask = imask(ifh.frames+1:end);
        else
            mask(1:length(imask)) = imask;
            mask(1:6) = 0;
            imask = [];
        end
    end
	
	%------- extract baseline for this run
	
	fprintf(' baseline ...');
	
	b = mean(img(:, mask>0),2);
	
	fprintf(' computed');
	
	%------- extract datapoints for this run
	
	fprintf(', extracting data ');
	
	for n = 1:nniz

	    % ----- initialize s and ss matrices
	    
	    if isempty(niz(n).s)
	        niz(n).s = zeros(size(img,1),niz(n).tlength);
	        niz(n).ss = zeros(size(img,1),niz(n).tlength);
        end
	
		while niz(n).frames(niz(n).c) < ifh.frames
			if (niz(n).frames(niz(n).c) + niz(n).f.max) < ifh.frames
				ts = frames(n,:) + niz(n).frames(niz(n).c);
				if ts(1) > 0
					niz(n).N = niz(n).N + 1;
					
					niz(n).s = niz(n).s + (img(:,ts(1):ts(2))-repmat(b, 1,niz(n).tlength))./10;
					niz(n).ss = niz(n).ss +((img(:,ts(1):ts(2))-repmat(b, 1,niz(n).tlength))./10).^2;

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
% 	----> Compute mean, sd and se

fprintf('\nComputing ...');

for n = 1:nniz
    niz(n).m = niz(n).s / niz(n).N;
    niz(n).sd = sqrt(niz(n).ss/niz(n).N - niz(n).m.^2);
    niz(n).se = niz(n).sd / sqrt(niz(n).N);
end

fprintf('Done!\n');


% ======================================================
% 	----> save

fprintf('\nSaving ');

for n = 1:nniz
    g_Save4DFP([ofile{n} '_ts_mean.4dfp.img'], niz(n).m);   fprintf('.');
    g_Save4DFP([ofile{n} '_ts_sd.4dfp.img'], niz(n).sd);    fprintf('.');
    g_Save4DFP([ofile{n} '_ts_se.4dfp.img'], niz(n).se);    fprintf('.');
end

fprintf(' done!\n');


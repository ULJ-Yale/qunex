function [out] = fc_ExtractTrialTimeseriesMasked(flist, roif, targetf, events, frames, scrubvar)

%function [out] = fc_ExtractTrialTimeseriesMasked(flist, roif, targetf, events, frames, scrubvar)
%
%
%	flist 	- file list with information on conc, fidl and individual roi files
%	roif 	- region "names" file
%   targetf - target matlab file with results
%	events 	- the events for which to extract timeseries, can be a cell array of combinations
%	frames 	- limits of frames to include in the extracted timeseries
%   scrubvar- critera to use for scrubbing data - scrub based on:
%               - [] do not scrub
%               - mov      ... overall movement displacement
%               - dvars    ... frame-to-frame variability
%               - dvarsme  ... median normalized frame-to-frame variability
%               - idvars   ... mov AND dvars
%               - idvarsme ... mov AND dvarsme
%               - udvars   ... mov OR dvars
%               - udvarsme ... mov OR dvarsme
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
%   Written by Grega Repovš, 22.1.2008
%   2011.11.07 - adjusted and partly rewriten to use gmrimage object
%   2012.04.20 - added the option of scrubbing the data
%   2013.07.24 - adjusted to use the new ROIMask method


if nargin < 6
    scrubvar = [];
    if nargin < 5
        error('ERROR: Five arguments need to be specified for function to run!');
    end
end

scrubit = true;
if isempty(scrubvar)
    scrubit = false;
end

% ======================================================
% 	----> set up the variables

fprintf('\n\nStarting ...');

nniz = length(events);							%--- number of separate sets we will be extracting
[t1, fbase, t2] = fileparts(roif);			%--- details about the filename
tlength = frames(2) - frames(1) + 1;			%--- number of timepoints in the timeseries
frames = int16(frames);

%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf('\n ... listing files to process');

subject = g_ReadSubjectsList(flist);
nsub = length(subject);

fprintf(' ... done.');

%   ------------------------------------------------------------------------------------------
%                                                         set up datastructure to save results

for n = 1:nsub
    data(n).subject = subject(n).id;
end


%   ------------------------------------------------------------------------------------------
%                                                The main loop ... go through all the subjects


for s = 1:nsub

    fprintf('\n ... processing %s', subject(s).id);

    % ---> reading ROI file

	fprintf('\n     ... creating ROI mask');

	if isfield(subject(s), 'roi')
	    sroifile = subject(s).roi;
	else
	    sroifile = [];
    end

    if strcmp(sroifile,'none')
        roi = gmrimage.mri_ReadROI(roif);
    else
        roi = gmrimage.mri_ReadROI(roif, sroifile);
    end
    nregions = length(roi.roi.roinames);

	% ---> reading image files

	fprintf('\n     ... reading image file(s)');

	y = gmrimage(subject(s).files{1});
  	for f = 2:length(subject(s).files)
	    y = [y gmrimage(subject(s).files{f})];
    end

    if scrubit
        if size(y.scrub, 1) ~= y.frames
            fprintf('\n     ... WARNING: missing or invalid scrubbing info!!!')
            scrub = zeros(1, y.frames);
        else
            scrub = y.scrub(:, ismember(y.scrub_hdr, scrubvar))';
        end
    else
        scrub = zeros(1, y.frames);
    end
    scrub = scrub == 1;

    nruns = length(y.runframes);
    run = [];
    for r = 1:nruns
        run = [run [zeros(1,5) ones(1,y.runframes(r)-5)*r]];
    end

    fprintf(' ... %d frames read, done.', y.frames);



    % ======================================================
    % 	----> filter out the events to include in the analysis

    fprintf('\n     ... reading event data');

    fevents = g_ReadEventFile(subject(s).fidl);
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
        niz(n).scrub = zeros(niz(n).nevents, tlength);              %--- a matrix to hold scrub markers
    	niz(n).baseline = zeros(nruns, nregions);					%--- a matrix to store baseline data for each region in each run
    	niz(n).eventbaseline = zeros(niz(n).nevents, nregions);		%--- run baseline recorded for each event
    	niz(n).run = zeros(1, niz(n).nevents);						%--- a list to record which run the trial comes from
    	niz(n).c = 1;
    	niz(n).N = 0;
    end

    % ======================================================
    % 	----> extract data

	%------- extract baseline for this run

	fprintf(' baseline ...');

    for ni = 1:nruns
	    for r = 1:nregions
    		m = mean(mean(y.data(roi.ROIMask(r), run == ni & ~scrub )));
    		for n = 1:nniz
    			niz(n).baseline(ni,r) = m;
    		end
    	end
    end

	fprintf(' computed');

	%------- extract datapoints for this run

	fprintf(', extracting data ');

	for n = 1:nniz
		while niz(n).frames(niz(n).c) < y.frames
			if (niz(n).frames(niz(n).c) + frames(2)) < y.frames
				ts = frames + niz(n).frames(niz(n).c);
				if ts(1) > 0
					niz(n).N = niz(n).N + 1;
                    niz(n).scrub(niz(n).N,:) = scrub(ts(1):ts(2));
                    for r = 1:nregions
                        try
                        	niz(n).timeseries(niz(n).N, :, r) = mean(y.data(roi.ROIMask(r), ts(1):ts(2)),1);
                        	ni = run(ts(1));
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
		fprintf('.');
	end
	fprintf(' done');

    data(s).subject = subject(s).id;
    data(s).niz = niz;
end

% ======================================================
% 	----> save

fprintf('\nSaving ...');

save(targetf, 'data');

fprintf('Done!\n');


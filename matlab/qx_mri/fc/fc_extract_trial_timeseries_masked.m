function [data] = fc_extract_trial_timeseries_masked(flist, roif, targetf, tevents, frames, scrubvar)

%``function [data] = fc_extract_trial_timeseries_masked(flist, roif, targetf, tevents, frames, scrubvar)``
%
%   Extracts trial timeseries for each of the specified ROI.
%
%   INPUT
%   =====
%
%	--flist       File list with information on .conc, .fidl, and individual
%                 roi (segmentation) files, or a well strucutured string (see
%                 general_read_file_list).
%	--roif 	      Region "names" file that specifies the ROI to extract trial
%                 timeseries for.
%   --targetf     The target matlab file with results.
%	--tevents     The indeces of the events for which to extract timeseries,
%                 can be a cell array of combinations of event indeces.
%	--frames      Limits of frames to include in the extracted timeseries.
%   --scrubvar    Critera to use for scrubbing data - scrub based on:
%
%                   - [] do not scrub
%                   - 'mov'      - overall movement displacement
%                   - 'dvars'    - frame-to-frame variability
%                   - 'dvarsme'  - median normalized dvars
%                   - 'idvars'   - mov AND dvars
%                   - 'idvarsme' - mov AND dvarsme
%                   - 'udvars'   - mov OR dvars
%                   - 'udvarsme' - mov OR dvarsme
%
%   OUTPUTS
%   =======
%
%   data(n)
%       A structure with extracted trial timeseries for each session:
%       
%       .session
%           Subject id
%
%       .set(n)
%           Extracted datasets for the session.
%           
%           .fevents.event  
%               a list of events processed
%           .fevents.frame  
%               start frames of the events processed
%           .fevents.events 
%               list of event names included
%           .nevents        
%               number of events processed
%           .frames         
%               a list of frames processed
%           .timeseries     
%               a 3D matrix with the dimensions:
%                   - number of events (trials)
%                   - number of frames extracted for each trial
%                   - number of regions to extract data from
%           .scrub
%               a matrix of scrub markers (nevents x n event frames)
%           .baseline
%               a matrix of baseline data for each ROI for each run (nrun x nroi)
%           .eventbaseline
%               a matrix of baseline for each event (trial) for each ROI (nevents x nroi)
%           .run            
%               a record of which run each event (trial) comes from
%
%   USE
%   ===
%
%   The function is used to extract per trial data from each session for the
%   specified events. The data is returned in a data structure described above,
%   as well as saved to a matlab data file.
%
%   EXAMPLE USE
%   ===========
%
%   ::
%
%       fc_extract_trial_timeseries_masked('scz+con.list', 'ccroi.names', ...
%       'ccroits', {[0], [1 2], [3 4]}, [2 4], 'udvarsme');
%
%   The above call would extract three sets of timeseries for a) event coded as
%   0, b) events coded as 1 or 2 and c) events coded as 3 and 4 in the fidl
%   file. For each matching event in the fidl file, it would extract for each of
%   the regions specified in the ccroi.names frames 2, 3, and 4. It would save
%   the results in a file 'ccroits.mat'. At extraction it would ignore all
%   frames that were marked bad using the 'udvarsme' criterion.


%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%
%   2008-01-22 Grega Repovs
%              Initial version.
%   2011-11-07 Grega Repovs
%              Adjusted and partly rewriten to use nimage object.
%   2012-04-20 Grega Repovs
%              Added the option of scrubbing the data.
%   2013-07-24 Grega Repovs
%              Adjusted to use the new ROIMask method.
%   2017-03-11 Grega Repovs
%              Cleaned code and updated documentation.
%   2017-04-18 Grega Repovs
%              Adjusted to use updated general_read_file_list.

if nargin < 6, scrubvar = []; end
if nargin < 5, error('ERROR: Five arguments need to be specified for the function to run!'); end

scrubit = true;
if isempty(scrubvar)
    scrubit = false;
end

% ======================================================
% 	----> set up the variables

fprintf('\n\nStarting ...');

nniz = length(tevents);							% --- number of separate sets we will be extracting
[t1, fbase, t2] = fileparts(roif);			    % --- details about the filename
tlength = frames(2) - frames(1) + 1;			% --- number of timepoints in the timeseries
frames = int16(frames);

%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf('\n ... listing files to process');

[session, nsub, nfiles, listname] = general_read_file_list(flist);

fprintf(' ... done.');

%   ------------------------------------------------------------------------------------------
%                                                         set up datastructure to save results

for n = 1:nsub
    data(n).session = session(n).id;
end


%   ------------------------------------------------------------------------------------------
%                                                The main loop ... go through all the sessions


for s = 1:nsub

    fprintf('\n ... processing %s', session(s).id);

    % ---> reading ROI file

	fprintf('\n     ... creating ROI mask');

	if isfield(session(s), 'roi')
	    sroifile = session(s).roi;
	else
	    sroifile = [];
    end

    if strcmp(sroifile,'none')
        roi = nimage.img_read_roi(roif);
    else
        roi = nimage.img_read_roi(roif, sroifile);
    end
    nregions = length(roi.roi.roinames);

	% ---> reading image files

	fprintf('\n     ... reading image file(s)');

	y = nimage(session(s).files{1});
  	for f = 2:length(session(s).files)
	    y = [y nimage(session(s).files{f})];
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
    %
    %   fevents: datastructure for coding events from fidl events file
    %       frame   - array with event start times in frames
    %       elength - array with event duration in frames
    %       event   - array with event codes
    %       events  - list of event names
    %       TR      - TR in s

    fprintf('\n     ... reading event data');

    fevents = general_read_event_file(session(s).fidl);
    temp = fevents.frame(:,1) + 1;
    bframes = int16([temp; 999999]);
    for n = 1:nniz
    	doIt = ismember(fevents.event, tevents{n});					% --- get a mask of events to process
    	niz(n).fevents.event = fevents.event(doIt);					% --- get a list of events we are processing
    	niz(n).fevents.frame = fevents.frame(doIt) + 1;				% --- get the start frames of events we are processing
    	niz(n).fevents.events = fevents.events(tevents{n}+1);		% --- get list of events names we included

    	niz(n).nevents = length(niz(n).fevents.event);				% --- get a number of events we are processing
    	niz(n).frames = int16([niz(n).fevents.frame; 999999]);		% --- get a list of frames we are processing plus an extra large nonexistent frame
    	niz(n).timeseries = zeros(niz(n).nevents, tlength, nregions);			% --- prepare a matrix to hold all the timeseries
        niz(n).scrub = zeros(niz(n).nevents, tlength);              % --- a matrix to hold scrub markers
    	niz(n).baseline = zeros(nruns, nregions);					% --- a matrix to store baseline data for each region in each run
    	niz(n).eventbaseline = zeros(niz(n).nevents, nregions);		% --- run baseline recorded for each event
    	niz(n).run = zeros(1, niz(n).nevents);						% --- a list to record which run the trial comes from
    	niz(n).c = 1;
    	niz(n).N = 0;
    end

    % ======================================================
    % 	----> extract data

	%------- extract baseline for this run

	fprintf(' baseline ...');

    for ni = 1:nruns
	    for r = 1:nregions
    		m = mean(mean(y.data(roi.img_roi_mask(r), run == ni & ~scrub )));
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
                        	niz(n).timeseries(niz(n).N, :, r) = mean(y.data(roi.img_roi_mask(r), ts(1):ts(2)),1);
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

    data(s).session = session(s).id;
    data(s).set = niz;
end

% ======================================================
% 	----> save

fprintf('\nSaving ...');

save(targetf, 'data');

fprintf('Done!\n');


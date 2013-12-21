function [] = g_ComputeBOLDListStats(flist, target, store, scrub, verbose)

%
%	function [] = g_ComputeBOLDListStats(flist, target, store, scrub, verbose)
%
%	Computes BOLD run per frame statistics and scrubs.
%
%	flist   	- conc-like style list of subject image files or conc files:
%                  subject id:<subject_id>
%                  roi:<path to the individual's brain segmentation file>
%                  file:<path to bold files - one per line>
%   target      - folder to save results into, default: where bold image is, 'none': do not save in external file
%   store       - how to store the data - 'same': in the same file, '<ext>': new file with extension, '': no img file
%   scrub       - whether and how to scrub - a string specifying parameters eg 'pre:1|post:1|fd:4|ignore:udvarsme'
%	verbose		- to report on progress or not [not]
%
% 	Created by Grega Repovš on 2011-07-09.
%   Grega Repovs - 2013-10-20 - Added embedding and scrubbing
%   Grega Repovs - 2013-12-19 - Split into two functions to separate list processing and actual statistic computation
%
% 	Copyright (c) 2011 Grega Repovs. All rights reserved.

if nargin < 5
	verbose = false;
    if nargin < 4
        scrub = [];
        if nargin < 3
            store = [];
        	if nargin < 2
        	    target = [];
        	end
        end
    end
end

% ======= Run main

if verbose, fprintf('\n\nStarting processing of %s...\n\n---> Reading in the file', flist); end

[subject nsubjects nallfiles] = g_ReadFileList(flist, verbose);

rois = ismember('roi', fields(subject));

for s = 1:nsubjects

    if verbose, fprintf('\n\nProcessing subject %s...', subject(s).id); end
    %   --- read in roi file
    mask = [];
    if rois
        if ~isempty(subject(s).roi)
            if ~strfind(subject(s).roi, 'none')
                if verbose, fprintf('\n---> Reading mask'); end
                mask = gmrimage(strfind(subject(s).roi));
            end
        end
    end

    nfiles = length(subject(s).files);
	for n = 1:nfiles

        g_ComputeBOLDStats(subject(s).files{n}, mask, target, store, scrub, verbose);

    end
end

if verbose, fprintf('\n\nFINISHED!'); end



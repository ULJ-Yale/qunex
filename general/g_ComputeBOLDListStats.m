function [] = g_ComputeBOLDListStats(flist, target, store, scrub, verbose)

%function [] = g_ComputeBOLDListStats(flist, target, store, scrub, verbose)
%
%	Computes BOLD run per frame statistics and scrubbing information for a list of subjects.
%
%   INPUT
%       flist  ... A list text file providing a list of subjects' image or conc files:
%                  subject id:<subject_id>
%                  roi:<path to the individual's brain segmentation file>
%                  file:<path to a bold file - one bold file per line>
%       target ... A folder to save results into, default: where bold image is,
%                  'none': do not save the results in an external file [''].
%       store  ... A string specifying how to store the data ['']:
%                  - 'same': in the same file,
%                  - '<ext>': new file with extension,
%                  - '': no img file
%       scrub  ... A string specifying whether and how to compute scrubbing
%                  information, e.g. 'pre:1|post:1|fd:4|ignore:udvarsme' []
%	    verbose	... Whether to report on progress or not [false].
%
%   USE
%   The function calls g_ComputeBOLDStats on each of the bolds for each of the
%   subjects specified in the list file. Please see g_ComputeBOLDStats for
%   more detailed information. If arguments are left empty, the defaults in
%   g_ComputeBOLDStats will be used.
%
%   ---
% 	Written by Grega Repovš, 2011-07-09.
%
%   Changelog
%   2013-10-20 Grega Repovs
%            - Added embedding and scrubbing
%   2013-12-19 Grega Repovs
%            - Split into two functions to separate list processing and actual statistic computation
%   2017-03-12 Grega Repovs
%            - Updated documentation
%   2018-06-20 Grega Repovš
%            - Added more detailed reporting of parameters used.
%

if nargin < 5 || isempty(verbose), verbose = false; end
if nargin < 4, scrub  = []; end
if nargin < 3, store  = []; end
if nargin < 2, target = []; end

% ======= Run main

if verbose,
    fprintf('\nRunning g_ComputeBOLDListStats\n------------------------------\n');
    fprintf('\nParameters:\n---------------');
    fprintf('\n          flist: %s', flist);
    fprintf('\n         target: %s', target);
    fprintf('\n          store: %s', store);
    fprintf('\n          scrub: %s\n', scrub);
end

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



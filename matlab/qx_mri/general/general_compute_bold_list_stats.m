function [] = general_compute_bold_list_stats(flist, target, store, scrub, verbose)

%``function [] = general_compute_bold_list_stats(flist, target, store, scrub, verbose)``
%
%	Computes BOLD run per frame statistics and scrubbing information for a list 
%   of sessions.
%
%   INPUTS
%   ======
%   --flist     A list text file providing a list of sessions' image or conc 
%               files:
%               
%               - session id:<session_id>
%               - roi:<path to the individual's brain segmentation file>
%               - file:<path to a bold file - one bold file per line>
%   --target    A folder to save results into, default: where bold image is,
%              'none': do not save the results in an external file [''].
%   --store     A string specifying how to store the data ['']:
%
%               - 'same': in the same file,
%               - '<ext>': new file with extension,
%               - '': no img file
%
%   --scrub     A string specifying whether and how to compute scrubbing
%               information, e.g. 'pre:1|post:1|fd:4|ignore:udvarsme' []
%	--verbose	Whether to report on progress or not [false].
%
%   USE
%   ===
%
%   The function calls general_compute_bold_stats on each of the bolds for each of the
%   sessions specified in the list file. Please see general_compute_bold_stats for
%   more detailed information. If arguments are left empty, the defaults in
%   general_compute_bold_stats will be used.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 5 || isempty(verbose), verbose = false; end
if nargin < 4, scrub  = []; end
if nargin < 3, store  = []; end
if nargin < 2, target = []; end

% ======= Run main

if verbose,
    fprintf('\nRunning general_compute_bold_list_stats\n------------------------------\n');
    fprintf('\nParameters:\n---------------');
    fprintf('\n          flist: %s', flist);
    fprintf('\n         target: %s', target);
    fprintf('\n          store: %s', store);
    fprintf('\n          scrub: %s\n', scrub);
end

if verbose, fprintf('\n\nStarting processing of %s...\n\n---> Reading in the file', flist); end

[session nsessions nallfiles] = general_read_file_list(flist, verbose);

rois = ismember('roi', fields(session));

for s = 1:nsessions

    if verbose, fprintf('\n\nProcessing session %s...', session(s).id); end
    %   --- read in roi file
    mask = [];
    if rois
        if ~isempty(session(s).roi)
            if ~strfind(session(s).roi, 'none')
                if verbose, fprintf('\n---> Reading mask'); end
                mask = nimage(strfind(session(s).roi));
            end
        end
    end

    nfiles = length(session(s).files);
	for n = 1:nfiles
        general_compute_bold_stats(session(s).files{n}, mask, target, store, scrub, verbose);

    end
end

if verbose, fprintf('\n\nFINISHED!'); end



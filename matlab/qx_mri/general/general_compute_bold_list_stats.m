function [] = general_compute_bold_list_stats(flist, target, store, scrub, verbose)

%``general_compute_bold_list_stats(flist, target, store, scrub, verbose)``
%
%   Computes BOLD run per frame statistics and scrubbing information for a list
%   of sessions.
%
%   Parameters:
%       --flist (str):
%           Path to a list text file providing a list of sessions' image or conc
%           files:
%
%           - session id:<session_id>
%           - roi:<path to the individual's brain segmentation file>
%           - file:<path to a bold file - one bold file per line>.
%
%       --target (str, default ''):
%           Path to the folder to save results into. By default this location is
%           set to where bold image is. If 'none' is used, the results are not
%           saved in an external file.
%
%       --store (str, default ''):
%           Specifies how to store the data:
%
%           - 'same': in the same file,
%           - '<ext>': new file with extension,
%           - '': no img file.
%
%       --scrub (str, default ''):
%           Specifies whether and how to compute scrubbing
%           information, e.g. 'pre:1|post:1|fd:4|ignore:udvarsme'.
%
%       --verbose (bool, default false):
%           Whether to report on progress or not.
%
%   Notes:
%       The function calls general_compute_bold_stats on each of the bolds for
%       each of the sessions specified in the list file. Please see
%       general_compute_bold_stats for more detailed information. If arguments
%       are left empty, the defaults in general_compute_bold_stats will be used.
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

list = general_read_file_list(flist, 'all', [], verbose);

rois = ismember('roi', fields(list.session));

for s = 1:list.nsessions

    if verbose, fprintf('\n\nProcessing session %s...', list.session(s).id); end
    %   --- read in roi file
    mask = [];
    if rois
        if ~isempty(list.session(s).roi)
            if ~strfind(list.session(s).roi, 'none')
                if verbose, fprintf('\n---> Reading mask'); end
                mask = nimage(strfind(list.session(s).roi));
            end
        end
    end

    nfiles = length(list.session(s).files);
    for n = 1:nfiles
        general_compute_bold_stats(list.session(s).files{n}, mask, target, store, scrub, verbose);

    end
end

if verbose, fprintf('\n\nFINISHED!'); end



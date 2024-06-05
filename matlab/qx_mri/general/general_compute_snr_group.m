function [snr, sd] = general_compute_snr_group(flist, target, fmask, verbose)

%``general_compute_snr_group(flist, target, fmask, verbose)``
%
%   Computes SNR and SD for the whole group.
%
%   Parameters:
%       --flist (str):
%           String or file path to conc-like style list of session
%           image files or conc files:
%
%           - session id:<session_id>
%           - roi:<path to the individual's ROI file>
%           - file:<path to bold files - one per line>.
%
%       --target (str, default ''):
%           Name of folder to save results into.
%
%       --fmask (int | vector | bool, default ''):
%           A scalar, vector or logical mask defining which frames to use (1)
%           and which not (0).
%
%       --verbose (bool, default false):
%           Whether to report on progress or not.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 4
    verbose = false;
    if nargin < 3
        target = [];
        if nargin < 2
            fmask = [];
        end
    end
end

% ======= Run main

if verbose, fprintf('\n\nStarting ...'); end

list = general_read_file_list(flist, 'all', [], verbose);

snr = zeros(list.nfiles,1);
sd  = zeros(list.nfiles,1);
[~, fname] = fileparts(flist);
fout = fopen(fullfile(target, [fname '_SNR_report.txt']), 'w');
fprintf(fout, 'image\tSNR\tSD\n');

c = 1;
for s = 1:list.nsessions
    
    %   --- reading in image files
    tic; 
    if verbose, fprintf('\n ... processing %s', list.session(s).id); end

    nfiles = length(list.session(s).files);
    for n = 1:nfiles
        [snr(c) sd(c)] = general_compute_snr(list.session(s).files{n}, [], fmask, target, [], [list.session(s).id '_file_' num2str(n)]);
        fprintf(fout, '%s\t%.3f\t%.3f\n', list.session(s).files{n}, snr(c), sd(c));
        c = c +1;
    end

end

fclose(fout);

if verbose, fprintf('\n ... Finished.'); end

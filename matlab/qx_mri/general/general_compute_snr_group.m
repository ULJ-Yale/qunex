function [snr, sd] = general_compute_snr_group(flist, target, fmask, verbose)

%	``function [snr, sd] = general_compute_snr_group(flist, fmask, target, verbose)``
%	
%   Computes SNR and SD for the whole group.
%	
%	INPUTS
%	======
%
%	--flist 	conc-like style list of session image files or conc files: 
%
%               - session id:<session_id>
%               - roi:<path to the individual's ROI file>
%               - file:<path to bold files - one per line>
%
%   --target 	file to save results into
%	--fmask		an array mask defining which frames to use (1) and which not (0)
%	--verbose	to report on progress or not [not]
%	

if nargin < 4
	verbose = false;
	if nargin < 3
	    target = [];
	    if nargin < 2
	    	mask = [];
	    end
	end
end

% ======= Run main

if verbose, fprintf('\n\nStarting ...'); end

[session nsessions nallfiles] = general_read_file_list(flist, verbose);

snr = zeros(nallfiles,1);
sd  = zeros(nallfiles,1);
[~, fname] = fileparts(flist);
fout = fopen(fullfile(target, [fname '_SNR_report.txt']), 'w');
fprintf(fout, 'image\tSNR\tSD\n');

c = 1;
for s = 1:nsessions
    
    %   --- reading in image files
    tic; 
	if verbose, fprintf('\n ... processing %s', session(s).id); end
	
	nfiles = length(session(s).files);
	for n = 1:nfiles
		[snr(c) sd(c)] = g_compute_snr(session(s).files{n}, [], fmask, target, [], [session(s).id '_file_' num2str(n)]);
		fprintf(fout, '%s\t%.3f\t%.3f\n', session(s).files{n}, snr(c), sd(c));
		c = c +1;
	end

end

fclose(fout);

if verbose, fprintf('\n ... Finished.'); end

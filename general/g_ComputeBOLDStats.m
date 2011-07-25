function [] = g_ComputeBOLDStats(flist, target, verbose)

%	
%	function [] = g_ComputeBOLDStats(flist, target, verbose)
%	
%	Computes BOLD run per frame statistics
%	
%	flist   	- conc-like style list of subject image files or conc files: 
%                  subject id:<subject_id>
%                  roi:<path to the individual's brain segmentation file>
%                  file:<path to bold files - one per line>
%   target      - folder to save results into, default: where bold image is
%	verbose		- to report on progress or not [not]
%	
% 	Created by Grega Repovš on 2011-07-09.
%
% 	Copyright (c) 2011 Grega Repovs. All rights reserved.

if nargin < 3
	verbose = false;
	if nargin < 2
	    target = [];
	end
end

brainthreshold = 300;

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
                if verbose, fprintf('---> Reading mask'); end
                mask = gmrimage(strfind(subject(s).roi));
            end
        end
    end
    
    nfiles = length(subject(s).files);
	for n = 1:nfiles
	
	    % --- read image
	    
	    if verbose, fprintf('---> Reading %s', subject(s).files{n}); end
	    img = gmrimage(subject(s).files{n});

        % --- find all below threshold voxels
        
        img.data = img.image2D;
        img.data(isnan(img.data)) = 0;
        img.data(img.data < brainthreshold) = 0;
        bmask = img.zeroframes(1);
        bmask.data = min(img.data, [], 2) > 0;
        
        % --- apply also subject roi mask
        
	    if mask
	        bmask.data(mask.data == 0) = 0;
	    end
        
        % --- compute stats
        
        if verbose, fprintf('---> Computing stats'); end
        stats = mri_StatsTime(img, [], bmask);
        
        % --- get filename to save to 
        
        if target
            [w fname] = fileparts(subject(s).files{n});
        else
            fname = subject(s).files{n};
        end
        
        fname = strrep(fname, '.img', '');
        fname = strrep(fname, '.ifh', '');
        fname = strrep(fname, '.4dfp', '');
        fname = strrep(fname, '.gz', '');
        fname = strrep(fname, '.nii', '');
        
        % --- open the file and save
        
        if verbose, fprintf('---> Saving stats'); end
        
        fout = fopen(fullfile(target, [fname '_bstats.txt']), 'w');
        fprintf(fout, 'frame\tn\tm\tmin\tmax\tvar\tsd\tdvars\tdvarsm\tdvarsme\n');
        for f = 1:img.frames
            fprintf(fout, '%d\t%d\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.2f\t%.2f\t%.2f\n', f, stats.n(f), stats.mean(f), stats.min(f), stats.max(f), stats.var(f), stats.sd(f), stats.dvars(f), stats.dvarsm(f), stats.dvarsme(f));
        end
        fclose(fout);
    end
end

if verbose, fprintf('\n\nFINISHED!'); end



function [] = g_ComputeBOLDStats(flist, target, store, scrub, verbose)

%
%	function [] = g_ComputeBOLDStats(flist, target, store, scrub, verbose)
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
                if verbose, fprintf('\n---> Reading mask'); end
                mask = gmrimage(strfind(subject(s).roi));
            end
        end
    end

    nfiles = length(subject(s).files);
	for n = 1:nfiles

	    % --- read image

	    if verbose, fprintf('\n---> Reading %s', subject(s).files{n}); end
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

        if verbose, fprintf(' ... computing stats'); end
        stats = mri_StatsTime(img, [], bmask);

        % --------------------------------------------------------------
        %                                       save in an external file

        ext = true;
        if target
            if strcmp(target, 'none')
                ext = false;
            end
        end

        [w fname] = fileparts(subject(s).files{n});

        % --- get filename to save to

        fname = strrep(fname, '.img', '');
        fname = strrep(fname, '.ifh', '');
        fname = strrep(fname, '.4dfp', '');
        fname = strrep(fname, '.gz', '');
        fname = strrep(fname, '.nii', '');


        % --------------------------------------------------------------
        %                                                  prepare stats

        img.fstats_hdr = {'frame', 'n', 'm', 'var', 'sd', 'dvars', 'dvarsm', 'dvarsme', 'fd'};
        img.fstats      = zeros(img.frames, 9);
        img.fstats(:,1) = 1:img.frames;
        img.fstats(:,2) = stats.n;
        img.fstats(:,3) = stats.mean;
        img.fstats(:,4) = stats.var;
        img.fstats(:,5) = stats.sd;
        img.fstats(:,6) = stats.dvars;
        img.fstats(:,7) = stats.dvarsm;
        img.fstats(:,8) = stats.dvarsme;


        % --------------------------------------------------------------
        %                                              compute scrubbing

        if ~isempty(scrub)
            img = img.mri_ComputeScrub(scrub);
        end


        % --------------------------------------------------------------
        %                                                 embed and save

        if ~isempty(store)


            if strcmp(store, 'same')
                img.mri_saveimage();
            else
                tname = strrep(img.filename, img.rootfilename, [img.rootfilename '_' store]);
                img.mri_saveimage(tname);
            end
        end


        % --------------------------------------------------------------
        %                                                  save external

        if ext

            % --- save stats

            if verbose, fprintf(' ... saving stats'); end

            if ismember('fd', img.fstats_hdr)
                stats.fd = img.fstats(:, ismember(img.fstats_hdr, {'fd'}));
            else
                stats.fd = zeros(1, img.frames);
            end

            fout = fopen(fullfile(w, target, [fname '.bstats']), 'w');
            fprintf(fout, 'frame\tn\tm\tvar\tsd\tdvars\tdvarsm\tdvarsme\tfd\n');
            for f = 1:img.frames
                fprintf(fout, '%d\t%d\t%.2f\t%.2f\t%.2f\t%.3f\t%.3f\t%.3f\t%.3f\n', f, stats.n(f), stats.mean(f), stats.var(f), stats.sd(f), stats.dvars(f), stats.dvarsm(f), stats.dvarsme(f), stats.fd(f));
            end
            fclose(fout);

            % --- save scrub

            if ~isempty(img.scrub_hdr)

                if verbose, fprintf(' ... saving scrubbing data'); end
                fout = fopen(fullfile(w, target, [fname '.scrub']), 'w');
                fprintf(fout, 'frame\tmov\tdvars\tdvarsme\tidvars\tidvarsme\tudvars\tudvarsme\n');
                for f = 1:img.frames
                    fprintf(fout, '%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n', img.scrub(f,:));
                end
                fclose(fout);
            end
        end

        if verbose, fprintf(' ... done!'); end
    end
end

if verbose, fprintf('\n\nFINISHED!'); end



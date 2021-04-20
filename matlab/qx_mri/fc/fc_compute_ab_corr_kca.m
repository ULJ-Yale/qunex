% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function [] = fc_compute_ab_corr_kca(flist, smask, tmask, nc, mask, root, options, dmeasure, nrep, verbose)

%``function [] = fc_compute_ab_corr_kca(flist, smask, tmask, nc, mask, root, options, dmeasure, nrep, verbose)``
%
%   Segments the voxels in smask based on their connectivity pattern with tmask 
%   voxels. Uses k-means to group voxels in smask.
%
%   INPUTS
%   ======
%
%   --flist       A file list with information on sessions bold runs and 
%                 segmentation files, or a well strucutured string (see 
%                 general_read_file_list).
%   --smask       .names file for source mask definition.
%   --tmask       .names file for target mask roi definition.
%   --nc          List of the number(s) of clusters to compute k-means on.
%   --mask        Either number of frames to omit or a mask of frames to use [0].
%   --root        The root of the filename where results are to be saved [flist].
%   --options     A string with ['g']:
%
%                 - g - save results based on group average correlations
%                 - i - save individual sessions' results
%
%   --dmeasure    Distance measure to used ['correlation'].
%   --nrep        Number of replications to run [10].
%   --verbose     whether to report the progress full, script, none [none]
%
%	RESULTS
%   =======
%
%   The resulting files are:
%
%   - group:
%
%       <root>_group_k[N]
%           Group based cluster assignments for k=N.
%
%       <root>_group_k[N]_cent
%           Group based centroids for k=N.
%
%   - individual:
%
%       <root>_<session id>_group_k[N]
%           Individual's cluster assignments for k=N.
%
%       <root>_<session id>_group_k[N]_cent
%           Individual's centroids for k=N.
%
%   If root is not specified, it is taken to be the root of the flist.
%
%   USE
%   ===
%
%   Use the function to cluster source voxels (specified by smask) based on their
%   correlation pattern with target voxels (specified by tmask). The clustering
%   is computed using k-means for the number of clusters specified in the nc
%   parameter. If more than one value is specfied, a solution will be computed
%   for each value.
%
%   Correlations are computed using the img_compute_ab_correlation gmri method. 
%   Clustering is computed using kmeans function with dmeasure as distance 
%   measure, and taking the best of nrep replications.
%
%   EXAMPLE USE
%   ===========
%
%   ::
%
%       fc_compute_ab_corr_kca('study.list', 'thalamus.names', 'PFC.names', [3:9], ...
%                              0, 'Th-PFC', 'g', 'correlations', 15);
%

if nargin < 10 || isempty(verbose),  verbose  = 'none';            end
if nargin < 9  || isempty(nrep),     nrep     = 10;                end
if nargin < 8  || isempty(dmeasure), dmeasure = 'correlation';     end
if nargin < 7  || isempty(options),  options  = 'g';               end
if nargin < 6, root = '';                                          end
if nargin < 5  || isempty(mask),     mask     = 0;                 end
if nargin < 4, error('ERROR: At least file list, source and target masks and number of clusters must be specified to run fc_compute_ab_corr_kca!'); end

if isempty(root)
    [ps, root, ext] = fileparts(root);
    root = fullfile(ps, root);
end

if strcmp(verbose, 'full')
    script = true;
    method = true;
else
    if strcmp(verbose, 'script')
        script = true;
        method = false;
    else
        script = false;
        method = false;
    end
end

if strfind(options, 'g')
    group = true;
else
    group = false;
end
if strfind(options, 'i')
    indiv = true;
else
    indiv = false;
end



if script, fprintf('\n\nStarting ...'), end


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------------- make a list of all the files to process

if script, fprintf('\n ... listing files to process'), end

[session, nsessions, nfiles, listname] = general_read_file_list(flist, verbose);

if isempty(root)
    root = listname;
end


if script, fprintf(' ... done.'), end


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------- The main loop ... go through all the sessions

%   --- Get variables ready first

sROI = nimage.img_read_roi(smask, session(1).roi);
tROI = nimage.img_read_roi(tmask, session(1).roi);

if length(sROI.roi.roicodes2) == 1 & length(sROI.roi.roicodes2{1}) == 0
    sROIload = false;
else
    sROIload = true;
end

if length(tROI.roi.roicodes2) == 1 & length(tROI.roi.roicodes2{1}) == 0
    tROIload = false;
else
    tROIload = true;
end

if group
    nframes = sum(sum(sROI.image2D > 0));
    gres = sROI.zeroframes(nframes);
    gcnt = sROI.zeroframes(1);
    gcnt.data = gcnt.image2D;
end

%   --- Start the loop

for s = 1:nsessions

    %   --- reading in image files
    if script, tic, end
	if script, fprintf('\n------\nProcessing %s', session(s).id), end
	if script, fprintf('\n... reading file(s) '), end

    % --- check if we need to load the session region file

    if ~strcmp(session(s).roi, 'none')
        if tROIload | sROIload
            roif = nimage(session(s).roi);
        end
    end

    if tROIload
	    tROI = nimage.img_read_roi(tmask, roif);
    end
    if sROIload
	    sROI = nimage.img_read_roi(smask, roif);
    end

    % --- load bold data

	nfiles = length(session(s).files);

	img = nimage(session(s).files{1});
	if mask, img = img.sliceframes(mask); end
	if script, fprintf('1'), end
	if nfiles > 1
    	for n = 2:nfiles
    	    new = nimage(session(s).files{n});
    	    if mask, new = new.sliceframes(mask); end
    	    img = [img new];
    	    if script, fprintf(', %d', n), end
        end
    end
    if script, fprintf('\n... computing ABCor'), end

    ABCor = img.img_compute_ab_correlation(sROI, tROI, method);

    if indiv
        data = fc_fisher(ABCor.image2D');
        CA = sROI.maskimg(sROI);
        Cent = tROI.maskimg(tROI);

        for c = 1:length(nc)
            k = nc(c);

            if script, fprintf('\n... computing %d individual CA solution', k), end
            ifile = [root '_' session(s).id '_k' num2str(k)];

            Cent = Cent.zeroframes(k);
            [CA.data Cent.data] = kmeans(data, k, 'distance', dmeasure, 'replicates', nrep);
            Cent.data = Cent.data';

            if script, fprintf('\n... saving %s\n', ifile); end
            CA.img_saveimage(ifile);
            Cent.img_saveimage([ifile '_cent']);
        end
    end

    if group
        if script, fprintf('\n... computing group results\n'); end
        gres.data = gres.data + fc_fisher(ABCor.data);
        if tROIload
            gcnt.data = gcnt.data + tROI.image2D > 0;
        end
    end

    if script, fprintf('... done [%.1fs]\n', toc); end
end


if group
    if script, fprintf('\n=======\nComputing group CA solution'), end

    if ~tROIload
        gcnt.data = (tROI.image2D > 0) .* nsessions;
    end

    gres.data = gres.data ./ repmat(gcnt.data,1,nframes);
    CA = sROI.maskimg(sROI);
    Cent = tROI.maskimg(sROI);

    for c = 1:length(nc)
        k = nc(c);
        if script, fprintf(' k: %d', k), end

        Cent = Cent.zeroframes(k);
        [CA.data Cent.data] = kmeans(gres.data', k, 'distance', dmeasure, 'replicates', nrep);
        Cent.data = Cent.data';

        if script, fprintf('\n... saving %s\n', ifile); end
        CA.img_saveimage([root '_group_k' num2str(k)]);
        Cent.img_saveimage([root '_group_k' num2str(k) '_cent']);
    end
end


if script, fprintf('\nDONE!\n\n'), end


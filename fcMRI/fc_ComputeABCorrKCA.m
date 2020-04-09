function [] = fc_ComputeABCorrKCA(flist, smask, tmask, nc, mask, root, options, dmeasure, nrep, verbose)

%function [] = fc_ComputeABCorrKCA(flist, smask, tmask, nc, mask, root, options, dmeasure, nrep, verbose)
%
%	Segments the voxels in smask based on their connectivity pattern with tmask voxels.
%   Uses k-means to group voxels in smask.
%
%   INPUTS
%       flist    - A file list with information on subjects bold runs and segmentation files,
%                  or a well strucutured string (see g_ReadFileList).
%       smask    - .names file for source mask definition.
%       tmask    - .names file for target mask roi definition.
%       nc       - List of the number(s) of clusters to compute k-means on.
%       mask     - Either number of frames to omit or a mask of frames to use [0].
%       root     - The root of the filename where results are to be saved [flist].
%       options  - A string with ['g']:
%                   : g - save results based on group average correlations
%                   : i - save individual subjects' results
%       dmeasure - Distance measure to used ['correlation'].
%       nrep     - Number of replications to run [10].
%       verbose - whether to report the progress full, script, none [none]
%
%	RESULTS
%   The resulting files are:
%
%   group:
%   <root>_group_k[N]       ... Group based cluster assignments for k=N.
%   <root>_group_k[N]_cent  ... Group based centroids for k=N.
%
%   individual:
%   <root>_<subject id>_group_k[N]      ... Individual's cluster assignments for k=N.
%   <root>_<subject id>_group_k[N]_cent ... Individual's centroids for k=N.
%
%   If root is not specified, it is taken to be the root of the flist.%
%
%   USE
%   Use the function to cluster source voxels (specified by smask) based on their
%   correlation pattern with target voxels (specified by tmask). The clustering
%   is computed using k-means for the number of clusters specified in the nc
%   parameter. If more than one value is specfied, a solution will be computed
%   for each value.
%
%   Correlations are computed using the img_ComputeABCor gmri method. Clustering
%   is computed using kmeans function with dmeasure as distance measure, and
%   taking the best of nrep replications.
%
%   EXAMPLE USE
%   fc_ComputeABCorrKCA('study.list', 'thalamus.names', 'PFC.names', [3:9], 0, 'Th-PFC', 'g', 'correlations', 15);
%
%   ---
% 	Written by Grega Repovš on 2010-08-13.
%
%   Changelog
%   2017-03-19 Grega Repovs
%            - Cleaned up the code
%            - Updated documentation
%   2017-04-18 Grega Repovs
%            - Adjusted to use g_ReadFileList
%

if nargin < 10 || isempty(verbose),  verbose  = 'none';            end
if nargin < 9  || isempty(nrep),     nrep     = 10;                end
if nargin < 8  || isempty(dmeasure), dmeasure = 'correlation';     end
if nargin < 7  || isempty(options),  options  = 'g';               end
if nargin < 6, root = '';                                          end
if nargin < 5  || isempty(mask),     mask     = 0;                 end
if nargin < 4, error('ERROR: At least file list, source and target masks and number of clusters must be specified to run fc_ComputeABCorrKCA!'); end

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

[subject, nsubjects, nfiles, listname] = g_ReadFileList(flist, verbose);

if isempty(root)
    root = listname;
end


if script, fprintf(' ... done.'), end


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------- The main loop ... go through all the subjects

%   --- Get variables ready first

sROI = nimage.img_ReadROI(smask, subject(1).roi);
tROI = nimage.img_ReadROI(tmask, subject(1).roi);

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

for s = 1:nsubjects

    %   --- reading in image files
    if script, tic, end
	if script, fprintf('\n------\nProcessing %s', subject(s).id), end
	if script, fprintf('\n... reading file(s) '), end

    % --- check if we need to load the subject region file

    if ~strcmp(subject(s).roi, 'none')
        if tROIload | sROIload
            roif = nimage(subject(s).roi);
        end
    end

    if tROIload
	    tROI = nimage.img_ReadROI(tmask, roif);
    end
    if sROIload
	    sROI = nimage.img_ReadROI(smask, roif);
    end

    % --- load bold data

	nfiles = length(subject(s).files);

	img = nimage(subject(s).files{1});
	if mask, img = img.sliceframes(mask); end
	if script, fprintf('1'), end
	if nfiles > 1
    	for n = 2:nfiles
    	    new = nimage(subject(s).files{n});
    	    if mask, new = new.sliceframes(mask); end
    	    img = [img new];
    	    if script, fprintf(', %d', n), end
        end
    end
    if script, fprintf('\n... computing ABCor'), end

    ABCor = img.img_ComputeABCor(sROI, tROI, method);

    if indiv
        data = fc_Fisher(ABCor.image2D');
        CA = sROI.maskimg(sROI);
        Cent = tROI.maskimg(tROI);

        for c = 1:length(nc)
            k = nc(c);

            if script, fprintf('\n... computing %d individual CA solution', k), end
            ifile = [root '_' subject(s).id '_k' num2str(k)];

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
        gres.data = gres.data + fc_Fisher(ABCor.data);
        if tROIload
            gcnt.data = gcnt.data + tROI.image2D > 0;
        end
    end

    if script, fprintf('... done [%.1fs]\n', toc); end
end


if group
    if script, fprintf('\n=======\nComputing group CA solution'), end

    if ~tROIload
        gcnt.data = (tROI.image2D > 0) .* nsubjects;
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


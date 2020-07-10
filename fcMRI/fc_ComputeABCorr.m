function [] = fc_ComputeABCorr(flist, smask, tmask, mask, root, options, verbose)

%``function [] = fc_ComputeABCorr(flist, smask, tmask, mask, root, options, verbose)`
%
%	Computes the correlation of each source mask voxel with each target mask 
%   voxel.
%
%   INPUTS
%   ======
%
%   --flist      File list with information on sessions bold runs and 
%                segmentation files, or a well strucutured string (see 
%                g_ReadFileList).
%   --smask      .names file for source mask definition.
%   --tmask      .names file for target mask roi definition.
%   --mask       Either number of frames to omit or a mask of frames to use [0].
%   --root       The root of the filename where results are to be saved [''].
%   --options    A string specifying what correlations to save ['g']:
%
%                - 'g' - compute mean correlation across sessions (only makes
%                  sense with the same sROI for each session)
%                - 'i' - save individual sessions' results
%
%   --verbose    Whether to report the progress full, script, none. ['none']
%
%	RESULTS
%   =======
%
%	The resulting files are:
%
%   - group:
%
%       <root>_group_ABCor_Fz
%           Mean Fisher Z value across participants.
%
%       <root>_group_ABCor_r
%           Mean Pearson r (converted from Fz) value across participants.
%
%   - individual:
%
%       <root>_<session id>_ABCor
%           Pearson r correlations for the individual.
%
%   If root is not specified, it is taken to be the root of the flist.
%
%   USE
%   ===
%
%   Use the function to compute individual and/or group correlations of each
%   smask voxel with each tmask voxel. tmask voxels are spread across the volume
%   and smask voxels are spread across the volumes. For more details see
%   `img_ComputeABCorr` - nimage method.
%
%   EXAMPLE USE
%   ===========
%
%   ::
%
%       fc_ComputeABCorr('scz.list', 'PFC.names', 'ACC.names', 5, ...
%                        'SCZ_PFC-ACC', 'g', 'full');
%

%	~~~~~~~~~~~~~~~~~~
%
% 	Changelog
%
%   2010-08-09 Grega Repovs
%              Initial version
%   2017-03-19 Grega Repovs
%              Updated documentation, cleaned code.
%   2017-04-18 Grega Repovs
%              Adjusted to use g_ReadFileList


if nargin < 7 || isempty(verbose), verbose = 'none'; end
if nargin < 6 || isempty(options), options = 'g';    end
if nargin < 5 root = []; end
if nargin < 4 mask = []; end
if nargin < 3 error('ERROR: At least file list, source and target masks must be specified to run fc_ComputeABCorr!'); end


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

[session, nsessions, nfiles, listname] = g_ReadFileList(flist, verbose);

if isempty(root)
    root = listname;
end

if script, fprintf(' ... done.'), end


%   ------------------------------------------------------------------------------------------
%   -------------------------------------------- The main loop ... go through all the sessions

%   --- Get variables ready first

sROI = nimage.img_ReadROI(smask, session(1).roi);
tROI = nimage.img_ReadROI(tmask, session(1).roi);

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
	    tROI = nimage.img_ReadROI(tmask, roif);
    end
    if sROIload
	    sROI = nimage.img_ReadROI(smask, roif);
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
    if script, fprintf('\n'), end

    ABCor = img.img_ComputeABCor(sROI, tROI, method);
    ABCor = ABCor.unmaskimg;

    if indiv
        ifile = [root '_' session(s).id '_ABCor'];
        if script, fprintf('\n... saving %s\n', ifile); end
        ABCor.img_saveimage(ifile);
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
    if script, fprintf('\n=======\nSaving group results'), end

    if ~tROIload
        gcnt.data = (tROI.image2D > 0) .* nsessions;
    end

    gres.data = gres.data ./ repmat(gcnt.data,1,nframes);
    gres.img_saveimage([root '_group_ABCor_Fz']);
    gres.data = fc_FisherInv(gres.data);
    gres.img_saveimage([root '_group_ABCor_r']);
end


if script, fprintf('\nDONE!\n\n'), end


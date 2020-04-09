function  [] = g_ComputeGroupBOLDStats(flist, tfile, stats, inmask, ignore)

% function  [] = g_ComputeGroupBOLDStats(flist, tfile, stats, inmask, ignore)
%
%   function for extraction of image statistics over the whole group.
%
%   INPUT
%       flist   ... A subjects list file.
%       tfile   ... The file root to save the results to [''].
%       stats   ... A cell array or a comma separated string specifying, which statistics to compute.
%       inmask  ... A mask of frames to exclude or an event string specifying which frames to use.
%       ignore  ... do we omit frames to be ignored (no)
%               -> 'no':    do not ignore any additional frames
%               -> 'fidl':  ignore frames as marked in .fidl file
%               -> '<col>': the column in *_scrub.txt file that matches bold file to be used for ignore mask
%
%   USE
%   The function computes for each subject the specified image statistics across
%   the BOLD image, using the nimage img_Stats method. Results are saved for
%   each computed statistics in a separate file with one volume for each subject
%   with order of volumes matching the order in which the subjects are listed in
%   the flist file. The root of the files in which the results are saved is
%   specified in tfile. If not specified (i.e. left empty) the root will be the
%   root of the flist.
%
%   The function is flexible in specifying what frames to use and/or exclude.
%   inmask parameter can specify either a mask of frames to exclude for each
%   subject, or it can specify an eventstring to be used with a per-subject
%   fidl file. If an eventstring is specifed, then the list file (flist) needs
%   to also list a fidl file for each subject. The eventstring will then be
%   used to create a regressor matrix using g_CreateTaskRegressors function,
%   and each frame for which there is a non-zero value in any of the regressor
%   columns will be included in the computation of statistics. As an example,
%   if the statistics are to be computed across the 3rd and 4th frames of each
%   'neutral' and 'negative' events specified in the fidl file, then the
%   eventstring would be:
%
%   'negative:block:3:4|neutral:block:3:4'
%
%   Additionally, the ignore parameter specifies which frames to exclude based
%   on image scrubbing information. If the information is to be taken out of a
%   .scrub file then the name of the relevant column needs to be specified in
%   the ignore parameter. If the ignore parameter is set to 'fidl' then the
%   ignore frames in the fidl file will be used.
%
%   EXAMPLE USE
%   To compute mean and standard variation and exclude the first 5 frames and
%   the frames marked bad using udvarsme criterion, use:
%
%   >>> g_ComputeGroupBOLDStats('scz-wm.list', [], 'm, sd', 5, 'udvarsme');
%
%   To compute the mean and standard variation for all negative trials (frames
%   3 & 4), and use ignore information in fidl file, use:
%
%   >>> g_ComputeGroupBOLDStats('scz-wm.list', [], 'm, sd', 'negative:block:3:4', 'fidl');
%
%   SEE ALSO
%   nimage.img_Stats
%   g_CreateTaskRegressors
%
%   ---
%   Written by Grega Repovs - 2013-09-15
%
%   Changelog
%   2017-03-12 Grega Repovs
%            - Updated documentation, cleaned code.


if nargin < 5, ignore = []; end
if nargin < 4 || isempty(inmask), inmask = 5; end
if nargin < 3 || isempty(stats),  stats  = 'sd'; end
if nargin < 2, tfile  = []; end
if nargin < 1, error('ERROR: Please specify list of files to process!'); end

if ~iscell(stats)
    stats = strtrim(regexp(stats, ',', 'split'));
end

nstats = length(stats);

if isempty(tfile)
    [fpathstr, fname, fext] = fileparts(flist);
    tfile = strrep(fname, '.list', '');
    tfile = strrep(tfile, '.conc', '');
    tfile = strrep(tfile, '.4dfp', '');
    tfile = strrep(tfile, '.img', '');
    tfile = strrep(tfile, '.nii', '');
    tfile = strrep(tfile, '.gz', '');
    tfile = strrep(tfile, '.dtseries', '');
end

if isempty(ignore)
    ignore = 'no';
end

if ~ischar(ignore)
    error('ERROR: Argument ignore has to be a string specifying whether and what to ignore!');
end

eventbased = false;
if isa(inmask, 'char')
    eventbased = true;
    if strcmp(ignore, 'fidl')
        fignore = 'ignore';
    else
        fignore = 'no';
    end
end


%   ------------------------------------------------------------------------------------------
%                                                                Check if the files are there!


go = true;

fprintf('\n\nChecking ...\n');
go = go & g_CheckFile(flist, 'image file list','error');
if ~go
    error('ERROR: Some files were not found. Please check the paths and start again!\n\n');
end


%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf('\n ... listing files to process');

subject = g_ReadFileList(flist);
nsub = length(subject);

fprintf(' ... done.');


%   ------------------------------------------------------------------------------------------
%                                                The main loop ... go through all the subjects

first = true;

for n = 1:nsub

    fprintf('\n ... processing %s', subject(n).id);

    % ---> reading image files

    fprintf('\n     ... reading image file(s)');

    y = nimage(subject(n).files{1});
    for f = 2:length(subject(n).files)
        y = [y nimage(subject(n).files{f})];
    end

    fprintf(' ... %d frames read, done.', y.frames);

    % ---> creating timeseries mask

    if eventbased
        mask = [];
        if isfield(subject(n), 'fidl')
            if subject(n).fidl
                rmodel = g_CreateTaskRegressors(subject(n).fidl, y.runframes, inmask, fignore);
                mask   = rmodel.run;
                nmask  = [];
                for r = 1:length(mask)
                    nmask = [nmask; sum(mask(r).matrix,2)>0];
                end
                mask = nmask;
            end
        end
    else
        mask = inmask;
    end

    % ---> slicing image

    if length(mask) == 1
        y = y.sliceframes(mask, 'perrun');
    else
        y = y.sliceframes(mask);                % this might need to be changed to allow for per run timeseries masks
    end

    % ---> remove additional frames to be ignored

    if ~ismember(ignore, {'no', 'fidl'})
        scol = ismember(y.scrub_hdr, ignore);
        if sum(scol) == 1;
            mask = y.scrub(:,scol)';
            y = y.sliceframes(mask==0);
        else
            fprintf('\n         WARNING: Field %s not present in scrubbing data, no frames scrubbed!', ignore);
        end
    end

    % ---> extracting statistics

    fprintf('\n     ... computing statistics ');

    for s = 1:nstats
        t = y.img_Stats(stats{s});
        t.data = t.image2D;
        if first
            r(s) = t.zeroframes(nsub);
        end
        r(s).data(:,n) = t.data();
    end

    first = false;

end


%   ------------------------------------------------------------------------------------------
%                                                                            Saving group data

fprintf('\n... saving ');

for s = 1:nstats
    fprintf('\n    ... %s ', stats{s});
    r(s).img_saveimage([tfile '_' stats{s}]);
end

fprintf('\n... DONE\n\n');

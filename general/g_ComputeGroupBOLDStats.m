function  [] = g_ComputeGroupBOLDStats(flist, tfile, stats, inmask, ignore)

% function  [] = g_ComputeGroupBOLDStats(flist, tfile, stats, inmask, ignore)
%
%   function for extraction of statistics over the whole group
%
%   flist   - file with subject list
%   tfile   - the file root to save the results to
%   stats   - which statistics to compute
%   inmask  - mask of frames to exclude
%   ignore  - do we omit frames to be ignored (no)
%           -> no:    do not ignore any additional frames
%           -> event: ignore frames as marked in .fidl file
%           -> other: the column in *_scrub.txt file that matches bold file to be used for ignore mask
%
%   (c) Grega Repovs - 2013-09-15


if nargin < 5
    scrub = [];
    if nargin < 4
        omit = [];
        if nargin < 3
            stats = [];
            if nargin < 2
                tfile = [];
                if nargin < 1
                    error('ERROR: Please specify list of files to process!');
                end
            end
        end
    end
end

if isempty(inmask) == [], inmask = 5; end
if isempty(stats)  == [], stats  = {'sd'} ; end
nstats = length(stats);

if isempty(tfile)
    [fpathstr, fname, fext] = fileparts(flist);
    tfile = strrep(fname, '.list', '');
    tfile = strrep(tfile, '.conc', '');
    tfile = strrep(tfile, '.4dfp', '');
    tfile = strrep(tfile, '.img', '');
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
    fprintf('ERROR: Some files were not found. Please check the paths and start again!\n\n');
    return
end


%   ------------------------------------------------------------------------------------------
%                                                      make a list of all the files to process

fprintf('\n ... listing files to process');

subject = g_ReadSubjectsList(flist);
nsub = length(subject);

fprintf(' ... done.');


%   ------------------------------------------------------------------------------------------
%                                                The main loop ... go through all the subjects

first = true;

for n = 1:nsub

    fprintf('\n ... processing %s', subject(n).id);

    % ---> reading image files

    fprintf('\n     ... reading image file(s)');

    y = gmrimage(subject(n).files{1});
    for f = 2:length(subject(n).files)
        y = [y gmrimage(subject(n).files{f})];
    end

    fprintf(' ... %d frames read, done.', y.frames);

    % ---> creating timeseries mask

    if eventbased
        mask = [];
        if isfield(subject(n), 'fidl')
            if subject(n).fidl
                mask = g_CreateTaskRegressors(subject(n).fidl, y.runframes, inmask, fignore);
                nmask = [];
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
        t = y.mri_Stats(stats{s});
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
    r(s).mri_saveimage([tfile '_' stats{s}]);
end

fprintf('\n... DONE\n\n');
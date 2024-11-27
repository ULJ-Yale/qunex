function [obj, commands] = img_compute_gbc_fc(obj, command, sroi, troi, options)

%``img_compute_gbc_fc(obj, command, sroi, troi, options)``
%
%   Computes whole brain GBC based on the specified masks and command string.
%
%   Parameters
%       --obj (nimage object):
%           Image with the timeseries to compute the GBC over.
%
%       --command (str):
%           A pipe separated string describing GBC to compute. 
%           There are a number of options available. They can be divided by
%           those that work on untransformed functional connectivity (Fc) values
%           e.g. covariance, and those that work on functional connectivity
%           estimates transformed to Fisher z (Fz) values. Note that the function
%           does not check the validity of using untransformed values or the
%           validity of their transform to Fz values.
%
%           The options that work on untransformed values are:
%
%           - mFc:t
%               computes mean Fc value across all voxels (over threshold t)
%           - aFc:t
%               computes mean absolute Fc value across all voxels (over
%               threshold t)
%           - pFc:t
%               computes mean positive Fc value across all voxels (over
%               threshold t)
%           - nFc:t
%               computes mean negative Fc value across all voxels (below
%               threshold t)
%
%           - aD:t
%               computes proportion of voxels with absolute Fc over t
%           - pD:t
%               computes proportion of voxels with positive Fc over t
%           - nD:t
%               computes proportion of voxels with negative Fc below t
%
%           - mFcp:n
%               computes mean Fc value across n proportional ranges
%           - aFcp:n
%               computes mean absolute Fc value across n proportional ranges
%           - mFcs:n
%               computes mean Fc value across n strength ranges
%           - pFcs:n
%               computes mean Fc value across n strength ranges for positive
%               correlations
%           - nFcs:n
%               computes mean Fc value across n strength ranges for negative
%               correlations
%           - aFcs:n
%               computes mean absolute Fc value across n strength ranges
%
%           - mDs:n
%               computes proportion of voxels within n strength ranges of Fc
%           - aDs:n
%               computes proportion of voxels within n strength ranges of
%               absolute Fc
%           - pDs:n
%               computes proportion of voxels within n strength ranges of
%               positive Fc
%           - nDs:n
%               computes proportion of voxels within n strength ranges of
%               negative Fc.
%
%           The options that first transform functional connectivity estimates
%           to Fisher z values are:
%
%           - mFz:t
%               computes mean Fz value across all voxels (over threshold t)
%           - aFz:t
%               computes mean absolute Fz value across all voxels (over
%               threshold t)
%           - pFz:t
%               computes mean positive Fz value across all voxels (over
%               threshold t)
%           - nFz:t
%               computes mean negative Fz value across all voxels (below
%               threshold t)
%
%           - mFzp:n
%               computes mean Fz value across n proportional ranges
%           - aFzp:n
%               computes mean absolute Fz value across n proportional ranges
%           - mFzs:n
%               computes mean Fz value across n strength ranges
%           - pFzs:n
%               computes mean Fz value across n strength ranges for positive
%               correlations
%           - nFzs:n
%               computes mean Fz value across n strength ranges for negative
%               correlations
%           - aFzs:n
%               computes mean absolute Fz value across n strength ranges
%
%       --sroi (nimage object):
%           An roi image specifying the voxels or greyordinates over which to 
%           compute the GBC. If multiple ROI are present, their union will be 
%           used. This image should be prepared using `img_prep_roi` function
%           and include the roi structure.
%
%       --troi (nimage object):
%           An roi image specifying the voxels or greyordinates for which to
%           compute the GBC. If multiple ROI are present, their union will be
%           used. This image should be prepared using `img_prep_roi` function
%           and include the roi structure.
%
%       --options (struct field or string):
%           Either a struct field or a pipe separated string of <key>:<value>
%           pairs specifying additional options.
%
%           It accepts the following keys and values:
%
%           - rmax
%               The r value above which the correlations are considered to be of 
%               the same functional ROI. Set to 0 if it should not be used.
%               Defaults to 0.
%
%           - time
%               Whether to print timing information. Defaults to 'false'.
%
%           - step
%               How many voxels or greyordinates to process in a single step.
%               Defaults to 12000.
%
%           - fcargs
%               Additional arguments for computing functional connectivity, e.g.
%               k for computation of mutual information or standardize and
%               shrinkage for computation of inverse covariance. These parameters
%               need to be provided as subfields of fcargs, e.g.:
%               'fcargs>standardize:partialcorr,shrinkage:LW'
%
%   Returns
%       --obj
%           The resulting nimage object with as many frames as there were commands 
%           given.
%
%       --commands
%           A data structure describing the parameters of commands used.
%
%   Notes:
%       The method enables computing a set of Global Brain Connectivity values. 
%       The input image is expected to hold a time- or data-series for each voxel,
%       across which the correlations (or covariances) will be computed. What is 
%       to be computed is specified using the command string. The string consists 
%       of a pipe separated key:value pairs. Key specifies what is to be computed 
%       (as listed above), whereas value specifies what threshold or number of 
%       strength or proportional ranges is to be used. Strength range is here 
%       defined as n intervals of correlation values. For instance, when 
%       computing mean Fz with n of 4 the ranges would be [-1 -.5], [-.5 0] 
%       [0 .5] [.5 1]. Proportional range would separate all the correlations 
%       into n strength groups of the same number of voxels in each group. An 
%       example of command string can be::
%
%       'mFz:0.1|mFz:0.2|aFz:0.1|aFz:0.2|pFz:0.1|pFz:0.2'
%
%       This would result in an image with 6 frames. The first frame would hold 
%       for each voxel the mean Fz of its correlation with all other voxels, 
%       where the correlation is higher than .1 or lower than -.1. The second 
%       frame would hold the results with the threshold of .2. The third and 
%       fourth frames would hold the mean absolute correlation above the 
%       respective thresholds, the fifth and sixth the mean of only positive 
%       correlations above the specified thresholds. Combining multiple commands 
%       in a single call significantly cuts down on time as the correlations 
%       need to be computed only once, just their aggregation function changes.
%
%       sroi defines the source mask, the voxels or grayordinates over which the
%       functiona connectivity is to be computed. troi defines the target mask, 
%       the voxels or grayordinates for which the functional connectivity with 
%       the source is to be computed. The final image will only contain values 
%       for the target mask.
%
%       As neighboring voxels can belong to the same functional parcel, 
%       correlation between them approaches 1. Including them in the computation 
%       of GBC can inflate its value. One way to deal with that is to assume 
%       that voxels or grayordinates  that have correlation higher than rmax 
%       belong to the same functional parcel and need to be excluded from the 
%       computation of the GBC. It has to be taken into account that sepecifying 
%       rmax does not exclude only the contiguous voxels or grayordinates but 
%       any voxel or grayordinate for which correlation is above threshold.
%
%       Computing GBC is computationally expensive. If time is set to true, the 
%       time it takes to compute GBC will be reported. This can inform setting 
%       of step. step defines how many voxels to compute the GBC for in a single
%       step. Having too small vstep results in more steps, which reduces the
%       inherent paralelization in computing correlations. Too large vstep can
%       result in chunks that don't fit into memory, which requires use of 
%       memory paging and consequent longer execution times.
%
%       The resulting commands variable will be a structure list. It will provide
%       fields 'command' with the type of GBC computed, 'parameter' with the
%       threshold or limits used in computation of GBC, and 'volumes' with the
%       information on how many volumes the results of the command will span 
%       (e.g. 5 for 5 strength ranges). The list will be in the same order as 
%       the volumes in the resulting image.
%
%   Example:
%
%       img = img.img_compute_gbc_fc('mFz:0.1|pFz:0.1|nFz:0.1', sroi, troi, ...
%           'rmax:0.99|time:false|step:100000');
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 5, options = ''; end
if nargin < 4, troi = [];    end
if nargin < 3, sroi = [];    end
if nargin < 2, error('ERROR: No command given to compute GBC!'); end

% ----- parse options
default = 'rmax=0|time=false|step=12000|verbose=true|printdebug=false';
options = general_parse_options([], options, default);

verbose = strcmp(options.verbose, 'true');
printdebug = strcmp(options.debug, 'true');
time = strcmp(options.time, 'true');

if ischar(options.rmax), options.rmax = false; end
options.time = strcmp(options.time, 'true');

% ---- prepare data

if verbose, fprintf('\nimg_compute_gbc_fc\n... setting up data\n'), end

obj.data = obj.image2D;
nvox = size(obj.image2D, 1);

if isempty(troi)
    ntvox = nvox;
    tmask = 1:ntvox;
else
    tmask = unique(vertcat(troi.roi.indeces));
    ntvox = length(tmask);
end

if isempty(sroi)
    nsvox = nvox;
    smask = 1:nsvox;
else
    smask = unique(vertcat(sroi.roi.indeces));
    nsvox = length(smask);
end

% ---- parse command

if verbose, fprintf('... starting GBC on %s\n', fullfile(obj.filepath, obj.filename)); stime = tic; end
commands  = parseCommand(command, nsvox);
ncommands = length(commands);
nvolumes  = sum([commands.volumes]);
coffsets  = [1 cumsum([commands.volumes])+1];
coffsets  = coffsets(1:ncommands);

% ---- set up results

results = zeros(ntvox, nvolumes);


% ---- do the loop

voxels = obj.voxels;
data   = fc_prepare(obj.data, options.fcmeasure);
cstep  = options.step;
nsteps = floor(ntvox/options.step);
lstep  = mod(ntvox,options.step);

if verbose
    if verbose, fprintf('... %d voxels & %d frames to process in %d steps\n... computing GBC for voxels:\n', ntvox, obj.frames, nsteps + 1); end
end

% x = data';

for n = 1:nsteps+1

    if n > nsteps, cstep=lstep; end
    fstart = options.step * (n-1) + 1;
    fend   = options.step * (n-1) + cstep;
    pevox  = false;

    if verbose
        crange = [num2str(fstart) ':' num2str(fend)];
        % for c = 1:slen, fprintf('\b'), end
        fprintf('     ... %14s\n', crange);
        % slen = length(crange);
    end

    if time, fprintf('     -> fc'); tic; end
    Fc = fc_compute(data(tmask(fstart:fend),:), data(smask, :), options.fcmeasure, true, options);
    if time, fprintf(' [%.3f s]\n', toc); end

    % -------- Compute common stuff ---------

    % coms = {commands.command};

    % Added to remove within region correlations defined as correlations above a 
    % specified rmax threshold. If not, it does not remove correlation with 
    % itself.

    if time, fprintf('     -> clip'); tic; end    
    if options.rmax
        clip = Fc < options.rmax;
        Fc = Fc .* clip;
        evoxels = sum(clip,1);
        clipped = voxels - evoxels;
        if verbose, fprintf(' cliped: %d ', sum(sum(clip))); end
    else
        clipped = 0;
        evoxels = voxels;
    end
    if time, fprintf(' [%.3f s]\n', toc); end    

    % -------- Run the command loop ---------
    
    sorted   = false;
    asorted  = false;
    fishered = false;
    aFc      = [];

    for c = 1:ncommands
        tcommand   = commands(c).command;
        tparameter = commands(c).parameter;
        tvolumes   = commands(c).volumes;
        toffset    = coffsets(c);
        tprefix    = tcommand(1);
        tsuffix    = tcommand(end);

        % ---> are we converting to Fisher z values

        if ~isempty(strfind(tcommand, 'Fz')) && ~fishered

            if time, fprintf('     -> Fz'); tic; end
            Fc = fc_fisher(Fc);
            if ~isreal(Fc)
                if verbose, fprintf(' c>r'); end
                Fc = real(Fc);
            end
            if time, fprintf(' [%.3f s]\n', toc); end
            
            aFc = [];
            asorted = false;
            fishered = true;
        end

        % ---> are we computing absolute values

        if strcmp(tprefix, 'a') && isempty(aFc)
            if time, fprintf('     -> abs'); tic; end
            aFc = abs(Fc);
            if time, fprintf(' [%.3f s]\n', toc); end
        end

        % ---> are we sorting
        if strcmp(tsuffix, 'p')
            if strcmp(tprefix, 'a') && ~asorted
                if time, fprintf('     -> sort'); tic; end
                aFc = sort(aFc, 2);
                if time, fprintf(' [%.3f s]\n', toc); end
                % fprintf(' %.3f %.3f', aFc(1, 1), aFc(end, 1));
                asorted = true;
            elseif ~sorted
                if time, fprintf('     -> sort'); tic; end
                Fc = sort(Fc, 2);
                if time, fprintf(' [%.3f s]\n', toc); end
                % fprintf(' %.3f %.3f', Fc(1, 1), Fc(end, 1));
                % if Fc(1,1) > -0.001
                %     fprintf(' resort');
                %     Fc = sort(Fc);
                %     fprintf(' %.3f %.3f', min(Fc(1,:)), max(Fc(end,:)));
                % end
                sorted = true;
            end
        end

        if time, fprintf('     -> %s', tcommand); tic; end

        switch tcommand

            % -----> compute mFz, mFc

            case {'mFz', 'mFc'}
                if tparameter == 0
                    results(fstart:fend, toffset) = sum(Fc, 2) ./ evoxels;
                else
                    results(fstart:fend, toffset) = rmean(Fc, (Fc >= tparameter) | (Fc <= tparameter), 2);
                end
            % -----> compute aFz, aFc

            case {'aFz', 'aFc'}
                if tparameter == 0
                    results(fstart:fend, toffset) = sum(aFc, 2)./evoxels;
                else
                    results(fstart:fend, toffset) = rmean(aFc, (aFc >= tparameter), 2);
                end

            % -----> compute pFz, pFc

            case {'pFz', 'pFc'}
                results(fstart:fend, toffset) = rmean(Fc, (Fc >= tparameter), 2);

            % -----> compute nFz, nFc

            case {'nFz', 'nFc'}
                results(fstart:fend, toffset) = rmean(Fc, (Fc <= tparameter), 2);

            % -----> compute pD

            case 'pD'
                results(fstart:fend, toffset) = sum(Fc >= tparameter, 2)./evoxels;

            % -----> compute nD

            case 'nD'
                results(fstart:fend, toffset) = sum(Fc <= tparameter, 2)./evoxels;

            % -----> compute aD

            case 'aD'
                results(fstart:fend, toffset) = sum(aFc >= tparameter, 2)./evoxels;

            % -----> compute over prange

            case {'mFzp', 'aFzp', 'mFcp', 'aFcp'}

                if ~pevox
                    pevox = tparameter(:, 2) - tparameter(:, 1) + 1;
                    if options.rmax
                        pevox = repmat(pevox, 1, cstep);
                        pevox(tvolumes, :) = pevox(tvolumes, :) - clipped;  % we're assuming all clipped voxels are in the top group
                    else
                        pevox(tvolumes) = pevox(tvolumes) - clipped;  % we're assuming all clipped voxels are in the top group
                    end
                end


                for p = 1:tvolumes
                    if strcmp(tcommand, 'mFzp') || strcmp(tcommand, 'mFcp')
                        results(fstart:fend,toffset+(p-1)) = sum(Fc(:, [tparameter(p, 1):tparameter(p, 2)]), 2)./pevox(p);
                    else
                        results(fstart:fend,toffset+(p-1)) = sum(aFc(:, [tparameter(p, 1):tparameter(p, 2)]), 2)./pevox(p);
                    end
                end

            % -----> compute over srange

            case {'mFzs', 'nFzs', 'pFzs', 'mFcs', 'nFcs', 'pFcs'}

                for s = 1:tvolumes
                    strength_mask = (Fc >= tparameter(s)) & (Fc < tparameter(s+1));
                    pevox = sum(strength_mask, 2);
                    results(fstart:fend,toffset+(s-1)) = rsum(Fc, strength_mask, 2) ./ pevox;
                end


            case {'aFzs', 'aFcs'}

                for s = 1:tvolumes
                    strength_mask = (aFc >= tparameter(s)) & (aFc < tparameter(s+1));
                    pevox = sum(strength_mask, 2);
                    results(fstart:fend,toffset+(s-1)) = rsum(aFc, strength_mask , 2) ./ pevox;
                end

            case {'mDs', 'nDs', 'pDs'}

                for s = 1:tvolumes
                    strength_mask = (Fc >= tparameter(s)) & (Fc < tparameter(s+1));
                    results(fstart:fend,toffset+(s-1)) = sum(strength_mask, 2) ./ evoxels;
                end

            case 'aDs'

                for s = 1:tvolumes
                    strength_mask = (aFc >= tparameter(s)) & (aFc < tparameter(s+1));
                    results(fstart:fend,toffset+(s-1)) = sum(strength_mask, 2) ./ evoxels;
                end

        end

        if time, fprintf(' [%.3f s]\n', toc); end

    end

end

if verbose, fprintf('... done! [%.3f s]\n', toc(stime)), end

obj = obj.zeroframes(nvolumes);
obj.data(tmask,:) = results;
obj.info = command;

end

% ----------  helper functions
%
%   Input
%       - s   : string specifying the types of GBC to be done
%               individual types of GBC are to be pipe delimited, parmeters colon separated
%               format:
%               * GBC type - mFz, aFz, pFz, nFz, mD, aD, pD, nD
%                 ... to each of these either p or s can be added at the end, for
%                     computing results for proportion or strength bands respectively
%               * threshold to be used for the GBC
%                 ... or number of bins for proportion or strength range bands
%
%       - nvox : the number of voxels in the mask (necessary to compute bands for prange)
%
%   Output
%       - out  : vector of structure with fields
%                - command      ... type of GBC to run
%                - parameter    ... threshold or limits to be used
%                - volumes      ... how many volumes the results will span
%
%  Notes:
%       The commands are sorted so that all the Fz commands are at the end. This enables
%       in-place replacement of Fc values by Fz. Also all commands that require absolute
%       values are computed at the end. This enables having memory as free as possible
%       as long as possible.


function [out] = parseCommand(s, nvox)

    a = splitby(s,'|');
    for n = 1:length(a)
        b = splitby(a{n}, ':');

        cmd(n).command_string = a{n};
        com = b{1};
        par = str2num(b{2});
        cmd(n).command = com;

        pre = com(1);
        pos = com(end);

        if ismember(pos, 'ps')
            if pos == 'p'
                sstep = nvox / par;
                cmd(n).parameter = floor([[1:sstep:nvox]', [1:sstep:nvox]'+(sstep-1)]);
            else
                if ismember(pre, 'ap')
                    sv = 0;
                    ev = 1;
                    al = 1;
                elseif pre == 'm'
                    sv = -1;
                    ev = 1;
                    al = 1;
                else
                    sv = -1;
                    ev = 0;
                    al = 0;
                end

                sstep = (ev-sv) / par;
                cmd(n).parameter = [sv:sstep:ev];

                % --- Switching to Fz
                if strfind(com, 'Fz')
                    cmd(n).parameter = fc_fisher(cmd(n).parameter);
                end
                cmd(n).parameter(end) = cmd(n).parameter(end) + al;
            end
            cmd(n).volumes = par;
        else
            if strfind(com, 'Fz')
                cmd(n).parameter = fc_fisher(par);
            else
                cmd(n).parameter = par;
            end
            cmd(n).volumes = 1;
        end
    end

    % --> sort command in optimal order that ensures that all Fz follow all Fc commands, and that
    %     absolute values are used at the end.

    process_order = {'mFc', 'pFc', 'nFc', 'pD', 'nD', 'mFcp', 'nFcp', 'pFcp', 'mFcs', ...
                     'pFcs', 'nFcs', 'mDs', 'pDs', 'nDs', 'aFc', 'aD', 'aFcp', 'aFcs', 'aDs', ...
                     'mFz', 'pFz', 'nFz', 'mFzp', 'mFzs', 'pFzs', 'nFzs', 'aFz', 'aFzp', 'aFzs'};

    [t, i] = ismember(process_order, {cmd.command});
    out = cmd(i(t));

end

function [out] = splitby(s, d)
    c = 0;
    while length(s) >=1
        c = c+1;
        [t, s] = strtok(s, d);
        if length(s) > 1, s = s(2:end); end
        out{c} = t;
    end
end

function [matrix] = rmean(matrix, mask, dim)
    if nargin < 3, dim = 1; end
    % matrix(~mask) = 0;
    matrix = matrix .* mask;
    matrix = sum(matrix, dim) ./ sum(mask, dim);
end

function [matrix] = rsum(matrix, mask, dim)
    if nargin < 3, dim = 1; end
    % matrix(~mask) = 0;
    matrix = matrix .* mask;
    matrix = sum(matrix, dim);
end

function [s] = strjoin(c)
    s = '';
    for n = 1:length(c)
        s = [s c{n}];
    end
end

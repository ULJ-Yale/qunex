function [obj, commands] = img_compute_gbc(obj, command, sroi, troi, options)

%``img_compute_gbc_fc(obj, command, sroi, troi, options)``
%
%   Computes whole brain GBC based on the specified masks and command string.
%
%   Parameters
%       --obj (nimage object):
%           Image with the timeseries to compute the GBC over.
%       --command (str):
%           A pipe separated string describing GBC to compute. The possible 
%           commands and parameters are
%
%            - mFz:t
%                computes mean Fz value across all voxels (over threshold t)
%            - aFz:t
%                computes mean absolute Fz value across all voxels (over 
%                threshold t)
%            - pFz:t
%                computes mean positive Fz value across all voxels (over 
%                threshold t)
%            - nFz:t
%                computes mean positive Fz value across all voxels (below 
%                threshold t)
%            - aD:t
%                computes proportion of voxels with absolute r over t
%            - pD:t
%                computes proportion of voxels with positive r over t
%            - nD:t
%                computes proportion of voxels with negative r below t
%            - mFzp:n
%                computes mean Fz value across n proportional ranges
%            - aFzp:n
%                computes mean absolute Fz value across n proportional ranges
%            - mFzs:n
%                computes mean Fz value across n strength ranges
%            - pFzs:n
%                computes mean Fz value across n strength ranges for positive 
%                correlations
%            - nFzs:n
%                computes mean Fz value across n strength ranges for negative 
%                correlations
%            - aFzs:n
%                computes mean absolute Fz value across n strength ranges
%            - mDs:n
%                computes proportion of voxels within n strength ranges of r
%            - aDs:n
%                computes proportion of voxels within n strength ranges of 
%                absolute r
%            - pDs:n
%                computes proportion of voxels within n strength ranges of 
%                positive r
%            - nDs:n
%                computes proportion of voxels within n strength ranges of 
%                negative r
%
%       --sroi (nimage object):
%           A mask specifying the voxels or greyordinates for which to compute
%           the GBC for.
%       --troi (nimage object):
%           A mask specifying the voxels over which the GBC is to be computed.
%       --options (struct field or string):
%           Either a struct field or a pipe separated string of <key>:<value>
%           pairs specifying additional options.
%
%           It accepts the following keys and values:
%
%           - rmax
%               The r value above which the correlations are considered to be of 
%               the same functional ROI - or false if it should not be used. 
%               [false]
%           - time
%               Whether to print timing information. [false]
%           - step
%               How many voxels or greyordinates to process in a single step 
%               [12000]
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
default = 'rmaks=false|time=false|step=12000|verbose=true|printdebug=false';
options = general_parse_options([], options, default);

verbose = strcmp(options.verbose, 'true');
printdebug = strcmp(options.debug, 'true');

if ischar(options.rmax), options.rmax = false; end
options.time = strcmp(options.time, 'true');

% ---- prepare data

if verbose, fprintf('\n... setting up data'), end

obj.data = obj.image2D;
nvox = size(obj.image2D, 1);

if isempty(troi)
    ntvox = nvox;
else
    ntvox = length(troi);
end

if isempty(sroi)
    nsvox = nvox;
else
    nsvox = length(sroi);
end

% ---- parse command

if verbose, fprintf('\n\nStarting GBC on %s', obj.filename); stime = tic; end
[commands, sortit] = parseCommand(command, nvox);
ncommands = length(commands);
nvolumes  = sum([commands.volumes]);
coffsets  = [1 cumsum([commands.volumes])+1];
coffsets  = coffsets(1:ncommands);

% ---- set up results

results = zeros(nvox, nvolumes);


% ---- do the loop

voxels = obj.voxels;
data   = obj.data;
% vstep = floor(56250/obj.frames);    % optimal matrix size : 5625000
% vstep  = 12000/2;
% vstep  = 100000;
cstep  = vstep;
nsteps = floor(voxels/vstep);
lstep  = mod(voxels,vstep);
rmax   = fc_fisher(rmax);
aFz    = false;

if verbose
    fprintf('\n... %d voxels & %d frames to process in %d steps\n... computing GBC for voxels:', voxels, obj.frames, nsteps+1);
end

x = data';

for n = 1:nsteps+1

    if n > nsteps, cstep=lstep; end
    fstart = vstep*(n-1) + 1;
    fend   = vstep*(n-1) + cstep;
    pevox  = false;

    if verbose
        crange = [num2str(fstart) ':' num2str(fend)];
        % for c = 1:slen, fprintf('\b'), end
        fprintf('\n     ... %14s', crange);
        slen = length(crange);
    end

    if time, fprintf(' r'); tic; end
    r = (data * x(:,fstart:fend));
    if time fprintf(' [%.3f s]', toc); end

    % fprintf('NaN: %d ', sum(sum(isnan(r))));


    % To save space we're switching to Fz and replacing r.
    % From here on, everything needs to be adjusted to work with Fz

    if time, fprintf(' Fz'); tic; end
    if ~cv, r = fc_fisher(r); end
    if ~isreal(r)
        fprintf(' c>r')
        r = real(r);
    end
    if time fprintf(' [%.3f s]', toc); end


    % -------- Compute common stuff ---------

    coms = {commands.command};

    % -- do we need absolute values?

    if strfind(strjoin(coms), 'aFz')
        if time, fprintf(' aFz'); tic; end
        aFz = abs(r);
        if time fprintf(' [%.3f s]', toc); end
    end

    % -- are we sorting?

    if sortit
        if time, fprintf(' sort'); tic; end
        r = sort(r, 1);
        fprintf(' %.3f %.3f', r(1,1), r(end,1));
        % if r(1,1) > -0.001
        %     fprintf(' resort');
        %     r = sort(r);
        %     fprintf(' %.3f %.3f', min(r(1,:)), max(r(end,:)));
        % end

        if strfind(strjoin(coms), 'aFz')
            fprintf('+');
            aFz = sort(aFz, 1);
        end
        if time fprintf(' [%.3f s]', toc); end
    end


    % added to remove within region correlations defined as
    % correlations above a specified rmax threshold if not, it
    % sets the correlation with itself to 0

    if time, fprintf(' clip'); tic; end
    evoxels = voxels;
    if rmax
        clip = r < rmax;
        r = r.*clip;
        evoxels = sum(clip,1);
        clipped = voxels - evoxels;
        if verbose == 3, fprintf(' cliped: %d ', sum(sum(clip))); end;
    else
        if sortit
            r(end,:) = 0;
            if aFz
                aFz(end,:) = 0;
            end
        else
            l = [0:(cstep-1)] * voxels + [fstart:fend];
            r(l) = 0;
        end
        clipped = 1;
        evoxels = voxels-1;
    end
    if time fprintf(' [%.3f s]', toc); end

    % .... let's not transpose to save on time

    % if time, fprintf(' transpose'); tic; end
    % r = r';
    % if time fprintf(' [%.3f s]', toc); end


    % -------- Run the command loop ---------

    for c = 1:ncommands
        tcommand   = commands(c).command;
        tparameter = commands(c).parameter;
        tvolumes   = commands(c).volumes;
        toffset    = coffsets(c);

        if time, fprintf(' %s', tcommand); tic; end

        switch tcommand

            % -----> compute mFz

            case 'mFz'
                results(fstart:fend,toffset) = sum(r,1)./evoxels;

            % -----> compute aFz

            case 'aFz'
                if tparameter == 0
                    results(fstart:fend,toffset) = sum(aFz,1)./evoxels;
                else
                    results(fstart:fend,toffset) = rmean(aFz, (aFz > tparameter), 1);
                end

            % -----> compute pFz

            case 'pFz'
                results(fstart:fend,toffset) = rmean(r, r >= tparameter, 1);


            % -----> compute pFz

            case 'nFz'
                results(fstart:fend,toffset) = rmean(r, r <= tparameter, 1);

            % -----> compute pD

            case 'pD'
                results(fstart:fend,toffset) = sum(r >= tparameter, 1)./evoxels;


            % -----> compute nD

            case 'nD'
                results(fstart:fend,toffset) = sum(r <= tparameter, 1)./evoxels;

            % -----> compute aD

            case 'aD'
                results(fstart:fend,toffset) = sum(aFz >= tparameter, 1)./evoxels;


            % -----> compute over prange

            case {'mFzp', 'aFzp'}

                if ~pevox
                    pevox = tparameter(:,2) - tparameter(:,1) + 1;
                    if rmax
                        pevox = repmat(pevox, 1, cstep);
                        pevox(tvolumes,:) = pevox(tvolumes,:) - clipped;  % we're assuming all clipped voxels are in the top group
                    else
                        pevox(tvolumes) = pevox(tvolumes) - clipped;  % we're assuming all clipped voxels are in the top group
                    end
                end


                for p = 1:tvolumes
                    if strcmp(tcommand, 'mFzp')
                        results(fstart:fend,toffset+(p-1)) = sum(r([tparameter(p,1):tparameter(p,2)],:),1)./pevox(p);
                    else
                        results(fstart:fend,toffset+(p-1)) = sum(aFz([tparameter(p,1):tparameter(p,2)],:),1)./pevox(p);
                    end
                end

            % -----> compute over srange

            case {'mFzs', 'nFzs', 'pFzs'}

                for s = 1:tvolumes
                    smask = (r >= tparameter(s)) & (r < tparameter(s+1));
                    pevox = sum(smask, 1);
                    results(fstart:fend,toffset+(s-1)) = rsum(r, smask, 1)./pevox;
                end


            case 'aFzs'

                for s = 1:tvolumes
                    smask = (aFz >= tparameter(s)) & (aFz < tparameter(s+1));
                    pevox = sum(smask, 1);
                    results(fstart:fend,toffset+(s-1)) = rsum(aFz, smask , 1)./pevox;
                end

            case {'mDs', 'nDs', 'pDs'}

                for s = 1:tvolumes
                    smask = (r >= tparameter(s)) & (r < tparameter(s+1));
                    results(fstart:fend,toffset+(s-1)) = sum(smask, 1)./evoxels;
                end

            case 'aDs'

                for s = 1:tvolumes
                    smask = (aFz >= tparameter(s)) & (aFz < tparameter(s+1));
                    results(fstart:fend,toffset+(s-1)) = sum(smask, 1)./evoxels;
                end

        end

        if time fprintf(' [%.3f s]', toc); end

    end

end

if verbose, fprintf('\n... done! [%.3f s]', toc(stime)), end

obj.data = results;
obj.info = command;
obj.frames = nvolumes;

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


function [out, sortit] = parseCommand(s, nvox)

    sortit = false;
    a = splitby(s,'|');
    for n = 1:length(a)
        b = splitby(a{n}, ':');

        com = b{1};
        par = str2num(b{2});
        out(n).command = com;

        pre = com(1);
        pos = com(end);

        if ismember(pos, 'ps')
            if pos == 'p'
                sstep = nvox / par;
                out(n).parameter = floor([[1:sstep:nvox]', [1:sstep:nvox]'+(sstep-1)]);
                sortit = true;
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
                out(n).parameter = [sv:sstep:ev];

                % --- Switching to Fz
                out(n).parameter = fc_fisher(out(n).parameter);
                out(n).parameter(end) = out(n).parameter(end) + al;
            end
            out(n).volumes = par;
        else
            out(n).parameter = fc_fisher(par);
            out(n).volumes = 1;
        end
    end
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
    matrix(~mask) = 0;
    matrix = sum(matrix, dim) ./ sum(mask, dim);
end

function [matrix] = rsum(matrix, mask, dim)
    if nargin < 3, dim = 1; end
    matrix(~mask) = 0;
    matrix = sum(matrix, dim);
end

function [s] = strjoin(c)
    s = '';
    for n = 1:length(c)
        s = [s c{n}];
    end
end

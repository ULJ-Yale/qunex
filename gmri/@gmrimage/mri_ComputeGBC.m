function [obj, commands] = mri_ComputeGBC(obj, command, fmask, mask, verbose, rmax, time)

%function [obj, commands] = mri_ComputeGBC(obj, command, fmask, mask, verbose, rmax, time)
%
%	Computes whole brain GBC based on specified mask and command string
%
%   Input
%	    obj     - image
%       command - string describing GBC to compute (pipe separated)
%                   > mFz:t  ... computes mean Fz value across all voxels (over threshold t)
%                   > aFz:t  ... computes mean absolute Fz value across all voxels (over threshold t)
%                   > pFz:t  ... computes mean positive Fz value across all voxels (over threshold t)
%                   > nFz:t  ... computes mean positive Fz value across all voxels (below threshold t)
%                   > aD:t   ... computes proportion of voxels with absolute r over t
%                   > pD:t   ... computes proportion of voxels with positive r over t
%                   > nD:t   ... computes proportion of voxels with negative r below t
%                   > mFzp:n ... computes mean Fz value across n proportional ranges
%                   > aFzp:n ... computes mean absolute Fz value across n proportional ranges
%                   > mFzs:n ... computes mean Fz value across n strength ranges
%                   > pFzs:n ... computes mean Fz value across n strength ranges for positive correlations
%                   > nFzs:n ... computes mean Fz value across n strength ranges for negative correlations
%                   > aFzs:n ... computes mean absolute Fz value across n strength ranges
%                   > mDs:n  ... computes proportion of voxels within n strength ranges of r
%                   > aDs:n  ... computes proportion of voxels within n strength ranges of absolute r
%                   > pDs:n  ... computes proportion of voxels within n strength ranges of positive r
%                   > nDs:n  ... computes proportion of voxels within n strength ranges of negative r
%
%       fmask   - frame mask to use (passed to sliceframes)
%       mask    - mask to use to define what voxels to include in GBC
%       verbose - should it talk a lot [no]
%       rmax    - the r value above which the correlations are considered to be of the same functional ROI
%       time    - whether to print timing information
%
%   Grega Repovš, 2009-11-08 - Original version
%   Grega Repovš, 2010-10-13 - Version with multiple voxels at a time
%   Grega Repovš, 2013-01-22 - A version that computes strength and proportion ranges not yet fully optimized
%

if nargin < 7, time = [];       end
if nargin < 6, rmax = [];       end
if nargin < 5, verbose = false; end
if nargin < 4, mask = [];       end
if nargin < 3, fmask = [];      end
if nargin < 2, error('ERROR: No command given to compute GBC!'); end


if ~isempty(fmask)
    obj = obj.sliceframes(fmask);
end
if isempty(rmax), rmax = false; end
if isempty(time), time = false; end


% ---- prepare data

if verbose, fprintf('\n... setting up data'), end

if ~obj.masked
    if ~isempty(mask)
        obj = obj.maskimg(mask);
    end
end

if ~obj.correlized
    obj = obj.correlize;
end

obj.data = obj.image2D;
nvox = size(obj.image2D, 1);


% ---- parse command

if verbose, fprintf('\n\nStarting GBC on %s', obj.filename); stime = tic; end
[commands, sortit] = parseCommand(command, nvox)
ncommands = length(commands);
nvolumes  = sum([commands.volumes]);
coffsets  = [1 cumsum([commands.volumes])+1];
coffsets  = coffsets(1:ncommands);


% ---- set up results

results = zeros(nvox, nvolumes);


% ---- do the loop

voxels = obj.voxels;
data   = obj.data;
%vstep = floor(56250/obj.frames);    % optimal matrix size : 5625000
vstep  = 12000/2;
cstep  = vstep;
nsteps = floor(voxels/vstep);
lstep  = mod(voxels,vstep);
Fz     = false;
aFz    = false;

if verbose
    fprintf('\n... %d voxels & %d frames to process in %d steps\n... computing GBC for voxels:', voxels, obj.frames, nsteps+1);
end

x = data';

for n = 1:nsteps+1

    if n > nsteps, cstep=lstep; end
    fstart = vstep*(n-1) + 1;
    fend   = vstep*(n-1) + cstep;

    if verbose
        crange = [num2str(fstart) ':' num2str(fend)];
        % for c = 1:slen, fprintf('\b'), end
	    fprintf('\n     ... %s', crange);
	    slen = length(crange);
    end

    if time, fprintf(' r'); tic; end
    r = (data * x(:,fstart:fend));
    if time fprintf(' [%.3f s]', toc); end

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
        l = [0:(cstep-1)] * voxels + [fstart:fend];
        r(l) = 0;
        clipped = 1;
        evoxels = voxels-1;
    end
    if time fprintf(' [%.3f s]', toc); end

    if sortit
        if time, fprintf(' sort'); tic; end
        r = sort(r);
        if time fprintf(' [%.3f s]', toc); end
    end

    if time, fprintf(' transpose'); tic; end
    r = r';
    if time fprintf(' [%.3f s]', toc); end

    % To save space we're switching to Fz and replacing r.
    % From here on, everything needs to be adjusted to work with Fz

    if time, fprintf(' Fz'); tic; end
    r = fc_Fisher(r);
    if time fprintf(' [%.3f s]', toc); end


    % -------- Compute common stuff ---------

    coms = {commands.command};

    % -- aFz

    if strfind(strjoin(coms), 'aFz')
        if time, fprintf(' aFz'); tic; end
        aFz = abs(r);
        if sortit
            aFz = sort(aFz, 2);
        end
        if time fprintf(' [%.3f s]', toc); end
    end


    % -------- Run the command loop ---------

    for c = 1:ncommands
        tcommand   = commands(c).command;
        tparameter = commands(c).parameter;
        tvolumes   = commands(c).volumes;
        toffset    = coffsets(c);

        if time, fprintf(' %s', tcommand); tic; end

        switch tcommand

            % !!! Missing thresholding

            % -----> compute mFz

            case 'mFz'
                results(fstart:fend,toffset) = sum(r,2)./evoxels;


            % -----> compute aFz

            case 'aFz'
                if tparameter == 0
                    results(fstart:fend,toffset) = sum(aFz,2)./evoxels;
                else
                    results(fstart:fend,toffset) = rmean(aFz, (aFz > tparameter),2);
                end

            % -----> compute pFz

            case 'pFz'
                results(fstart:fend,toffset) = rmean(r, r >= tparameter, 2);


            % -----> compute pFz

            case 'nFz'
                results(fstart:fend,toffset) = rmean(r, r <= tparameter, 2);

            % -----> compute pD

            case 'pD'
                results(fstart:fend,toffset) = sum(r >= tparameter, 2)./evoxels;


            % -----> compute nD

            case 'nD'
                results(fstart:fend,toffset) = sum(r <= tparameter, 2)./evoxels;

            % -----> compute aD

            case 'aD'
                results(fstart:fend,toffset) = sum(aFz >= tparameter, 2)./evoxels;


            % -----> compute over prange

            case 'mFzp'

                pevox = tparameter(:,2) - tparameter(:,1) + 1;
                pevox(tvolumes) = pevox(tvolumes) - clipped;  % we're assuming all clipped voxels are in the top group
                for p = 1:tvolumes
                    results(fstart:fend,toffset+(p-1)) = sum(r(:,[tparameter(p,1):tparameter(p,2)]),2)./pevox(p);
                end


            case 'aFzp'

                pevox = tparameter(:,2) - tparameter(:,1) + 1;
                pevox(tvolumes) = pevox(tvolumes) - clipped;  % we're assuming all clipped voxels are in the top group
                for p = 1:tvolumes
                    results(fstart:fend,toffset+(p-1)) = sum(aFz(:,[tparameter(p,1):tparameter(p,2)]),2)./pevox(p);
                end

            % -----> compute over srange

            case {'mFzs', 'nFzs', 'pFzs'}

                for s = 1:tvolumes
                    smask = (r >= tparameter(s)) & (r < tparameter(s+1));
                    pevox = sum(smask, 2);
                    results(fstart:fend,toffset+(s-1)) = rsum(r, smask,2)./pevox;
                end


            case 'aFzs'

                for s = 1:tvolumes
                    smask = (aFz >= tparameter(s)) & (aFz < tparameter(s+1));
                    pevox = sum(smask, 2);
                    results(fstart:fend,toffset+(s-1)) = rsum(aFz, smask ,2)./pevox;
                end

            case {'mDs', 'nDs', 'pDs'}

                for s = 1:tvolumes
                    smask = (r >= tparameter(s)) & (r < tparameter(s+1));
                    results(fstart:fend,toffset+(s-1)) = sum(smask, 2)./evoxels;
                end

            case 'aDs'

                for s = 1:tvolumes
                    smask = (aFz >= tparameter(s)) & (aFz < tparameter(s+1));
                    results(fstart:fend,toffset+(s-1)) = sum(smask, 2)./evoxels;
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
%       - out  : vector of structure with fieldsČ
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
                out(n).parameter = fc_Fisher(out(n).parameter);
                out(n).parameter(end) = out(n).parameter(end) + al;
            end
            out(n).volumes = par;
        else
            out(n).parameter = fc_Fisher(par);
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
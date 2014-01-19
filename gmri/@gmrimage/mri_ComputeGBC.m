function [obj, commands] = mri_ComputeGBC(obj, command, fmask, mask, verbose, rmax, time)

%function [obj, commands] = mri_ComputeGBC(obj, command, fmask, mask, verbose, rmax, time)
%
%	Computes whole brain GBC based on specified mask and command string
%
%   Input
%	    obj     - image
%       command - string describing GBC to compute
%                   > mFz:t  ... computes mean Fz value across all voxels (over threshold t)
%                   > aFz:t  ... computes mean absolute Fz value across all voxels (over threshold t)
%                   > pFz:t  ... computes mean positive Fz value across all voxels (over threshold t)
%                   > nFz:t  ... computes mean positive Fz value across all voxels (over threshold t)
%                   > aD:t   ... computes number of voxels with absolute r over t
%                   > pD:t   ... computes number of voxels with positive r over t
%                   > nD:t   ... computes number of voxels with negative r over t
%
%       fmask   - frame mask to use (passed to sliceframes)
%       mask    - mask to use to define what voxels to include in GBC
%       verbose - should it talk a lot [no]
%       rmax    -
%
%   Grega Repovš, 2009-11-08 - Original version
%   Grega Repovš, 2010-10-13 - Version with multiple voxels at a time
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

if verbose, fprintf('\n\nStarting GBC on %s', obj.filename), tic, end
commands, sortit  = parseCommand(command, nvox);
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
vstep  = 12000;
cstep  = vstep;
nsteps = floor(voxels/vstep);
lstep  = mod(voxels,vstep);

if verbose
    crange = ['1:' num2str(vstep)];
    fprintf('\n... %d voxels & %d frames to process in %d steps\n... computing GBC for voxels: %s', voxels, obj.frames, nsteps+1, crange);
    slen = length(crange);
end

x = data';

for n = 1:nsteps+1

    if n > nsteps, cstep=lstep; end
    fstart = vstep*(n-1) + 1;
    fend   = vstep*(n-1) + cstep;

    if verbose
        crange = [num2str(fstart) ':' num2str(fend)];
        for c = 1:slen, fprintf('\b'), end
	    fprintf('%s', crange);
	    slen = length(crange);
    end

    r = (data * x(:,fstart:fend))';
    if sortit
        r = sort(r, 2);
    end

    % added to remove within region correlations defined as
    % correlations above a specified rmax threshold

    evoxels = voxels;
    if rmax
        clip = r < rmax;
        r = r.*clip;
        evoxels = sum(clip,2);
        clipped = voxels - evoxels;
        if verbose == 3, fprintf(' cliped: %d ', sum(sum(clip))); end;
    end

    % removes correlations of voxels with themselves
    % - code would be expensive on memory and possibly time
    % - we're adjusting the results in computations below instead
    %
    % self = [0:cstep-1]*voxels + [fstart:fend];
    % r = reshape(r(~ismember(1:voxels*cstep,self)),voxels-1,cstep)';

    doFz = true;
    mFz  = [];
    aFz  = [];

    for c = 1:ncommands
        tcommand   = commands(c).command;
        tparameter = commands(c).parameter;
        scommand   = commands(c).subset;
        tvolumes   = commands(c).volumes;
        slimits    = commands(c).limits;
        toffset    = coffsets(c);

        if time, fprintf(' %s', tcommand); tic; end

        switch tcommand

            % -----> compute mFz

            case 'mFz'
            	if doFz, Fz = fc_Fisher(r); doFz = false; end

                % --- no subrange

            	if isempty(scommand)
                    if isempty(mFz)
                        if rmax
                            mFz = sum(Fz,2)./evoxels;
                        else
                            mFz = (sum(Fz,2)-fc_Fisher(1))./(evoxels-1);
                        end
                    end
                    results(fstart:fend,toffset) = mFz;

                % --- prange

                elseif strcmp(scommand, 'prange')
                    pevox = slimits(:,2) - slimits(:,1) + 1;
                    if rmax, pevox(tvolumes) = pevox(tvolumes) - clipped; end  % we're assuming all clipped voxels are in the top group
                    for p = 1:tvolumes
                        if ~rmax && p = tvolumes
                            results(fstart:fend,toffset+(p-1)) = (sum(Fz(slimits(p,1):slimits(p,2),:),2)-fc_Fisher(1))./(pevox(p)-1);
                        else
                            results(fstart:fend,toffset+(p-1)) = sum(Fz(slimits(p,1):slimits(p,2),:),2)./pevox(p);
                        end
                    end

                % --- srange

                elseif strcmp(scommand, 'srange')
                    for s = 1:tvolumes
                        smask = Fz >= slimits(s) && Fz < slimits(s+1);
                        pevox = sum(smask, 2);
                        if rmax && 0 >= slimits(s) && 0 < slimits(s+1); pevox = pevox - clipped; end
                        if ~rmax && p = tvolumes
                            results(fstart:fend,toffset+(s-1)) = (sum(Fz(smask),2)-fc_Fisher(1))./(pevox-1);
                        else
                            results(fstart:fend,toffset+(s-1)) = sum(Fz(smask),2)./pevox;
                        end
                    end
                end


            % -----> compute aFz

            case 'aFz'
            	if doFz, Fz = fc_Fisher(r); doFz = false; end
            	if time, fprintf(' aFz'); tic; end

                % --- no subrange

                if isempty(scommand)
                    if isempty(aFz)
                        if rmax
                            aFz = sum(abs(Fz),2)./evoxels;
                        else
                            aFz = (sum(abs(Fz),2)-fc_Fisher(1))./(evoxels-1);
                        end
                    end
                    results(fstart:fend,c) = aFz;

                % --- prange

                elseif strcmp(scommand, 'prange')
                    pevox = slimits(:,2) - slimits(:,1) + 1;
                    if rmax, pevox(tvolumes) = pevox(tvolumes) - clipped; end  % we're assuming all clipped voxels are in the top group
                    for p = 1:tvolumes
                        if ~rmax && p = tvolumes
                            results(fstart:fend,toffset+(p-1)) = (sum(abs(Fz(slimits(p,1):slimits(p,2),:),2)-fc_Fisher(1)))./(pevox(p)-1);
                        else
                            results(fstart:fend,toffset+(p-1)) = sum(abs(Fz(slimits(p,1):slimits(p,2),:),2))./pevox(p);
                        end
                    end

                % --- srange

                elseif strcmp(scommand, 'srange')
                    taFz = abs(Fz);
                    for s = 1:tvolumes
                        smask = taFz >= slimits(s) && taFz < slimits(s+1);
                        pevox = sum(smask, 2);
                        if rmax && 0 >= slimits(s) && 0 < slimits(s+1); pevox = pevox - clipped; end
                        if ~rmax && p = tvolumes
                            results(fstart:fend,toffset+(s-1)) = (sum(taFz(smask),2)-fc_Fisher(1))./(pevox-1);
                        else
                            results(fstart:fend,toffset+(s-1)) = sum(taFz(smask),2)./pevox;
                        end
                    end
                end


                if time fprintf(' [%.3f s]', toc);


            % -----> compute pFz

            case 'pFz'
            	if doFz, Fz = fc_Fisher(r); doFz = false; end
            	if isempty(mFz)
            	    if rmax
            	        mFz = sum(Fz,2)./evoxels;
            	    else
            	        mFz = (sum(Fz,2)-fc_Fisher(1))./(evoxels-1);
            	    end
        	    end
            	if isempty(aFz)
            	    if rmax
            	        aFz = sum(abs(Fz),2)./evoxels;
            	    else
            	        aFz = (sum(abs(Fz),2)-fc_Fisher(1))./(evoxels-1);
            	    end
        	    end
            	rp = mean(Fz>0,2);
            	results(fstart:fend,c) = (mFz+aFz)./(rp.*2);


            % -----> compute nFz

            case 'nFz'
            	if doFz, Fz = fc_Fisher(r); doFz = false; end
            	if isempty(mFz)
            	    if rmax
            	        mFz = sum(Fz,2)./evoxels;
            	    else
            	        mFz = (sum(Fz,2)-fc_Fisher(1))./(evoxels-1);
            	    end
        	    end
            	if isempty(aFz)
            	    if rmax
            	        aFz = sum(abs(Fz),2)./evoxels;
            	    else
            	        aFz = (sum(abs(Fz),2)-fc_Fisher(1))./(evoxels-1);
            	    end
        	    end
            	rn = mean(Fz<0,2);
            	results(fstart:fend,c) = (mFz-aFz)./(rn.*2);


            % -----> compute pD

            case 'pD'
            	if rmax
            	    results(fstart:fend,c) = sum(r >= tparameter, 2)./voxels;
            	else
                    results(fstart:fend,c) = (sum(r >= tparameter, 2)-1)./voxels;
                end


            % -----> compute nD

            case 'nD'
                results(fstart:fend,c) = sum(r <= -tparameter, 2)./voxels;


            % -----> compute aD

            case 'aD'
            	if rmax
            	    results(fstart:fend,c) = sum(abs(r) >= tparameter, 2)./voxels;
            	else
                    results(fstart:fend,c) = (sum(abs(r) >= tparameter, 2)-1)./voxels;
                end
        end

        if time, fprintf(' [%.3f s]', toc); end

    end
end

if verbose, fprintf('\n... done! [%.3f s]', toc), end

obj.data = results;
obj.info = command;
obj.frames = ncommands;

end

% ----------  helper functions
%
%   Input
%       - s   : string specifying the types of GBC to be done
%               individual types of GBC are to be pipe delimited, parmeters colon separated
%               format:
%               * GBC type - mFz, aFz, pFz, nFz, aD, pD, nD
%               * threshold to be used for the GBC
%               * optional string specifying the way to specify the "bands" for subsampling of the target space
%                 - srange : the bands are defined based on the actual strength of correlation values
%                 - prange : the bands are specified by the proportion of voxels sorted from -1 to 1
%               * optional number of bands to use (default is 10)
%       - nvox : the number of voxels in the mask (necessary to compute bands for prange)
%
%   Output
%       - out  : vector of structure with fieldsČ
%                - command      ... type of GBC to run
%                - parameter    ... threshold
%                - subset       ... what type of subset to use (or [])
%                - volumes      ... how many volumes the results wil span
%                - limits       ... what are the limits for prange/srange to use


function [out, sortit] = parseCommand(s, nvox)

    sortit = false;
    a = splitby(s,'|');
    for n = 1:length(a)
        b = splitby(a{n}, ':');
        out(n).command = b{1};
        out(n).parameter = str2num(b{2});
        if length(b) > 2
            out(n).subset  = b{3};
            if length(b) == 3
                out(n).volumes = 10;
            else
                out(n).volumes = str2num(b{4});
            end

            if strcmp(b{3}, 'srange')
                sstep = 2 / out(n).volumes;
                out(n).limits = [-1:sstep:1];
                out(n).limits = out(n).limits + 0.1;
            elseif strcmp(b{3}, 'prange')
                sstep = nvox / out(n).volumes;
                out(n).limits = floor([[1:sstep:nvox]', [1:sstep:nvox]'+(sstep-1)]);
                sortit = true;
            else
                error('\nERROR: unknown subset %s in mri_ComputeGBC [%s]!\n\n', b{3}, s);
            end

        else
            out(n).subset  = [];
            out(n).volumes = 1;
            out(n).limits  = [];
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

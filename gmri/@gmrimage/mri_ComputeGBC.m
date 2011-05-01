function [obj, commands] = mri_ComputeGBC(obj, command, fmask, mask, verbose, rmax)

%	
%	Computes whole brain GBC based on specified mask and command string
%	
%	obj     - image
%   mask    - mask to use
%   command - string describing GBC to compute
%   verbose - should it talk a lot [no]
%
%   Grega Repovš, 2009-11-08 - Original version
%   Grega Repovš, 2010-10-13 - Version with multiple voxels at a time
%
if nargin < 6
    rmax = false;
    if nargin < 5
        verbose = false;
        if nargin < 4;
            mask = [];
            if nargin < 3
                fmask = [];
                if nargin < 2
                    error('ERROR: No command given to compute GBC!')
                end
            end
        end
    end
end

if ~isempty(fmask)
    obj = obj.sliceframes(fmask);
end

% ---- parse command

if verbose, fprintf('\n\nStarting GBC on %s', obj.filename), tic, end
commands  = parseCommand(command);
ncommands = length(commands);

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

results = zeros(obj.voxels, ncommands);
obj.data = obj.image2D;


% ---- do the loop

voxels = obj.voxels;
data   = obj.data;
%vstep  = floor(56250/obj.frames);    % optimal matrix size : 5625000
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
    
    % added to remove within region correlations defined as
    % correlations above a specified rmax threshold
    
    evoxels = voxels;
    if rmax
        clip = r >= rmax;
        r(clip) = 0;
        evoxels = evoxels - sum(clip,2);
        if verbose == 3, fprintf(' cliped: %d ', sum(sum(clip))); end;
    end
    
    % removes correlations of voxels with themselves
    % - code would be expensive on memory and possibly time
    % - we're adjusting the results in computations below instead
    %
    % self = [0:cstep-1]*voxels + [fstart:fend];
    % r = reshape(r(~ismember(1:voxels*cstep,self)),voxels-1,cstep)'; 
    
    doFz = true;
    mFz = [];
    aFz = [];

    for c = 1:ncommands
        tcommand   = commands(c).command;
        tparameter = commands(c).parameter;
        
        switch tcommand
        
            case 'mFz'
            	if doFz, Fz = fc_Fisher(r); doFz = false; end
            	% fprintf(' mFz');
            	% tic;
            	if isempty(mFz)
            	    if rmax
            	        mFz = sum(Fz,2)./evoxels;
            	    else
            	        mFz = (sum(Fz,2)-fc_Fisher(1))./(evoxels-1); 
            	    end
        	    end
                results(fstart:fend,c) = mFz;
                % fprintf(' [%.3f s]', toc);
            
            case 'aFz'
            	if doFz, Fz = fc_Fisher(r); doFz = false; end
            	% fprintf(' aFz');
            	% tic;
            	if isempty(aFz)
            	    if rmax
            	        aFz = sum(abs(Fz),2)./evoxels; 
            	    else
            	        aFz = (sum(abs(Fz),2)-fc_Fisher(1))./(evoxels-1); 
            	    end
        	    end
                results(fstart:fend,c) = aFz;
                % fprintf(' [%.3f s]', toc);
            
            case 'pFz'
            	if doFz, Fz = fc_Fisher(r); doFz = false; end
            	% fprintf(' pFz');
            	% tic;
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
                % results(fstart:fend,c) = sum(Fz.*(Fz > 0),2)./sum(Fz > 0,2); % mean(Fz(Fz>0), 2);
                % fprintf(' [%.3f s]', toc);
                
            case 'nFz'
            	if doFz, Fz = fc_Fisher(r); doFz = false; end
            	% fprintf(' nFz');
            	% tic;
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
                % results(fstart:fend,c) = sum(Fz.*(Fz < 0),2)./sum(Fz < 0,2);; % mean(Fz(Fz<0), 2);
                % fprintf(' [%.3f s]', toc);
                
            case 'pD'
            	% fprintf(' pD %.2f', tparameter);
            	% tic;
            	if rmax
            	    results(fstart:fend,c) = sum(r >= tparameter, 2)./voxels;
            	else
                    results(fstart:fend,c) = (sum(r >= tparameter, 2)-1)./voxels;
                end
                % fprintf(' [%.3f s]', toc);

            case 'nD'
            	% fprintf(' nD');
            	% tic;
                results(fstart:fend,c) = sum(r <= -tparameter, 2)./voxels;
                % fprintf(' [%.3f s]', toc);
                
            case 'aD'
            	% fprintf(' aD');
            	% tic;
            	if rmax
            	    results(fstart:fend,c) = sum(abs(r) >= tparameter, 2)./voxels;
            	else
                    results(fstart:fend,c) = (sum(abs(r) >= tparameter, 2)-1)./voxels;
                end
                % fprintf(' [%.3f s]', toc);
        end
    
    end
end

if verbose, fprintf('\n... done! [%.3f s]', toc), end

obj.data = results;
obj.info = command;
obj.frames = ncommands;

end
     
% ----------  helper functions

function [out] = parseCommand(s)
    a = splitby(s,'|');
    for n = 1:length(a)
        b = splitby(a{n}, ':');
        out(n).command = b{1};
        out(n).parameter = str2num(b{2});
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

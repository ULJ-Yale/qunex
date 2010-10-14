function [obj, commands] = mri_ComputeGBCp(obj, command, fmask, mask, verbose)

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

if ~isempty(fmask)
    obj = obj.sliceframes(fmask);
end

% ---- parse command

if verbose, fprintf('\n\nStarting GBC on %s', obj.filename), end
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
vstep  = 25500;
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
    
    r = data * x(:,fstart:fend);
    doFz = true;

    for c = 1:ncommands
        tcommand   = commands(c).command;
        tparameter = commands(c).parameter;
        
        switch tcommand
        
            case 'mFz'
            	if doFz, Fz = fc_Fisher(r); doFz = false; end
                results(fstart:fend,c) = mean(Fz, 1)';
            
            case 'aFz'
            	if doFz, Fz = fc_Fisher(r); doFz = false; end
                results(fstart:fend,c) = mean(abs(Fz), 1)';
            
            case 'pFz'
            	if doFz, Fz = fc_Fisher(r); doFz = false; end
                results(fstart:fend,c) = mean(Fz(Fz>0), 1)';
                
            case 'nFz'
            	if doFz, Fz = fc_Fisher(r); doFz = false; end
                results(fstart:fend,c) = mean(Fz(Fz<0), 1)';
                
            case 'pD'
                results(fstart:fend,c) = sum(r >= tparameter, 1)'./voxels;

            case 'nD'
                results(fstart:fend,c) = sum(r <= -tparameter, 1)'./voxels;
                
            case 'aD'
                results(fstart:fend,c) = sum(abs(r) > tparameter, 1)'./voxels;
        end
    
    end
end

if verbose, fprintf('\n... done!'), end

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

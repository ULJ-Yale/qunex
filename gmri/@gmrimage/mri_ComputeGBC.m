function [obj, commands] = mri_ComputeGBC(obj, command, fmask, mask, verbose)

%	
%	Computes whole brain GBC based on specified mask and command string
%	
%	obj     - image
%   mask    - mask to use
%   command - string describing GBC to compute
%   verbose - should it talk a lot [no]
%
%   Grega Repovš, 2009-11-08
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
commands = parseCommand(command);
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
data = obj.data;

if verbose, fprintf('\n... %d voxels & %d frames to process\n... computing GBC for voxel:        1', voxels, obj.frames), end

for n = 1:voxels

    if mod(n,20) == 0
	    fprintf('\b\b\b\b\b\b\b\b%8d', n);
    end
    
    x = data(n,:)';
    r = data * x;
    Fz = fc_Fisher(r);

    for c = 1:ncommands
        tcommand   = commands(c).command;
        tparameter = commands(c).parameter;
        
        switch tcommand
        
            case 'mFz'
                results(n,c) = mean(Fz);
            
            case 'aFz'
                results(n,c) = mean(abs(Fz));
            
            case 'pFz'
                results(n,c) = mean(Fz(Fz>0));
                
            case 'nFz'
                results(n,c) = mean(Fz(Fz<0));
                
            case 'pD'
                results(n,c) = sum(r >= tparameter)/voxels;

            case 'nD'
                results(n,c) = sum(r <= -tparameter)/voxels;
                
            case 'aD'
                results(n,c) = sum(abs(r) > tparameter)/voxels;
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

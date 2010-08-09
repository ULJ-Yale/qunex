function [obj] = mri_ComputeABCor(obj, smask, tmask, verbose)

%function [obj] = mri_ComputeABCor(obj, smask, tmask, verbose)
%	
%	Compute correlation between each source and target voxels and returns a correlational image.
%	
%	obj     - bold data
%   smask   - mask of source voxels
%   tamsk   - mask of target voxels (that will form an image)
%   verbose - should it talk a lot [no]
%
%   Grega Repovš, 2010-08-08
%

if nargin < 4
    verbose = false;
    if nargin < 3;
        error('ERROR: Both mask for source and target voxels needs to be provided!');
    end
end


% ---- prepare data

if verbose, fprintf('\n... setting up data'), end

jmask = smask + tmask;

if ~obj.correlized    
    if ~obj.masked
        obj = obj.maskimg(jmask);
    end
    obj = obj.correlize;
end

obj = obj.demaskimg(jmask);
src = obj.maskimg(smask);
obj = obj.maskimg(tmask);

% ---- do the deed

if verbose, fprintf('\n... setting up data'), end

obj.data = obj.image2D*src.image2D';
obj.frames = src.voxels;


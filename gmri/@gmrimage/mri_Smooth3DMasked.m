function img = mri_Smooth3DMasked(img, mask, fwhm, mlimit, verbose)

%	function img = mri_Smooth3DMasked(img, mask, fwhm, mlimit, verbose)
%	
%	Function for smoothing that takes into account only the voxels
%	within a specified mask.
%
%   Input:
%       mask    - the mask to use for limiting smoothing
%       fwhm    - size of smoothing in voxels
%       mlimit  - whether to limit the output to mask
%       verbose - to be talkative or not
%	
%	Grega Repovs 2010-11-16
%   Modified by Grega Rrepovs 2010-12-01

% ---------  basic settings

rmasked = false;
zeroed  = false;

if nargin < 5
    verbose = false;
    if nargin < 4
        mlimit = true;
        if nargin < 3
            fhwm = []
            if nargin < 2 
                if img.masked
                    mask = img.mask;
                    img = img.unmaskimg();
                    rmasked = true;
                    zeroed  = true;
                else 
                    error('ERROR: No mask was provided as input to mri_Smooth3DMasked!');
                end
            end
        end
    end
end


% -------- zero voxels outside mask

if ~zeroed
    img = zerononmask(img, mask);
end


% -------- do the smoothing

if verbose, fprintf('... running masked smoothing '); end

img = img.mri_Smooth3D(fwhm, verbose);
smask = mask.mri_Smooth3D(fwhm, verbose);


% -------- adjust for mask (or not)

if mlimit
    if verbose, fprintf('... cutting to mask '); end
    img = zerononmask(img, mask);
    [smask mask] = zerononmask(smask, mask);
    smask = repmat(smask.data(mask.data,1), 1, img.frames);
    img.data(mask.data,:) = img.data(mask.data,:) ./ smask;
else
    if verbose, fprintf('... normalizing to mask '); end
    img.data = img.image2D;
    smask = repmat(smask.image2D, 1, img.frames);
    img.data = img.data ./ smask;
end

if rmasked
    img = img.maskimg(mask);
end

end

function [img mask] = zerononmask(img, mask)

    mask.data = mask.data ~= 0;
    mask.data = mask.image2D;
    img.data  = img.image2D;
    img.data(~mask.data,:) = 0;

end


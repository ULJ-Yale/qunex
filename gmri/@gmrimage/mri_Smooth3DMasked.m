function img = mri_Smooth3DMasked(img, mask, fwhm, verbose)

%	function img = mri_Smooth3DMasked(img, mask, fwhm, verbose)
%	
%	Function for smoothing that takes into account only the voxels
%	within a specified mask.
%	
%	
%	Grega Repovs 2010-11-16

% ---------  basic settings

rmasked = false;
zeroed  = false;

if nargin < 4
    verbose = false;
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


% -------- zero voxels outside mask

if ~zeroed
    img = zerononmask(img, mask);
end


% -------- do the smoothing

img = img.mri_Smooth3D(fwhm, verbose);
smask = mask.mri_Smooth3D(fwhm, verbose);


% -------- adust for mask

img = zerononmask(img, mask);
smask = zerononmask(smask, mask);
smask = repmat(smask.data(mask.data,1), 1, img.frames);
img.data(mask.data,:) = img.data(mask.data,:) ./ smask;

if rmasked
    img = img.maskimg(mask);
end

end

function img = zerononmask(img, mask)

    mask.data = mask.data ~= 0;
    mask.data = mask.image2D;
    img.data  = img.image2D;
    img.data(~mask.data,:) = 0;

end


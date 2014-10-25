function img = mri_Smooth3DMasked(img, mask, fwhm, mlimit, verbose)

%	function img = mri_Smooth3DMasked(img, mask, fwhm, mlimit, verbose)
%
%	Function for smoothing that takes into account only the voxels
%	within a specified mask.
%
%   Input:
%       mask    - the mask to use for limiting smoothing (gmrimage or filename)
%       fwhm    - size of smoothing in voxels
%       mlimit  - whether to limit the output to mask (true, same for the same as mask, gmrimage or filename)
%       verbose - to be talkative or not
%
%	Grega Repovs 2010-11-16
%   Modified by Grega Rrepovs 2010-12-01
%   Further update by Grega Repovs 2014-08-15

% ---------  basic settings

rmasked = false;
zeroed  = false;

if nargin < 5 || isempty(verbose), verbose = false; end
if nargin < 4 || isempty(mlimit),  mlimit  = true;  end
if nargin < 3, fhwm   = []; end
if nargin < 2, mask   = []; end

if isempty(mask)
    if img.masked
        mask = img.mask;
        img = img.unmaskimg();
        rmasked = true;
        zeroed  = true;
    else
        error('\nERROR: No mask was provided as input to mri_Smooth3DMasked!\n');
    end
end

% -------- set up mask and mlimit

mask = createImage(img, mask);

if isa(mlimit, 'logical')
    if mlimit
        dmask = mask;
    end
elseif isa(mlimit, 'char')
    if strcmp(mlimit, 'false')
        mlimit = false;
    elseif strcmp(mlimit, 'true')
        dmask  = mask;
        mlimit = true;
    elseif strcmp(mlimit, 'same')
        dmask = mask;
        mlimit = true;
    else
        dmask  = createImage(img, mlimit);
        mlimit = true;
    end
else
    dmask  = createImage(img, mlimit);
    mlimit = true;
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
    img = zerononmask(img, dmask);
    [smask dmask] = zerononmask(smask, dmask);
    smask = repmat(smask.data(dmask.data,1), 1, img.frames);
    img.data(dmask.data,:) = img.data(dmask.data,:) ./ smask;
else
    if verbose, fprintf('... normalizing to mask '); end
    img.data = img.image2D;
    smask = repmat(smask.image2D, 1, img.frames);
    img.data = img.data ./ smask;
end

img.data(~isfinite(img.data)) = 0;

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



function [nimg] = createImage(img, data)

    if ~isa(data, 'gmrimage')
        if isa(data, 'char')
            nimg = gmrimage(data);
        elseif isa(data, 'numeric') || isa(data, 'logical')
            if prod(size(data)) == img.voxels
                nimg = img.zeroframes(1);
                nimg.data = data;
                nimg.data = nimg.image2D;
            else
                error('\nERROR: Matrix does not match image size!\n');
            end
        else
            error('\nERROR: Could not parse data!\n');
        end
    else
        nimg = data;
    end
end



% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

function img = img_smooth_3d_masked(img, mask, fwhm, mlimit, verbose, ftype, ksize)

%function img = img_smooth_3d_masked(img, mask, fwhm, mlimit, verbose, ftype, ksize)
%
%   Function for smoothing that takes into account only the voxels within a
%   specified mask.
%
%   INPUTS
%   ======
%
%   --img       nimage object with (isometric) volume data to be smoothed.
%   --mask      The mask to use for limiting smoothing (nimage or a filename of 
%               a mask).
%   --fwhm      Size of smoothing in voxels (Full width at half maximum).
%   --mlimit    Whether to limit the output to mask. Options are:
%
%               - 'true' or 'same' ... Use the same mask as for smoothing.
%               - nimage object    ... Use the image in the nimage object as a 
%                 final mask.
%               - filename         ... Use the image in the filename as the 
%                 final mask.
%
%   --verbose   to be talkative or not [false]
%   --ftype     Type of smoothing filter, 'gaussian' or 'box'. []
%   --ksize     Size of the smoothing kernel. []
%
%   OUTPUT
%   ======
%
%   img
%       A smoothed image.
%
%   USE
%   ===
%
%   The function is used when one wants to run a 3D smoothing on volume data,
%   but limit the smoothing only to the volume specified in the mask. The mask
%   might specify a specific brain structure, or all the gray matter. The final
%   image will only take into account the signal from within the specified mask.
%
%   The signal within the mask can be smoothed outside of the mask. That signal
%   will still consist only of signal within the mask, it will however be
%   smudged outside of the mask. To limit the final image, specify 'mlimit'
%   argument to either 'true'/'same', which will limit the results to the mask
%   used to define the signal, or another mask that specifies the desired final
%   extent of the image.
%
%   A common use scenario might be when one wants to compute a smoothed image of
%   the gray matter signal, but because the signal will be used in a second
%   level analysis, one would let the signal be smoothed out to cover all the
%   voxels in the desired atlas space.
%
%   EXAMPLE
%   =======
%
%   ::
%   
%       smoothed = img_smooth_3d_masked(subjectMask, 3, atlasMask);
%

% ---------  basic settings

rmasked = false;
zeroed  = false;

if nargin < 7                      ksize   = [];    end
if nargin < 6                      ftype   = [];    end
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
        error('\nERROR: No mask was provided as input to img_smooth_3d_masked!\n');
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

img = img.img_smooth_3d(fwhm, verbose);
smask = mask.img_smooth_3d(fwhm, verbose);


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

    if ~isa(data, 'nimage')
        if isa(data, 'char')
            nimg = nimage(data);
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



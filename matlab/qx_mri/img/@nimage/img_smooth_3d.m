function img = img_smooth_3d(img, fwhm, verbose, ftype, ksize)

%``function img = img_smooth_3d(img, fwhm, verbose, ftype, ksize)``
%
%   Does 3D gaussian smoothing of the gmri image.
%
%   INPUTS
%	======
%
%   --img     	A nimage object with data in volume representation.
%   --fwhm    	Full Width at Half Maximum in voxels
%   --verbose 	Whether to report the progress. [false]
%   --ftype   	Type of smoothing filter, 'gaussian' or 'box'. ['gaussian']
%   --ksize   	Size of the smoothing kernel. [7]
%
%   OUTPUT
%	======
%
%   img
%		Image with data smoothed.
%
%   USE
%	===
%
%   The method enables smoothing of (isometric) volume MR data. The smoothing is
%   specified in voxels. The default smoothing kernel is 'gaussian' with kernel
%   size 7. The function checks for the availability of smooth3f function, which
%   speeds up the computation about 4-fold. If not present, it uses the built in
%   smooth3 function.
%
%   smooth3f and the supporting functions can be found at:
%   `<https://github.com/VincentToups/matlab-utils/tree/master/chronux/spikesort/utility>`_
%
%   EXAMPLE
%	=======
%
%	::
%
%   	smooth = img.img_smooth_3d(3, true);
%

if nargin < 5 || isempty(ksize),   ksize   = 7;          end
if nargin < 4 || isempty(ftype),   ftype   = 'gaussian'; end
if nargin < 3 || isempty(verbose), verbose = false;      end


ksd = fwhm/(2*sqrt(2*log(2)));

img.data = img.image4D;
data = single(img.data);

if verbose, fprintf('Smoothing frame     ');, end
for n = 1:img.frames
	if verbose, fprintf('\b\b\b\b%4d',n);, end
    if exist('smooth3f')
        data(:,:,:,n) = smooth3f(data(:,:,:,n), ftype, ksize, ksd);
    else
        data(:,:,:,n) = smooth3(data(:,:,:,n), ftype, ksize, ksd);
    end
end
if verbose, fprintf('\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b                    \b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b');, end
img.data = single(data);


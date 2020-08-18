function [obj] = img_ComputeABCor(obj, smask, tmask, verbose)

%``function [obj] = img_ComputeABCor(obj, smask, tmask, verbose)``
%
%	Compute correlation between each source and target voxels and returns a
%	correlational image.
%
%   INPUTS
%	======
%
%	--obj     	nimage data object.
%   --smask   	Mask of source voxels. It can be a gmriimage file or a matrix.
%   --tmask   	Mask of target voxels. It can be a gmriimage file or a matrix.
%   --verbose 	should it talk a lot [no]
%
%   OUTPUT
%	======
%
%   obj
%		A resulting nimage data object.
%
%   USE
%	===
%
%   The method enables computing correlations betweeen specific sets of source
%   and target voxels from the same timeseries image. The resulting image holds
%   correlations of each target voxel with each source voxel. Specifically, the
%   first frame of the resulting image will hold correlations of each target
%   voxel with the first source voxel, the second image will hold correlations
%   of each target voxels with the second source voxel and so on.
%
%   Each mask can be provided either as a row vector the number of voxels in the
%   image coding the voxels to use with true or more than 0, or as a nimage
%   object with image data specifying the same.
%
%   EXAMPLE USE
%	===========
%
%	::
%
%   	img = img.img_ComputeABCor(roiAimage, roiBimage);
%

%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%
%	2010-08-08 Grega Repovs
%			   Initial version.
%   2016-11-25 Grega Repovs
%			   Updated documentation.
%

if nargin < 4
    verbose = false;
    if nargin < 3;
        error('ERROR: Both mask for source and target voxels needs to be provided!');
    end
end


% ---- prepare data

if verbose, fprintf('\nComputing A*B correlation'), end
if verbose, fprintf('\n... setting up data'), end

jmask = smask + tmask;

if ~obj.correlized
    if ~obj.masked
        obj = obj.maskimg(jmask);
    end
    obj = obj.correlize;
end

obj = obj.unmaskimg();
src = obj.maskimg(smask);
obj = obj.maskimg(tmask);

% ---- do the deed

if verbose, fprintf('\n... computing'), end

obj.data = obj.image2D * src.image2D';
obj.frames = src.voxels;

if verbose, fprintf('\n... done!\n'), end


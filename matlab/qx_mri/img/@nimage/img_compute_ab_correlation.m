function [obj] = img_compute_ab_correlation(obj, smask, tmask, verbose)

%``img_compute_ab_correlation(obj, smask, tmask, verbose)``
%
%   Computes correlation between each source and target voxels and returns a
%   correlational image.
%
%   Parameters
%       --obj (nimage object)
%           Image on which the correlations should be completed.
%       --smask (nimage object or an array)
%           Mask of source voxels. If nimage, then the first volume will be used
%           as a mask. If an array the size of the image volume, it will be used
%           as a mask. If a shorter numeric array, it will be used as a vector 
%           of indices that define an ROI. The representation has to be the same
%           as for tmask.
%       --tmask (nimage object or an array)
%           Mask of target voxels. The same applies as for smask
%       --verbose (boolean, default 'true)
%           Whether to print out the progress of computations.
%
%   Outputs:
%       obj
%           A resulting nimage object.
%
%   Notes:
%       The method enables computing correlations betweeen specific sets of 
%       source and target voxels from the same timeseries image. The resulting 
%       image holds correlations of each target voxel with each source voxel. 
%       Specifically, the first frame of the resulting image will hold 
%       correlations of each target voxel with the first source voxel, the 
%       second image will hold correlations of each target voxels with the 
%       second source voxel and so on.
%
%       Masks can be provided as nimage objects in which all the nonzero voxels
%       in the first volume will define the ROI, as a matrix of the same, or as
%       an array of indices of voxels that form a ROI.
%
%   Examples:
%
%       img = img.img_compute_ab_correlation(roiAimage, roiBimage);
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 4 || isempty(verbose), verbose = false; end
if nargin < 3, error('ERROR: Both mask for source and target voxels needs to be provided!'), end

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


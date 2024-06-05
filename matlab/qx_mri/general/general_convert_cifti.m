function [] = general_convert_cifti(fin, fout, output_format, atlas, parcel_method, verbose)

%``general_find_peaks(fin, fout, output_format, parcel_img, parcel_method, verbose)``
%
%   Performs smoothing using img_smooth() method and uses img_find_peaks method
%   to define peak ROI using a watershed algorithm to grow regions from peaks.
%
%   Parameters:
%       --fin (str):
%           The input cifti file path to be converted.
%
%       --fout (str):
%           Output cifti file path.
%
%       --output_format (str):
%           The desired output format:
%
%           - 'dense'      ... dense cifti image
%           - 'parcellated ... parcellated cifti image
%           - 'label'      ... label cifti image
%
%       --atlas (str, default ''):
%           The parcellated atlas image.
%           Only required for dense to parcellated conversion.
%
%       --parcel_method (str, default 'mean'):
%           The parcellation method:
%
%           - 'mean'      ... average value of the ROI
%           - 'median'    ... median value across the ROI
%	        - 'max'       ... maximum value across the ROI
%	        - 'min'       ... minimum value across the ROI
%           - 'pca'       ... first eigenvariate of the ROI
%           - 'threshold' ... average of all voxels above threshold
%           - 'maxn'      ... average of highest n voxels
%           - 'weighted'  ... weighted average across ROI voxels
%           - 'all'       ... all voxels within a ROI 
%
%       --verbose (bool, default false):
%           Whether to be verbose.
%
%   Output files:
%       The script saves the resulting converted file under the specified filename.
%
%   Notes:
%       The function is a wrapper to the `nimage.img_convert_cifti` method and
%       is used to convert cifti files from between dense, parcellated and
%       label formats. Please see the method documentation for specifics about
%       the parameters.
%
%   Examples:
%       Dense to parcellated conversion:
%           To convert a dtseries image to a parcellated ptseries object using
%           a dlabel atlas with the defined parcels use::
%
%               qunex general_convert_cifti \
%                   --fin='bold.dtseries.nii' \
%                   --fout='bold.ptseries.nii' \
%                   --output_format='parcellated' \
%                   --atlas='atlas.dlabel.nii' \
%                   --parcel_method='mean' \
%                   --verbose=1
%
%       Parcellated to dense conversion:
%           To convert (expand) a ptseries image to a dtseries object use::
%
%               qunex general_convert_cifti \
%                   --fin='bold.ptseries.nii' \
%                   --fout='bold.dtseries.nii' \
%                   --output_format='dense' \
%                   --verbose=1
%
%       Parcellated to label conversion:
%           To convert a ptseries image to a label image use::
%
%               qunex general_convert_cifti \
%                   --fin='bold.ptseries.nii' \
%                   --fout='bold.label.nii' \
%                   --output_format='label' \
%                   --verbose=1
%
%       Dense to label conversion:
%           To convert a dtseries image to a label image use::
%
%               qunex general_convert_cifti \
%                   --fin='bold.dtseries.nii' \
%                   --fout='bold.label.nii' \
%                   --output_format='label' \
%                   --verbose=1
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 6 || isempty(verbose),       verbose = false;        end
if nargin < 5 || isempty(parcel_method), parcel_method = 'mean'; end
if nargin < 4 || isempty(atlas),         atlas = [];             end

% --- read image and call FindPeaks
if verbose, fprintf('\n---> Reading image'); end
img = nimage(fin);

if ~isempty(atlas)
    if verbose, fprintf('\n---> Reading atlas'); end
    atlas = nimage(atlas);
end

% --- convert the image
if verbose, fprintf('\n---> Converting image'); end
img = img.img_convert_cifti(output_format, atlas, parcel_method, {}, verbose);

if verbose, fprintf('\n---> Saving image'); end
img.img_saveimage(fout);

if verbose, fprintf('\n---> Done\n');

end

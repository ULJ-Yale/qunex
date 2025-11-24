function change_voxel_dimensions(x, n)

%``function change_voxel_dimensions(filename, description, v, prepend)``
%
%   Artificially increase voxel dimensions so traditional piplines
%   can work on mouse data.
%
%   INPUTS
%   ======
%   --x    Headername without the .hdr extension.
%   --n    The increase factor.
%   OUTPUT
%   ======
%   
%		Whether the file was found (true or false).
%
%
%   EXAMPLE USE
%   ===========
%  
%   To increase voxels by 10-fold for rsfMRI.hdr use
%
%       change_voxel_dimensions('rsfMRI', 10);
%
%   Authors: Valerio Zerbi and Jure Demsar

% SPDX-FileCopyrightText: 2022 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

% load helper scripts
lib_path = strcat(getenv('QUNEXLIBRARYETC'), '/mice_pipelines/matlab');
addpath(lib_path);

% load header
AAA = load_untouch_header_only([x, '.hdr']);

% get voxel sizes
ValueX = AAA.dime.pixdim(2);
ValueY = AAA.dime.pixdim(3);
ValueZ = AAA.dime.pixdim(4);

% increase voxel sizes
AAA.dime.pixdim(2) = ValueX * n;
AAA.dime.pixdim(3) = ValueY * n;
AAA.dime.pixdim(4) = ValueZ * n;

% save
save_untouch_header_only(AAA, [x, '.hdr'])

end

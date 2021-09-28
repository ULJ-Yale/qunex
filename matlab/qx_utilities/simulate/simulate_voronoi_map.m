function [m] = simulate_voronoi_map(w,h,p)

%``function [m] = simulate_voronoi_map(w,h,p)``
%   
%   Function for creating w by h Voronoi bitmap with points p.
%
%	INPUTS
%	======
%
%	--w
%	--h
%	--p
%
%	OUTPUT
%	======
%
%	m
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 3
    error('ERROR: VoronoiMap needs three arguments (w, h, p) to create a map!');
end

% ---> prepare measuring sticks

npoints = size(p,1);

xr = 1:w;
yr = [1:h]';
xr = repmat(xr, [1, 1, npoints]);
yr = repmat(yr, [1, 1, npoints]);

% ---> prepare location data

xp = repmat(reshape(p(:,1),[1,1,npoints]),[1, w, 1]);
yp = repmat(reshape(p(:,2),[1,1,npoints]),[h, 1, 1]);

% ---> compute distances

xd = (xr-xp).^2;
yd = (yr-yp).^2;
d  = sqrt(repmat(xd,[h,1,1])+repmat(yd,[1,w,1]));
[c, m] = min(d, [], 3);


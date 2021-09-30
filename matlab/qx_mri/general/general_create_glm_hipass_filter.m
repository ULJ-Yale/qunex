function F = general_create_glm_hipass_filter(nframes,levels)

%``function F = general_create_glm_hipass_filter(nframes,levels)`
%
%   Creates a high-pass filtering matrix by creating a pair of regressors with
%   0.25 phase difference for 1:levels number of full cycles over nframes.
%
%	INPUTS
%	======
%
%	--nframes
%	--levels
%
%	OUTPUT
%	======
%
%	F
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

F = zeros(nframes, levels);

base = (0:nframes-1)'/(nframes-1);

F = [];
for n = 1:levels
    F = [F sin(base*2*pi*n)];
    F = [F sin(base*2*pi*n+0.25*2*pi)];
end



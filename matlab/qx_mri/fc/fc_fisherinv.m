function [r] = fc_fisherinv(fz)

%``fc_fisherinv(fz)``
%
%    Converts Fisher z values to Pearson correlations.
%
%    Parameters:
%       --fz (float):
%           Fisher z values.
%
%    Returns:
%       r
%           Pearson correlations.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

t = exp(fz*2);
r = (t-1)./(t+1);

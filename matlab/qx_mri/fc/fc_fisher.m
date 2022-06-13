function [Fz] = fc_fisher(r)

%``function [Fz] = fc_fisher(r)``
%
%    Converts Pearson correlations to Fisher z values. As a pre-pass, to avoid
%    infinite Fisher z values, it multiplies all correlations with 0.9999999.
%
%    Parameters:
%       --f (float):
%           Pearson's correlation coefficients.
%
%    Returns:
%       Fz
%           Fisher Z values.
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

r = double(r);
r = r * 0.9999999;
Fz = atanh(r);
Fz = single(Fz);
if ~isreal(Fz)
    Fz = real(Fz);
end

function [y] = changeform(x, d)

%    ``function [a] = changeform(b, d)``
%
%   Function that converts vector to matrix or the other way arround depending 
%   on input.
%
%   INPUTS
%    ======
%
%   --x     input vector or matrix
%   --d     optional value for diagonal (default 1)
%
%   OUTPUT
%    ======
%
%   y
%        output vector or matrix
%

% SPDX-FileCopyrightText: 2021 QuNex development team <https://qunex.yale.edu/>
%
% SPDX-License-Identifier: GPL-3.0-or-later

if nargin < 2
    d = 1;
end

if min(size(x)) == 1;
    y = squareform(x);
    y(eye(size(y,1))==1) = d;
else
    x(eye(size(x,1))==1) = 0;
    y = squareform(x);
end


    
    
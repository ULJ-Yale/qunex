function [y] = changeform(x, d)

%	function [a] = changeform(b, d)
%	
%   Function that converts vector to matrix or the other way arround depending on input.
%
%   Inputs
%       - x     input vector or matrix
%       - d     optional value for diagonal (default 1)
%
%   Outputs
%       - y     output vector or matrix
%	
% 	Created by Grega Repovš on 2010-10-09.
%

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


    
    
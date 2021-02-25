function [Fz] = fc_fisher(r)

%``function [Fz] = fc_fisher(r)``
%
%	Converts Pearson correlations to Fisher z values. As a pre-pass, to avoid
%	infinite Fisher z values, it multiplies all correlations with 0.9999999.
%
%	INPUT
%	=====
%
%	--f 		Pearson's correlation coefficients.
%
%	OUTPUT
%	======
%	
%	Fz
%		Fisher Z values
%

%   ~~~~~~~~~~~~~~~~~~
%
%	Changelog
% 
%   2007-06-23 Grega Repovs
%			   Initial version.	
%	2017-03-19 Grega Repovs
%			   Updated documentation.


r = double(r);
r = r * 0.9999999;
Fz = atanh(r);
Fz = single(Fz);
if ~isreal(Fz)
    Fz = real(Fz);
end

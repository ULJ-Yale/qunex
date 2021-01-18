function [r] = fc_fisherinv(fz)

%``function [r] = fc_fisherinv(fz)`
%
%	Converts Fisher z values to pearson correlations.
%
%	INPUT
%	=====
%
%	--fz 	Fisher z values
%
%	OUTPUT
%	======
%
%	r 	
%		Pearson correlations
%

%	~~~~~~~~~~~~~~~~~~
%
%	Changelog
% 
%   2007-06-23 Grega Repovs
%			   Initial version.	
%	2017-03-19 Grega Repovs
%			   Updated documentation.

t = exp(fz*2);
r = (t-1)./(t+1);


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

t = exp(fz*2);
r = (t-1)./(t+1);

function [r] = fc_FisherInv(fz)

%function [r] = fc_FisherInv(fz)
%
%  Converts Fisher z values to pearson correlations.
%
%  INPUT
%       fz - Fisher z values
%
%  OUTPUT
%       r  - Pearson correlations
%
%  ---
%  Written by Grega Repovs, 2007-06-23.
%
%  Changelog
%  2017-03-19 Grega Repovs - updated documentation

t = exp(fz*2);
r = (t-1)./(t+1);



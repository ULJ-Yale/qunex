function [Fz] = fc_Fisher(r)

%function [Fz] = fc_Fisher(r)
%
%  Converts Pearson correlations to Fisher z values. As a pre-pass, to avoid
%  infinite Fisher z values, it multiplies all correlations with 0.9999999.
%
%  INPUT
%       f  - Peason's correlation coefficients.
%
%  OUTPUT
%       Fz - Fisher Z values
%
%  ---
%  Written by Grega Repovs, 2007-06-23.
%
%  Changelog
%  2017-03-19 Grega Repovs - updated documentation


r = double(r);
r = r * 0.9999999;
Fz = atanh(r);
Fz = single(Fz);
if ~isreal(Fz)
    Fz = real(Fz);
end



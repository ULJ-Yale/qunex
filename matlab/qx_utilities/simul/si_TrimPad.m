function [ts] = si_TrimPad(ts,l)

%``function [ts] = si_TrimPad(ts,l)``
%	
%   Function that trimms or pads timeseries to specified length.
%
%   INPUTS
%	======
%
%   --ts	timeseries (timepoints x voxels)
%   --l  	desired length
%
%   OUTPUT
%	======
%
%   ts
%		trimmed / padded timeseries
%	

%   ~~~~~~~~~~~~~~~~~~
%
%   Changelog
%	
%	2010-10-09 Grega Repovs
%			   Initial version.
%	

if nargin < 2
    error('ERROR: not enough parameters to trim or pad the timeseries!');
end

tlen = size(ts,1);

if tlen > l
    ts = ts(1:l,:);
elseif tlen < l
    ts = [ts; zeros(l-tlen, size(ts,2))];
end


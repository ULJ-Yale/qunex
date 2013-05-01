function [ts] = si_TrimPad(ts,l)

%	function [ts] = si_TrimPad(ts,l)
%	
%   Function that trimms or pads timeseries to specified length
%
%   Inputs
%       - ts:   timeseries (timepoints x voxels)
%       - l:    desired length
%
%   Outputs
%       - ts    trimmed / padded timeseries
%	
% 	Created by Grega Repovš on 2010-10-09.
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

